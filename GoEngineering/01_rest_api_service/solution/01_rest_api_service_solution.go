// Package main — reference solution for Problem 01: REST API service.
//
// See ../explanation/01_rest_api_service_explanation.go for the full spec,
// acceptance criteria, hints, and stretch goals. This file implements that
// spec end to end and explains, in comments directly above each block, why
// it's written the way it is.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
	"unicode/utf8"
)

// ---------------------------------------------------------------------------
// Domain type
// ---------------------------------------------------------------------------

// Task is the resource this API exposes. Field tags control JSON casing —
// keeping the wire format snake_case while Go code stays idiomatic
// CamelCase is a convention worth holding consistently across a codebase.
type Task struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	Done      bool      `json:"done"`
	CreatedAt time.Time `json:"created_at"`
}

// ---------------------------------------------------------------------------
// Store
//
// A plain map keyed by ID does NOT preserve insertion order (Go
// randomizes map iteration deliberately, to stop anyone depending on it).
// The spec requires List() to return a stable, creation-ordered result, so
// we keep an explicit []string of IDs alongside the map. This is the same
// trade-off a real repository layer makes when the backing store doesn't
// naturally sort the way callers want: maintain an index rather than
// re-deriving order on every read.
//
// sync.RWMutex (not sync.Mutex) because reads (List/Get) vastly outnumber
// writes (Create/Update/Delete) in a typical CRUD workload, and RWMutex
// lets concurrent readers proceed without blocking each other.
// ---------------------------------------------------------------------------

// ErrNotFound is a sentinel error returned by TaskStore methods when an id
// doesn't exist. Sentinel + errors.Is is the idiomatic way to let a caller
// (here, the HTTP layer) branch on "did this fail, and specifically how"
// without the store package knowing anything about HTTP status codes. That
// separation matters: the store has zero net/http imports, so it's equally
// usable from a CLI, a gRPC handler, or a test — this is the same principle
// problem 18 (ports and adapters) generalizes.
var ErrNotFound = errors.New("task not found")

// TaskStore is a concurrency-safe in-memory collection of tasks.
type TaskStore struct {
	mu     sync.RWMutex
	tasks  map[string]Task
	order  []string // creation order of IDs, for stable List()
	nextID atomic.Uint64
}

// NewTaskStore returns an empty, ready-to-use TaskStore.
func NewTaskStore() *TaskStore {
	return &TaskStore{
		tasks: make(map[string]Task),
	}
}

// newID generates a simple, monotonically increasing, process-unique ID.
//
// A real service would use a UUID (github.com/google/uuid, already vendored
// in this module for later problems) or a database-assigned key. A plain
// atomic counter is deliberately used here to keep this problem's focus on
// HTTP/JSON/concurrency rather than ID-generation strategy, and because
// atomic.Uint64.Add is itself a good, cheap example of lock-free state that
// doesn't need the store's mutex at all.
func (s *TaskStore) newID() string {
	return "t" + strconv.FormatUint(s.nextID.Add(1), 10)
}

// Create inserts a new task with the given (already-validated) title.
//
// Validation happens at the HTTP layer, not here — the store's contract is
// "store what you're given," which keeps it reusable by callers that have
// already validated by other means (e.g. a batch-import job).
func (s *TaskStore) Create(title string) Task {
	s.mu.Lock()
	defer s.mu.Unlock()

	t := Task{
		ID:        s.newID(),
		Title:     title,
		Done:      false,
		CreatedAt: time.Now().UTC(),
	}
	s.tasks[t.ID] = t
	s.order = append(s.order, t.ID)
	return t
}

// Get returns the task with the given id, or ErrNotFound.
func (s *TaskStore) Get(id string) (Task, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	t, ok := s.tasks[id]
	if !ok {
		return Task{}, ErrNotFound
	}
	return t, nil
}

// List returns all tasks in creation order. It returns a fresh slice each
// call so callers can't mutate the store's internal state through the
// returned value — an easy-to-miss aliasing bug if we ever returned a
// slice backed by store-owned memory.
func (s *TaskStore) List() []Task {
	s.mu.RLock()
	defer s.mu.RUnlock()

	out := make([]Task, 0, len(s.order))
	for _, id := range s.order {
		out = append(out, s.tasks[id])
	}
	return out
}

// Update overwrites the title/done fields of an existing task, preserving
// ID and CreatedAt (PUT here is a full-resource replace of the mutable
// fields, not "replace everything including identity").
func (s *TaskStore) Update(id string, title string, done bool) (Task, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	t, ok := s.tasks[id]
	if !ok {
		return Task{}, ErrNotFound
	}
	t.Title = title
	t.Done = done
	s.tasks[id] = t
	return t, nil
}

// Delete removes a task by id. Deleting from s.order is O(n); acceptable
// for an in-memory demo store, and a real implementation would swap in a
// doubly-linked structure or accept the O(n) cost bounded by store size.
func (s *TaskStore) Delete(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.tasks[id]; !ok {
		return ErrNotFound
	}
	delete(s.tasks, id)
	for i, existing := range s.order {
		if existing == id {
			s.order = append(s.order[:i], s.order[i+1:]...)
			break
		}
	}
	return nil
}

// ---------------------------------------------------------------------------
// JSON error envelope
//
// Every error response, from any handler, must have the exact same shape:
// {"error": {"code": "...", "message": "..."}}. Centralizing this in one
// pair of functions (writeError/writeJSON) is what actually guarantees
// that — if each handler built its own error JSON inline, the shape would
// drift the first time someone copy-pasted a handler and tweaked it.
// ---------------------------------------------------------------------------

type apiErrorBody struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

type apiError struct {
	Error apiErrorBody `json:"error"`
}

// writeJSON encodes v as JSON with the given status code.
//
// The header (Content-Type + status) must be written before any body
// bytes — http.ResponseWriter latches the status on the first Write call
// with an implicit 200 if WriteHeader was never called explicitly, so
// ordering here isn't optional.
//
// If Encode fails after the header is already sent, the status code can no
// longer change; we can only log it. This is an inherent limitation of
// streaming JSON encoding directly into a ResponseWriter (the alternative —
// encode to a buffer first, then write — costs an extra allocation+copy on
// every response to guard against a failure mode that in practice only
// happens for pathological inputs like an unencodable float). We choose the
// streaming approach and log-only on failure, which is the standard
// trade-off net/http itself makes.
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		slog.Error("writeJSON: encode failed after headers sent", "error", err)
	}
}

// writeError writes an error response using the apiError envelope.
func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, apiError{Error: apiErrorBody{Code: code, Message: message}})
}

// ---------------------------------------------------------------------------
// Request decoding
//
// DisallowUnknownFields rejects a body containing a field the target
// struct doesn't declare — this turns a silent typo ("tilte" instead of
// "title") into an immediate, loud 400 instead of a confusing empty-title
// task. The second Decode()-into-RawMessage call catches a body with
// trailing content after the first JSON value (e.g. a client that
// concatenated two objects by mistake) — without it, `{"title":"a"}{"x":1}`
// would decode the first object and silently ignore the rest.
// ---------------------------------------------------------------------------

func decodeJSON(r *http.Request, dst any) error {
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		return fmt.Errorf("decode request body: %w", err)
	}
	var trailing json.RawMessage
	if err := dec.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return errors.New("request body must contain exactly one JSON value")
		}
		return fmt.Errorf("decode request body: %w", err)
	}
	return nil
}

type createTaskRequest struct {
	Title string `json:"title"`
}

type updateTaskRequest struct {
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// validateTitle enforces the spec's title rules and returns the
// normalized (trimmed) value. Returning the normalized value alongside the
// error means callers never have to re-trim — "validate" and "normalize"
// are the same pass here, which avoids a class of bug where validation
// checks the untrimmed string but storage uses the trimmed one (or
// vice versa).
func validateTitle(title string) (string, error) {
	trimmed := strings.TrimSpace(title)
	if trimmed == "" {
		return "", errors.New("title is required")
	}
	if utf8.RuneCountInString(trimmed) > 200 {
		return "", errors.New("title must be 200 characters or fewer")
	}
	return trimmed, nil
}

// ---------------------------------------------------------------------------
// Handlers
//
// Each handler that needs the store is a function returning an
// http.HandlerFunc closing over *TaskStore — this is dependency injection
// without a framework: the mux wiring (newMux) is the single place that
// decides what each handler depends on, and handlers themselves stay unit-
// testable by calling them directly with a store of your choosing.
// ---------------------------------------------------------------------------

func handleHealthz(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func handleCreateTask(store *TaskStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req createTaskRequest
		if err := decodeJSON(r, &req); err != nil {
			writeError(w, http.StatusBadRequest, "bad_request", err.Error())
			return
		}
		title, err := validateTitle(req.Title)
		if err != nil {
			writeError(w, http.StatusBadRequest, "validation_failed", err.Error())
			return
		}
		task := store.Create(title)
		writeJSON(w, http.StatusCreated, task)
	}
}

func handleListTasks(store *TaskStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, store.List())
	}
}

// handleGetTask reads {id} via r.PathValue("id") — the Go 1.22+
// ServeMux feature that removed the need for a third-party router just to
// extract path segments.
func handleGetTask(store *TaskStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		task, err := store.Get(id)
		if errors.Is(err, ErrNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "task not found")
			return
		}
		writeJSON(w, http.StatusOK, task)
	}
}

func handleUpdateTask(store *TaskStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var req updateTaskRequest
		if err := decodeJSON(r, &req); err != nil {
			writeError(w, http.StatusBadRequest, "bad_request", err.Error())
			return
		}
		title, err := validateTitle(req.Title)
		if err != nil {
			writeError(w, http.StatusBadRequest, "validation_failed", err.Error())
			return
		}
		task, err := store.Update(id, title, req.Done)
		if errors.Is(err, ErrNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "task not found")
			return
		}
		writeJSON(w, http.StatusOK, task)
	}
}

// handleDeleteTask responds 204 No Content on success. A 204 response must
// not have a body — we call w.WriteHeader directly rather than going
// through writeJSON, which would (harmlessly, but pointlessly) encode
// `null`.
func handleDeleteTask(store *TaskStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		err := store.Delete(id)
		if errors.Is(err, ErrNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "task not found")
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}
}

// ---------------------------------------------------------------------------
// Routing
//
// Go 1.22 added method-aware patterns directly to http.ServeMux:
// "GET /tasks/{id}" only matches GET requests to that path shape, and a
// request to a registered path with a different method automatically gets
// a 405 (with an Allow header) — no manual r.Method switch needed. This
// removed the single biggest reason most Go services used to reach for
// gorilla/mux or chi. We deliberately use only the standard library here.
// ---------------------------------------------------------------------------

func newMux(store *TaskStore) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", handleHealthz)
	mux.HandleFunc("POST /tasks", handleCreateTask(store))
	mux.HandleFunc("GET /tasks", handleListTasks(store))
	mux.HandleFunc("GET /tasks/{id}", handleGetTask(store))
	mux.HandleFunc("PUT /tasks/{id}", handleUpdateTask(store))
	mux.HandleFunc("DELETE /tasks/{id}", handleDeleteTask(store))
	return mux
}

// newServer wraps the mux in an *http.Server with production-sane
// timeouts. A bare http.Server{} (or http.ListenAndServe(addr, mux))
// has NO timeouts at all: a client that opens a connection and trickles
// headers one byte at a time (a "slow-loris" attack, or just a bad
// network) can hold a goroutine and a file descriptor forever.
// ReadHeaderTimeout alone fixes the classic slow-loris; WriteTimeout and
// IdleTimeout bound the rest of the connection lifecycle.
func newServer(addr string, store *TaskStore) *http.Server {
	return &http.Server{
		Addr:              addr,
		Handler:           newMux(store),
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
}

// ---------------------------------------------------------------------------
// main: real server, real graceful shutdown
//
// signal.NotifyContext gives us a context.Context that is canceled the
// moment SIGINT or SIGTERM arrives — this is the idiomatic Go 1.16+
// replacement for manually managing a `chan os.Signal` and a select loop.
// ListenAndServe runs in its own goroutine because it blocks until the
// server stops; the main goroutine's job is to wait for either a shutdown
// signal or a fatal startup error, then drive Shutdown with a bounded
// grace period so in-flight requests get to finish instead of being cut
// off mid-response.
// ---------------------------------------------------------------------------

func main() {
	store := NewTaskStore()
	srv := newServer(":8080", store)

	serveErr := make(chan error, 1)
	go func() {
		log.Printf("listening on %s", srv.Addr)
		// ListenAndServe always returns a non-nil error; ErrServerClosed
		// is the expected one when Shutdown was called deliberately.
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveErr <- err
			return
		}
		serveErr <- nil
	}()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	select {
	case err := <-serveErr:
		if err != nil {
			log.Fatalf("server failed to start: %v", err)
		}
	case <-ctx.Done():
		stop() // restore default signal behavior (a second signal force-kills)
		log.Print("shutdown signal received, draining in-flight requests")

		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := srv.Shutdown(shutdownCtx); err != nil {
			log.Fatalf("graceful shutdown failed: %v", err)
		}
		<-serveErr // wait for the ListenAndServe goroutine to actually exit
		log.Print("shutdown complete")
	}
}

/*
BEST PRACTICES

  - Keep the store's package (here, just the top of this file) free of any
    net/http types. HTTP status codes and error envelopes are a concern of
    the transport layer, not the domain layer — this is what lets the same
    TaskStore back a gRPC service or a CLI with zero changes.
  - Centralize error-response construction (writeError) so the envelope
    shape can never drift handler-to-handler.
  - Always set explicit server timeouts. There is no safe default.
  - Use context.Context (via signal.NotifyContext + Shutdown's own context)
    for lifecycle control instead of os.Exit or a bare close(chan).

ALTERNATIVE APPROACHES / TRADE-OFFS

  - Third-party routers (chi, gorilla/mux, gin): buy you regex path
    params, route groups, and built-in middleware chaining, at the cost of
    a dependency. Since Go 1.22, method+wildcard routing needs none of that
    for the common case — reach for a router when you need regex
    constraints on path segments, longest-prefix priority tie-breaking
    control, or a large existing ecosystem of router-specific middleware.
  - In-memory store vs database/sql: the interface shape here (Create/Get/
    List/Update/Delete returning (Task, error) and a sentinel ErrNotFound)
    is exactly what a `database/sql`-backed store implements in problem 09
    — same handlers, same tests, different constructor.
  - json.NewEncoder(w).Encode vs json.Marshal + w.Write: Encode streams
    directly to the connection (lower peak memory, no intermediate []byte),
    but forfeits the ability to change the status code after a partial
    write failure. Marshal-then-Write buys that safety back at the cost of
    buffering the whole body. For small JSON payloads like this API's, the
    difference is negligible either way; Encode is shown here because it's
    the more common production default for arbitrarily large payloads.

TESTING NOTES

  - Test through newMux(store), not main() — main() starts a real
    listener and blocks; it's for humans running `go run`, not tests.
  - Use httptest.NewServer(newMux(store)) for full-stack tests that
    exercise real routing (method matching, 405s, path params) and
    httptest.NewRequest/ResponseRecorder for cheaper single-handler tests.
  - Run `go test -race ./...` — the whole point of TaskStore's RWMutex is
    to be race-free under concurrent access; a race detector run is the
    only way to actually prove that rather than assume it.

FAILURE MODES TO CONSIDER

  - Client sends Content-Length larger than the actual body / hangs
    mid-body: bounded by ReadHeaderTimeout + the server's default body
    handling; a stricter service would also wrap r.Body in
    http.MaxBytesReader to cap request body size.
  - Two concurrent PUTs to the same task: last-write-wins under the
    store's mutex — no lost-update *corruption* (the mutex prevents
    torn writes), but there is a lost-update *race at the business level*
    (whoever's Update call acquires the lock second overwrites the first
    unconditionally). Fixing that requires optimistic concurrency (ETag/
    If-Match), listed as a stretch goal.
*/
