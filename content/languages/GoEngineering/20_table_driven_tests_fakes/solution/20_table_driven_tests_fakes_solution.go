/*
Problem 20 — Table-Driven Tests & Fakes (solution)
=====================================================

Reference implementation of the User HTTP handler specified in
explanation/20_table_driven_tests_fakes_explanation.go. The interesting
content for this topic lives in the test file
(20_table_driven_tests_fakes_test.go) sitting next to this one — table-driven
subtests, a hand-written fake, a golden-file test, and t.Parallel(). This
file is deliberately small: it's the thing under test, not the lesson.
*/
package httpuser

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"strings"
)

// ErrNotFound is returned by UserStore.GetUser when id has no matching
// user.
var ErrNotFound = errors.New("httpuser: user not found")

// User is the JSON-serializable shape returned by the handler.
type User struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

// UserStore is the dependency boundary the handler is written against.
type UserStore interface {
	GetUser(ctx context.Context, id string) (User, error)
}

// Handler serves GET /users/{id} using Store to look users up.
type Handler struct {
	Store UserStore
	mux   *http.ServeMux
}

// NewHandler builds a Handler backed by store, registering both
// "GET /users/{id}" and "GET /users/" (no wildcard) on the same function.
// The second pattern exists solely so a request with an empty id segment
// (e.g. "/users/") reaches our handler and gets a deliberate 400, instead
// of net/http's built-in "404 page not found" for an unmatched wildcard —
// {id} does not match an empty path segment at all, so without this second
// registration the empty-id case would never reach application code.
func NewHandler(store UserStore) *Handler {
	h := &Handler{Store: store}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /users/{id}", h.getUser)
	mux.HandleFunc("GET /users/", h.getUser)
	h.mux = mux
	return h
}

// ServeHTTP satisfies http.Handler by delegating to the registered mux.
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	h.mux.ServeHTTP(w, r)
}

func (h *Handler) getUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if id == "" {
		writeJSONError(w, http.StatusBadRequest, "id is required")
		return
	}

	u, err := h.Store.GetUser(r.Context(), id)
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			writeJSONError(w, http.StatusNotFound, "not found")
			return
		}
		// The client gets a generic message; only the server log gets the
		// real error — never ship err.Error() to a caller.
		log.Printf("httpuser: GetUser(%q): %v", id, err)
		writeJSONError(w, http.StatusInternalServerError, "internal error")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(u)
}

// writeJSONError sends a {"error": msg} JSON body with the given status.
// Every error path in getUser routes through this so Content-Type and body
// shape can never drift between branches.
func writeJSONError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

// FormatUserReport renders a deterministic multi-line text report for u.
// Deterministic by construction: it only reads u's three plain string
// fields in a fixed order, so there is no timestamp or map-iteration-order
// dependency to normalize before this can be golden-tested.
func FormatUserReport(u User) string {
	var b strings.Builder
	b.WriteString("User Report\n")
	b.WriteString("===========\n")
	fmt.Fprintf(&b, "ID:    %s\n", u.ID)
	fmt.Fprintf(&b, "Name:  %s\n", u.Name)
	fmt.Fprintf(&b, "Email: %s\n", u.Email)
	return b.String()
}
