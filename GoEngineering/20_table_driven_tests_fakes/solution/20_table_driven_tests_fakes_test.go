package httpuser

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// -update regenerates golden files from the current output instead of
// comparing against them. This is the de facto Go convention for golden
// tests — not a stdlib feature, wired here by hand.
var update = flag.Bool("update", false, "update golden files")

// fakeUserStore is a hand-written in-memory UserStore. Unlike a generated
// mock it's plain Go: readable, debuggable with a normal debugger, and
// configurable per table case without mock-framework ceremony. When err is
// set it takes priority over users, letting one fake simulate both the
// not-found path (a lookup miss) and the generic-error path (err set).
type fakeUserStore struct {
	users map[string]User
	err   error
}

func (f *fakeUserStore) GetUser(_ context.Context, id string) (User, error) {
	if f.err != nil {
		return User{}, f.err
	}
	u, ok := f.users[id]
	if !ok {
		return User{}, ErrNotFound
	}
	return u, nil
}

// TestHandler_GetUser drives the handler through httptest.NewRecorder for
// every status-code branch in one table, each case its own parallel subtest.
func TestHandler_GetUser(t *testing.T) {
	tests := []struct {
		name       string
		path       string
		store      *fakeUserStore
		wantStatus int
		wantUser   *User // non-nil only for the 200 case
	}{
		{
			name:       "empty id",
			path:       "/users/",
			store:      &fakeUserStore{users: map[string]User{}},
			wantStatus: http.StatusBadRequest,
		},
		{
			name:       "not found",
			path:       "/users/missing",
			store:      &fakeUserStore{users: map[string]User{}},
			wantStatus: http.StatusNotFound,
		},
		{
			name:       "store error",
			path:       "/users/u1",
			store:      &fakeUserStore{err: errors.New("connection reset by peer")},
			wantStatus: http.StatusInternalServerError,
		},
		{
			name: "success",
			path: "/users/u1",
			store: &fakeUserStore{users: map[string]User{
				"u1": {ID: "u1", Name: "Ada Lovelace", Email: "ada@example.com"},
			}},
			wantStatus: http.StatusOK,
			wantUser:   &User{ID: "u1", Name: "Ada Lovelace", Email: "ada@example.com"},
		},
	}

	for _, tt := range tests {
		// Go 1.22+ gives each loop iteration its own tt, so this closure
		// safely captures the current case even though t.Run schedules the
		// parallel subtest to actually run later, after the loop has moved
		// on — no `tt := tt` capture workaround needed on this module's
		// go.mod language version.
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			h := NewHandler(tt.store)
			req := httptest.NewRequest(http.MethodGet, tt.path, nil)
			rec := httptest.NewRecorder()
			h.ServeHTTP(rec, req)

			if rec.Code != tt.wantStatus {
				t.Fatalf("status = %d, want %d (body: %s)", rec.Code, tt.wantStatus, rec.Body.String())
			}
			if ct := rec.Header().Get("Content-Type"); ct != "application/json" {
				t.Errorf("Content-Type = %q, want application/json", ct)
			}

			if tt.wantUser != nil {
				var got User
				if err := json.NewDecoder(rec.Body).Decode(&got); err != nil {
					t.Fatalf("decode response body: %v", err)
				}
				if got != *tt.wantUser {
					t.Errorf("body = %+v, want %+v", got, *tt.wantUser)
				}
				return
			}

			// Every non-200 path must carry a generic {"error": ...} body —
			// and, critically, never the fake's raw internal error string,
			// which would be an information-disclosure bug if this were a
			// real backend error reaching a client.
			var body map[string]string
			if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
				t.Fatalf("decode error body: %v", err)
			}
			if body["error"] == "" {
				t.Errorf("error body missing \"error\" key: %v", body)
			}
			if tt.store.err != nil && strings.Contains(body["error"], tt.store.err.Error()) {
				t.Errorf("error body leaked internal error string: %v", body)
			}
		})
	}
}

// TestHandler_GetUser_RealServer exercises the handler through a real
// httptest.NewServer + http.Client, not just an in-process ResponseRecorder
// — proving it also behaves correctly through the full net/http client
// stack (status line parsing, real headers over a real loopback socket),
// which NewRecorder alone never touches.
func TestHandler_GetUser_RealServer(t *testing.T) {
	store := &fakeUserStore{users: map[string]User{
		"u1": {ID: "u1", Name: "Ada Lovelace", Email: "ada@example.com"},
	}}
	srv := httptest.NewServer(NewHandler(store))
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/users/u1")
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	var got User
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatalf("decode: %v", err)
	}
	want := User{ID: "u1", Name: "Ada Lovelace", Email: "ada@example.com"}
	if got != want {
		t.Errorf("body = %+v, want %+v", got, want)
	}
}

// TestFormatUserReport_Golden checks FormatUserReport's output against
// testdata/golden/user_report.golden. Run with
//
//	go test -run TestFormatUserReport_Golden -update ./20_table_driven_tests_fakes/solution/...
//
// to regenerate the golden file from current output; run without -update
// (the normal case) to verify against it.
func TestFormatUserReport_Golden(t *testing.T) {
	got := FormatUserReport(User{ID: "u1", Name: "Ada Lovelace", Email: "ada@example.com"})
	golden := filepath.Join("testdata", "golden", "user_report.golden")

	if *update {
		if err := os.MkdirAll(filepath.Dir(golden), 0o755); err != nil {
			t.Fatalf("mkdir golden dir: %v", err)
		}
		if err := os.WriteFile(golden, []byte(got), 0o644); err != nil {
			t.Fatalf("write golden file: %v", err)
		}
	}

	want := readGolden(t, golden)
	// Trailing-newline differences between an editor-saved golden file and
	// the function's own output are cosmetic, not a real mismatch — trim
	// both sides the same way so this test only fails on an actual content
	// difference.
	if strings.TrimRight(got, "\n") != strings.TrimRight(want, "\n") {
		t.Errorf("FormatUserReport output does not match golden file %s\n--- got ---\n%s\n--- want ---\n%s", golden, got, want)
	}
}

func readGolden(t *testing.T, path string) string {
	t.Helper()
	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open golden file %s: %v (run with -update to create it)", path, err)
	}
	defer f.Close()
	b, err := io.ReadAll(f)
	if err != nil {
		t.Fatalf("read golden file %s: %v", path, err)
	}
	return string(b)
}
