/*
FOUNDATION LEVEL 11 - Putting it all together: one complete, PROTECTED CRUD resource
========================================================================================
Nothing new here. Every idea from levels 00-10 - routing, JSON, path params,
query params, body validation, real status codes, headers, middleware,
authentication, and authorization - combined on one resource, end to end.
Reads are public; writes require a valid bearer token (level 09); deleting
requires the "admin" role specifically (level 10). This is deliberately the
same shape as ../../labs/golang/02_json_crud_validation and
../../labs/golang/05_api_key_auth_and_ownership: once this feels easy, those
labs (real auth schemes, rate limiting, Gin/Echo frameworks) are the very
next step, not a jump.

You will learn
  - how the previous 10 small lessons compose into one real-looking, real-
    SECURED API
  - that "a REST API" is not one big new idea - it is these small ideas,
    layered together, in a deliberate order (route -> validate -> authenticate
    -> authorize -> act)

Run it         go run ./REST/Foundation/golang/11_complete_in_memory_crud
Keep serving   go run ./REST/Foundation/golang/11_complete_in_memory_crud -serve   (curl -i localhost:8080/tasks)
*/
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
	"strings"
)

type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

type identity struct {
	User string
	Role string
}

var (
	tasks  = map[int]Task{}
	nextID = 1

	// level 09/10's identity table, unchanged in shape - a real service
	// verifies a signed JWT or looks a token up in a database instead.
	tokens = map[string]identity{
		"alice-token": {User: "alice", Role: "admin"},
		"bob-token":   {User: "bob", Role: "viewer"},
	}
)

func sendJSON(w http.ResponseWriter, status int, payload any, headers map[string]string) {
	for k, v := range headers {
		w.Header().Set(k, v)
	}
	if payload != nil {
		w.Header().Set("Content-Type", "application/json")
	}
	w.WriteHeader(status)
	if payload != nil {
		json.NewEncoder(w).Encode(payload)
	}
}

func taskID(path string) (int, bool) {
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 2 || parts[0] != "tasks" {
		return 0, false
	}
	id, err := strconv.Atoi(parts[1])
	return id, err == nil
}

// level 09's authentication check, reused as a plain function.
func authenticate(r *http.Request) (identity, bool) {
	token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
	if !ok {
		return identity{}, false
	}
	id, known := tokens[token]
	return id, known
}

func handler(w http.ResponseWriter, r *http.Request) {
	id, hasID := taskID(r.URL.Path)

	switch {
	// ---- Read: public, collection with a query filter (levels 01 + 04) -----
	case r.Method == http.MethodGet && r.URL.Path == "/tasks":
		q := r.URL.Query()
		results := make([]Task, 0, len(tasks))
		for _, t := range tasks {
			results = append(results, t)
		}
		if v := q.Get("done"); v != "" {
			wanted := v == "true"
			filtered := []Task{}
			for _, t := range results {
				if t.Done == wanted {
					filtered = append(filtered, t)
				}
			}
			results = filtered
		}
		sendJSON(w, http.StatusOK, results, nil)

	case r.Method == http.MethodGet && hasID:
		if t, ok := tasks[id]; ok {
			sendJSON(w, http.StatusOK, t, nil)
		} else {
			sendJSON(w, http.StatusNotFound, map[string]string{"error": "task not found"}, nil)
		}

	// ---- Create: authenticated + body validation + 201/Location -----------
	case r.Method == http.MethodPost && r.URL.Path == "/tasks":
		// level 09: writes require SOMEONE to be identified - reads never did.
		if _, ok := authenticate(r); !ok {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing or invalid bearer token"}, nil)
			return
		}
		var body struct {
			Title string `json:"title"`
			Done  bool   `json:"done"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Title == "" {
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "'title' is required"}, nil)
			return
		}
		t := Task{ID: nextID, Title: body.Title, Done: body.Done}
		tasks[nextID] = t
		nextID++
		sendJSON(w, http.StatusCreated, t, map[string]string{"Location": fmt.Sprintf("/tasks/%d", t.ID)})

	case r.Method == http.MethodPost:
		sendJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "POST is only allowed on /tasks"}, map[string]string{"Allow": "GET"})

	// ---- Replace: authenticated (levels 06 + 09) ----------------------------
	case r.Method == http.MethodPut && hasID:
		if _, ok := authenticate(r); !ok {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing or invalid bearer token"}, nil)
			return
		}
		if _, ok := tasks[id]; !ok {
			sendJSON(w, http.StatusNotFound, map[string]string{"error": "task not found"}, nil)
			return
		}
		var body struct {
			Title string `json:"title"`
			Done  bool   `json:"done"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Title == "" {
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "PUT replaces the whole task: 'title' is required"}, nil)
			return
		}
		tasks[id] = Task{ID: id, Title: body.Title, Done: body.Done}
		sendJSON(w, http.StatusOK, tasks[id], nil)

	// ---- Remove: authenticated AND authorized (levels 06 + 09 + 10) --------
	case r.Method == http.MethodDelete && hasID:
		who, ok := authenticate(r)
		if !ok {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing or invalid bearer token"}, nil)
			return
		}
		if who.Role != "admin" {
			sendJSON(w, http.StatusForbidden, map[string]string{"error": "requires role 'admin'"}, nil)
			return
		}
		delete(tasks, id) // idempotent, same as level 06's DELETE
		sendJSON(w, http.StatusNoContent, nil, nil)

	default:
		sendJSON(w, http.StatusNotFound, map[string]string{"error": "not found"}, nil)
	}
}

func call(method, base, path, body, token string) (int, http.Header, string) {
	var reqBody io.Reader
	if body != "" {
		reqBody = strings.NewReader(body)
	}
	req, _ := http.NewRequest(method, base+path, reqBody)
	if body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, res.Header, string(b)
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	if *serve {
		log.Println("listening on http://localhost:8080")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", http.HandlerFunc(handler)))
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	s, _, b := call("POST", base, "/tasks", `{"title": "learn REST from zero"}`, "")
	fmt.Printf("POST /tasks  (no token)             -> %d %s   (writes need authentication)\n", s, b)
	if s != 401 {
		panic("FAILED")
	}

	s, h, b := call("POST", base, "/tasks", `{"title": "learn REST from zero"}`, "bob-token")
	fmt.Printf("POST /tasks  (bob, viewer)          -> %d Location=%s %s", s, h.Get("Location"), b)
	if s != 201 {
		panic("FAILED")
	}

	call("POST", base, "/tasks", `{"title": "already done", "done": true}`, "bob-token")

	s, _, b = call("GET", base, "/tasks?done=true", "", "")
	fmt.Printf("GET  /tasks?done=true  (public, no token) -> %d %s", s, b)
	if s != 200 || !strings.Contains(b, "already done") {
		panic("FAILED")
	}

	s, _, b = call("PUT", base, "/tasks/1", `{"title": "learn REST from zero", "done": true}`, "bob-token")
	fmt.Printf("PUT  /tasks/1  (bob, viewer)         -> %d %s", s, b)
	if s != 200 {
		panic("FAILED")
	}

	s, _, b = call("DELETE", base, "/tasks/1", "", "bob-token")
	fmt.Printf("DELETE /tasks/1  (bob, viewer)       -> %d %s   (authenticated, but wrong role)\n", s, b)
	if s != 403 {
		panic("FAILED")
	}

	s1, _, _ := call("DELETE", base, "/tasks/1", "", "alice-token")
	s2, _, _ := call("DELETE", base, "/tasks/1", "", "alice-token")
	fmt.Printf("DELETE /tasks/1 x2  (alice, admin)   -> %d, %d\n", s1, s2)
	if s1 != 204 || s2 != 204 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
