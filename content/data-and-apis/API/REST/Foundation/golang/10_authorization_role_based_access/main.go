/*
FOUNDATION LEVEL 10 - Authorization: what are you allowed to do
====================================================================
Authentication (level 09) established WHO is making the request. Authorization
is a SEPARATE question: is THIS identified caller allowed to do THIS specific
action? Two different users can both pass authentication and still get
different answers here. This level adds a role check on top of level 09's
authentication: any logged-in caller can READ the reports, but only an
"admin" may DELETE one.

You will learn
  - authorization middleware runs AFTER authentication - you need
    r.Context()'s identity (set by authentication) before you can decide
    what that identity is allowed to do
  - 403 Forbidden means "we know exactly who you are, and the answer is
    still no" - do not confuse this with 401 (level 09), which means "who
    even ARE you"
  - role-based access control (RBAC), in its simplest form: look up the
    identified caller's role, compare it against what THIS action requires
  - the SAME endpoint shape (DELETE /reports/{id}) can behave differently
    per caller - that decision lives in middleware, not scattered through
    the handler

Run it   go run ./REST/Foundation/golang/10_authorization_role_based_access
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
	"strconv"
	"strings"
)

type identity struct {
	User string `json:"user"`
	Role string `json:"role"`
}

type report struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

var reports = map[int]report{1: {ID: 1, Title: "Q1 report"}}

type ctxKey string

const userCtxKey ctxKey = "user"

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if payload != nil {
		json.NewEncoder(w).Encode(payload)
	}
}

// ---- level 09's authentication middleware, unchanged ----------------------
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
		ctx := context.WithValue(r.Context(), userCtxKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// ---- NEW: authorization middleware - runs only once we know the identity ----
func requireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			id := r.Context().Value(userCtxKey).(identity) // set by withAuthentication above
			if id.Role != role {
				sendJSON(w, http.StatusForbidden, map[string]string{"error": fmt.Sprintf("requires role '%s'", role)})
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func listReportsHandler(w http.ResponseWriter, r *http.Request) {
	list := make([]report, 0, len(reports))
	for _, rep := range reports {
		list = append(list, rep)
	}
	sendJSON(w, http.StatusOK, list)
}

func deleteReportHandler(w http.ResponseWriter, r *http.Request) {
	id, _ := strconv.Atoi(r.PathValue("id"))
	delete(reports, id) // idempotent, same as level 06's DELETE
	sendJSON(w, http.StatusNoContent, nil)
}

func main() {
	mux := http.NewServeMux()
	// ANY authenticated caller may read.
	mux.Handle("GET /reports", withAuthentication(http.HandlerFunc(listReportsHandler)))
	// Authentication wraps the outside; requireRole("admin") wraps the
	// inside, so by the time it runs, r.Context() already holds the identity.
	mux.Handle("DELETE /reports/{id}", withAuthentication(requireRole("admin")(http.HandlerFunc(deleteReportHandler))))

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	call := func(method, path, token string) (int, string) {
		req, _ := http.NewRequest(method, base+path, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(b)
	}

	s, b := call("GET", "/reports", "bob-token")
	fmt.Printf("GET    /reports          (viewer)  -> %d %s\n", s, b)
	if s != 200 {
		panic("FAILED")
	}

	s, b = call("DELETE", "/reports/1", "bob-token")
	fmt.Printf("DELETE /reports/1        (viewer)  -> %d %s   (authenticated, but not allowed)\n", s, b)
	if s != 403 {
		panic("FAILED")
	}

	s, b = call("DELETE", "/reports/1", "alice-token")
	fmt.Printf("DELETE /reports/1        (admin)   -> %d %s\n", s, b)
	if s != 204 {
		panic("FAILED")
	}

	s, b = call("GET", "/reports", "alice-token")
	fmt.Printf("GET    /reports          (admin)   -> %d %s   (the delete above really happened)\n", s, b)
	if s != 200 || b != "[]\n" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
