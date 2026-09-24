package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestChainOrder(t *testing.T) {
	var mu sync.Mutex
	var order []string
	record := func(name string) Middleware {
		return func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				mu.Lock()
				order = append(order, name+":in")
				mu.Unlock()
				next.ServeHTTP(w, r)
				mu.Lock()
				order = append(order, name+":out")
				mu.Unlock()
			})
		}
	}

	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		order = append(order, "handler")
		mu.Unlock()
	})

	h := Chain(record("A"), record("B"), record("C"))(final)
	h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/", nil))

	want := []string{"A:in", "B:in", "C:in", "handler", "C:out", "B:out", "A:out"}
	if len(order) != len(want) {
		t.Fatalf("order = %v, want %v", order, want)
	}
	for i := range want {
		if order[i] != want[i] {
			t.Fatalf("order[%d] = %q, want %q (full: %v)", i, order[i], want[i], order)
		}
	}
}

func TestChainEmpty(t *testing.T) {
	called := false
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { called = true })
	h := Chain()(final)
	h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/", nil))
	if !called {
		t.Fatal("empty Chain did not invoke final handler")
	}
}

func TestRequestID_GeneratesWhenAbsent(t *testing.T) {
	var seen string
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		seen = RequestIDFromContext(r.Context())
	})
	h := RequestID(final)
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	h.ServeHTTP(rec, req)

	if seen == "" {
		t.Fatal("no request id present in context")
	}
	if got := rec.Header().Get(RequestIDHeader); got != seen {
		t.Fatalf("response header %q = %q, want %q", RequestIDHeader, got, seen)
	}
}

func TestRequestID_ForwardsExisting(t *testing.T) {
	var seen string
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		seen = RequestIDFromContext(r.Context())
	})
	h := RequestID(final)
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set(RequestIDHeader, "client-supplied-id")
	h.ServeHTTP(rec, req)

	if seen != "client-supplied-id" {
		t.Fatalf("request id = %q, want forwarded client-supplied-id", seen)
	}
	if got := rec.Header().Get(RequestIDHeader); got != "client-supplied-id" {
		t.Fatalf("response header = %q, want client-supplied-id", got)
	}
}

func TestRequestIDFromContext_Absent(t *testing.T) {
	if got := RequestIDFromContext(context.Background()); got != "" {
		t.Fatalf("expected empty string for missing request id, got %q", got)
	}
}

func TestRecoverer_CatchesPanic(t *testing.T) {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("boom")
	})
	h := Recoverer(final)
	rec := httptest.NewRecorder()

	// Must not panic out of ServeHTTP.
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))

	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("status = %d, want 500", rec.Code)
	}
	var body apiError
	if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
		t.Fatalf("decode body: %v", err)
	}
	if body.Error.Code != "internal_error" {
		t.Fatalf("error code = %q, want internal_error", body.Error.Code)
	}
}

func TestRecoverer_PassesThroughNormalResponses(t *testing.T) {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusTeapot)
	})
	h := Recoverer(final)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Code != http.StatusTeapot {
		t.Fatalf("status = %d, want 418", rec.Code)
	}
}

func TestLogger_CapturesStatus(t *testing.T) {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusCreated)
		w.Write([]byte("hi"))
	})
	h := Logger(final)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/x", nil))
	if rec.Code != http.StatusCreated {
		t.Fatalf("status = %d, want 201", rec.Code)
	}
	if rec.Body.String() != "hi" {
		t.Fatalf("body = %q, want hi", rec.Body.String())
	}
}

func TestLogger_DefaultsTo200(t *testing.T) {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("no explicit WriteHeader"))
	})
	h := Logger(final)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/x", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}
}

func TestTimeout_FiresAndCancelsContext(t *testing.T) {
	cancelObserved := make(chan struct{})
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-r.Context().Done():
			close(cancelObserved)
		case <-time.After(2 * time.Second):
			t.Error("handler context was never canceled")
		}
	})

	h := Timeout(50 * time.Millisecond)(final)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))

	if rec.Code != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want 503", rec.Code)
	}
	var body apiError
	if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
		t.Fatalf("decode body: %v", err)
	}
	if body.Error.Code != "timeout" {
		t.Fatalf("error code = %q, want timeout", body.Error.Code)
	}

	select {
	case <-cancelObserved:
	case <-time.After(2 * time.Second):
		t.Fatal("handler goroutine never observed context cancellation (leak)")
	}
}

func TestTimeout_DoesNotFireWhenFastEnough(t *testing.T) {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	h := Timeout(1 * time.Second)(final)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}
}

func TestAuth_TableDriven(t *testing.T) {
	mw := Auth("supersecret")
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	h := mw(final)

	tests := []struct {
		name       string
		authHeader string
		wantStatus int
	}{
		{"missing header", "", http.StatusUnauthorized},
		{"wrong scheme", "Basic supersecret", http.StatusUnauthorized},
		{"wrong token", "Bearer wrongtoken", http.StatusUnauthorized},
		{"empty bearer", "Bearer ", http.StatusUnauthorized},
		{"correct token", "Bearer supersecret", http.StatusOK},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec := httptest.NewRecorder()
			req := httptest.NewRequest(http.MethodGet, "/secret", nil)
			if tt.authHeader != "" {
				req.Header.Set("Authorization", tt.authHeader)
			}
			h.ServeHTTP(rec, req)
			if rec.Code != tt.wantStatus {
				t.Fatalf("status = %d, want %d (body: %s)", rec.Code, tt.wantStatus, rec.Body.String())
			}
			if tt.wantStatus == http.StatusUnauthorized {
				var body apiError
				if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
					t.Fatalf("decode body: %v", err)
				}
				if body.Error.Code != "unauthorized" {
					t.Fatalf("error code = %q, want unauthorized", body.Error.Code)
				}
			}
		})
	}
}

func TestFullChain_PanicStillGetsRequestID(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /boom", func(w http.ResponseWriter, r *http.Request) {
		panic("kaboom")
	})
	h := Chain(RequestID, Recoverer, Logger, Timeout(time.Second))(mux)

	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/boom", nil))

	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("status = %d, want 500", rec.Code)
	}
	if rec.Header().Get(RequestIDHeader) == "" {
		t.Fatal("expected X-Request-ID header on panicked response")
	}
}

func TestFullChain_AuthRoute(t *testing.T) {
	protected := Auth("supersecret")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	mux := http.NewServeMux()
	mux.Handle("GET /secret", protected)
	h := Chain(RequestID, Recoverer, Logger, Timeout(time.Second))(mux)

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/secret", nil)
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d, want 401 without token", rec.Code)
	}

	rec = httptest.NewRecorder()
	req = httptest.NewRequest(http.MethodGet, "/secret", nil)
	req.Header.Set("Authorization", "Bearer supersecret")
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200 with valid token", rec.Code)
	}
}

func TestRequestID_UniquePerRequest(t *testing.T) {
	seenIDs := map[string]bool{}
	var mu sync.Mutex
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		seenIDs[RequestIDFromContext(r.Context())] = true
		mu.Unlock()
	})
	h := RequestID(final)

	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/", nil))
		}()
	}
	wg.Wait()

	if len(seenIDs) != 20 {
		t.Fatalf("got %d unique ids, want 20 (race or non-unique generation)", len(seenIDs))
	}
}

func TestAuth_MalformedHeaderNoPanic(t *testing.T) {
	mw := Auth("supersecret")
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
	h := mw(final)
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", strings.Repeat("x", 3)) // shorter than "Bearer "
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d, want 401 for malformed header", rec.Code)
	}
}
