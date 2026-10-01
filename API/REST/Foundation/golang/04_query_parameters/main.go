/*
FOUNDATION LEVEL 04 - Query parameters: /books?author=...&limit=...
=======================================================================
A path parameter (level 03) identifies WHICH resource. A query parameter
filters or shapes a COLLECTION: /books?author=Hunt&limit=1. It lives after
the "?" and is never part of routing - two requests with different query
strings hit the exact same handler and route.

You will learn
  - r.URL.Query() parses "?author=Hunt&limit=1" into a url.Values (a
    map[string][]string - a key CAN repeat: ?tag=a&tag=b)
  - Query().Get("x") is a convenience for "give me the first value, or empty
    string if missing" - you still convert types (limit -> int) yourself
  - missing query params should have sane defaults, not a panic

Run it   go run ./REST/Foundation/golang/04_query_parameters
*/
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
)

type Book struct {
	ID     int    `json:"id"`
	Title  string `json:"title"`
	Author string `json:"author"`
}

var books = []Book{
	{1, "SICP", "Abelson"},
	{2, "The Pragmatic Programmer", "Hunt"},
	{3, "Effective Go", "Hunt"},
}

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/books" {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	q := r.URL.Query()

	results := books
	if author := q.Get("author"); author != "" {
		filtered := []Book{}
		for _, b := range results {
			if b.Author == author {
				filtered = append(filtered, b)
			}
		}
		results = filtered
	}

	limit := len(results)
	if v := q.Get("limit"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			limit = n
		}
	}
	if limit > len(results) {
		limit = len(results)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results[:limit])
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	get := func(path string) []Book {
		res, err := http.Get(base + path)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		raw, _ := io.ReadAll(res.Body)
		var out []Book
		json.Unmarshal(raw, &out)
		return out
	}

	all := get("/books")
	fmt.Printf("GET /books                      -> %d book(s)\n", len(all))
	if len(all) != 3 {
		panic("FAILED")
	}

	byHunt := get("/books?author=Hunt")
	fmt.Printf("GET /books?author=Hunt          -> %d book(s)\n", len(byHunt))
	if len(byHunt) != 2 {
		panic("FAILED")
	}

	limited := get("/books?author=Hunt&limit=1")
	fmt.Printf("GET /books?author=Hunt&limit=1  -> %d book(s)\n", len(limited))
	if len(limited) != 1 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
