/*
FOUNDATION LEVEL 05 - Reading a request body, and rejecting bad input
========================================================================
GET requests carry data in the URL (levels 03-04). POST/PUT carry data in the
BODY instead, after the request's headers end. net/http already
gives you r.Body as a stream - you (1) decode it as JSON and (2) VALIDATE the
shape before trusting any of it.

You will learn
  - r.Body is an io.ReadCloser; json.NewDecoder(r.Body).Decode(&v) reads AND parses in one step
  - malformed JSON must not crash the server - Decode returns an error, handle it
  - "well-formed JSON" is not the same as "valid data" - a struct with an
    empty required field is still just wrong, and that is a 400, not a 500

Run it   go run ./REST/Foundation/golang/05_request_body_and_validation
*/
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
)

type User struct {
	Email string `json:"email"`
}

var users []User

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/users" || r.Method != http.MethodPost {
		sendJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
		return
	}

	var u User
	if err := json.NewDecoder(r.Body).Decode(&u); err != nil {
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "request body is not valid JSON"})
		return
	}
	if u.Email == "" {
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "'email' is required"})
		return
	}
	users = append(users, u)
	sendJSON(w, http.StatusCreated, u)
}

func post(base, path, body string) (int, string) {
	res, err := http.Post(base+path, "application/json", strings.NewReader(body))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, string(b)
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	s, b := post(base, "/users", `{"email": "ada@example.com"}`)
	fmt.Printf("POST /users  {\"email\": ...}   -> %d %s\n", s, b)
	if s != 201 {
		panic("FAILED")
	}

	s, b = post(base, "/users", `{"name": "no email field"}`)
	fmt.Printf("POST /users  {\"name\": ...}    -> %d %s  (missing required field)\n", s, b)
	if s != 400 {
		panic("FAILED")
	}

	s, b = post(base, "/users", `{this is not json`)
	fmt.Printf("POST /users  <garbage bytes>    -> %d %s  (parse error, not a crash)\n", s, b)
	if s != 400 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
