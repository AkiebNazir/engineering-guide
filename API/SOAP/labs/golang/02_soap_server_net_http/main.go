/*
LAB 02 (basic) - A SOAP server with net/http: dispatch, faults with detail, WSDL, concurrency-safe state
========================================================================================================
You will learn
  - the whole server in one screen: read a bounded body -> find the operation in <soap:Body> ->
    decode the request struct -> run your function -> encode the response (or a Fault)
  - a tiny GENERIC registry so each operation is just a typed Go function:
    Register(s, "GetBalance", func(ctx, GetBalanceReq) (GetBalanceResp, error) { ... })
  - dispatch by the first element of the Body using xml.Decoder tokens (not by URL - SOAP has one endpoint)
  - error mapping: return *BusinessFault for expected failures (client can catch <InsufficientFunds> by
    name); anything else becomes a generic Server fault without leaking internals
  - transport checks: method, Content-Type (text/xml or application/soap+xml), body limit, HTTP 500 for faults
  - serving the WSDL on GET ?wsdl
  - concurrency: 40 goroutines making transfers at once; a mutex keeps balances correct and the total
    conserved (money must not appear or vanish)

Run it   go run ./SOAP/labs/golang/02_soap_server_net_http
Serve    go run ./SOAP/labs/golang/02_soap_server_net_http -serve      (then: curl localhost:8080/bank?wsdl)
*/
package main

import (
	"bytes"
	"context"
	"encoding/xml"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
	"net/http"
	"strings"
	"sync"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsBank = "http://bank.example.com/ws"
)

// ----------------------------------------------------------- SOAP plumbing ---
type BusinessFault struct {
	Code       string // "soap:Client" (caller's fault) or "soap:Server"
	Message    string
	DetailName string
	Detail     map[string]string
}

func (f *BusinessFault) Error() string { return f.Message }

type opFunc func(ctx context.Context, d *xml.Decoder, start xml.StartElement) (any, error)

type Server struct {
	ops  map[xml.Name]opFunc
	wsdl string
}

// Register adds a typed operation. Req and Resp are plain structs with xml tags.
func Register[Req, Resp any](s *Server, name string, fn func(context.Context, Req) (Resp, error)) {
	s.ops[xml.Name{Space: nsBank, Local: name}] = func(ctx context.Context, d *xml.Decoder, start xml.StartElement) (any, error) {
		var req Req
		if err := d.DecodeElement(&req, &start); err != nil {
			return nil, &BusinessFault{Code: "soap:Client", Message: "malformed request body"}
		}
		return fn(ctx, req)
	}
}

func envelope(inner []byte) []byte {
	var b bytes.Buffer
	b.WriteString(xml.Header)
	fmt.Fprintf(&b, `<soap:Envelope xmlns:soap=%q><soap:Body>`, nsSOAP)
	b.Write(inner)
	b.WriteString(`</soap:Body></soap:Envelope>`)
	return b.Bytes()
}

func faultXML(f *BusinessFault) []byte {
	var b bytes.Buffer
	fmt.Fprintf(&b, "<soap:Fault><faultcode>%s</faultcode><faultstring>", f.Code)
	xml.EscapeText(&b, []byte(f.Message))
	b.WriteString("</faultstring>")
	if f.DetailName != "" {
		fmt.Fprintf(&b, `<detail><%s xmlns=%q>`, f.DetailName, nsBank)
		for k, v := range f.Detail {
			fmt.Fprintf(&b, "<%s>", k)
			xml.EscapeText(&b, []byte(v))
			fmt.Fprintf(&b, "</%s>", k)
		}
		fmt.Fprintf(&b, "</%s></detail>", f.DetailName)
	}
	b.WriteString("</soap:Fault>")
	return b.Bytes()
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet && strings.EqualFold(r.URL.RawQuery, "wsdl") {
		w.Header().Set("Content-Type", "text/xml; charset=utf-8")
		fmt.Fprint(w, s.wsdl)
		return
	}
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "GET, POST")
		http.Error(w, "SOAP requires POST", http.StatusMethodNotAllowed)
		return
	}
	if ct := r.Header.Get("Content-Type"); !strings.HasPrefix(ct, "text/xml") && !strings.HasPrefix(ct, "application/soap+xml") {
		http.Error(w, "Content-Type must be text/xml or application/soap+xml", http.StatusUnsupportedMediaType)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)

	reply := func(status int, inner []byte) {
		w.Header().Set("Content-Type", "text/xml; charset=utf-8")
		w.WriteHeader(status)
		w.Write(envelope(inner))
	}
	fault := func(f *BusinessFault) { reply(http.StatusInternalServerError, faultXML(f)) } // SOAP 1.1: faults = HTTP 500

	d := xml.NewDecoder(r.Body)
	// walk tokens to <Body>, then take its FIRST child element: that is the operation
	var op *xml.StartElement
	inBody := false
	for op == nil {
		tok, err := d.Token()
		if err != nil {
			var tooBig *http.MaxBytesError
			if errors.As(err, &tooBig) {
				http.Error(w, "request too large", http.StatusRequestEntityTooLarge)
				return
			}
			fault(&BusinessFault{Code: "soap:Client", Message: "malformed SOAP message"})
			return
		}
		if se, ok := tok.(xml.StartElement); ok {
			switch {
			case se.Name.Space == nsSOAP && se.Name.Local == "Body":
				inBody = true
			case inBody:
				op = &se
			}
		}
	}
	handler, ok := s.ops[op.Name]
	if !ok {
		fault(&BusinessFault{Code: "soap:Client", Message: "unknown operation {" + op.Name.Space + "}" + op.Name.Local})
		return
	}
	resp, err := handler(r.Context(), d, *op)
	if err != nil {
		var bf *BusinessFault
		if !errors.As(err, &bf) {
			log.Printf("internal error: %v", err) // details in the LOG, never in the response
			bf = &BusinessFault{Code: "soap:Server", Message: "internal error"}
		}
		fault(bf)
		return
	}
	out, err := xml.Marshal(resp)
	if err != nil {
		fault(&BusinessFault{Code: "soap:Server", Message: "internal error"})
		return
	}
	reply(http.StatusOK, out)
}

// -------------------------------------------------------------- the service ---
type GetBalanceReq struct {
	XMLName   xml.Name `xml:"http://bank.example.com/ws GetBalance"`
	AccountID string   `xml:"http://bank.example.com/ws accountId"`
}
type GetBalanceResp struct {
	XMLName  xml.Name `xml:"http://bank.example.com/ws GetBalanceResponse"`
	Balance  string   `xml:"balance"`
	Currency string   `xml:"currency"`
}
type TransferReq struct {
	XMLName xml.Name `xml:"http://bank.example.com/ws Transfer"`
	From    string   `xml:"http://bank.example.com/ws fromAccount"`
	To      string   `xml:"http://bank.example.com/ws toAccount"`
	Amount  string   `xml:"http://bank.example.com/ws amount"`
}
type TransferResp struct {
	XMLName       xml.Name `xml:"http://bank.example.com/ws TransferResponse"`
	TransactionID string   `xml:"transactionId"`
	Status        string   `xml:"status"`
}

type Bank struct {
	mu       sync.Mutex
	balances map[string]*big.Rat
	txSeq    int
}

func (b *Bank) GetBalance(_ context.Context, r GetBalanceReq) (GetBalanceResp, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	bal, ok := b.balances[r.AccountID]
	if !ok {
		return GetBalanceResp{}, &BusinessFault{"soap:Client", "No such account: " + r.AccountID, "AccountNotFound", map[string]string{"accountId": r.AccountID}}
	}
	return GetBalanceResp{Balance: bal.FloatString(2), Currency: "EUR"}, nil
}

func (b *Bank) Transfer(_ context.Context, r TransferReq) (TransferResp, error) {
	amount, ok := new(big.Rat).SetString(strings.TrimSpace(r.Amount)) // exact decimal, no floats for money
	if !ok || amount.Sign() <= 0 {
		return TransferResp{}, &BusinessFault{"soap:Client", "Amount must be a positive decimal", "InvalidAmount", map[string]string{"amount": r.Amount}}
	}
	b.mu.Lock()
	defer b.mu.Unlock() // the WHOLE check-and-move is one critical section
	from, okF := b.balances[r.From]
	to, okT := b.balances[r.To]
	if !okF || !okT {
		return TransferResp{}, &BusinessFault{"soap:Client", "Unknown account", "AccountNotFound", map[string]string{"accountId": r.From + "/" + r.To}}
	}
	if from.Cmp(amount) < 0 {
		return TransferResp{}, &BusinessFault{"soap:Client", "Insufficient funds", "InsufficientFunds",
			map[string]string{"available": from.FloatString(2), "requested": amount.FloatString(2)}}
	}
	from.Sub(from, amount)
	to.Add(to, amount)
	b.txSeq++
	return TransferResp{TransactionID: fmt.Sprintf("TX-%06d", b.txSeq), Status: "COMPLETED"}, nil
}

const wsdl = `<?xml version="1.0" encoding="utf-8"?>
<definitions name="BankService" targetNamespace="http://bank.example.com/ws" xmlns="http://schemas.xmlsoap.org/wsdl/"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:tns="http://bank.example.com/ws">
  <types><xsd:schema targetNamespace="http://bank.example.com/ws" elementFormDefault="qualified">
    <xsd:element name="GetBalance"><xsd:complexType><xsd:sequence><xsd:element name="accountId" type="xsd:string"/></xsd:sequence></xsd:complexType></xsd:element>
    <xsd:element name="GetBalanceResponse"><xsd:complexType><xsd:sequence><xsd:element name="balance" type="xsd:decimal"/><xsd:element name="currency" type="xsd:string"/></xsd:sequence></xsd:complexType></xsd:element>
    <xsd:element name="Transfer"><xsd:complexType><xsd:sequence><xsd:element name="fromAccount" type="xsd:string"/><xsd:element name="toAccount" type="xsd:string"/><xsd:element name="amount" type="xsd:decimal"/></xsd:sequence></xsd:complexType></xsd:element>
    <xsd:element name="TransferResponse"><xsd:complexType><xsd:sequence><xsd:element name="transactionId" type="xsd:string"/><xsd:element name="status" type="xsd:string"/></xsd:sequence></xsd:complexType></xsd:element>
  </xsd:schema></types>
  <message name="GetBalanceInput"><part name="parameters" element="tns:GetBalance"/></message>
  <message name="GetBalanceOutput"><part name="parameters" element="tns:GetBalanceResponse"/></message>
  <message name="TransferInput"><part name="parameters" element="tns:Transfer"/></message>
  <message name="TransferOutput"><part name="parameters" element="tns:TransferResponse"/></message>
  <portType name="BankPortType">
    <operation name="GetBalance"><input message="tns:GetBalanceInput"/><output message="tns:GetBalanceOutput"/></operation>
    <operation name="Transfer"><input message="tns:TransferInput"/><output message="tns:TransferOutput"/></operation>
  </portType>
  <binding name="BankBinding" type="tns:BankPortType"><soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="GetBalance"><soap:operation soapAction="http://bank.example.com/ws/GetBalance"/><input><soap:body use="literal"/></input><output><soap:body use="literal"/></output></operation>
    <operation name="Transfer"><soap:operation soapAction="http://bank.example.com/ws/Transfer"/><input><soap:body use="literal"/></input><output><soap:body use="literal"/></output></operation>
  </binding>
  <service name="BankService"><port name="BankPort" binding="tns:BankBinding"><soap:address location="http://localhost:8080/bank"/></port></service>
</definitions>`

func NewBankServer() (*Server, *Bank) {
	bank := &Bank{balances: map[string]*big.Rat{"ACC-1001": big.NewRat(104250, 100), "ACC-2002": big.NewRat(8710, 100)}}
	s := &Server{ops: map[xml.Name]opFunc{}, wsdl: wsdl}
	Register(s, "GetBalance", bank.GetBalance)
	Register(s, "Transfer", bank.Transfer)
	return s, bank
}

// -------------------------------------------------------------------- demo ---
func post(url, contentType, body string) (int, string) {
	req, _ := http.NewRequest("POST", url, strings.NewReader(body))
	req.Header.Set("Content-Type", contentType)
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, string(b)
}

func call(url, op, inner string) (int, string) {
	return post(url, "text/xml; charset=utf-8", fmt.Sprintf(`<soap:Envelope xmlns:soap=%q><soap:Body><%s xmlns=%q>%s</%s></soap:Body></soap:Envelope>`, nsSOAP, op, nsBank, inner, op))
}

func between(s, a, b string) string {
	i := strings.Index(s, a)
	if i < 0 {
		return ""
	}
	i += len(a)
	return s[i : i+strings.Index(s[i:], b)]
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	serve := flag.Bool("serve", false, "listen on :8080")
	flag.Parse()
	srv, bank := NewBankServer()
	mux := http.NewServeMux()
	mux.Handle("/bank", srv)
	if *serve {
		log.Println("SOAP bank on http://localhost:8080/bank  (WSDL: /bank?wsdl)")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	go http.Serve(ln, mux)
	url := "http://" + ln.Addr().String() + "/bank"

	fmt.Println("== 1. operations ==")
	st, body := call(url, "GetBalance", "<accountId>ACC-1001</accountId>")
	fmt.Printf("  GetBalance -> %d balance=%s currency=%s\n", st, between(body, "<balance>", "<"), between(body, "<currency>", "<"))
	must(st == 200 && between(body, "<balance>", "<") == "1042.50", "balance")
	st, body = call(url, "Transfer", "<fromAccount>ACC-1001</fromAccount><toAccount>ACC-2002</toAccount><amount>100.25</amount>")
	fmt.Printf("  Transfer   -> %d %s %s\n", st, between(body, "<transactionId>", "<"), between(body, "<status>", "<"))
	must(st == 200, "transfer")

	fmt.Println("\n== 2. faults ==")
	for _, c := range []struct{ label, op, inner string }{
		{"unknown account", "GetBalance", "<accountId>NOPE</accountId>"},
		{"insufficient funds", "Transfer", "<fromAccount>ACC-2002</fromAccount><toAccount>ACC-1001</toAccount><amount>99999</amount>"},
		{"invalid amount", "Transfer", "<fromAccount>ACC-1001</fromAccount><toAccount>ACC-2002</toAccount><amount>-5</amount>"},
		{"unknown operation", "DeleteEverything", ""},
	} {
		st, body := call(url, c.op, c.inner)
		fmt.Printf("  %-19s -> HTTP %d  %s: %s\n", c.label, st, between(body, "<faultcode>", "<"), between(body, "<faultstring>", "<"))
		must(st == 500 && strings.Contains(body, "soap:Client"), c.label)
	}
	_, body = call(url, "Transfer", "<fromAccount>ACC-2002</fromAccount><toAccount>ACC-1001</toAccount><amount>99999</amount>")
	fmt.Printf("  detail: <InsufficientFunds> available=%s requested=%s\n", between(body, "<available>", "<"), between(body, "<requested>", "<"))
	must(strings.Contains(body, "InsufficientFunds"), "typed detail")

	fmt.Println("\n== 3. transport checks ==")
	st, _ = post(url, "application/json", "{}")
	fmt.Println("  Content-Type: application/json ->", st)
	must(st == http.StatusUnsupportedMediaType, "415")
	st, _ = post(url, "text/xml", "<not-xml")
	fmt.Println("  malformed XML                  ->", st, "(a SOAP fault)")
	must(st == 500, "malformed => fault")
	st, _ = post(url, "text/xml", "<soap:Envelope xmlns:soap='"+nsSOAP+"'><soap:Body><a>"+strings.Repeat("x", 2<<20))
	fmt.Println("  2 MiB body                     ->", st, "(refused: the size limit stops the decoder)")
	must(st == http.StatusRequestEntityTooLarge || st == 500, "size limit")
	res, _ := http.Get(url + "?wsdl")
	wb, _ := io.ReadAll(res.Body)
	fmt.Printf("  GET ?wsdl                      -> %d, %d bytes of WSDL\n", res.StatusCode, len(wb))
	must(res.StatusCode == 200 && bytes.Contains(wb, []byte("BankPortType")), "wsdl")

	fmt.Println("\n== 4. concurrency: 40 goroutines shuffle money both ways ==")
	total := func() *big.Rat {
		bank.mu.Lock()
		defer bank.mu.Unlock()
		return new(big.Rat).Add(bank.balances["ACC-1001"], bank.balances["ACC-2002"])
	}
	before := total()
	var wg sync.WaitGroup
	for i := 0; i < 40; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			from, to := "ACC-1001", "ACC-2002"
			if i%2 == 1 {
				from, to = to, from
			}
			call(url, "Transfer", fmt.Sprintf("<fromAccount>%s</fromAccount><toAccount>%s</toAccount><amount>7.31</amount>", from, to))
		}()
	}
	wg.Wait()
	fmt.Printf("  total before: %s, after: %s (must be identical)\n", before.FloatString(2), total().FloatString(2))
	must(before.Cmp(total()) == 0, "money conserved under concurrency")
	fmt.Println("\nOK")
}
