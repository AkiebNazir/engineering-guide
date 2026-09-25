# REST API: The Complete Masterclass

To truly master <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> (Representational State Transfer), you must move beyond basic `GET` and `POST` commands and embrace <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> semantics, Idempotency, and Resource-Oriented Design.

## Part 1: The Core Philosophy (Resource-Oriented Design)

<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> is not a protocol; it is an architectural style built tightly around <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>. 
The biggest mistake engineers make is thinking in terms of **actions** (verbs) instead of **entities** (nouns).

**Anti-Pattern (Action-Based):**
`POST /createUser`
`GET /getAllUsers`
`POST /updateUser?id=5`

**Master Pattern (Resource-Based):**
`POST /users` (Create a user)
`GET /users` (Get all users)
`PATCH /users/5` (Update user 5)

The URL identifies the **Resource**, and the <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> Method provides the **Action**.

---

## Part 2: <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> Methods, Idempotency, and Safety

Understanding how <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> methods behave in a distributed system is critical for preventing data corruption.

1. **Safe Methods**: Do not modify data. Can be cached freely.
   - `GET`: Retrieve a resource.
   - `OPTIONS`: Ask the server what methods are allowed.

2. **Idempotent Methods**: If a client sends this request 1 time or 1,000 times, the final state on the server is exactly the same. Crucial for retries during network failures.
   - `PUT`: Completely replace a resource. If you `PUT` the same data 10 times, the resource just gets overwritten with the same data.
   - `DELETE`: Delete a resource. Deleting a deleted resource still leaves it deleted.

3. **Non-Idempotent Methods**: Calling this multiple times results in different states.
   - `POST`: Create a new resource. If a network blip causes a client to retry a `POST`, you might accidentally create two identical users! (Requires idempotency keys to fix).
   - `PATCH`: Partially update a resource. (E.g., `PATCH { "views": "+1" }` run twice adds 2 views).

---

## Part 3: Building a Real-World Project (Task <abbr title="Application Programming Interface">API</abbr>)

Let's look at how a Senior Engineer structures a <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr> in Go.

### Go Implementation (Standard Library)
```go
package main

import (
	"encoding/json"
	"net/http"
	"strings"
)

type Task struct {
	ID     string `json:"id"`
	Title  string `json:"title"`
	Status string `json:"status"`
}

var db = map[string]Task{
	"1": {ID: "1", Title: "Learn REST", Status: "IN_PROGRESS"},
}

func tasksHandler(w http.ResponseWriter, r *http.Request) {
	// Root /tasks endpoints
	switch r.Method {
	case http.MethodGet:
		// Return all tasks
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(db)
		
	case http.MethodPost:
		// Create a task
		var t Task
		json.NewDecoder(r.Body).Decode(&t)
		db[t.ID] = t
		w.WriteHeader(http.StatusCreated) // 201 Created
		json.NewEncoder(w).Encode(t)
		
	default:
		w.WriteHeader(http.StatusMethodNotAllowed) // 405 Method Not Allowed
	}
}

func singleTaskHandler(w http.ResponseWriter, r *http.Request) {
	// Extract ID from /tasks/1
	id := strings.TrimPrefix(r.URL.Path, "/tasks/")
	
	task, exists := db[id]
	if !exists {
		http.Error(w, "Task not found", http.StatusNotFound) // 404 Not Found
		return
	}

	switch r.Method {
	case http.MethodGet:
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(task)
		
	case http.MethodPut:
		// Complete Replacement
		var t Task
		json.NewDecoder(r.Body).Decode(&t)
		t.ID = id // Enforce URL ID
		db[id] = t
		w.WriteHeader(http.StatusOK) // 200 OK
		
	case http.MethodDelete:
		delete(db, id)
		w.WriteHeader(http.StatusNoContent) // 204 No Content (Standard for DELETE)
	}
}
```

---

## Part 4: Production Mastery & Advanced Concepts

### 1. <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> Status Codes (The Vocabulary of <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>)
Do not return `200 OK` for errors with a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> body `{"error": true}`. Use standard <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> codes so load balancers, proxies, and clients can react automatically.
- **201 Created**: Successful `POST`.
- **204 No Content**: Successful `DELETE` or empty `PUT`.
- **400 Bad Request**: The client sent malformed <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> or failed validation.
- **401 Unauthorized**: Missing or invalid Auth Token.
- **403 Forbidden**: Token is valid, but user lacks permissions.
- **404 Not Found**: Resource doesn't exist.
- **409 Conflict**: Trying to register an email that already exists.
- **429 Too Many Requests**: Rate limiting kicked in.
- **500 Internal Server Error**: Your backend code crashed.

### 2. Pagination (Offset vs. Cursor)
Never return `GET /users` with 10,000 records.
- **Offset Pagination**: `?limit=10&offset=20`. Simple to implement with <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> (`LIMIT 10 OFFSET 20`). **Problem**: Terrible performance on large tables, and prone to skipping records if data is inserted during pagination.
- **Cursor Pagination**: `?limit=10&after=cursor_xyz`. **Master approach**. The cursor is usually an encoded timestamp or ID. `WHERE id > cursor LIMIT 10`. O(1) performance and stable.

### 3. Caching (ETag & Cache-Control)
A true <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr> leverages the web's caching infrastructure.
- The server sends a `GET` response with an `ETag: "v1.0"` (a hash of the data).
- The client stores it. On the next request, the client sends `If-None-Match: "v1.0"`.
- The server checks the DB. If the data hasn't changed, the server returns **304 Not Modified** with an *empty body*. This saves massive bandwidth and <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> parsing time!

### 4. HATEOAS (Hypermedia as the Engine of Application State)
The highest level of <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> maturity (Richardson Maturity Model Level 3). 
A resource includes hyperlinks to state transitions, allowing the client to dynamically discover what actions it can take.
```json
{
  "id": "123",
  "status": "PENDING",
  "links": {
     "self": "/orders/123",
     "cancel": "/orders/123/cancel",
     "pay": "/orders/123/pay"
  }
}
```
If the status changes to `PAID`, the backend stops returning the `cancel` link, and the frontend dynamically hides the cancel button.
