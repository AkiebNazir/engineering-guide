/*
LAB 05 (advanced) - API-key authentication, scopes and object-level authorization
=================================================================================
You will learn
  - how to store API keys: only a HASH is kept, like a password (a database leak must not leak keys)
  - key format  "ak_<id>.<secret>"  so lookup is by the public id and the secret is verified in
    constant time (crypto/subtle) - no timing side channel
  - three layers, each with its own status code:
    authentication  (who are you?)               -> 401 + WWW-Authenticate
    scope           (may this KEY do this?)      -> 403
    ownership       (is THIS object yours?)      -> 404   <- the BOLA / IDOR check
  - passing the authenticated principal down with context (typed accessor, unexported key)
  - per-route middleware:  mux.Handle("DELETE /notes/{id}", requireScope("notes:write")(handler))
  - never logging the secret; showing keys only once at creation

Request path:

	request --> authenticate --> requireScope --> handler --> ownership check on the loaded object
	             401               403                          404

Run it   go run ./REST/labs/golang/05_api_key_auth_and_ownership
*/
package main

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"slices"
	"strconv"
	"strings"
	"sync"
)

// --------------------------------------------------------------- key store --
type APIKey struct {
	ID      string
	Hash    [32]byte // SHA-256 of the secret. High-entropy random secrets do not need bcrypt.
	Owner   string
	Scopes  []string
	Revoked bool
}

type KeyStore struct {
	mu   sync.RWMutex
	keys map[string]*APIKey
}

// Issue creates a key and returns the plaintext ONCE. Only the hash is stored.
func (s *KeyStore) Issue(owner string, scopes ...string) string {
	idb, secb := make([]byte, 6), make([]byte, 24)
	rand.Read(idb)
	rand.Read(secb)
	id := base64.RawURLEncoding.EncodeToString(idb)
	secret := base64.RawURLEncoding.EncodeToString(secb)

	s.mu.Lock()
	defer s.mu.Unlock()
	if s.keys == nil {
		s.keys = map[string]*APIKey{}
	}
	s.keys[id] = &APIKey{ID: id, Hash: sha256.Sum256([]byte(secret)), Owner: owner, Scopes: scopes}
	return "ak_" + id + "." + secret
}

func (s *KeyStore) Revoke(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if k := s.keys[id]; k != nil {
		k.Revoked = true
	}
}

func (s *KeyStore) Verify(presented string) (*APIKey, bool) {
	rest, ok := strings.CutPrefix(presented, "ak_")
	if !ok {
		return nil, false
	}
	id, secret, ok := strings.Cut(rest, ".")
	if !ok {
		return nil, false
	}
	s.mu.RLock()
	k := s.keys[id]
	s.mu.RUnlock()

	got := sha256.Sum256([]byte(secret))
	if k == nil { // still burn the same work so "unknown id" and "wrong secret" look alike
		subtle.ConstantTimeCompare(got[:], make([]byte, 32))
		return nil, false
	}
	if subtle.ConstantTimeCompare(got[:], k.Hash[:]) != 1 || k.Revoked {
		return nil, false
	}
	return k, true
}

// -------------------------------------------------------------- middleware --
type principalKey struct{}

func principal(ctx context.Context) *APIKey { k, _ := ctx.Value(principalKey{}).(*APIKey); return k }

func authenticate(store *KeyStore, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
		if !ok {
			token = r.Header.Get("X-API-Key") // accept either header style
		}
		key, valid := store.Verify(token)
		if !valid {
			w.Header().Set("WWW-Authenticate", `Bearer realm="notes-api"`)
			writeErr(w, http.StatusUnauthorized, "missing or invalid API key") // same message for every failure
			return
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), principalKey{}, key)))
	})
}

func requireScope(scope string, next http.HandlerFunc) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !slices.Contains(principal(r.Context()).Scopes, scope) {
			writeErr(w, http.StatusForbidden, "this key lacks the scope "+scope)
			return
		}
		next(w, r)
	})
}

func writeErr(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

// --------------------------------------------------------------------- app --
type Note struct {
	ID    int    `json:"id"`
	Owner string `json:"-"` // never serialised
	Text  string `json:"text"`
}

func newApp(store *KeyStore, notes map[int]*Note) http.Handler {
	mux := http.NewServeMux()
	mux.Handle("GET /notes/{id}", requireScope("notes:read", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.PathValue("id"))
		n := notes[id]
		// OWNERSHIP CHECK: the scope says "may read notes", not "may read EVERY note".
		if n == nil || n.Owner != principal(r.Context()).Owner {
			writeErr(w, http.StatusNotFound, "note not found") // 404, not 403: don't confirm it exists
			return
		}
		json.NewEncoder(w).Encode(n)
	}))
	mux.Handle("DELETE /notes/{id}", requireScope("notes:write", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.PathValue("id"))
		if n := notes[id]; n == nil || n.Owner != principal(r.Context()).Owner {
			writeErr(w, http.StatusNotFound, "note not found")
			return
		}
		delete(notes, id)
		w.WriteHeader(http.StatusNoContent)
	}))
	return authenticate(store, mux) // everything below is behind authentication
}

func main() {
	store := &KeyStore{}
	aliceRead := store.Issue("alice", "notes:read")
	aliceWrite := store.Issue("alice", "notes:read", "notes:write")
	bobRead := store.Issue("bob", "notes:read")
	notes := map[int]*Note{1: {1, "alice", "alice's secret plan"}, 2: {2, "bob", "bob's grocery list"}}
	app := newApp(store, notes)

	call := func(method, path, key string) (int, string) {
		req := httptest.NewRequest(method, path, nil)
		if key != "" {
			req.Header.Set("Authorization", "Bearer "+key)
		}
		rec := httptest.NewRecorder()
		app.ServeHTTP(rec, req)
		return rec.Code, strings.TrimSpace(rec.Body.String())
	}
	must := func(got, want int, label string) {
		fmt.Printf("%-42s -> %d\n", label, got)
		if got != want {
			panic(fmt.Sprintf("FAILED %s: got %d want %d", label, got, want))
		}
	}

	fmt.Println("issued (shown once):", aliceRead[:12]+"...")
	fmt.Printf("stored in memory: id + 32-byte hash only; secret not recoverable\n\n")

	st, _ := call("GET", "/notes/1", "")
	must(st, 401, "no key")
	st, _ = call("GET", "/notes/1", "ak_nonexistent.secret")
	must(st, 401, "garbage key")
	st, _ = call("GET", "/notes/1", aliceRead[:len(aliceRead)-2]+"xx")
	must(st, 401, "right id, wrong secret")

	st, body := call("GET", "/notes/1", aliceRead)
	must(st, 200, "alice reads her note")
	fmt.Println("    body:", body)

	st, _ = call("GET", "/notes/2", aliceRead)
	must(st, 404, "alice reads BOB's note (BOLA blocked)")

	st, body = call("DELETE", "/notes/1", aliceRead)
	must(st, 403, "read-only key tries DELETE")
	fmt.Println("    body:", body)

	st, _ = call("DELETE", "/notes/2", aliceWrite)
	must(st, 404, "write key deletes BOB's note")
	st, _ = call("DELETE", "/notes/1", aliceWrite)
	must(st, 204, "write key deletes its own note")

	id := strings.Split(strings.TrimPrefix(bobRead, "ak_"), ".")[0]
	store.Revoke(id)
	st, _ = call("GET", "/notes/2", bobRead)
	must(st, 401, "bob's key after revocation")
	fmt.Println("OK")
}
