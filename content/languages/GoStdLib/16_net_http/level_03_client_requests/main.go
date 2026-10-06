/*
LEVEL 03 (idiom) - building real client requests: context, headers, query, JSON body

You will learn
  - http.Get/http.Post are fine for scripts; real code builds the request
    with http.NewRequestWithContext so it can carry a deadline/cancellation,
    headers and a body, then sends it with a *http.Client you configured
  - query strings are built with url.Values (it escapes for you), never by
    string concatenation
  - a JSON body is any io.Reader; set Content-Type yourself - net/http does
    not guess it for requests
  - one http.Client (and its Transport) is meant to be created once and
    shared: it is safe for concurrent use and it owns the connection pool

Run: cd content/languages/GoStdLib && go run ./16_net_http/level_03_client_requests
*/

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"time"
)

type createOrder struct {
	SKU string `json:"sku"`
	Qty int    `json:"qty"`
}

// echo reports back what the server actually received.
func echo(w http.ResponseWriter, r *http.Request) {
	body, _ := io.ReadAll(r.Body)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"method":       r.Method,
		"path":         r.URL.Path,
		"q":            r.URL.Query().Get("q"),
		"page":         r.URL.Query().Get("page"),
		"auth":         r.Header.Get("Authorization"),
		"content_type": r.Header.Get("Content-Type"),
		"body":         string(body),
	})
}

var client = &http.Client{Timeout: 5 * time.Second} // create once, reuse everywhere

func main() {
	srv := httptest.NewServer(http.HandlerFunc(echo))
	defer srv.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// GET with an escaped query string and a header.
	q := url.Values{}
	q.Set("q", "tents & stoves")
	q.Set("page", "2")
	u := srv.URL + "/search?" + q.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer demo-token")
	got := do(req)
	fmt.Println("GET  sent URL :", u)
	fmt.Println("GET  received :", got)
	if got["q"] != "tents & stoves" || got["page"] != "2" || got["auth"] != "Bearer demo-token" {
		panic("query or header did not arrive intact")
	}

	// POST a JSON body.
	payload, _ := json.Marshal(createOrder{SKU: "TENT-2", Qty: 1})
	req, err = http.NewRequestWithContext(ctx, http.MethodPost, srv.URL+"/orders", bytes.NewReader(payload))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Type", "application/json")
	got = do(req)
	fmt.Println("POST received :", got)
	var echoed createOrder
	if err := json.Unmarshal([]byte(got["body"]), &echoed); err != nil || echoed.SKU != "TENT-2" || echoed.Qty != 1 {
		panic(fmt.Sprintf("JSON body did not round-trip: %v %+v", err, echoed))
	}
	if got["content_type"] != "application/json" {
		panic("Content-Type must be set explicitly on requests")
	}
	fmt.Println("OK")
}

func do(req *http.Request) map[string]string {
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	var out map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		panic(err)
	}
	return out
}
