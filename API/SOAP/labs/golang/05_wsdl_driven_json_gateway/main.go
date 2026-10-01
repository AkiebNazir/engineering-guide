/*
LAB 05 (advanced) - An anti-corruption gateway: expose a legacy SOAP service as a clean JSON API
===============================================================================================
The pattern that keeps SOAP out of the rest of your architecture:

	modern clients --JSON/REST--> [ GATEWAY ] --SOAP/XML--> legacy bank (WSDL)
	                                |  translates requests, responses AND errors
	                                |  owns timeouts, retries, logging, validation

You will learn
  - reading a WSDL at runtime with encoding/xml to DISCOVER: the endpoint address, the operations,
    and the fields of every request/response element (types come from the embedded XML Schema)
  - a GENERIC translation layer - no hand-written code per operation:
    JSON {"fromAccount":"A","amount":"5"}  ->  <Transfer xmlns=...><fromAccount>A</fromAccount>...
    <TransferResponse><status>OK</status></TransferResponse>  ->  JSON {"status":"OK"}
  - validating JSON input against the WSDL-derived schema (missing / unknown fields) before calling
  - keeping DECIMALS as strings in JSON (never float64 for money)
  - fault -> HTTP mapping with RFC 9457 problem+json:
    soap Client fault -> 422 (+ machine-readable detail)   soap Server fault -> 502
    timeout -> 504     backend unreachable -> 503
  - a self-describing GET /api/operations endpoint generated from the WSDL

Run it   go run ./SOAP/labs/golang/05_wsdl_driven_json_gateway
*/
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"time"
)

const nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"

// ============================================================ WSDL discovery ===
type wsdlDoc struct {
	TargetNamespace string `xml:"targetNamespace,attr"`
	Schema          struct {
		Elements []struct {
			Name     string `xml:"name,attr"`
			Sequence []struct {
				Name string `xml:"name,attr"`
				Type string `xml:"type,attr"`
			} `xml:"complexType>sequence>element"`
		} `xml:"element"`
	} `xml:"types>schema"`
	Messages []struct {
		Name string `xml:"name,attr"`
		Part struct {
			Element string `xml:"element,attr"`
		} `xml:"part"`
	} `xml:"message"`
	Operations []struct {
		Name  string `xml:"name,attr"`
		Input struct {
			Message string `xml:"message,attr"`
		} `xml:"input"`
		Output struct {
			Message string `xml:"message,attr"`
		} `xml:"output"`
	} `xml:"portType>operation"`
	Address struct {
		Location string `xml:"location,attr"`
	} `xml:"service>port>address"`
}

type Field struct{ Name, XSDType string }

type Operation struct {
	Name            string  `json:"name"`
	Input           []Field `json:"input"`
	Output          []Field `json:"output"`
	ResponseElement string  `json:"-"`
	Idempotent      bool    `json:"idempotent"`
}

type Contract struct {
	Namespace string
	Endpoint  string
	Ops       map[string]*Operation
}

func local(qname string) string { // "tns:GetBalance" -> "GetBalance"
	if i := strings.LastIndex(qname, ":"); i >= 0 {
		return qname[i+1:]
	}
	return qname
}

func LoadContract(wsdlURL string, idempotent map[string]bool) (*Contract, error) {
	res, err := http.Get(wsdlURL)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	var doc wsdlDoc
	if err := xml.NewDecoder(io.LimitReader(res.Body, 4<<20)).Decode(&doc); err != nil {
		return nil, fmt.Errorf("cannot parse WSDL: %w", err)
	}
	fields := map[string][]Field{}
	for _, e := range doc.Schema.Elements {
		for _, f := range e.Sequence {
			fields[e.Name] = append(fields[e.Name], Field{f.Name, local(f.Type)})
		}
	}
	msgElement := map[string]string{}
	for _, m := range doc.Messages {
		msgElement[m.Name] = local(m.Part.Element)
	}
	c := &Contract{Namespace: doc.TargetNamespace, Endpoint: doc.Address.Location, Ops: map[string]*Operation{}}
	for _, o := range doc.Operations {
		in, out := msgElement[local(o.Input.Message)], msgElement[local(o.Output.Message)]
		c.Ops[o.Name] = &Operation{Name: o.Name, Input: fields[in], Output: fields[out], ResponseElement: out, Idempotent: idempotent[o.Name]}
	}
	return c, nil
}

// =========================================================== the translation ===
type SOAPFault struct{ Code, Message, DetailXML string }

func (f *SOAPFault) Error() string { return f.Code + ": " + f.Message }

func esc(s string) string { var b bytes.Buffer; xml.EscapeText(&b, []byte(s)); return b.String() }

type Gateway struct {
	C      *Contract
	HTTP   *http.Client
	Router *http.ServeMux
}

// toSOAP builds the request XML from JSON using ONLY what the WSDL says.
func (g *Gateway) toSOAP(op *Operation, in map[string]any) (string, error) {
	known := map[string]bool{}
	var inner strings.Builder
	for _, f := range op.Input {
		known[f.Name] = true
		v, ok := in[f.Name]
		if !ok {
			return "", fmt.Errorf("missing field %q", f.Name)
		}
		s := fmt.Sprint(v)
		if n, isNum := v.(json.Number); isNum {
			s = n.String() // keeps 100.25 exactly as written
		}
		fmt.Fprintf(&inner, "<%s>%s</%s>", f.Name, esc(s), f.Name)
	}
	for k := range in {
		if !known[k] {
			return "", fmt.Errorf("unknown field %q", k)
		}
	}
	return fmt.Sprintf(`<soap:Envelope xmlns:soap=%q><soap:Body><%s xmlns=%q>%s</%s></soap:Body></soap:Envelope>`,
		nsSOAP, op.Name, g.C.Namespace, inner.String(), op.Name), nil
}

// fromSOAP walks the response element's children with a token decoder: generic, no per-operation struct.
func (g *Gateway) fromSOAP(op *Operation, raw []byte) (map[string]any, error) {
	d := xml.NewDecoder(bytes.NewReader(raw))
	out := map[string]any{}
	types := map[string]string{}
	for _, f := range op.Output {
		types[f.Name] = f.XSDType
	}
	var fault *SOAPFault
	var current string
	var text strings.Builder
	inDetail := false
	var detail bytes.Buffer
	for {
		tok, err := d.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("unparseable SOAP response: %w", err)
		}
		switch t := tok.(type) {
		case xml.StartElement:
			switch {
			case t.Name.Local == "Fault":
				fault = &SOAPFault{}
			case fault != nil && t.Name.Local == "detail":
				inDetail = true
			case inDetail:
				fmt.Fprintf(&detail, "<%s>", t.Name.Local)
			default:
				current = t.Name.Local
				text.Reset()
			}
		case xml.CharData:
			text.Write(t)
			if inDetail {
				detail.Write(t)
			}
		case xml.EndElement:
			switch {
			case fault != nil && t.Name.Local == "faultcode":
				fault.Code = strings.TrimSpace(text.String())
			case fault != nil && t.Name.Local == "faultstring":
				fault.Message = strings.TrimSpace(text.String())
			case t.Name.Local == "detail":
				inDetail = false
				fault.DetailXML = detail.String()
			case inDetail:
				fmt.Fprintf(&detail, "</%s>", t.Name.Local)
			case fault == nil && types[t.Name.Local] != "":
				v := strings.TrimSpace(text.String())
				switch types[t.Name.Local] {
				case "int", "integer", "long":
					out[current] = json.Number(v)
				case "boolean":
					out[current] = v == "true" || v == "1"
				default: // string AND decimal: decimals stay STRINGS so no precision is lost
					out[current] = v
				}
			}
		}
	}
	if fault != nil {
		return nil, fault
	}
	return out, nil
}

func (g *Gateway) call(ctx context.Context, op *Operation, in map[string]any) (map[string]any, error) {
	body, err := g.toSOAP(op, in)
	if err != nil {
		return nil, &badInput{err.Error()}
	}
	attempts := 1
	if op.Idempotent {
		attempts = 3
	}
	var lastErr error
	for i := 0; i < attempts; i++ {
		req, _ := http.NewRequestWithContext(ctx, "POST", g.C.Endpoint, strings.NewReader(body))
		req.Header.Set("Content-Type", "text/xml; charset=utf-8")
		req.Header.Set("SOAPAction", fmt.Sprintf(`"%s/%s"`, g.C.Namespace, op.Name))
		res, err := g.HTTP.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		raw, _ := io.ReadAll(io.LimitReader(res.Body, 1<<20))
		res.Body.Close()
		out, err := g.fromSOAP(op, raw)
		var f *SOAPFault
		if errors.As(err, &f) && !strings.HasSuffix(strings.ToLower(f.Code), "client") {
			lastErr = err // a Server fault: retry only if idempotent (loop condition)
			continue
		}
		return out, err
	}
	return nil, lastErr
}

type badInput struct{ msg string }

func (b *badInput) Error() string { return b.msg }

// ======================================================= HTTP surface (JSON) ===
func problem(w http.ResponseWriter, status int, title, detail string, extra map[string]any) {
	w.Header().Set("Content-Type", "application/problem+json")
	w.WriteHeader(status)
	p := map[string]any{"type": "about:blank", "title": title, "status": status, "detail": detail}
	for k, v := range extra {
		p[k] = v
	}
	json.NewEncoder(w).Encode(p)
}

func NewGateway(c *Contract, client *http.Client) *Gateway {
	g := &Gateway{C: c, HTTP: client, Router: http.NewServeMux()}
	g.Router.HandleFunc("GET /api/operations", func(w http.ResponseWriter, r *http.Request) {
		names := make([]string, 0, len(c.Ops))
		for n := range c.Ops {
			names = append(names, n)
		}
		sort.Strings(names)
		var ops []*Operation
		for _, n := range names {
			ops = append(ops, c.Ops[n])
		}
		json.NewEncoder(w).Encode(map[string]any{"endpoint": c.Endpoint, "operations": ops})
	})
	g.Router.HandleFunc("POST /api/{operation}", func(w http.ResponseWriter, r *http.Request) {
		op, ok := c.Ops[r.PathValue("operation")]
		if !ok {
			problem(w, 404, "Unknown operation", r.PathValue("operation"), nil)
			return
		}
		dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
		dec.UseNumber()
		var in map[string]any
		if err := dec.Decode(&in); err != nil {
			problem(w, 400, "Invalid JSON", err.Error(), nil)
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 800*time.Millisecond)
		defer cancel()
		out, err := g.call(ctx, op, in)
		var bi *badInput
		var f *SOAPFault
		switch {
		case err == nil:
			json.NewEncoder(w).Encode(out)
		case errors.As(err, &bi):
			problem(w, 400, "Invalid request", bi.msg, nil)
		case errors.As(err, &f) && strings.HasSuffix(strings.ToLower(f.Code), "client"):
			problem(w, 422, "Request rejected by the backend", f.Message, map[string]any{"backend_detail": f.DetailXML})
		case errors.As(err, &f):
			problem(w, 502, "Backend failure", "the legacy service reported an internal error", nil)
		case errors.Is(err, context.DeadlineExceeded):
			problem(w, 504, "Backend timeout", "the legacy service did not answer in time", nil)
		default:
			problem(w, 503, "Backend unavailable", "could not reach the legacy service", nil)
		}
	})
	return g
}

// ===================================================== the legacy backend =====
const legacyWSDL = `<?xml version="1.0"?>
<definitions name="Bank" targetNamespace="http://bank.example.com/ws" xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:tns="http://bank.example.com/ws">
<types><xsd:schema targetNamespace="http://bank.example.com/ws">
 <xsd:element name="GetBalance"><xsd:complexType><xsd:sequence><xsd:element name="accountId" type="xsd:string"/></xsd:sequence></xsd:complexType></xsd:element>
 <xsd:element name="GetBalanceResponse"><xsd:complexType><xsd:sequence><xsd:element name="balance" type="xsd:decimal"/><xsd:element name="currency" type="xsd:string"/></xsd:sequence></xsd:complexType></xsd:element>
 <xsd:element name="Transfer"><xsd:complexType><xsd:sequence><xsd:element name="fromAccount" type="xsd:string"/><xsd:element name="toAccount" type="xsd:string"/><xsd:element name="amount" type="xsd:decimal"/></xsd:sequence></xsd:complexType></xsd:element>
 <xsd:element name="TransferResponse"><xsd:complexType><xsd:sequence><xsd:element name="transactionId" type="xsd:string"/><xsd:element name="approved" type="xsd:boolean"/><xsd:element name="sequence" type="xsd:int"/></xsd:sequence></xsd:complexType></xsd:element>
</xsd:schema></types>
<message name="GetBalanceInput"><part name="p" element="tns:GetBalance"/></message><message name="GetBalanceOutput"><part name="p" element="tns:GetBalanceResponse"/></message>
<message name="TransferInput"><part name="p" element="tns:Transfer"/></message><message name="TransferOutput"><part name="p" element="tns:TransferResponse"/></message>
<portType name="P"><operation name="GetBalance"><input message="tns:GetBalanceInput"/><output message="tns:GetBalanceOutput"/></operation>
<operation name="Transfer"><input message="tns:TransferInput"/><output message="tns:TransferOutput"/></operation></portType>
<service name="S"><port name="Port" binding="tns:B"><soap:address location="%s"/></port></service></definitions>`

func legacyBackend(mode *string, hits map[string]int) *httptest.Server {
	var srv *httptest.Server
	srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "GET" {
			fmt.Fprintf(w, legacyWSDL, srv.URL+"/soap")
			return
		}
		raw, _ := io.ReadAll(r.Body)
		reply := func(status int, inner string) {
			w.Header().Set("Content-Type", "text/xml")
			w.WriteHeader(status)
			fmt.Fprintf(w, `<soap:Envelope xmlns:soap=%q><soap:Body>%s</soap:Body></soap:Envelope>`, nsSOAP, inner)
		}
		s := string(raw)
		op := "?"
		for _, name := range []string{"GetBalance", "Transfer"} {
			if strings.Contains(s, "<"+name+" ") {
				op = name
			}
		}
		hits[op]++
		switch *mode {
		case "slow":
			time.Sleep(2 * time.Second)
		case "servererror":
			reply(500, `<soap:Fault><faultcode>soap:Server</faultcode><faultstring>ORA-00600 internal error at bank-db-03</faultstring></soap:Fault>`)
			return
		}
		switch op {
		case "GetBalance":
			if strings.Contains(s, "NOPE") {
				reply(500, `<soap:Fault><faultcode>soap:Client</faultcode><faultstring>No such account</faultstring><detail><AccountNotFound><accountId>NOPE</accountId></AccountNotFound></detail></soap:Fault>`)
				return
			}
			reply(200, `<GetBalanceResponse xmlns="http://bank.example.com/ws"><balance>1042.50</balance><currency>EUR</currency></GetBalanceResponse>`)
		case "Transfer":
			if strings.Contains(s, "<amount>99999") {
				reply(500, `<soap:Fault><faultcode>soap:Client</faultcode><faultstring>Insufficient funds</faultstring><detail><InsufficientFunds><available>1042.50</available></InsufficientFunds></detail></soap:Fault>`)
				return
			}
			reply(200, `<TransferResponse xmlns="http://bank.example.com/ws"><transactionId>TX-000042</transactionId><approved>true</approved><sequence>42</sequence></TransferResponse>`)
		default:
			reply(500, `<soap:Fault><faultcode>soap:Client</faultcode><faultstring>unknown op</faultstring></soap:Fault>`)
		}
	}))
	return srv
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	mode := "ok"
	hits := map[string]int{}
	backend := legacyBackend(&mode, hits)
	defer backend.Close()

	fmt.Println("== 1. the gateway learns the contract from the WSDL at startup ==")
	contract, err := LoadContract(backend.URL+"?wsdl", map[string]bool{"GetBalance": true /* reads may be retried; Transfer must not */})
	must(err == nil, fmt.Sprint(err))
	fmt.Println("  namespace:", contract.Namespace, "\n  endpoint :", contract.Endpoint)
	for _, n := range []string{"GetBalance", "Transfer"} {
		op := contract.Ops[n]
		fmt.Printf("  %-10s in=%v out=%v\n", n, op.Input, op.Output)
	}
	must(len(contract.Ops) == 2 && len(contract.Ops["Transfer"].Input) == 3, "operations and fields discovered")

	gw := NewGateway(contract, &http.Client{Transport: &http.Transport{DialContext: (&net.Dialer{Timeout: time.Second}).DialContext}})
	front := httptest.NewServer(gw.Router)
	defer front.Close()

	post := func(path, body string) (int, map[string]any) {
		res, err := http.Post(front.URL+path, "application/json", strings.NewReader(body))
		must(err == nil, fmt.Sprint(err))
		defer res.Body.Close()
		var m map[string]any
		json.NewDecoder(res.Body).Decode(&m)
		return res.StatusCode, m
	}
	show := func(label string, st int, m map[string]any) {
		b, _ := json.Marshal(m)
		fmt.Printf("  %-26s -> %d %s\n", label, st, b)
	}

	fmt.Println("\n== 2. happy path: JSON in, JSON out, no SOAP visible ==")
	st, m := post("/api/GetBalance", `{"accountId":"ACC-1001"}`)
	show("POST /api/GetBalance", st, m)
	must(st == 200 && m["balance"] == "1042.50", "decimal stays a string")
	st, m = post("/api/Transfer", `{"fromAccount":"ACC-1001","toAccount":"ACC-2002","amount":100.25}`)
	show("POST /api/Transfer", st, m)
	must(st == 200 && m["approved"] == true && fmt.Sprint(m["sequence"]) == "42", "typed output: bool and int")
	fmt.Println("  (xsd:boolean became a JSON true, xsd:int a JSON number, xsd:decimal stays an exact string)")

	fmt.Println("\n== 3. input validation from the WSDL schema ==")
	st, m = post("/api/GetBalance", `{}`)
	show("missing field", st, m)
	must(st == 400, "missing")
	st, m = post("/api/GetBalance", `{"accountId":"A","extra":1}`)
	show("unknown field", st, m)
	must(st == 400, "unknown")
	st, m = post("/api/Nope", `{}`)
	show("unknown operation", st, m)
	must(st == 404, "404")
	before := hits["GetBalance"] + hits["Transfer"]
	must(before == 2, "invalid requests never reached the backend")

	fmt.Println("\n== 4. SOAP faults translated to HTTP problems ==")
	st, m = post("/api/GetBalance", `{"accountId":"NOPE"}`)
	show("Client fault", st, m)
	must(st == 422 && strings.Contains(fmt.Sprint(m["backend_detail"]), "AccountNotFound"), "422 with detail")
	st, m = post("/api/Transfer", `{"fromAccount":"A","toAccount":"B","amount":99999}`)
	show("business fault", st, m)
	must(st == 422, "insufficient funds")
	mode = "servererror"
	st, m = post("/api/GetBalance", `{"accountId":"ACC-1001"}`)
	show("Server fault (read, retried)", st, m)
	must(st == 502 && !strings.Contains(fmt.Sprint(m), "ORA-00600"), "502 without leaking the Oracle error")
	fmt.Println("  the backend's internal 'ORA-00600 ... bank-db-03' text is NOT forwarded to clients")
	hitsBefore := hits["Transfer"]
	st, _ = post("/api/Transfer", `{"fromAccount":"A","toAccount":"B","amount":5}`)
	must(st == 502 && hits["Transfer"] == hitsBefore+1, "a failed Transfer is NOT retried")
	fmt.Println("  Transfer got 502 after exactly ONE backend attempt (non-idempotent), GetBalance was retried 3 times")
	must(hits["GetBalance"] >= 5, "read retried")

	fmt.Println("\n== 5. slow and dead backends ==")
	mode = "slow"
	t := time.Now()
	st, m = post("/api/GetBalance", `{"accountId":"ACC-1001"}`)
	show("backend hangs", st, m)
	fmt.Printf("  answered in %s: the gateway's 800ms deadline protects its callers\n", time.Since(t).Round(50*time.Millisecond))
	must(st == 504 && time.Since(t) < 1500*time.Millisecond, "504 within the deadline")
	backend.Close()
	st, m = post("/api/GetBalance", `{"accountId":"ACC-1001"}`)
	show("backend down", st, m)
	must(st == 503, "503")

	fmt.Println("\n== 6. the gateway describes itself ==")
	res, _ := http.Get(front.URL + "/api/operations")
	var desc struct {
		Operations []struct {
			Name       string
			Idempotent bool
			Input      []Field
		}
	}
	json.NewDecoder(res.Body).Decode(&desc)
	for _, o := range desc.Operations {
		fmt.Printf("  %s (idempotent=%v) takes %v\n", o.Name, o.Idempotent, o.Input)
	}
	must(len(desc.Operations) == 2, "operations listing")
	fmt.Println("\nOK")
}
