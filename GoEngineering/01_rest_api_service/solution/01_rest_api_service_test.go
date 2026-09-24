package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// newTestServer spins up a real httptest.Server so tests exercise actual
// Go 1.22 method+path routing (including the automatic 405 behavior),
// rather than calling handlers directly and bypassing the mux.
func newTestServer(t *testing.T) (*httptest.Server, *TaskStore) {
	t.Helper()
	store := NewTaskStore()
	srv := httptest.NewServer(newMux(store))
	t.Cleanup(srv.Close)
	return srv, store
}

func doJSON(t *testing.T, method, url string, body any) *http.Response {
	t.Helper()
	var reader *bytes.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal request body: %v", err)
		}
		reader = bytes.NewReader(b)
	} else {
		reader = bytes.NewReader(nil)
	}
	req, err := http.NewRequest(method, url, reader)
	if err != nil {
		t.Fatalf("build request: %v", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("do request: %v", err)
	}
	return resp
}

func decodeInto(t *testing.T, resp *http.Response, v any) {
	t.Helper()
	defer resp.Body.Close()
	if err := json.NewDecoder(resp.Body).Decode(v); err != nil {
		t.Fatalf("decode response body: %v", err)
	}
}

func TestHealthz(t *testing.T) {
	srv, _ := newTestServer(t)
	resp := doJSON(t, http.MethodGet, srv.URL+"/healthz", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
}

func TestCreateAndGetTask(t *testing.T) {
	srv, _ := newTestServer(t)

	resp := doJSON(t, http.MethodPost, srv.URL+"/tasks", createTaskRequest{Title: "write tests"})
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("create status = %d, want 201", resp.StatusCode)
	}
	var created Task
	decodeInto(t, resp, &created)
	if created.Title != "write tests" {
		t.Fatalf("created.Title = %q, want %q", created.Title, "write tests")
	}
	if created.ID == "" {
		t.Fatal("created.ID is empty")
	}

	resp2 := doJSON(t, http.MethodGet, srv.URL+"/tasks/"+created.ID, nil)
	if resp2.StatusCode != http.StatusOK {
		t.Fatalf("get status = %d, want 200", resp2.StatusCode)
	}
	var fetched Task
	decodeInto(t, resp2, &fetched)
	if fetched != created {
		t.Fatalf("fetched = %+v, want %+v", fetched, created)
	}
}

func TestGetTaskNotFound(t *testing.T) {
	srv, _ := newTestServer(t)
	resp := doJSON(t, http.MethodGet, srv.URL+"/tasks/does-not-exist", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("status = %d, want 404", resp.StatusCode)
	}
	var body apiError
	decodeInto(t, resp, &body)
	if body.Error.Code != "not_found" {
		t.Fatalf("error.code = %q, want %q", body.Error.Code, "not_found")
	}
}

func TestCreateTaskValidation(t *testing.T) {
	tests := []struct {
		name string
		body string // raw JSON, so we can send deliberately malformed input
		want string // expected error code
	}{
		{"empty title", `{"title": "   "}`, "validation_failed"},
		{"missing title", `{}`, "validation_failed"},
		{"title too long", `{"title": "` + strings.Repeat("x", 201) + `"}`, "validation_failed"},
		{"unknown field", `{"title": "ok", "extra": 1}`, "bad_request"},
		{"malformed json", `{"title": `, "bad_request"},
		{"trailing garbage", `{"title":"a"}{"title":"b"}`, "bad_request"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			srv, _ := newTestServer(t)
			req, err := http.NewRequest(http.MethodPost, srv.URL+"/tasks", strings.NewReader(tt.body))
			if err != nil {
				t.Fatalf("build request: %v", err)
			}
			req.Header.Set("Content-Type", "application/json")
			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				t.Fatalf("do request: %v", err)
			}
			if resp.StatusCode != http.StatusBadRequest {
				t.Fatalf("status = %d, want 400", resp.StatusCode)
			}
			var body apiError
			decodeInto(t, resp, &body)
			if body.Error.Code != tt.want {
				t.Fatalf("error.code = %q, want %q", body.Error.Code, tt.want)
			}
		})
	}
}

func TestListTasksOrderAndUpdateDelete(t *testing.T) {
	srv, _ := newTestServer(t)

	var created []Task
	for _, title := range []string{"first", "second", "third"} {
		resp := doJSON(t, http.MethodPost, srv.URL+"/tasks", createTaskRequest{Title: title})
		var task Task
		decodeInto(t, resp, &task)
		created = append(created, task)
	}

	listResp := doJSON(t, http.MethodGet, srv.URL+"/tasks", nil)
	var list []Task
	decodeInto(t, listResp, &list)
	if len(list) != 3 {
		t.Fatalf("len(list) = %d, want 3", len(list))
	}
	for i, task := range list {
		if task.ID != created[i].ID {
			t.Fatalf("list order mismatch at %d: got %s, want %s", i, task.ID, created[i].ID)
		}
	}

	// Update the second task.
	target := created[1]
	updResp := doJSON(t, http.MethodPut, srv.URL+"/tasks/"+target.ID, updateTaskRequest{Title: "second (edited)", Done: true})
	if updResp.StatusCode != http.StatusOK {
		t.Fatalf("update status = %d, want 200", updResp.StatusCode)
	}
	var updated Task
	decodeInto(t, updResp, &updated)
	if updated.Title != "second (edited)" || !updated.Done {
		t.Fatalf("updated = %+v, want title %q done true", updated, "second (edited)")
	}
	if updated.ID != target.ID || !updated.CreatedAt.Equal(target.CreatedAt) {
		t.Fatalf("update must preserve ID and CreatedAt: got %+v, original %+v", updated, target)
	}

	// Delete the first task.
	delResp := doJSON(t, http.MethodDelete, srv.URL+"/tasks/"+created[0].ID, nil)
	defer delResp.Body.Close()
	if delResp.StatusCode != http.StatusNoContent {
		t.Fatalf("delete status = %d, want 204", delResp.StatusCode)
	}

	getResp := doJSON(t, http.MethodGet, srv.URL+"/tasks/"+created[0].ID, nil)
	defer getResp.Body.Close()
	if getResp.StatusCode != http.StatusNotFound {
		t.Fatalf("get after delete status = %d, want 404", getResp.StatusCode)
	}

	// Deleting again is a 404, not a 500 or a silent no-op.
	delAgainResp := doJSON(t, http.MethodDelete, srv.URL+"/tasks/"+created[0].ID, nil)
	defer delAgainResp.Body.Close()
	if delAgainResp.StatusCode != http.StatusNotFound {
		t.Fatalf("second delete status = %d, want 404", delAgainResp.StatusCode)
	}
}

func TestMethodNotAllowed(t *testing.T) {
	srv, _ := newTestServer(t)
	// Go 1.22's ServeMux returns 405 automatically for a registered path
	// hit with a method that has no matching pattern.
	resp := doJSON(t, http.MethodPatch, srv.URL+"/tasks", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want 405", resp.StatusCode)
	}
}

// TestStoreConcurrentAccess exercises TaskStore directly (no HTTP layer)
// under concurrent readers and writers. Run with `go test -race` to prove
// the RWMutex actually prevents data races rather than merely assuming it.
func TestStoreConcurrentAccess(t *testing.T) {
	store := NewTaskStore()
	const n = 100

	done := make(chan struct{})
	for i := 0; i < n; i++ {
		go func(i int) {
			defer func() { done <- struct{}{} }()
			task := store.Create("concurrent")
			store.List()
			_, _ = store.Get(task.ID)
			_, _ = store.Update(task.ID, "updated", true)
		}(i)
	}
	for i := 0; i < n; i++ {
		<-done
	}

	if got := len(store.List()); got != n {
		t.Fatalf("len(store.List()) = %d, want %d", got, n)
	}
}
