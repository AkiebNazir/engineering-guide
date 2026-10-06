/*
FOUNDATION LEVEL 04 - XML namespaces: why every tag has two halves
======================================================================
Every level so far wrote struct tags like
`xml:"http://foundation.example.com/soap symbol"` and you took it on faith.
Here is the why: an XML document can mix vocabularies from different authors,
and two authors will absolutely both use the tag `<Amount>`. A NAMESPACE is a
globally unique string (usually a URL that nobody ever fetches) that says which
vocabulary a tag belongs to.

	<t:Amount xmlns:t="http://orders.example.com">   "Amount, the orders one"
	<s:Amount xmlns:s="http://shipping.example.com"> "Amount, the shipping one"

The PREFIX (`t:`, `s:`) is throwaway shorthand chosen per document; the
namespace URI it maps to is the real identity. Two documents using different
prefixes for the same URI are the SAME document as far as any parser cares.

THE CLASSIC BUG, demonstrated below: a struct tag with NO namespace
(`xml:"Amount"`) matches an element by local name only - so it happily matches
the wrong vocabulary's element. It works perfectly on your test message and
corrupts data in production the day someone adds a second namespace.

You will learn
  - what a namespace is, and that the prefix is NOT part of the identity
  - the two forms of a Go struct tag: `xml:"<ns> <local>"` vs `xml:"<local>"`,
    and why the second one is a loaded gun
  - xml.Name.Space vs xml.Name.Local when you inspect an element by hand
  - that re-prefixing a document changes nothing about its meaning
  - the default namespace (xmlns="...") and why it makes prefix-matching worse

Run it   go run ./SOAP/Foundation/golang/04_xml_namespaces
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
	nsSOAP     = "http://schemas.xmlsoap.org/soap/envelope/"
	nsOrders   = "http://orders.example.com"   // our own operation vocabulary
	nsShipping = "http://shipping.example.com" // a DIFFERENT team's vocabulary
)

// ---- THE CORRECT WAY: every field names its namespace explicitly ----
type correctEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		PriceOrder struct {
			Goods    string `xml:"http://orders.example.com Amount"`
			Shipping string `xml:"http://shipping.example.com Amount"`
		} `xml:"http://orders.example.com PriceOrder"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// ---- THE BUG: no namespace, so "any element whose local name is Amount" ----
// This is what you write when you strip namespaces to "keep things simple".
type naiveEnvelope struct {
	XMLName xml.Name `xml:"Envelope"`
	Body    struct {
		PriceOrder struct {
			Amount string `xml:"Amount"`
		} `xml:"PriceOrder"`
	} `xml:"Body"`
}

type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Response struct {
			Total string `xml:"http://orders.example.com Total"`
		} `xml:"http://orders.example.com PriceOrderResponse"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func dispatch(raw []byte) (int, []byte) {
	var correct correctEnvelope
	if err := xml.Unmarshal(raw, &correct); err != nil {
		return http.StatusBadRequest, []byte("cannot decode request")
	}
	goods, _ := strconv.ParseFloat(correct.Body.PriceOrder.Goods, 64)
	shipping, _ := strconv.ParseFloat(correct.Body.PriceOrder.Shipping, 64)

	// Decode the SAME bytes with the namespace-blind struct, to see what it got.
	var naive naiveEnvelope
	_ = xml.Unmarshal(raw, &naive)

	fmt.Printf("  [server] correct tags : goods=%.2f shipping=%.2f\n", goods, shipping)
	fmt.Printf("  [server] naive tag    : Amount=%q - one field, two candidate elements;\n",
		naive.Body.PriceOrder.Amount)
	fmt.Println("           the bug takes whichever came last and calls it the answer")

	var out responseEnvelope
	out.Body.Response.Total = fmt.Sprintf("%.2f", goods+shipping)
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

func post(url, envelope string) (int, []byte) {
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(envelope)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	return res.StatusCode, raw
}

func total(raw []byte) string {
	var env responseEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		log.Fatal(err)
	}
	return env.Body.Response.Total
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

	// Our request carries TWO elements whose local name is "Amount": the goods
	// total (ours) and the shipping surcharge (the shipping team's). Only the
	// namespace tells them apart.
	prefixed := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/><soap:Body>`+
			`<o:PriceOrder xmlns:o="%s" xmlns:s="%s">`+
			`<o:Amount>100.00</o:Amount><s:Amount>7.50</s:Amount>`+
			`</o:PriceOrder></soap:Body></soap:Envelope>`, nsSOAP, nsOrders, nsShipping)

	fmt.Println("== 1. two elements, same local name, different namespaces ==")
	fmt.Println("  " + prefixed)
	status, raw := post(url, prefixed)
	fmt.Printf("  total -> %s   (100.00 goods + 7.50 shipping)\n", total(raw))
	if status != http.StatusOK || total(raw) != "107.50" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. the prefix is throwaway: DIFFERENT prefixes, identical meaning ==")
	// Same namespaces, renamed prefixes, and the goods amount uses the DEFAULT
	// namespace (no prefix at all). A parser sees the exact same document.
	reprefixed := fmt.Sprintf(
		`<env:Envelope xmlns:env="%s"><env:Header/><env:Body>`+
			`<PriceOrder xmlns="%s" xmlns:ship="%s">`+
			`<Amount>100.00</Amount><ship:Amount>7.50</ship:Amount>`+
			`</PriceOrder></env:Body></env:Envelope>`, nsSOAP, nsOrders, nsShipping)
	fmt.Println("  " + reprefixed)
	_, raw = post(url, reprefixed)
	fmt.Printf("  total -> %s   (same answer: prefixes carry no meaning)\n", total(raw))
	if total(raw) != "107.50" {
		panic("FAILED")
	}

	fmt.Println("\n== 3. proof, at the token level ==")
	// Walk the raw tokens and print each element's identity as Go sees it.
	decoder := xml.NewDecoder(bytes.NewReader([]byte(reprefixed)))
	var seen []xml.Name
	for {
		token, err := decoder.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatal(err)
		}
		if start, ok := token.(xml.StartElement); ok && start.Name.Local == "Amount" {
			seen = append(seen, start.Name)
			fmt.Printf("  <%s> -> Space=%q Local=%q\n", start.Name.Local, start.Name.Space, start.Name.Local)
		}
	}
	if len(seen) != 2 || seen[0].Local != seen[1].Local || seen[0].Space == seen[1].Space {
		panic("FAILED")
	}
	fmt.Println("  -> identical Local, different Space. ALWAYS put the namespace in the")
	fmt.Println("     struct tag. Never strip namespaces 'for simplicity'.")

	fmt.Println("\nOK")
}
