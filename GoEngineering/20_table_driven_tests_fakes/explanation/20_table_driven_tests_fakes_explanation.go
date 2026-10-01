/*
Problem 20 — Table-Driven Tests & Fakes (httptest, golden files, fakes,
subtests, parallel tests)

WHAT WE'RE BUILDING

A small, real HTTP handler — GET /users/{id} — backed by a UserStore
dependency, plus (the actual point of this problem) a test file that
demonstrates the full toolkit a production Go codebase uses to test HTTP
handlers without a real database:

 1. A hand-written fake UserStore (an in-memory map, not a mock framework)
    that the test file configures per case.
 2. Table-driven subtests (t.Run per case) exercising the handler through
    httptest.NewRecorder and, separately, through a real httptest.Server
    for one end-to-end case.
 3. A golden-file test for FormatUserReport's text output, with the
    standard `-update` flag pattern for regenerating the golden file.
 4. t.Parallel() subtests, and why Go 1.22+ made this safe to reach for by
    default (per-iteration loop variables).

# WHY THIS MATTERS IN REAL SYSTEMS

Almost every HTTP handler in a real service depends on something external
— a database, another service, a clock. Testing it well means testing the
handler's *logic* (status codes, response shape, error mapping) without
spinning up that dependency. Two techniques do this:

  - **httptest** (`httptest.NewRecorder`, `httptest.NewServer`) lets you
    drive an `http.Handler` directly in-process — no real socket needed for
    NewRecorder, a real loopback listener for NewServer when you need to
    exercise the full net/http client stack (timeouts, redirects,
    connection reuse).
  - **Fakes** (a hand-written struct implementing the same interface the
    handler depends on) beat mock-generation frameworks for most cases:
    they're plain Go, debuggable with a normal debugger, and force you to
    design a real interface at the dependency boundary — which is good
    architecture independent of testing (see problem 18's ports-and-
    adapters). Reach for a generated mock only when you need to assert
    call sequences/counts a fake would be tedious to hand-track.

Golden files matter for any function whose expected output is large,
structured text (a report, a rendered template, a formatted error) where
inlining the expected string in the test would be unreadable and
painful to update. The `-update` flag convention (`go test -update`
regenerates the golden files from current output) is a de facto Go
standard, not a stdlib feature — you wire it yourself, as this file does.

CONCEPTS COVERED

  - `httptest.NewRecorder`, `httptest.NewServer`, `httptest.NewRequest`
  - A fake dependency (in-memory UserStore) vs a generated mock
  - Table-driven tests: `[]struct{ name string; ... }`, `t.Run(tt.name, ...)`
  - Golden files: `testdata/golden/*.golden`, a `-update` flag, `t.Helper()`
  - `t.Parallel()` and why Go 1.22+'s per-iteration `for` loop variable
    semantics (each iteration gets its own `tt`) made the old
    `tt := tt` capture workaround unnecessary
  - `net/http`'s 1.22+ method+pattern routing (`"GET /users/{id}"`,
    `r.PathValue("id")`)

# SPEC

User struct: ID, Name, Email (all string).

UserStore interface: GetUser(ctx context.Context, id string) (User, error)
  - Returns ErrNotFound (a sentinel) when id doesn't exist.

Handler struct wrapping a UserStore, implementing http.Handler via a
net/http.ServeMux registered on pattern "GET /users/{id}":
  - 200 + JSON body {"id":...,"name":...,"email":...} on success.
  - 404 + JSON body {"error":"not found"} if the store returns ErrNotFound.
  - 500 + JSON body {"error":"internal error"} on any other store error
    (never leak the raw error string to the client — log it, don't ship
    it).
  - 400 if {id} is empty.

FormatUserReport(u User) string
  - Deterministic, multi-line plain-text report of a User (used for the
    golden-file test — deterministic output is what makes a function
    golden-testable at all; nothing with a timestamp or map-iteration-
    order in its output belongs in a golden test without normalizing it
    first).

fakeUserStore (test-only, in solution/*_test.go): an in-memory
map[string]User implementing UserStore, with an injectable error for
testing the 500 path.

ACCEPTANCE CRITERIA

  - `go build ./20_table_driven_tests_fakes/...` and
    `go vet ./20_table_driven_tests_fakes/...` are clean.
  - `go test ./20_table_driven_tests_fakes/solution/...` passes, covering
    all four handler status codes via a single table-driven subtest set.
  - `go test -run TestFormatUserReport_Golden -update ./20_table_driven_tests_fakes/solution/...`
    regenerates testdata/golden/user_report.golden, and running the test
    again without -update passes against that file.
  - At least one subtest uses `t.Parallel()`.
*/
package httpuser

import (
	"context"
	"errors"
	"net/http"
)

// ErrNotFound is returned by UserStore.GetUser when id has no matching
// user.
var ErrNotFound = errors.New("httpuser: user not found")

// User is the JSON-serializable shape returned by the handler.
type User struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

// UserStore is the dependency boundary the handler is written against.
// The solution's fake implements exactly this interface for tests; a real
// implementation (not part of this problem) would wrap database/sql or an
// RPC client.
type UserStore interface {
	GetUser(ctx context.Context, id string) (User, error)
}

// Handler serves GET /users/{id} using Store to look users up.
//
// TODO: give Handler a Store field and a way to obtain an http.Handler
// (e.g. a Mux() method returning a *http.ServeMux, or make Handler itself
// implement ServeHTTP by delegating to an internally built mux).
type Handler struct {
	// TODO: add Store UserStore
}

// TODO: implement NewHandler, constructing the registered *http.ServeMux
// (pattern "GET /users/{id}") backed by store.
func NewHandler(store UserStore) *Handler {
	panic("TODO: implement NewHandler")
}

// TODO: implement ServeHTTP (or expose the built mux) so Handler satisfies
// http.Handler. Must handle: empty {id} -> 400, ErrNotFound -> 404, any
// other store error -> 500 (generic body, don't leak err.Error()),
// success -> 200 + JSON user.
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	panic("TODO: implement ServeHTTP")
}

// FormatUserReport renders a deterministic multi-line text report for u.
//
// TODO: implement. Must be deterministic — no timestamps, no
// map-iteration-order-dependent content — since this is the function
// under golden-file test.
func FormatUserReport(u User) string {
	panic("TODO: implement FormatUserReport")
}

/*
HINTS

  - net/http's ServeMux has supported method+pattern registration
    ("GET /users/{id}") and r.PathValue("id") since Go 1.22 — no third-
    party router needed for a path this simple.
  - Write the JSON error responses through one small helper
    (`writeJSONError(w, status, msg)`) so all four status paths share
    identical Content-Type and encoding behavior — divergent ad-hoc
    `fmt.Fprintf(w, ...)` calls per branch are a common source of subtly
    wrong Content-Type headers.
  - For the golden file: read testdata/golden/user_report.golden with
    os.ReadFile; when the `-update` flag is set, os.WriteFile the actual
    output there first and then proceed to compare (so a single test run
    with -update both regenerates AND verifies the file it just wrote).
  - `t.Helper()` inside any small test-support function (like a golden-file
    read/compare helper or a JSON-decode-response helper) makes failures
    reported at the *caller's* line, not inside the helper — do this for
    every non-trivial helper you factor out of the table loop.

COMMON PITFALLS

  - Looping over the test table with `for _, tt := range tests { t.Run(...) }`
    and calling `t.Parallel()` inside the subtest on a pre-Go-1.22 module —
    before 1.22, `tt` was one shared loop variable and every parallel
    subtest could see the *last* table entry's `tt` by the time it actually
    ran (they all start after the non-parallel part of the loop returns).
    This module's go.mod targets Go 1.22+, so this specific footgun is
    fixed language-wide — but the fix is via `go.mod`'s language version,
    not something the code opts into, so don't assume it's safe on an
    older module without checking.
  - A fake that always returns success — this tests nothing new versus not
    depending on the interface at all. A useful fake must be configurable
    to simulate at least the not-found and generic-error paths the real
    dependency can produce, or the 404/500 branches never get test
    coverage.
  - Comparing golden-file output with `==` after reading with a trailing
    newline mismatch (editor adds a final newline to the golden file, the
    function under test doesn't emit one) — normalize (e.g.
    `strings.TrimRight(s, "\n")` on both sides, consistently) or you'll get
    permanently-flaky-looking golden test failures that have nothing to do
    with the function's actual correctness.
  - Leaking the raw internal error string in a 500 response body
    (`err.Error()` sent to the client) — logs get the detail, the HTTP
    response gets a generic message; this is a real security/information-
    disclosure concern, not just style.

STRETCH GOALS

  - Add a case to the table that exercises the handler through a real
    httptest.NewServer + http.Client (not just NewRecorder), to prove the
    handler also behaves correctly through the full HTTP stack (headers,
    status line parsing) — not just against an in-process ResponseRecorder.
  - Add a `fakeUserStore` option to inject artificial latency and write a
    subtest asserting the handler still responds correctly under
    `context.WithTimeout` — connects back to problem 3's deadline handling.
  - Convert FormatUserReport's golden test to cover two different Users in
    one golden file (e.g. testdata/golden/user_report_full.golden vs
    _empty_email.golden) to show golden files scale to multiple named
    fixtures, not just one.
*/
