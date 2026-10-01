/*
FOUNDATION LEVEL 11 - CAPSTONE: one complete, secured SOAP service
======================================================================
Nothing new here. Every idea from levels 00-10 - the envelope, headers, typed
parameters, nested responses, namespaces, Faults with detail, the HTTP status
convention, middleware, authentication and authorization - combined into one
small service with three operations and one deliberate access policy:

	GetStatus     public          anyone, no credentials at all
	CreateOrder   authenticated   any recognized caller (level 09)
	CancelOrder   admin only      role check on top (level 10)

This is deliberately the same shape as ../../labs/golang/02_soap_server_net_http:
once this feels easy, the labs (a real generated WSDL, real WS-Security
digests, SOAP 1.2, mustUnderstand, a JSON gateway over a legacy service) are
the very next step, not a jump.

You will learn
  - how ten small lessons compose into one real-looking, real-secured service
  - the deliberate order of a SOAP request's life: parse -> read headers ->
    authenticate -> authorize -> validate -> act -> build response
  - that a per-operation policy table beats an if inside every operation
  - that every error path in a SOAP service ends in exactly one place: a Fault

Run it   go run ./SOAP/Foundation/golang/11_complete_soap_service
*/
package main

import (
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsWSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
	nsTNS  = "http://foundation.example.com/orders"
)

type identity struct {
	User string
	Role string
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

// THE POLICY, in one readable place. nil = public. Otherwise: the roles
// allowed to call the operation. A key missing from this map entirely is an
// unknown operation, not a public one - see withAuthentication/withAuthorization.
var policy = map[string][]string{
	"GetStatus":   nil,
	"CreateOrder": {"viewer", "admin"},
	"CancelOrder": {"admin"},
}

type order struct {
	SKU      string
	Quantity int
	Total    float64
	State    string
	Owner    string
}

var (
	orders    = map[string]*order{}
	startedAt = time.Now()
)

type request struct {
	envelope  requestEnvelope
	operation string
	caller    *identity
}

type dispatcher func(*request) (int, []byte)

type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  struct {
		Password string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Security>UsernameToken>Password"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body struct {
		Operation struct {
			XMLName   xml.Name
			SKU       string `xml:"http://foundation.example.com/orders sku"`
			Quantity  string `xml:"http://foundation.example.com/orders quantity"`
			UnitPrice string `xml:"http://foundation.example.com/orders unitPrice"`
			OrderID   string `xml:"http://foundation.example.com/orders orderId"`
		} `xml:",any"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// ---- responses ----
type statusResponse struct {
	XMLName    xml.Name `xml:"http://foundation.example.com/orders GetStatusResponse"`
	Status     string   `xml:"http://foundation.example.com/orders status"`
	OrderCount int      `xml:"http://foundation.example.com/orders orderCount"`
	UptimeSecs int64    `xml:"http://foundation.example.com/orders uptimeSeconds"`
}

type orderResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/orders CreateOrderResponse"`
	Order   struct {
		ID    string `xml:"id,attr"`
		State string `xml:"http://foundation.example.com/orders state"`
		Owner string `xml:"http://foundation.example.com/orders owner"`
		Total string `xml:"http://foundation.example.com/orders total"`
	} `xml:"http://foundation.example.com/orders order"`
}

type cancelResponse struct {
	XMLName     xml.Name `xml:"http://foundation.example.com/orders CancelOrderResponse"`
	OrderID     string   `xml:"http://foundation.example.com/orders orderId"`
	State       string   `xml:"http://foundation.example.com/orders state"`
	CancelledBy string   `xml:"http://foundation.example.com/orders cancelledBy"`
}

type soapFault struct {
	XMLName xml.Name     `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string       `xml:"faultcode"`
	String  string       `xml:"faultstring"`
	Detail  *faultDetail `xml:"detail,omitempty"`
}

type faultDetail struct {
	Named namedDetail `xml:",any"`
}

type namedDetail struct {
	XMLName xml.Name
	Fields  []detailField `xml:",any"`
}

type detailField struct {
	XMLName xml.Name
	Value   string `xml:",chardata"`
}

type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Status *statusResponse
		Order  *orderResponse
		Cancel *cancelResponse
		Fault  *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func marshalEnvelope(env responseEnvelope) []byte {
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

func faultResponse(code, message, detailName string, fields ...string) (int, []byte) {
	f := &soapFault{Code: code, String: message}
	if detailName != "" {
		named := namedDetail{XMLName: xml.Name{Space: nsTNS, Local: detailName}}
		for i := 0; i+1 < len(fields); i += 2 {
			named.Fields = append(named.Fields, detailField{
				XMLName: xml.Name{Space: nsTNS, Local: fields[i]},
				Value:   fields[i+1],
			})
		}
		f.Detail = &faultDetail{Named: named}
	}
	var env responseEnvelope
	env.Body.Fault = f
	return http.StatusInternalServerError, marshalEnvelope(env)
}

func required(value, name string) (string, bool) {
	if value == "" {
		return "", false
	}
	return value, true
}

// ---------------------------------------------------------------- operations --
func getStatus() (int, []byte) {
	var env responseEnvelope
	env.Body.Status = &statusResponse{
		Status:     "UP",
		OrderCount: len(orders),
		UptimeSecs: int64(time.Since(startedAt).Seconds()),
	}
	return http.StatusOK, marshalEnvelope(env)
}

func createOrder(r *request) (int, []byte) {
	op := r.envelope.Body.Operation
	sku, ok := required(op.SKU, "sku")
	if !ok {
		return faultResponse("soap:Client", "<sku> is required", "MissingElement", "element", "sku")
	}
	if _, ok := required(op.Quantity, "quantity"); !ok {
		return faultResponse("soap:Client", "<quantity> is required", "MissingElement", "element", "quantity")
	}
	quantity, err := strconv.Atoi(op.Quantity)
	if err != nil || quantity < 1 {
		return faultResponse("soap:Client", "quantity must be an integer of at least 1",
			"InvalidValue", "element", "quantity", "got", op.Quantity)
	}
	unitPriceText := op.UnitPrice
	if unitPriceText == "" {
		unitPriceText = "10.00"
	}
	unitPrice, err := strconv.ParseFloat(unitPriceText, 64)
	if err != nil {
		return faultResponse("soap:Client", "unitPrice must be a decimal", "InvalidValue", "element", "unitPrice")
	}

	orderID := fmt.Sprintf("ORD-%04d", len(orders)+1)
	o := &order{SKU: sku, Quantity: quantity, Total: unitPrice * float64(quantity), State: "OPEN", Owner: r.caller.User}
	orders[orderID] = o

	var env responseEnvelope
	resp := &orderResponse{}
	resp.Order.ID = orderID
	resp.Order.State = o.State
	resp.Order.Owner = o.Owner
	resp.Order.Total = fmt.Sprintf("%.2f", o.Total)
	env.Body.Order = resp
	return http.StatusOK, marshalEnvelope(env)
}

func cancelOrder(r *request) (int, []byte) {
	op := r.envelope.Body.Operation
	orderID, ok := required(op.OrderID, "orderId")
	if !ok {
		return faultResponse("soap:Client", "<orderId> is required", "MissingElement", "element", "orderId")
	}
	o, found := orders[orderID]
	if !found {
		return faultResponse("soap:Client", "no such order: "+orderID, "OrderNotFound", "orderId", orderID)
	}
	if o.State == "CANCELLED" {
		return faultResponse("soap:Client", "order "+orderID+" is already cancelled",
			"IllegalState", "orderId", orderID, "state", o.State)
	}

	o.State = "CANCELLED"
	var env responseEnvelope
	env.Body.Cancel = &cancelResponse{OrderID: orderID, State: o.State, CancelledBy: r.caller.User}
	return http.StatusOK, marshalEnvelope(env)
}

func dispatch(r *request) (int, []byte) {
	switch r.operation {
	case "GetStatus":
		return getStatus()
	case "CreateOrder":
		return createOrder(r)
	case "CancelOrder":
		return cancelOrder(r)
	}
	return faultResponse("soap:Client", "unknown operation "+r.operation, "UnknownOperation", "operation", r.operation)
}

// -------------------------------------------------------------- middleware --
func withLogging(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		started := time.Now()
		status, out := next(r)
		caller := "-"
		if r.caller != nil {
			caller = r.caller.User
		}
		fmt.Printf("  [log] %-12s caller=%-8s -> HTTP %d (%.2fms)\n",
			r.operation, caller, status, time.Since(started).Seconds()*1000)
		return status, out
	}
}

func withRecovery(next dispatcher) dispatcher {
	return func(r *request) (status int, out []byte) {
		defer func() {
			if rec := recover(); rec != nil {
				fmt.Printf("  [recovery] bug in %s: %v\n", r.operation, rec)
				status, out = faultResponse("soap:Server", "internal error", "")
			}
		}()
		return next(r)
	}
}

// ---- who is this? (level 09, unchanged) ----
func withAuthentication(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		allowed, known := policy[r.operation]
		if known && allowed == nil {
			return next(r) // a public operation, no credential needed
		}
		caller, ok := tokens[r.envelope.Header.Password]
		if r.envelope.Header.Password == "" || !ok {
			return faultResponse("soap:Client", "missing or invalid credentials", "Unauthenticated")
		}
		r.caller = &caller
		return next(r)
	}
}

// ---- what may this caller do? (level 10, unchanged) ----
func withAuthorization(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		allowed, known := policy[r.operation]
		if !known || allowed == nil {
			return next(r) // unknown op falls through to dispatch's UnknownOperation fault
		}
		permitted := false
		for _, role := range allowed {
			if r.caller.Role == role {
				permitted = true
			}
		}
		if !permitted {
			roles := ""
			for i, role := range allowed {
				if i > 0 {
					roles += ","
				}
				roles += role
			}
			return faultResponse("soap:Client",
				fmt.Sprintf("role %q may not call %s", r.caller.Role, r.operation),
				"Forbidden", "requiredRole", roles)
		}
		return next(r)
	}
}

// Outside in, and the order IS the design:
//
//	log everything -> convert any panic to a Fault -> identify -> permit -> act
var pipeline = withLogging(withRecovery(withAuthentication(withAuthorization(dispatch))))

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/orders" {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	raw, _ := io.ReadAll(r.Body)

	var parsed requestEnvelope
	var status int
	var out []byte
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		status, out = faultResponse("soap:Client", "malformed SOAP request", "")
	} else {
		status, out = pipeline(&request{envelope: parsed, operation: parsed.Body.Operation.XMLName.Local})
	}

	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

// -------------------------------------------------------------------- demo --
func call(url, operation, token, params string) (int, responseEnvelope) {
	header := ""
	if token != "" {
		header = fmt.Sprintf(
			`<wsse:Security xmlns:wsse="%s"><wsse:UsernameToken>`+
				`<wsse:Password>%s</wsse:Password></wsse:UsernameToken></wsse:Security>`, nsWSSE, token)
	}
	body := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header>%s</soap:Header><soap:Body>`+
			`<t:%s xmlns:t="%s">%s</t:%s></soap:Body></soap:Envelope>`,
		nsSOAP, header, operation, nsTNS, params, operation)

	res, err := http.Post(url, "text/xml; charset=utf-8", strings.NewReader(body))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	var parsed responseEnvelope
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}
	return res.StatusCode, parsed
}

func detailOf(env responseEnvelope) string {
	if env.Body.Fault == nil || env.Body.Fault.Detail == nil {
		return ""
	}
	return env.Body.Fault.Detail.Named.XMLName.Local
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/orders", handler)
	go http.Serve(listener, mux)
	url := "http://" + listener.Addr().String() + "/orders"

	fmt.Println("== 1. GetStatus is public ==")
	status, env := call(url, "GetStatus", "", "")
	fmt.Printf("  -> %d status=%s\n", status, env.Body.Status.Status)
	if status != http.StatusOK {
		panic("FAILED")
	}

	fmt.Println("\n== 2. CreateOrder needs a credential ==")
	status, env = call(url, "CreateOrder", "", "<t:sku>WIDGET-1</t:sku><t:quantity>3</t:quantity>")
	fmt.Printf("  anonymous        -> %d <%s>\n", status, detailOf(env))
	if detailOf(env) != "Unauthenticated" {
		panic("FAILED")
	}

	status, env = call(url, "CreateOrder", "bob-token",
		"<t:sku>WIDGET-1</t:sku><t:quantity>3</t:quantity><t:unitPrice>9.99</t:unitPrice>")
	fmt.Printf("  bob (viewer)     -> %d id=%s owner=%s total=%s\n",
		status, env.Body.Order.Order.ID, env.Body.Order.Order.Owner, env.Body.Order.Order.Total)
	if status != http.StatusOK || env.Body.Order.Order.Total != "29.97" {
		panic("FAILED")
	}
	orderID := env.Body.Order.Order.ID

	fmt.Println("\n== 3. validation still applies to an authenticated caller ==")
	for _, tc := range []struct{ label, params, expected string }{
		{"missing sku", "<t:quantity>1</t:quantity>", "MissingElement"},
		{"quantity='many'", "<t:sku>X</t:sku><t:quantity>many</t:quantity>", "InvalidValue"},
		{"quantity=0", "<t:sku>X</t:sku><t:quantity>0</t:quantity>", "InvalidValue"},
	} {
		status, env = call(url, "CreateOrder", "bob-token", tc.params)
		fmt.Printf("  %-16s -> %d <%s> %q\n", tc.label, status, detailOf(env), env.Body.Fault.String)
		if detailOf(env) != tc.expected {
			panic("FAILED")
		}
	}

	fmt.Println("\n== 4. CancelOrder is admin only ==")
	status, env = call(url, "CancelOrder", "bob-token", "<t:orderId>"+orderID+"</t:orderId>")
	fmt.Printf("  bob (viewer)     -> %d <%s>\n", status, detailOf(env))
	if detailOf(env) != "Forbidden" {
		panic("FAILED")
	}
	if orders[orderID].State != "OPEN" {
		panic("FAILED: a refused call must change nothing")
	}

	status, env = call(url, "CancelOrder", "alice-token", "<t:orderId>"+orderID+"</t:orderId>")
	fmt.Printf("  alice (admin)    -> %d state=%s by=%s\n",
		status, env.Body.Cancel.State, env.Body.Cancel.CancelledBy)
	if status != http.StatusOK || orders[orderID].State != "CANCELLED" {
		panic("FAILED")
	}

	fmt.Println("\n== 5. business rules, unknown ids, unknown operations ==")
	status, env = call(url, "CancelOrder", "alice-token", "<t:orderId>"+orderID+"</t:orderId>")
	fmt.Printf("  cancel twice     -> %d <%s>\n", status, detailOf(env))
	if detailOf(env) != "IllegalState" {
		panic("FAILED")
	}

	status, env = call(url, "CancelOrder", "alice-token", "<t:orderId>ORD-9999</t:orderId>")
	fmt.Printf("  unknown order    -> %d <%s>\n", status, detailOf(env))
	if detailOf(env) != "OrderNotFound" {
		panic("FAILED")
	}

	status, env = call(url, "DropDatabase", "alice-token", "")
	fmt.Printf("  unknown operation-> %d <%s>\n", status, detailOf(env))
	if detailOf(env) != "UnknownOperation" {
		panic("FAILED")
	}

	fmt.Println("\n== 6. and the public operation still works, after all that ==")
	status, env = call(url, "GetStatus", "", "")
	fmt.Printf("  -> %d orderCount=%d\n", status, env.Body.Status.OrderCount)
	if status != http.StatusOK || env.Body.Status.OrderCount != 1 {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
