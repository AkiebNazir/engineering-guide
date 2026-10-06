/*
FOUNDATION LEVEL 10 - Authorization: what this caller is allowed to do
==========================================================================
Level 09 answered "who are you?". This answers the completely different
question "may you do THIS?". Mixing the two is the classic security bug, and in
SOAP it has a very concrete form: both answers are faultcode soap:Client, so if
you do not distinguish them in <detail>, a caller cannot tell "log in again"
from "stop asking, you will never be allowed".

	AUTHENTICATION failed -> <Unauthenticated/>   the 401 of SOAP: try again with a credential
	AUTHORIZATION  failed -> <Forbidden/>         the 403 of SOAP: your credential is fine and the answer is still no

Authorization is per-OPERATION, which is where SOAP's single-endpoint design
actually helps: the whole access-control policy is one table next to the
operation table, and one middleware enforces it for every operation at once.

You will learn
  - a second middleware, layered on top of level 09's, reading the identity it
    attached rather than re-checking the token
  - a per-operation role table - the smallest honest access-control policy
  - the Fault that means "we know exactly who you are, still no"
  - why <Forbidden/> must be distinguishable from <Unauthenticated/> by a
    machine, not just by an English sentence
  - that the same caller can be allowed one operation and refused the next

Run it   go run ./SOAP/Foundation/golang/10_authorization_role_based_access
*/
package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"sort"
	"strconv"
	"strings"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsWSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
	nsTNS  = "http://foundation.example.com/soap"
)

type identity struct {
	User string
	Role string
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

// THE POLICY, in one readable place. One SOAP endpoint serves every operation,
// so this table IS the service's access-control surface - easy to review, easy
// to audit, and impossible to forget to apply (the middleware does it).
var requiredRoles = map[string][]string{
	"ListDocuments":  {"admin", "viewer"}, // anyone recognized
	"DeleteDocument": {"admin"},           // admins only
}

var documents = map[string]string{"DOC-1": "quarterly report", "DOC-2": "org chart"}

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
			XMLName xml.Name
			ID      string `xml:"http://foundation.example.com/soap id"`
		} `xml:",any"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// ---- responses ----
type listResponse struct {
	XMLName   xml.Name   `xml:"http://foundation.example.com/soap ListDocumentsResponse"`
	Documents []document `xml:"http://foundation.example.com/soap documents>document"`
}

type document struct {
	ID    string `xml:"id,attr"`
	Title string `xml:",chardata"`
}

type deleteResponse struct {
	XMLName   xml.Name `xml:"http://foundation.example.com/soap DeleteDocumentResponse"`
	Remaining int      `xml:"http://foundation.example.com/soap remaining"`
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
		List   *listResponse
		Delete *deleteResponse
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

// ---- level 09, unchanged: who is this? ----
func withAuthentication(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		caller, known := tokens[r.envelope.Header.Password]
		if r.envelope.Header.Password == "" || !known {
			return faultResponse("soap:Client", "missing or invalid credentials", "Unauthenticated")
		}
		r.caller = &caller
		return next(r)
	}
}

// ---- NEW: may this caller run THIS operation? ----
func withAuthorization(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		// Note what this does NOT do: it never looks at the token again. The
		// identity is already established; re-deriving it here is how the two
		// checks drift apart and a hole opens up.
		allowed, known := requiredRoles[r.operation]
		if !known {
			return faultResponse("soap:Client", "unknown operation "+r.operation, "UnknownOperation")
		}

		permitted := false
		for _, role := range allowed {
			if r.caller.Role == role {
				permitted = true
			}
		}
		if !permitted {
			sort.Strings(allowed)
			fmt.Printf("  [authz] %s (role=%s) refused %s, needs one of %v\n",
				r.caller.User, r.caller.Role, r.operation, allowed)
			// The 403 of SOAP. The caller is authenticated - retrying with the
			// same credential will fail forever, and <Forbidden/> says so.
			return faultResponse("soap:Client",
				fmt.Sprintf("role %q may not call %s", r.caller.Role, r.operation),
				"Forbidden", "requiredRole", strings.Join(allowed, ","))
		}
		return next(r)
	}
}

func dispatch(r *request) (int, []byte) {
	var env responseEnvelope

	switch r.operation {
	case "ListDocuments":
		response := &listResponse{}
		ids := make([]string, 0, len(documents))
		for id := range documents {
			ids = append(ids, id)
		}
		sort.Strings(ids) // maps have no order; a contract needs one
		for _, id := range ids {
			response.Documents = append(response.Documents, document{ID: id, Title: documents[id]})
		}
		env.Body.List = response
		return http.StatusOK, marshalEnvelope(env)

	case "DeleteDocument":
		delete(documents, r.envelope.Body.Operation.ID) // idempotent: twice is not an error
		env.Body.Delete = &deleteResponse{Remaining: len(documents)}
		return http.StatusOK, marshalEnvelope(env)
	}

	return faultResponse("soap:Client", "unreachable", "")
}

// Order is the lesson: identify FIRST, then decide. Authorization cannot run
// before authentication, because it reads the identity that step attached.
var pipeline = withAuthentication(withAuthorization(dispatch))

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)

	var parsed requestEnvelope
	var status int
	var out []byte
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		status, out = faultResponse("soap:Client", "malformed SOAP request", "")
	} else {
		status, out = pipeline(&request{
			envelope:  parsed,
			operation: parsed.Body.Operation.XMLName.Local,
		})
	}

	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

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

	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(body)))
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
	mux.HandleFunc("/soap", handler)
	go http.Serve(listener, mux)
	url := "http://" + listener.Addr().String() + "/soap"

	fmt.Println("== 1. no credentials: authentication stops it, authorization never runs ==")
	_, parsed := call(url, "ListDocuments", "", "")
	fmt.Printf("  ListDocuments (anonymous)  -> <%s>\n", detailOf(parsed))
	if detailOf(parsed) != "Unauthenticated" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. bob (viewer) may read ==")
	status, parsed := call(url, "ListDocuments", "bob-token", "")
	titles := []string{}
	for _, d := range parsed.Body.List.Documents {
		titles = append(titles, d.Title)
	}
	fmt.Printf("  ListDocuments (bob)        -> %d %v\n", status, titles)
	if status != http.StatusOK || len(titles) != 2 {
		panic("FAILED")
	}

	fmt.Println("\n== 3. bob (viewer) may NOT delete - the whole point of this level ==")
	status, parsed = call(url, "DeleteDocument", "bob-token", "<t:id>DOC-1</t:id>")
	fmt.Printf("  DeleteDocument (bob)       -> %d <%s> %q\n",
		status, detailOf(parsed), parsed.Body.Fault.String)
	if detailOf(parsed) != "Forbidden" {
		panic("FAILED")
	}
	if _, stillThere := documents["DOC-1"]; !stillThere {
		panic("FAILED: a refused call must not have changed anything")
	}

	fmt.Println("\n== 4. alice (admin) may delete ==")
	status, parsed = call(url, "DeleteDocument", "alice-token", "<t:id>DOC-1</t:id>")
	fmt.Printf("  DeleteDocument (alice)     -> %d remaining=%s\n",
		status, strconv.Itoa(parsed.Body.Delete.Remaining))
	if status != http.StatusOK || parsed.Body.Delete.Remaining != 1 {
		panic("FAILED")
	}

	fmt.Println("\n== 5. the two faults a client MUST tell apart ==")
	_, anonymous := call(url, "ListDocuments", "", "")
	_, refused := call(url, "DeleteDocument", "bob-token", "<t:id>DOC-2</t:id>")
	sameCode := anonymous.Body.Fault.Code == refused.Body.Fault.Code
	fmt.Printf("  identical faultcode? %t   -> so <detail> is the ONLY reliable signal\n", sameCode)
	fmt.Printf("    <%s> means: get a credential and retry\n", detailOf(anonymous))
	fmt.Printf("    <%s>      means: retrying changes nothing, ask an admin\n", detailOf(refused))
	if !sameCode || detailOf(anonymous) == detailOf(refused) {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
