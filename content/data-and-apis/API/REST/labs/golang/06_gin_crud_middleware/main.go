/*
LAB 06 (framework) - Gin: full CRUD with PATCH, middleware, and param parsing
==============================================================================
You will learn
  - Gin's router and path params: r.PATCH("/tasks/:id", ...) + c.Param("id")
  - query string parsing: c.Query / c.DefaultQuery, then validating the string
    yourself into an int or bool (Gin does not do that part for you)
  - binding + validating a JSON body in one call: c.ShouldBindJSON plus struct
    tags (`binding:"required"`) instead of hand-rolled decode/validate code
  - building a middleware chain with r.Use(...): gin.Logger() and gin.Recovery()
    come built in, and you can write your own gin.HandlerFunc the same way
  - gin.Context is the ONE object carrying the request, the response writer,
    route params, query, the JSON binder, AND a per-request key/value store
    (c.Set/c.Get) -- in net/http lab 02 that was a ResponseWriter, a *Request,
    and (in lab 03) a context.Context value, three separate things
  - PATCH with pointer fields: the SAME nil-means-not-sent convention as lab 02
    (Gin does not change this decision, it only changes how you decode)

Compared to lab 02 (stdlib net/http): Gin buys you route-param extraction,
JSON binding + validation, and composable middleware out of the box, at the
cost of one more dependency and a bit of magic under c.ShouldBindJSON.

Run it   go run ./REST/labs/golang/06_gin_crud_middleware
*/
package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"
)

// ------------------------------------------------------------------ model ---
type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

// Input for POST (whole resource). `binding:"required"` makes ShouldBindJSON
// reject an empty/missing title on its own, before our handler even runs.
type TaskInput struct {
	Title string `json:"title" binding:"required"`
	Done  bool   `json:"done"`
}

// Input for PATCH: pointers so "absent" (nil) differs from "false"/"" -- the
// exact same convention as lab 02's TaskPatch.
type TaskPatch struct {
	Title *string `json:"title"`
	Done  *bool   `json:"done"`
}

type Problem struct { // RFC 9457, same shape as lab 02
	Type   string `json:"type"`
	Title  string `json:"title"`
	Status int    `json:"status"`
	Detail string `json:"detail,omitempty"`
}

func problem(c *gin.Context, status int, title, detail string) {
	c.Header("Content-Type", "application/problem+json")
	c.AbortWithStatusJSON(status, Problem{Type: "about:blank", Title: title, Status: status, Detail: detail})
}

// ------------------------------------------------------------------ store ---
type Store struct {
	mu     sync.RWMutex // Gin handlers run on the server's goroutine-per-request too
	nextID int
	tasks  map[int]Task
}

func NewStore() *Store { return &Store{nextID: 1, tasks: map[int]Task{}} }

// ------------------------------------------------------------- middleware ---
// requestID is a hand-written gin.HandlerFunc: generate an id, stash it with
// c.Set so later handlers/middleware can read it via c.Get, echo it back as a
// response header, log it, then call c.Next() to run the rest of the chain.
func requestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		id := c.GetHeader("X-Request-Id")
		if id == "" {
			b := make([]byte, 8)
			rand.Read(b)
			id = hex.EncodeToString(b)
		}
		c.Set("request_id", id)
		c.Header("X-Request-Id", id)
		log.Printf("req=%s %s %s", id, c.Request.Method, c.Request.URL.Path)
		c.Next() // hand off to the rest of the chain; code after this runs on the way back out
	}
}

// --------------------------------------------------------------- handlers ---
func routes(s *Store) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery(), requestID()) // built-ins first, then our own

	r.POST("/tasks", func(c *gin.Context) {
		var in TaskInput
		if err := c.ShouldBindJSON(&in); err != nil {
			problem(c, http.StatusUnprocessableEntity, "Validation failed", err.Error())
			return
		}
		if strings.TrimSpace(in.Title) == "" { // "   " passes `required` but is still empty
			problem(c, http.StatusUnprocessableEntity, "Validation failed", "title must not be blank")
			return
		}
		s.mu.Lock()
		t := Task{ID: s.nextID, Title: strings.TrimSpace(in.Title), Done: in.Done}
		s.tasks[t.ID] = t
		s.nextID++
		s.mu.Unlock()
		c.Header("Location", "/tasks/"+strconv.Itoa(t.ID))
		c.JSON(http.StatusCreated, t)
	})

	r.GET("/tasks", func(c *gin.Context) {
		limit, offset := 100, 0
		if v := c.Query("limit"); v != "" {
			n, err := strconv.Atoi(v)
			if err != nil || n < 0 {
				problem(c, http.StatusBadRequest, "Bad Request", "limit must be a non-negative integer")
				return
			}
			limit = n
		}
		if v := c.DefaultQuery("offset", "0"); v != "" {
			n, err := strconv.Atoi(v)
			if err != nil || n < 0 {
				problem(c, http.StatusBadRequest, "Bad Request", "offset must be a non-negative integer")
				return
			}
			offset = n
		}
		var doneFilter *bool
		if v := c.Query("done"); v != "" {
			b, err := strconv.ParseBool(v)
			if err != nil {
				problem(c, http.StatusBadRequest, "Bad Request", "done must be true or false")
				return
			}
			doneFilter = &b
		}

		s.mu.RLock()
		out := make([]Task, 0, len(s.tasks))
		for id := 1; id < s.nextID; id++ { // stable order for a repeatable demo
			t, ok := s.tasks[id]
			if !ok {
				continue
			}
			if doneFilter != nil && t.Done != *doneFilter {
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
		c.JSON(http.StatusOK, out[offset:end])
	})

	r.GET("/tasks/:id", func(c *gin.Context) {
		id, err := strconv.Atoi(c.Param("id"))
		if err != nil {
			problem(c, http.StatusBadRequest, "Bad Request", "id must be an integer")
			return
		}
		s.mu.RLock()
		t, ok := s.tasks[id]
		s.mu.RUnlock()
		if !ok {
			problem(c, http.StatusNotFound, "Not Found", "no such task")
			return
		}
		c.JSON(http.StatusOK, t)
	})

	r.PATCH("/tasks/:id", func(c *gin.Context) {
		id, err := strconv.Atoi(c.Param("id"))
		if err != nil {
			problem(c, http.StatusBadRequest, "Bad Request", "id must be an integer")
			return
		}
		var p TaskPatch
		if err := c.ShouldBindJSON(&p); err != nil {
			problem(c, http.StatusBadRequest, "Bad Request", "malformed JSON: "+err.Error())
			return
		}
		s.mu.Lock()
		defer s.mu.Unlock()
		t, ok := s.tasks[id]
		if !ok {
			problem(c, http.StatusNotFound, "Not Found", "no such task")
			return
		}
		if p.Title != nil { // only touch what the client actually sent
			t.Title = *p.Title
		}
		if p.Done != nil {
			t.Done = *p.Done
		}
		s.tasks[id] = t
		c.JSON(http.StatusOK, t)
	})

	r.DELETE("/tasks/:id", func(c *gin.Context) {
		id, err := strconv.Atoi(c.Param("id"))
		if err != nil {
			problem(c, http.StatusBadRequest, "Bad Request", "id must be an integer")
			return
		}
		s.mu.Lock()
		delete(s.tasks, id) // idempotent: deleting twice, or deleting nothing, is still success
		s.mu.Unlock()
		c.Status(http.StatusNoContent)
	})

	return r
}

// ------------------------------------------------------------------- demo ---
func main() {
	gin.SetMode(gin.ReleaseMode) // quiet down Gin's own startup banner for a clean demo trace

	s := NewStore()
	srv := &http.Server{Handler: routes(s)}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	go srv.Serve(ln)
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
	show := func(label string, status int, body string) { fmt.Printf("%-28s -> %d %s\n", label, status, body) }

	// create
	st, h, b := do("POST", "/tasks", `{"title":"learn Gin","done":false}`)
	show("create", st, b)
	check(st == 201 && h.Get("Location") == "/tasks/1", "create")

	st, _, b = do("POST", "/tasks", `{"title":"write tests","done":true}`)
	show("create #2", st, b)
	check(st == 201, "create #2")

	// empty title rejected
	st, _, b = do("POST", "/tasks", `{"title":"   "}`)
	show("empty title rejected", st, b)
	check(st == 422, "empty title validation")

	// get by id: found
	st, _, b = do("GET", "/tasks/1", "")
	show("get 1", st, b)
	check(st == 200 && strings.Contains(b, "learn Gin"), "get by id")

	// get by id: bad id -> 404
	st, _, b = do("GET", "/tasks/999", "")
	show("get missing id -> 404", st, b)
	check(st == 404, "get missing id")

	// patch one field, other untouched
	st, _, b = do("PATCH", "/tasks/1", `{"done":true}`)
	show("patch done only", st, b)
	check(st == 200 && strings.Contains(b, `"done":true`) && strings.Contains(b, "learn Gin"), "patch preserves title")

	// list with query filter
	st, _, b = do("GET", "/tasks?done=true", "")
	show("list ?done=true", st, b)
	var filtered []Task
	json.Unmarshal([]byte(b), &filtered)
	check(st == 200 && len(filtered) == 2, "filter by done=true matches both tasks after patch")

	st, _, b = do("GET", "/tasks?done=false", "")
	show("list ?done=false", st, b)
	json.Unmarshal([]byte(b), &filtered)
	check(st == 200 && len(filtered) == 0, "filter by done=false matches none")

	// pagination
	st, _, b = do("GET", "/tasks?limit=1&offset=0", "")
	show("list ?limit=1&offset=0", st, b)
	json.Unmarshal([]byte(b), &filtered)
	check(st == 200 && len(filtered) == 1, "pagination limit")

	// bad query value -> 400
	st, _, b = do("GET", "/tasks?done=maybe", "")
	show("list ?done=maybe -> 400", st, b)
	check(st == 400, "bad query value")

	st, _, b = do("GET", "/tasks?limit=notanumber", "")
	show("list ?limit=notanumber -> 400", st, b)
	check(st == 400, "bad limit value")

	// delete then delete again: both 204
	st1, _, _ := do("DELETE", "/tasks/1", "")
	st2, _, _ := do("DELETE", "/tasks/1", "")
	fmt.Println("delete, delete          ->", st1, st2)
	check(st1 == 204 && st2 == 204, "idempotent delete")

	// delete then get: 404
	st, _, b = do("GET", "/tasks/1", "")
	show("get after delete -> 404", st, b)
	check(st == 404, "get after delete")

	fmt.Println("OK")
}
