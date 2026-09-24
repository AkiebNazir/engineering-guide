/*
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Middleware (level 08) is the mechanism; authentication is one specific thing
people put in it. Authentication answers exactly ONE question: "do we
recognize this request at all?" It says NOTHING about what that caller is
allowed to do - that is level 10, authorization, and it is a deliberately
separate concept.

This checks a bearer token against a hardcoded lookup table. Real systems
verify a signed JWT or look a token up in a database (see
../../labs/golang/05_api_key_auth_and_ownership) - the SHAPE of the check is
identical: reject before the real handler ever runs if the token is missing
or unknown.

You will learn
  - the "Authorization: Bearer <token>" header convention
  - authentication middleware runs BEFORE the real handler, and can
    short-circuit the whole chain by writing a response and simply not
    calling next.ServeHTTP
  - 401 Unauthorized means specifically "we do not know who you are" - never
    confuse it with 403 (level 10), which means the opposite problem
  - context.WithValue is how Go attaches the identified caller onto the
    request so the handler downstream (and level 10's authorization check)
    can use it without re-checking the token

Run it   go run ./REST/Foundation/golang/09_authentication_bearer_tokens
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
)

type identity struct {
	User string `json:"user"`
	Role string `json:"role"`
}

// A stand-in for "who is allowed in", the way a real system would consult a
// database or verify a signed token instead of this map.
var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

type ctxKey string

const userCtxKey ctxKey = "user"

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
		if !ok {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing bearer token"})
			return
		}
		id, known := tokens[token]
		if !known {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid token"})
			return
		}
		// Now every handler downstream knows who this is, via the request's context.
		ctx := context.WithValue(r.Context(), userCtxKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func whoamiHandler(w http.ResponseWriter, r *http.Request) {
	id := r.Context().Value(userCtxKey).(identity) // set by withAuthentication above
	sendJSON(w, http.StatusOK, id)
}

func main() {
	mux := http.NewServeMux()
	mux.Handle("GET /whoami", withAuthentication(http.HandlerFunc(whoamiHandler)))

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	get := func(token string) (int, map[string]string) {
		req, _ := http.NewRequest("GET", base+"/whoami", nil)
		if token != "" {
			req.Header.Set("Authorization", "Bearer "+token)
		}
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		raw, _ := io.ReadAll(res.Body)
		var parsed map[string]string
		json.Unmarshal(raw, &parsed)
		return res.StatusCode, parsed
	}

	s, b := get("")
	fmt.Printf("GET /whoami  (no header)              -> %d %v\n", s, b)
	if s != 401 {
		panic("FAILED")
	}

	s, b = get("not-a-real-token")
	fmt.Printf("GET /whoami  Authorization: Bearer bad -> %d %v\n", s, b)
	if s != 401 {
		panic("FAILED")
	}

	s, b = get("alice-token")
	fmt.Printf("GET /whoami  Authorization: Bearer alice-token -> %d %v\n", s, b)
	if s != 200 || b["user"] != "alice" || b["role"] != "admin" {
		panic("FAILED")
	}

	s, b = get("bob-token")
	fmt.Printf("GET /whoami  Authorization: Bearer bob-token   -> %d %v\n", s, b)
	if s != 200 || b["user"] != "bob" || b["role"] != "viewer" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
