/*
LAB 07 (framework) - Echo: full CRUD with PATCH, middleware, and param parsing
===============================================================================
You will learn
  - Echo's router and path params:  c.Param("id")            (vs r.PathValue("id") in lab 02)
  - query string parsing:           c.QueryParam("limit")     parsed/validated BY HAND, 400 on garbage
  - binding a JSON body:            c.Bind(&in)                Echo decodes it, but YOU still validate it
  - echo.Context: the ONE object carrying request, response, path params, query and body together -
    handlers take a single func(echo.Context) error instead of (http.ResponseWriter, *http.Request)
  - a middleware chain:             e.Use(middleware.Logger(), middleware.Recover())  - free, built-in
  - writing your OWN middleware:    func(echo.HandlerFunc) echo.HandlerFunc  - a hand-rolled request-ID
    middleware, so you see the shape every Echo middleware has, not just how to switch one on
  - PATCH with pointer fields, the SAME convention lab 02 uses: a nil pointer means "field not sent",
    so PATCH can tell "not sent" from "sent as false/empty"
  - Echo vs net/http (lab 02): the router hands you params/query/binding for free instead of
    strconv.Atoi(r.PathValue(...)) and json.NewDecoder(r.Body) by hand - less plumbing, same ideas.
  - Echo vs Gin (both live in this module): Echo gives every handler one echo.Context and makes you
    `return err` on failure so a handler is still just a plain, testable function; Gin hands you
    *gin.Context and expects you to call c.JSON/c.Abort yourself and let it fall off the end - Echo's
    explicit-return style is a bit more "just Go", Gin's is a bit more "the framework is in charge".

Run it   go run ./REST/labs/golang/07_echo_crud_middleware
*/
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

// ------------------------------------------------------------------ model ---
type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// Input for POST (the whole resource, minus the server-assigned ID).
type TaskInput struct {
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// Input for PATCH: pointers so "absent" (nil) differs from "sent as false/empty" -
// the exact trick lab 02 uses for partial updates.
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
type Problem struct { // RFC 9457, same shape as lab 02
	Type   string       `json:"type"`
	Title  string       `json:"title"`
	Status int          `json:"status"`
	Detail string       `json:"detail,omitempty"`
	Errors []FieldError `json:"errors,omitempty"`
}

// problem writes application/problem+json. Echo's c.JSON only sets Content-Type when it is
// still empty (see echo's writeContentType), so setting it first here sticks.
func problem(c echo.Context, status int, title, detail string, errs []FieldError) error {
	c.Response().Header().Set(echo.HeaderContentType, "application/problem+json")
	return c.JSON(status, Problem{Type: "about:blank", Title: title, Status: status, Detail: detail, Errors: errs})
}

// ------------------------------------------------------------------ store ---
type Store struct {
	mu     sync.RWMutex // handlers run concurrently in Echo too - same guard as lab 02
	nextID int
	tasks  map[int]Task
}

func NewStore() *Store { return &Store{nextID: 1, tasks: map[int]Task{}} }

// ---------------------------------------------------------------- handlers ---
func (s *Store) create(c echo.Context) error {
	var in TaskInput
	if err := c.Bind(&in); err != nil { // c.Bind decodes JSON (by Content-Type) into in
		return problem(c, http.StatusBadRequest, "Bad Request", err.Error(), nil)
	}
	if errs := in.Validate(); len(errs) > 0 { // Bind does NOT validate - that part is still ours
		return problem(c, http.StatusUnprocessableEntity, "Validation failed", "", errs)
	}
	s.mu.Lock()
	t := Task{ID: s.nextID, Title: strings.TrimSpace(in.Title), Done: in.Done}
	s.tasks[t.ID] = t
	s.nextID++
	s.mu.Unlock()
	c.Response().Header().Set(echo.HeaderLocation, "/tasks/"+strconv.Itoa(t.ID))
	return c.JSON(http.StatusCreated, t)
}

// list supports ?done=true|false to filter by status, and ?limit=&offset= to page -
// both are plain strings off the query string that we parse and validate ourselves.
func (s *Store) list(c echo.Context) error {
	var donePtr *bool
	if v := c.QueryParam("done"); v != "" {
		b, err := strconv.ParseBool(v)
		if err != nil {
			return problem(c, http.StatusBadRequest, "Bad Request", "invalid 'done' query value: "+v, nil)
		}
		donePtr = &b
	}
	limit := 100 // default: effectively "no cap" for this tiny demo
	if v := c.QueryParam("limit"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 0 {
			return problem(c, http.StatusBadRequest, "Bad Request", "invalid 'limit' query value: "+v, nil)
		}
		limit = n
	}
	offset := 0
	if v := c.QueryParam("offset"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 0 {
			return problem(c, http.StatusBadRequest, "Bad Request", "invalid 'offset' query value: "+v, nil)
		}
		offset = n
	}

	s.mu.RLock()
	ids := make([]int, 0, len(s.tasks))
	for id := range s.tasks {
		ids = append(ids, id)
	}
	sort.Ints(ids) // map iteration order is random; the list must be deterministic
	out := make([]Task, 0, len(ids))
	for _, id := range ids {
		t := s.tasks[id]
		if donePtr != nil && t.Done != *donePtr {
			continue
		}
		out = append(out, t)
	}
	s.mu.RUnlock()

	if offset > len(out) {
		offset = len(out)
	}
	end := offset + limit
	if end > len(out) {
		end = len(out)
	}
	return c.JSON(http.StatusOK, out[offset:end])
}

func (s *Store) get(c echo.Context) error {
	id, _ := strconv.Atoi(c.Param("id")) // non-numeric -> id 0 -> not found, same as lab 02
	s.mu.RLock()
	t, ok := s.tasks[id]
	s.mu.RUnlock()
	if !ok {
		return problem(c, http.StatusNotFound, "Not Found", "no such task", nil)
	}
	return c.JSON(http.StatusOK, t)
}

func (s *Store) patch(c echo.Context) error {
	id, _ := strconv.Atoi(c.Param("id"))
	var p TaskPatch
	if err := c.Bind(&p); err != nil {
		return problem(c, http.StatusBadRequest, "Bad Request", err.Error(), nil)
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	t, ok := s.tasks[id]
	if !ok {
		return problem(c, http.StatusNotFound, "Not Found", "no such task", nil)
	}
	if p.Title != nil { // only touch what the client actually sent
		t.Title = *p.Title
	}
	if p.Done != nil {
		t.Done = *p.Done
	}
	s.tasks[id] = t
	return c.JSON(http.StatusOK, t)
}

func (s *Store) remove(c echo.Context) error {
	id, _ := strconv.Atoi(c.Param("id"))
	s.mu.Lock()
	delete(s.tasks, id) // idempotent: deleting twice, or deleting nothing, still succeeds
	s.mu.Unlock()
	return c.NoContent(http.StatusNoContent)
}

// -------------------------------------------------------------- middleware ---
// requestID is a middleware written by hand: the shape every Echo middleware has is
//
//	func(echo.HandlerFunc) echo.HandlerFunc
//
// wrap "next", do work before, call next(c), optionally do work after, return its error.
func requestID(next echo.HandlerFunc) echo.HandlerFunc {
	return func(c echo.Context) error {
		id := c.Request().Header.Get("X-Request-Id") // honour an upstream id, else make one
		if id == "" {
			b := make([]byte, 8)
			rand.Read(b)
			id = hex.EncodeToString(b)
		}
		c.Set("request_id", id) // request-scoped value on the Context (Gin's c.Set does the same job)
		c.Response().Header().Set("X-Request-Id", id)
		log.Printf("req=%s %s %s", id, c.Request().Method, c.Request().URL.Path)
		return next(c) // MUST call next and return its error, or the chain stops dead here
	}
}

func routes() *echo.Echo {
	e := echo.New()
	e.HideBanner = true
	e.Use(middleware.Logger())  // built-in, one line: logs every request
	e.Use(middleware.Recover()) // built-in, one line: turns a handler panic into a 500, not a dead server
	e.Use(requestID)            // ours: the func(echo.HandlerFunc) echo.HandlerFunc shape above

	s := NewStore()
	e.POST("/tasks", s.create)
	e.GET("/tasks", s.list)
	e.GET("/tasks/:id", s.get) // Echo's path-param syntax: :id, read back with c.Param("id")
	e.PATCH("/tasks/:id", s.patch)
	e.DELETE("/tasks/:id", s.remove)
	return e
}

// ------------------------------------------------------------------- demo ---
func main() {
	log.SetFlags(0)
	e := routes()

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	go e.Server.Serve(ln) // echo.New() already wired e.Server.Handler = e
	base := "http://" + ln.Addr().String()

	do := func(method, path, body string) (int, http.Header, string) {
		var rdr io.Reader
		if body != "" {
			rdr = strings.NewReader(body)
		}
		req, _ := http.NewRequest(method, base+path, rdr)
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
	show := func(label string, status int, body string) { fmt.Printf("%-26s -> %d %s\n", label, status, body) }

	st, h, b := do("POST", "/tasks", `{"title":"learn Echo","done":false}`)
	show("create task 1", st, b)
	check(st == http.StatusCreated && h.Get("Location") == "/tasks/1", "create")
	check(h.Get("X-Request-Id") != "", "custom middleware set X-Request-Id")

	st, _, b = do("POST", "/tasks", `{"title":"write tests","done":true}`)
	show("create task 2", st, b)
	check(st == http.StatusCreated, "create task 2")

	st, _, b = do("POST", "/tasks", `{"title":"ship it","done":false}`)
	show("create task 3", st, b)
	check(st == http.StatusCreated, "create task 3")

	st, _, b = do("POST", "/tasks", `{"title":"   "}`)
	show("empty title rejected", st, b)
	check(st == http.StatusUnprocessableEntity, "validation")

	st, _, b = do("GET", "/tasks/999", "")
	show("get bad id", st, b)
	check(st == http.StatusNotFound, "get missing")

	st, _, b = do("PATCH", "/tasks/1", `{"done":true}`) // title must stay untouched
	show("patch done only", st, b)
	check(st == http.StatusOK && strings.Contains(b, `"done":true`) && strings.Contains(b, "learn Echo"), "patch preserves untouched field")

	st, _, b = do("GET", "/tasks?done=false", "")
	show("list ?done=false", st, b)
	check(st == http.StatusOK && strings.Contains(b, "ship it") &&
		!strings.Contains(b, "learn Echo") && !strings.Contains(b, "write tests"), "filter by done")

	st, _, b = do("GET", "/tasks?done=maybe", "")
	show("list bad done value", st, b)
	check(st == http.StatusBadRequest, "bad query value -> 400")

	st, _, b = do("GET", "/tasks?limit=notanumber", "")
	show("list bad limit value", st, b)
	check(st == http.StatusBadRequest, "bad limit -> 400")

	st, _, b = do("GET", "/tasks?limit=1&offset=1", "")
	show("list limit=1 offset=1", st, b)
	check(st == http.StatusOK && strings.Count(b, `"id":`) == 1 && strings.Contains(b, `"id":2`), "pagination window")

	st1, _, _ := do("DELETE", "/tasks/1", "")
	st2, _, _ := do("DELETE", "/tasks/1", "")
	st3, _, _ := do("GET", "/tasks/1", "")
	fmt.Println("delete, delete, get        ->", st1, st2, st3)
	check(st1 == http.StatusNoContent && st2 == http.StatusNoContent, "delete is idempotent")
	check(st3 == http.StatusNotFound, "get after delete -> 404")

	fmt.Println("OK")
}
