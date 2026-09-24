/*
LAB 02 (basic) - JSON CRUD done properly with net/http
======================================================
You will learn
  - decoding a request body SAFELY:
    http.MaxBytesReader        -> a client cannot make you read a gigabyte
    DisallowUnknownFields      -> typos like "titel" are errors, not silent no-ops
    "only one JSON value"      -> reject trailing garbage
  - validation errors that tell the client WHICH field is wrong
  - one error format everywhere: RFC 9457 application/problem+json
  - 201 + Location on create, 204 on delete, PATCH with pointer fields
    (nil pointer = "field not sent", so PATCH can tell "not sent" from "false")
  - guarding shared state with sync.RWMutex (handlers run concurrently!)

Run it   go run ./REST/labs/golang/02_json_crud_validation
*/
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strconv"
	"strings"
	"sync"
)

// ------------------------------------------------------------------ model ---
type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// Input for POST / PUT (whole resource).
type TaskInput struct {
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// Input for PATCH: pointers so "absent" (nil) differs from "false".
type TaskPatch struct {
	Title *string `json:"title"`
	Done  *bool   `json:"done"`
}

type FieldError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

func (in TaskInput) Validate() (errs []FieldError) {
	if t := strings.TrimSpace(in.Title); t == "" {
		errs = append(errs, FieldError{"title", "must not be empty"})
	} else if len(t) > 100 {
		errs = append(errs, FieldError{"title", "must be at most 100 characters"})
	}
	return
}

// ---------------------------------------------------------------- helpers ---
type Problem struct { // RFC 9457
	Type   string       `json:"type"`
	Title  string       `json:"title"`
	Status int          `json:"status"`
	Detail string       `json:"detail,omitempty"`
	Errors []FieldError `json:"errors,omitempty"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeProblem(w http.ResponseWriter, p Problem) {
	w.Header().Set("Content-Type", "application/problem+json")
	w.WriteHeader(p.Status)
	json.NewEncoder(w).Encode(p)
}

// decode reads exactly one JSON document into dst, strictly.
func decode(w http.ResponseWriter, r *http.Request, dst any) error {
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20) // 1 MiB cap
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		var tooBig *http.MaxBytesError
		switch {
		case errors.As(err, &tooBig):
			return fmt.Errorf("body too large (limit %d bytes)", tooBig.Limit)
		case errors.Is(err, io.EOF):
			return errors.New("request body is empty")
		default:
			return fmt.Errorf("malformed JSON: %v", err)
		}
	}
	if dec.More() { // e.g. `{"title":"a"} {"title":"b"}`
		return errors.New("body must contain a single JSON value")
	}
	return nil
}

func badRequest(w http.ResponseWriter, detail string) {
	writeProblem(w, Problem{Type: "about:blank", Title: "Bad Request", Status: 400, Detail: detail})
}

// ------------------------------------------------------------------ store ---
type Store struct {
	mu     sync.RWMutex // many readers OR one writer
	nextID int
	tasks  map[int]Task
}

func NewServer() http.Handler {
	s := &Store{nextID: 1, tasks: map[int]Task{}}
	mux := http.NewServeMux()

	mux.HandleFunc("POST /tasks", func(w http.ResponseWriter, r *http.Request) {
		var in TaskInput
		if err := decode(w, r, &in); err != nil {
			badRequest(w, err.Error())
			return
		}
		if errs := in.Validate(); len(errs) > 0 {
			writeProblem(w, Problem{"about:blank", "Validation failed", http.StatusUnprocessableEntity, "", errs})
			return
		}
		s.mu.Lock()
		t := Task{ID: s.nextID, Title: strings.TrimSpace(in.Title), Done: in.Done}
		s.tasks[t.ID] = t
		s.nextID++
		s.mu.Unlock()
		w.Header().Set("Location", "/tasks/"+strconv.Itoa(t.ID))
		writeJSON(w, http.StatusCreated, t)
	})

	mux.HandleFunc("GET /tasks/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.PathValue("id"))
		s.mu.RLock()
		t, ok := s.tasks[id]
		s.mu.RUnlock()
		if !ok {
			writeProblem(w, Problem{Type: "about:blank", Title: "Not Found", Status: 404, Detail: "no such task"})
			return
		}
		writeJSON(w, http.StatusOK, t)
	})

	mux.HandleFunc("PATCH /tasks/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.PathValue("id"))
		var p TaskPatch
		if err := decode(w, r, &p); err != nil {
			badRequest(w, err.Error())
			return
		}
		s.mu.Lock()
		defer s.mu.Unlock()
		t, ok := s.tasks[id]
		if !ok {
			writeProblem(w, Problem{Type: "about:blank", Title: "Not Found", Status: 404})
			return
		}
		if p.Title != nil { // only touch what the client sent
			t.Title = *p.Title
		}
		if p.Done != nil {
			t.Done = *p.Done
		}
		s.tasks[id] = t
		writeJSON(w, http.StatusOK, t)
	})

	mux.HandleFunc("DELETE /tasks/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.PathValue("id"))
		s.mu.Lock()
		delete(s.tasks, id) // idempotent
		s.mu.Unlock()
		w.WriteHeader(http.StatusNoContent)
	})
	return mux
}

// ------------------------------------------------------------------- demo ---
func main() {
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	go http.Serve(ln, NewServer())
	base := "http://" + ln.Addr().String()

	do := func(method, path, body string) (int, http.Header, string) {
		req, _ := http.NewRequest(method, base+path, strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			panic(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, res.Header, strings.TrimSpace(string(b))
	}
	check := func(cond bool, msg string) {
		if !cond {
			panic("FAILED: " + msg)
		}
	}
	show := func(label string, status int, body string) { fmt.Printf("%-22s -> %d %s\n", label, status, body) }

	st, h, b := do("POST", "/tasks", `{"title":"learn Go","done":false}`)
	show("create", st, b)
	check(st == 201 && h.Get("Location") == "/tasks/1", "create")

	st, _, b = do("PATCH", "/tasks/1", `{"done":true}`) // title untouched, done flipped
	show("patch done only", st, b)
	check(strings.Contains(b, `"done":true`) && strings.Contains(b, "learn Go"), "patch")

	st, _, b = do("POST", "/tasks", `{"title":"   "}`)
	show("empty title", st, b)
	check(st == 422, "validation")

	st, _, b = do("POST", "/tasks", `{"titel":"typo"}`)
	show("unknown field (typo)", st, b)
	check(st == 400, "unknown field")

	st, _, b = do("POST", "/tasks", `{"title":"a"} {"title":"b"}`)
	show("two JSON values", st, b)
	check(st == 400, "trailing data")

	st, _, b = do("POST", "/tasks", `{"title":"`+strings.Repeat("x", 2<<20)+`"}`)
	show("2 MiB body", st, b[:80]+"...")
	check(st == 400 && strings.Contains(b, "too large"), "too large")

	st1, _, _ := do("DELETE", "/tasks/1", "")
	st2, _, _ := do("DELETE", "/tasks/1", "")
	st3, _, _ := do("GET", "/tasks/1", "")
	fmt.Println("delete, delete, get    ->", st1, st2, st3)
	check(st1 == 204 && st2 == 204 && st3 == 404, "delete")
	fmt.Println("OK")
}
