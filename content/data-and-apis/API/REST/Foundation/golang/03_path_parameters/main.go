/*
FOUNDATION LEVEL 03 - Path parameters: /books/{id}
=====================================================
So far every path was a fixed string. Real resources are addressed by an ID
that lives INSIDE the path: /books/7 means "the book whose id is 7". Go
1.22+'s http.ServeMux can extract this for you with a "{id}" pattern and
r.PathValue("id") - this level uses that built-in support directly (unlike
the Python version of this level, which parses the path by hand, because
Python's stdlib http.server has no equivalent router).

You will learn
  - "GET /books/{id}" registers a pattern with a named wildcard segment
  - r.PathValue("id") reads exactly what matched that segment, as a string
  - why an id that is not a valid integer is a 400, never a crash
  - a numeric id that parses fine but matches no book is a 404 - two
    different failure reasons, two different status codes

Run it   go run ./REST/Foundation/golang/03_path_parameters
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
	ID    int    `json:"id"`
	Title string `json:"title"`
}

var books = map[int]Book{
	1: {1, "Structure and Interpretation of Computer Programs"},
	2: {2, "The Pragmatic Programmer"},
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false) // this is an API response, not HTML - don't escape < > &
	enc.Encode(payload)
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /books/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.Atoi(r.PathValue("id"))
		if err != nil {
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "expected /books/<integer id>"})
			return
		}
		book, ok := books[id]
		if !ok {
			sendJSON(w, http.StatusNotFound, map[string]string{"error": fmt.Sprintf("no book with id %d", id)})
			return
		}
		sendJSON(w, http.StatusOK, book)
	})

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	get := func(path string) (int, string) {
		res, err := http.Get(base + path)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(b)
	}

	s, b := get("/books/1")
	fmt.Printf("GET /books/1   -> %d %s", s, b)
	if s != 200 {
		panic("FAILED")
	}

	s, b = get("/books/999")
	fmt.Printf("GET /books/999 -> %d %s  (well-formed id, does not exist)\n", s, b)
	if s != 404 {
		panic("FAILED")
	}

	s, b = get("/books/abc")
	fmt.Printf("GET /books/abc -> %d %s  (not even an id -> 400, never a crash)\n", s, b)
	if s != 400 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
