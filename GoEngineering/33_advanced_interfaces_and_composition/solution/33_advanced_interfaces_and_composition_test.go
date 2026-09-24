package ifaces

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// 1. nil interfaces
// ----------------------------------------------------------------------------

func TestLesson_TypedNilIsNotNil(t *testing.T) {
	err := ValidateBad("alice") // valid input!
	if err == nil {
		t.Fatal("expected the typed-nil bug to produce a non-nil error")
	}
	t.Logf("ValidateBad(valid) → err != nil is %v; dynamic type %T, value %v", err != nil, err, reflect.ValueOf(err).IsNil())

	if err := Validate("alice"); err != nil {
		t.Fatalf("Validate(valid) = %v", err)
	}

	var verr *ValidationError
	if err := Validate(""); !errors.As(err, &verr) || verr.Field != "name" {
		t.Fatalf("errors.As should still find the concrete type: %v", err)
	}
}

func TestIsNil(t *testing.T) {
	var p *ValidationError
	var m map[string]int
	var s []int
	var f func()
	cases := []struct {
		v    any
		want bool
	}{
		{nil, true}, {p, true}, {m, true}, {s, true}, {f, true},
		{0, false}, {"", false}, {&ValidationError{}, false}, {[]int{}, false},
	}
	for _, c := range cases {
		if got := IsNil(c.v); got != c.want {
			t.Errorf("IsNil(%#v) = %v, want %v", c.v, got, c.want)
		}
	}
}

// ----------------------------------------------------------------------------
// 2. Decorators
// ----------------------------------------------------------------------------

func TestCountingStoreOverridesOnlyGet(t *testing.T) {
	var s Store = NewCountingStore(NewMemStore())
	_ = s.Set("a", "1") // promoted from the embedded Store
	_, _ = s.Get("a")
	_, err := s.Get("missing")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("err = %v", err)
	}
	_ = s.Delete("a") // promoted

	gets, misses := s.(*CountingStore).Stats()
	if gets != 2 || misses != 1 {
		t.Fatalf("gets=%d misses=%d, want 2/1", gets, misses)
	}
}

func TestLesson_NilEmbeddedInterfacePanicsOnPromotedMethods(t *testing.T) {
	c := &CountingStore{} // bypassed the constructor: Store is nil
	defer func() {
		r := recover()
		if r == nil {
			t.Fatal("expected a nil pointer dereference")
		}
		t.Logf("promoted method on nil embedded interface → panic: %v", r)
	}()
	_ = c.Set("k", "v")
}

// ----------------------------------------------------------------------------
// 3. Optional interfaces through wrappers
// ----------------------------------------------------------------------------

func TestLesson_WrapperHidesFlusherButResponseControllerFindsIt(t *testing.T) {
	var sawFlusherAssertion bool
	var flushErr error
	var statuses []int

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, sawFlusherAssertion = w.(http.Flusher) // what pre-1.20 code does
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusAccepted)
		for i := range 3 {
			fmt.Fprintf(w, "event %d\n", i)
			flushErr = http.NewResponseController(w).Flush() // unwraps StatusRecorder
			if flushErr != nil {
				return
			}
			time.Sleep(5 * time.Millisecond)
		}
	})
	srv := httptest.NewServer(RecordStatus(handler, func(s int) { statuses = append(statuses, s) }))
	defer srv.Close()

	resp, err := http.Get(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	sc := bufio.NewScanner(resp.Body)
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}

	if sawFlusherAssertion {
		t.Fatal("StatusRecorder unexpectedly satisfied http.Flusher via type assertion")
	}
	if flushErr != nil {
		t.Fatalf("ResponseController.Flush through the wrapper failed: %v", flushErr)
	}
	if len(lines) != 3 || resp.StatusCode != http.StatusAccepted || len(statuses) != 1 || statuses[0] != http.StatusAccepted {
		t.Fatalf("lines=%v status=%d recorded=%v", lines, resp.StatusCode, statuses)
	}
	t.Log("w.(http.Flusher) through the middleware: false; http.NewResponseController(w).Flush(): ok (via Unwrap)")
}

func TestStatusRecorderImplicit200(t *testing.T) {
	var got int
	h := RecordStatus(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, "ok") // no explicit WriteHeader
	}), func(s int) { got = s })
	h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/", nil))
	if got != http.StatusOK {
		t.Fatalf("status = %d", got)
	}
}

func TestCountingWriterComposesWithStdlib(t *testing.T) {
	var buf bytes.Buffer
	cw := &CountingWriter{W: &buf}
	var _ io.Writer = cw
	n, err := io.Copy(cw, strings.NewReader(strings.Repeat("x", 10_000)))
	if err != nil || n != 10_000 || cw.N != 10_000 || buf.Len() != 10_000 {
		t.Fatalf("n=%d N=%d buf=%d err=%v", n, cw.N, buf.Len(), err)
	}
}

// ----------------------------------------------------------------------------
// 4. Type switches
// ----------------------------------------------------------------------------

type both struct{}

func (both) Error() string  { return "boom" }
func (both) String() string { return "pretty" }

type celsius float64

func (c celsius) String() string { return fmt.Sprintf("%.1f°C", float64(c)) }

func TestDescribe(t *testing.T) {
	cases := []struct {
		in   any
		want string
	}{
		{nil, "nil"},
		{errors.New("disk full"), "error: disk full"},
		{both{}, "error: boom"}, // error case listed first wins
		{celsius(21.5), "stringer: 21.5°C"},
		{"héllo", "string(6): héllo"},
		{[]byte("abc"), "bytes(3)"},
		{int16(-7), "int: -7"},
		{map[string]any{"b": 1, "a": 2}, "object{a,b}"},
		{3.14, "other: float64"},
		{(*ValidationError)(nil), "error: invalid "}, // typed nil still matches `error`...
	}
	for _, c := range cases {
		func() {
			defer func() {
				if r := recover(); r != nil {
					// ...and calling Error() on it dereferences nil.
					if c.want != "error: invalid " {
						t.Errorf("Describe(%#v) panicked: %v", c.in, r)
					}
				}
			}()
			if got := Describe(c.in); got != c.want {
				t.Errorf("Describe(%#v) = %q, want %q", c.in, got, c.want)
			}
		}()
	}
}

// ----------------------------------------------------------------------------
// 5. Method sets
// ----------------------------------------------------------------------------

func TestLesson_MethodSets(t *testing.T) {
	if _, ok := AsIncrementer(Counter{}); ok {
		t.Fatal("Counter (value) must not satisfy Incrementer")
	}
	c := &Counter{}
	inc, ok := AsIncrementer(c)
	if !ok {
		t.Fatal("*Counter must satisfy Incrementer")
	}
	inc.Inc()
	inc.Inc()
	if c.Value() != 2 {
		t.Fatalf("Value = %d", c.Value())
	}

	valueMethods := reflect.TypeFor[Counter]().NumMethod()
	ptrMethods := reflect.TypeFor[*Counter]().NumMethod()
	if valueMethods != 1 || ptrMethods != 2 {
		t.Fatalf("method sets: Counter=%d *Counter=%d, want 1 and 2", valueMethods, ptrMethods)
	}
	t.Logf("method set sizes: Counter=%d {Value}, *Counter=%d {Inc, Value}", valueMethods, ptrMethods)

	// Copy trap: calling Inc on a copy changes the copy.
	orig := Counter{}
	cp := orig
	cp.Inc() // legal: cp is addressable, Go rewrites to (&cp).Inc()
	if orig.Value() != 0 || cp.Value() != 1 {
		t.Fatal("copies must be independent")
	}
}

// ----------------------------------------------------------------------------
// 6. Embedding is not inheritance
// ----------------------------------------------------------------------------

func TestLesson_NoVirtualDispatchThroughEmbedding(t *testing.T) {
	s := Service{Greeter: Greeter{Prefix: "> "}, ID: "billing"}
	if s.Name() != "service billing" {
		t.Fatalf("shadowing: %q", s.Name())
	}
	if s.Greeter.Name() != "greeter" {
		t.Fatalf("explicit selector: %q", s.Greeter.Name())
	}
	// Greet is promoted, but its receiver is the embedded Greeter, which
	// calls Greeter.Name — not Service.Name.
	if got := s.Greet(); got != "> hello from greeter" {
		t.Fatalf("Greet = %q", got)
	}
	t.Logf("s.Name()=%q but s.Greet()=%q — promoted methods don't see the outer type's overrides", s.Name(), s.Greet())
}

// ----------------------------------------------------------------------------
// 7. Comparable interfaces
// ----------------------------------------------------------------------------

func TestLesson_UnhashableDynamicTypePanics(t *testing.T) {
	counts, err := CountKeys("a", 1, "a", [2]int{1, 2})
	if err != nil || counts["a"] != 2 || counts[[2]int{1, 2}] != 1 {
		t.Fatalf("comparable keys: %v %v", counts, err)
	}
	_, err = CountKeys("a", []int{1, 2}) // compiles fine, panics at run time
	if err == nil || !strings.Contains(err.Error(), "unhashable") {
		t.Fatalf("expected unhashable key error, got %v", err)
	}
	t.Log(err)
}

// ----------------------------------------------------------------------------
// Benchmarks — the cost of dynamic dispatch
// ----------------------------------------------------------------------------

type adder struct{ total int }

//go:noinline
func (a *adder) Add(n int) { a.total += n }

type Adder interface{ Add(int) }

func BenchmarkCallConcrete(b *testing.B) {
	a := &adder{}
	for i := 0; b.Loop(); i++ {
		a.Add(i)
	}
}

func BenchmarkCallInterface(b *testing.B) {
	var a Adder = &adder{}
	for i := 0; b.Loop(); i++ {
		a.Add(i)
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleValidateBad() {
	err := ValidateBad("valid-name")
	fmt.Println(err == nil, err != nil)
	fmt.Printf("%T\n", err)
	// Output:
	// false true
	// *ifaces.ValidationError
}

func ExampleCountingStore() {
	store := NewCountingStore(NewMemStore())
	_ = store.Set("user:1", "ada")
	v, _ := store.Get("user:1")
	_, err := store.Get("user:2")
	gets, misses := store.Stats()
	fmt.Println(v, errors.Is(err, ErrNotFound), gets, misses)
	// Output: ada true 2 1
}

func ExampleDescribe() {
	for _, v := range []any{nil, 42, "go", errors.New("eof"), []byte{1, 2}} {
		fmt.Println(Describe(v))
	}
	// Output:
	// nil
	// int: 42
	// string(2): go
	// error: eof
	// bytes(2)
}
