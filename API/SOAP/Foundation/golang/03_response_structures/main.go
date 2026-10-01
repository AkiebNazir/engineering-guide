/*
FOUNDATION LEVEL 03 - Response structures: nesting, and the array that isn't
================================================================================
Levels 00-02 answered with one or two flat values. Real operations answer with a
STRUCTURE: an order with a customer inside it and a list of lines inside that.
XML expresses nesting by nesting elements, which is easy - but it has no array
type at all, which trips up everyone arriving from JSON.

JSON says `"items": [{...},{...}]`. XML says: repeat the element.

	<items>              <- a wrapper element, by convention
	  <item>...</item>   <- the "array" is just <item> appearing twice
	  <item>...</item>
	</items>

So "is this a list or a single value?" is not visible in the XML at all - it
lives in the contract (the WSDL's maxOccurs). A one-element list and a single
value look IDENTICAL on the wire, which is why a Go slice field happily decodes
both and a non-slice field silently keeps only the last one.

You will learn
  - nested structs marshal to nested elements, one level per struct
  - a SLICE field is how Go says "this element may repeat" - the array
  - the `parent>child` tag shorthand for reaching through a wrapper element
  - `xml:"...,attr"` for an attribute instead of a child element
  - that a list of length one is indistinguishable from a scalar on the wire

Run it   go run ./SOAP/Foundation/golang/03_response_structures
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
	"strconv"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

// ---- the response shape, as nested Go types ----
type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Response getOrderResponse `xml:"http://foundation.example.com/soap GetOrderResponse"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type getOrderResponse struct {
	Order order `xml:"http://foundation.example.com/soap order"`
}

type order struct {
	// An ATTRIBUTE instead of a child element. Both are legal; the rule of
	// thumb is attributes for identity/metadata, elements for data.
	ID string `xml:"id,attr"`

	Customer customer `xml:"http://foundation.example.com/soap customer"`

	// A SLICE, reached through the <items> wrapper with the `parent>child`
	// shorthand. This one line is the whole "XML has no arrays" story: the
	// wrapper is convention, the repetition is the array.
	Items []item `xml:"http://foundation.example.com/soap items>item"`

	Total string `xml:"http://foundation.example.com/soap total"`
}

type customer struct {
	Name    string `xml:"http://foundation.example.com/soap name"`
	Country string `xml:"http://foundation.example.com/soap country"`
}

type item struct {
	SKU   string `xml:"http://foundation.example.com/soap sku"`
	Qty   int    `xml:"http://foundation.example.com/soap qty"`
	Price string `xml:"http://foundation.example.com/soap price"`
}

var orders = map[string]order{
	"ORD-1": {
		ID:       "ORD-1",
		Customer: customer{Name: "Ada Lovelace", Country: "GB"},
		Items: []item{
			{SKU: "WIDGET-1", Qty: 2, Price: "9.99"},
			{SKU: "GIZMO-7", Qty: 1, Price: "24.50"},
		},
	},
	// Deliberately ONE item: on the wire this looks exactly like a single
	// value, which is why clients need the contract to know it is a list.
	"ORD-2": {
		ID:       "ORD-2",
		Customer: customer{Name: "Alan Turing", Country: "GB"},
		Items:    []item{{SKU: "WIDGET-1", Qty: 1, Price: "9.99"}},
	},
}

type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		GetOrder *struct {
			OrderID string `xml:"http://foundation.example.com/soap orderId"`
		} `xml:"http://foundation.example.com/soap GetOrder"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func dispatch(raw []byte) (int, []byte) {
	var env requestEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		return http.StatusBadRequest, []byte("cannot decode request")
	}
	if env.Body.GetOrder == nil {
		return http.StatusBadRequest, []byte("unknown operation")
	}
	found, known := orders[env.Body.GetOrder.OrderID]
	if !known {
		return http.StatusBadRequest, []byte("unknown order")
	}

	// Compute the total from the nested slice, then hand the whole tree to the
	// marshaller - one call, however deep the structure goes.
	total := 0.0
	for _, line := range found.Items {
		price, _ := strconv.ParseFloat(line.Price, 64)
		total += float64(line.Qty) * price
	}
	found.Total = fmt.Sprintf("%.2f", total)

	var out responseEnvelope
	out.Body.Response = getOrderResponse{Order: found}
	body, err := xml.Marshal(out)
	if err != nil {
		return http.StatusInternalServerError, []byte(err.Error())
	}
	return http.StatusOK, append([]byte(xml.Header), body...)
}

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

func getOrder(url, orderID string) (int, []byte) {
	envelope := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/><soap:Body>`+
			`<t:GetOrder xmlns:t="%s"><t:orderId>%s</t:orderId></t:GetOrder>`+
			`</soap:Body></soap:Envelope>`, nsSOAP, nsTNS, orderID)
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(envelope)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	return res.StatusCode, raw
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

	fmt.Println("== 1. a nested response, as raw XML ==")
	status, raw := getOrder(url, "ORD-1")
	fmt.Println("  " + string(bytes.ReplaceAll(raw, []byte("><"), []byte(">\n  <"))))
	if status != http.StatusOK {
		panic("FAILED")
	}

	fmt.Println("== 2. the same response, decoded into Go structs ==")
	var env responseEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		log.Fatal(err)
	}
	decoded := env.Body.Response.Order
	fmt.Printf("  id=%s customer=%q country=%s items=%d total=%s\n",
		decoded.ID, decoded.Customer.Name, decoded.Customer.Country, len(decoded.Items), decoded.Total)
	for _, line := range decoded.Items {
		fmt.Printf("    - %s x%d @ %s\n", line.SKU, line.Qty, line.Price)
	}
	if decoded.ID != "ORD-1" || decoded.Customer.Name != "Ada Lovelace" ||
		len(decoded.Items) != 2 || decoded.Total != "44.48" {
		panic("FAILED")
	}

	fmt.Println("\n== 3. a ONE-item list looks exactly like a scalar on the wire ==")
	_, raw = getOrder(url, "ORD-2")
	var single responseEnvelope
	if err := xml.Unmarshal(raw, &single); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  slice field  -> %d item(s): %+v\n",
		len(single.Body.Response.Order.Items), single.Body.Response.Order.Items)
	if len(single.Body.Response.Order.Items) != 1 {
		panic("FAILED")
	}

	// The trap, made concrete: decode the SAME bytes with a non-slice field.
	// Nothing errors. You just quietly get one item, and for ORD-1 you would
	// quietly get the LAST one and lose the other.
	var naive struct {
		XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
		Body    struct {
			Item item `xml:"http://foundation.example.com/soap GetOrderResponse>order>items>item"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
	}
	if err := xml.Unmarshal(raw, &naive); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  scalar field -> %+v   (no error, no warning - the contract is the only clue)\n",
		naive.Body.Item)
	if naive.Body.Item.SKU != "WIDGET-1" {
		panic("FAILED")
	}

	_, ord1 := getOrder(url, "ORD-1")
	if err := xml.Unmarshal(ord1, &naive); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  the same scalar field on the TWO-item order -> %+v\n", naive.Body.Item)
	fmt.Println("  -> it kept only the last <item> and dropped the first. Always use a slice")
	fmt.Println("     for anything the contract says may repeat.")
	if naive.Body.Item.SKU != "GIZMO-7" {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
