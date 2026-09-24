// BASIC EXAMPLE: Go Inbuilt net/http + encoding/xml
// Demonstrates raw SOAP Envelope construction via structs
package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
)

type Envelope struct {
	XMLName xml.Name `xml:"soap:Envelope"`
	Soap    string   `xml:"xmlns:soap,attr"`
	Body    Body
}

type Body struct {
	XMLName       xml.Name       `xml:"soap:Body"`
	NumberToWords *NumberToWords `xml:"NumberToWords"`
}

type NumberToWords struct {
	Xmlns  string `xml:"xmlns,attr"`
	UbiNum int    `xml:"ubiNum"`
}

func main() {
	env := Envelope{
		Soap: "http://schemas.xmlsoap.org/soap/envelope/",
		Body: Body{
			NumberToWords: &NumberToWords{
				Xmlns:  "http://www.dataaccess.com/webservicesserver/",
				UbiNum: 500,
			},
		},
	}
	
	payload, _ := xml.Marshal(env)

	resp, err := http.Post(
		"http://www.dataaccess.com/webservicesserver/numberconversion.wso",
		"text/xml; charset=utf-8",
		bytes.NewReader(payload),
	)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("Raw XML Response:\n%s\n", string(body))
}
