/*
Problem 27 — cgo and unsafe (calling C, pointer-passing rules, memory
layout, padding, zero-copy conversions)

WHAT WE'RE BUILDING

A small package that crosses the two "escape hatches" of Go's safety model
and PROVES, with runnable tests, what each one costs:

 1. cgo wrappers — CAdd, CStrlen, CUpper, SumInt32 — calling C functions
    defined in the file's cgo preamble, managing C memory correctly
    (C.CString / C.free), and passing a Go slice to C legally.
 2. CheckPointerRule — deliberately violates the cgo pointer-passing rule
    and returns the runtime panic as an error, so you see the rule enforced
    instead of reading about it.
 3. Struct layout — Padded vs Packed: the same five fields in two orders,
    40 bytes vs 24 bytes on 64-bit, plus a Layout() helper that prints
    offset/size/alignment of every field.
 4. Zero-copy conversions — BytesToString / StringToBytes using
    unsafe.String, unsafe.StringData, unsafe.Slice, unsafe.SliceData
    (Go 1.20+), and a test that shows the aliasing hazard live.
 5. Pointer arithmetic — Int64At using unsafe.Add, with manual bounds
    checking because the compiler no longer does it for you.

WHY THIS MATTERS IN REAL SYSTEMS

Real Go services hit these features more often than people expect:

  - cgo: SQLite (mattn/go-sqlite3), librdkafka (confluent-kafka-go), image
    codecs, GPU/ML runtimes, OS APIs without a pure-Go binding, HSMs and
    vendor SDKs. Every one of them changes your build (needs a C toolchain,
    CGO_ENABLED=1, breaks trivial cross-compilation, breaks static
    "FROM scratch" images unless you link statically) and your runtime
    (each call crosses a scheduler boundary).
  - unsafe: every high-performance serialization, networking and database
    library uses it somewhere (zero-copy []byte→string for map keys,
    reading packed binary headers, strings.Builder itself). You must be
    able to review such code and recognise when it is wrong.
  - Struct layout: a 16-byte saving per element in a []Event with 50M
    entries is 800 MB of RAM and a noticeably faster GC mark phase.

MENTAL MODEL 1 — WHAT A CGO CALL ACTUALLY DOES

    Go goroutine (on a small, growable Go stack)
         │  C.add(a, b)
         ▼
    ┌────────────────────────────────────────────────────────────┐
    │ runtime.cgocall                                            │
    │   1. mark the goroutine's M as "in a C call"               │
    │   2. switch from the goroutine stack to the M's system     │
    │      stack (C needs a big, fixed stack)                    │
    │   3. tell the scheduler: if C blocks, hand this P to       │
    │      another M so other goroutines keep running            │
    └────────────────────────────────────────────────────────────┘
         │
         ▼
    C function runs on an OS thread; the Go GC will NOT move or
    scan memory that C allocated; C cannot be preempted by Go.
         │
         ▼
    return path: switch stacks back, re-acquire a P, resume goroutine

Consequences:
  - Per-call overhead is real. Measured on this machine (Apple M4 Pro,
    go1.26, `go test -bench .`):

        BenchmarkGoAddNoInline    1.65 ns/op   (plain non-inlined Go call)
        BenchmarkCAdd            15.70 ns/op   (same addition through cgo)

    ~14 ns per crossing. Irrelevant for one call per request, fatal for one
    call per element in a hot loop. Batch work into ONE C call.
  - Batching can flip the result entirely. Summing 4096 int32s:

        BenchmarkSumInt32C        155 ns/op    (one cgo call; clang -O2
                                                auto-vectorises the loop)
        BenchmarkSumInt32Go      3664 ns/op    (Go's compiler emits a
                                                scalar loop)

    The 14 ns crossing is noise next to the ~24x SIMD win. Measure; don't
    assume "cgo is slow" or "cgo is fast".
  - A C call that blocks for a long time pins an OS thread. Thousands of
    concurrent blocking C calls = thousands of OS threads.
  - The C compiler cannot inline across the boundary and the Go compiler
    cannot see into C, so escape analysis treats C-bound pointers
    conservatively.

MENTAL MODEL 2 — WHO OWNS WHICH MEMORY

    ┌─────────────── Go heap (GC-managed) ───────────────┐
    │  s := "hello"          []int32{1,2,3}              │
    └────────────────────────────────────────────────────┘
               │ C.CString(s)  copies bytes + NUL via malloc
               ▼
    ┌─────────────── C heap (malloc/free) ───────────────┐
    │  "hello\0"   ◀── YOU must C.free this, the GC       │
    │                  never will. Leak otherwise.        │
    └────────────────────────────────────────────────────┘
               │ C.GoString(p)  copies back into the Go heap
               ▼
         new Go string (safe to keep after free)

	cs := C.CString(s)              // malloc'd copy
	defer C.free(unsafe.Pointer(cs)) // free takes void*, hence unsafe.Pointer
	n := C.strlen(cs)

THE CGO POINTER-PASSING RULES (ENFORCED BY CGOCHECK)

  - Go code MAY pass a Go pointer to C, provided the Go memory it points
    to does not itself contain any unpinned Go pointers.
    Passing &xs[0] of a []int32 is fine: int32s contain no pointers.
    Passing &holder where holder is struct{ p *int } panics with
    "argument of cgo function has Go pointer to unpinned Go pointer".
  - C code must not keep a copy of a Go pointer after the call returns
    (the GC may move or free that memory). If it must, pin it with
    runtime.Pinner (Go 1.21+) and Unpin when C is done.
  - Go code must not store a Go pointer in C memory (unless pinned).
  - C code may return C pointers freely; they are invisible to the GC.

MENTAL MODEL 3 — ALIGNMENT AND PADDING

Every type has an alignment: a field of type T must start at an offset that
is a multiple of unsafe.Alignof(T). The compiler inserts padding to make it
so, and the struct's total size is rounded up to its largest field
alignment (so arrays of the struct line up too). Go NEVER reorders fields.

    type Padded struct {          offset  size
        Active bool               0       1   ▓░░░░░░░   7 bytes padding
        ID     int64              8       8   ▓▓▓▓▓▓▓▓
        Flags  uint16             16      2   ▓▓░░░░░░   6 bytes padding
        Score  float64            24      8   ▓▓▓▓▓▓▓▓
        Kind   uint8              32      1   ▓░░░░░░░   7 bytes tail padding
    }                             Sizeof = 40 bytes, 20 of them wasted

    type Packed struct {          offset  size
        ID     int64              0       8   ▓▓▓▓▓▓▓▓
        Score  float64            8       8   ▓▓▓▓▓▓▓▓
        Flags  uint16             16      2   ▓▓
        Active bool               18      1     ▓
        Kind   uint8              19      1      ▓░░░░   4 bytes tail padding
    }                             Sizeof = 24 bytes

Rule of thumb: order fields from largest alignment to smallest. The
fieldalignment analyzer (golang.org/x/tools/go/analysis/passes/fieldalignment)
finds these automatically. Don't reorder blindly, though: grouping fields
that are read together can matter more for cache locality, and a zero-size
field (struct{}) at the END of a struct forces extra padding so a pointer to
it doesn't point past the allocation.

MENTAL MODEL 4 — THE UNSAFE.POINTER CONVERSION RULES

unsafe.Pointer is the only type that converts to and from every pointer
type and uintptr. The compiler and GC understand it; uintptr is just an
integer the GC does NOT treat as a reference. The valid patterns
(from the unsafe package docs) include:

  - *T1 → unsafe.Pointer → *T2, when T2 is no larger than T1 and shares
    an equivalent memory layout.
  - unsafe.Pointer → uintptr → unsafe.Pointer with arithmetic, but ONLY in
    a single expression: p = unsafe.Pointer(uintptr(p) + off). Storing the
    uintptr in a variable first lets the GC move/free the object in between.
    Prefer unsafe.Add(p, off), which has no such trap.
  - Converting syscall/reflect results (reflect.Value.Pointer) in the same
    expression that uses them.

Go 1.20 added purpose-built helpers that replace most hand-rolled header
hacks (the old reflect.StringHeader / SliceHeader tricks are deprecated):

	unsafe.String(ptr *byte, len) string     // build a string over existing bytes
	unsafe.StringData(s string) *byte         // pointer to a string's bytes
	unsafe.Slice(ptr *T, len) []T             // build a slice over existing memory
	unsafe.SliceData(s []T) *T                // pointer to a slice's backing array

MENTAL MODEL 5 — ZERO-COPY CONVERSION AND ALIASING

    b := []byte("hello")                 string(b) — the SAFE way
    ┌─┬─┬─┬─┬─┐                          ┌─┬─┬─┬─┬─┐   ┌─┬─┬─┬─┬─┐
    │h│e│l│l│o│ ◀── b                     │h│e│l│l│o│   │h│e│l│l│o│ ◀── copy
    └─┴─┴─┴─┴─┘                          └─┴─┴─┴─┴─┘   └─┴─┴─┴─┴─┘
         ▲                                    b          s (1 alloc)
         └── s := BytesToString(b)  NO copy, NO alloc, SAME memory

    b[0] = 'J'  →  s now reads "Jello". Strings are supposed to be
    immutable; map keys built from s silently corrupt; a string you
    passed to another goroutine races with the writer.

The reverse, StringToBytes, is worse: a string literal lives in read-only
memory, so writing through the returned slice is a SIGSEGV/bus error that
recover() cannot catch.

When zero-copy is legitimate: the []byte is never modified again for the
lifetime of the string (e.g. converting a freshly read buffer you then
discard). Note the compiler already avoids the copy for m[string(b)] map
lookups, string(b) == "literal" comparisons, and switch string(b) — so
measure before reaching for unsafe.

SPEC

	const PtrSize = unsafe.Sizeof(uintptr(0))

	func CAdd(a, b int) int                 // calls C add()
	func CStrlen(s string) int              // C strlen over a C copy of s; frees it
	func CUpper(s string) string            // C upper-cases a C copy in place; frees it
	func SumInt32(xs []int32) int64         // one C call over the Go slice's memory
	func CheckPointerRule() error           // violates the rule; returns the recovered panic as error

	type Padded struct { Active bool; ID int64; Flags uint16; Score float64; Kind uint8 }
	type Packed struct { ID int64; Score float64; Flags uint16; Active bool; Kind uint8 }
	type FieldInfo struct { Name string; Offset, Size, Align uintptr }
	func Layout(v any) (size uintptr, fields []FieldInfo)   // v must be a struct value

	func BytesToString(b []byte) string     // zero-copy; "" for empty input
	func StringToBytes(s string) []byte     // zero-copy; nil for ""; MUST NOT be written to
	func Int64At(xs []int64, i int) (int64, bool)  // unsafe.Add; false when out of range

ACCEPTANCE CRITERIA

  - `go test -v ./27_cgo_and_unsafe/solution/...` passes (needs
    CGO_ENABLED=1 and a C compiler: `go env CGO_ENABLED` must print 1).
  - CStrlen("héllo") == 6: C counts BYTES, not runes.
  - CheckPointerRule returns an error mentioning "Go pointer".
  - Sizeof(Padded) == 40 and Sizeof(Packed) == 24 on 64-bit platforms.
  - A test shows that mutating the []byte after BytesToString changes the
    string, and that BytesToString performs 0 allocations.

HOW TO RUN

	go test -v ./27_cgo_and_unsafe/solution/...
	go test -run Example -v ./27_cgo_and_unsafe/solution/...
	go test -run '^$' -bench . -benchmem ./27_cgo_and_unsafe/solution/...
	GODEBUG=cgocheck=0 go test ...   # disables the check; NEVER in production

HINTS

  - cgo types: C.int, C.size_t, C.int32_t, C.int64_t. Convert explicitly:
    int(C.add(C.int(a), C.int(b))).
  - Passing a slice: (*C.int32_t)(unsafe.Pointer(&xs[0])) — guard len==0
    first, &xs[0] on an empty slice panics.
  - CheckPointerRule: `defer func(){ if r := recover(); r != nil { err = fmt.Errorf("%v", r) } }()`
    then pass unsafe.Pointer(&holder) where holder contains a *int.
  - Layout: reflect.TypeOf(v).Field(i).Offset is exactly unsafe.Offsetof.
  - Int64At: unsafe.Add(unsafe.Pointer(unsafe.SliceData(xs)), i*8) then
    dereference as *int64. Check 0 <= i < len(xs) BEFORE doing that.

COMMON PITFALLS

  - Forgetting C.free → a C heap leak that no Go tool (pprof heap, GC
    stats) will ever show you. Look at process RSS instead.
  - Freeing and then using: C.GoString after C.free is use-after-free.
  - `import "C"` must come IMMEDIATELY after the preamble comment with no
    blank line, or cgo silently ignores the preamble.
  - //export functions in a file forbid DEFINITIONS in that file's preamble
    (declarations only) — duplicate symbol link errors otherwise.
  - Storing uintptr(unsafe.Pointer(&x)) in a variable and converting back
    later: the GC does not see a uintptr as a reference.
  - Assuming layout: sizes differ on 32-bit (int, uintptr, pointers are 4
    bytes). Tests that assert 40/24 must guard on PtrSize == 8.
  - 64-bit atomics on 32-bit platforms: plain int64 fields used with
    atomic.AddInt64 must be first in the struct for alignment. atomic.Int64
    (Go 1.19+) handles alignment for you — prefer it.

STRETCH GOALS

  - Add an //export'ed Go callback that C calls back into (needs a second
    file whose preamble only DECLARES functions).
  - Use runtime.Pinner to hand a Go buffer to C that C keeps across calls.
  - Build with CGO_ENABLED=0 and provide a pure-Go fallback file guarded by
    //go:build !cgo so the package still compiles.
*/

package cgounsafe

/*
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static int add(int a, int b) { return a + b; }

static void upper_inplace(char *s) {
    for (; *s; s++) *s = (char)toupper((unsigned char)*s);
}

static int64_t sum_int32(const int32_t *xs, size_t n) {
    int64_t total = 0;
    for (size_t i = 0; i < n; i++) total += xs[i];
    return total;
}

static void touch(void *p) { (void)p; }
*/
import "C"

import "unsafe"

// PtrSize is the size of a pointer on this platform (8 on 64-bit).
const PtrSize = unsafe.Sizeof(uintptr(0))

// ============================================================================
// 1. cgo wrappers
// ============================================================================

// CAdd calls the C function add.
func CAdd(a, b int) int {
	// TODO: return int(C.add(C.int(a), C.int(b)))
	panic("not implemented")
}

// CStrlen returns C's strlen of s (a byte count).
func CStrlen(s string) int {
	// TODO: cs := C.CString(s); defer C.free(unsafe.Pointer(cs)); return int(C.strlen(cs))
	panic("not implemented")
}

// CUpper upper-cases ASCII letters of s using C.
func CUpper(s string) string {
	// TODO: C.CString → C.upper_inplace → C.GoString (BEFORE free) → free.
	panic("not implemented")
}

// SumInt32 sums xs in a single C call over the Go slice's own memory.
func SumInt32(xs []int32) int64 {
	// TODO: guard empty; pass (*C.int32_t)(unsafe.Pointer(&xs[0])), C.size_t(len(xs)).
	panic("not implemented")
}

// CheckPointerRule passes C a pointer to Go memory that itself contains a Go
// pointer, and returns the runtime's panic as an error.
func CheckPointerRule() (err error) {
	// TODO: recover into err; holder := struct{ p *int }{p: new(int)};
	// C.touch(unsafe.Pointer(&holder))
	panic("not implemented")
}

// ============================================================================
// 2. Memory layout
// ============================================================================

// Padded declares fields in an order that wastes space.
type Padded struct {
	Active bool
	ID     int64
	Flags  uint16
	Score  float64
	Kind   uint8
}

// Packed holds the same fields ordered largest-alignment first.
type Packed struct {
	// TODO: reorder Padded's fields to minimise padding.
}

// FieldInfo describes one struct field's placement in memory.
type FieldInfo struct {
	Name   string
	Offset uintptr
	Size   uintptr
	Align  uintptr
}

// Layout reports the size of struct value v and the placement of each field.
func Layout(v any) (size uintptr, fields []FieldInfo) {
	// TODO: t := reflect.TypeOf(v); panic if not a struct;
	// for each field: Name, Offset, Type.Size(), uintptr(Type.Align()).
	panic("not implemented")
}

// ============================================================================
// 3. Zero-copy conversions and pointer arithmetic
// ============================================================================

// BytesToString returns a string sharing b's memory. b must not be modified
// afterwards.
func BytesToString(b []byte) string {
	// TODO: unsafe.String(unsafe.SliceData(b), len(b)); handle len 0.
	panic("not implemented")
}

// StringToBytes returns a slice sharing s's memory. The result must never be
// written to.
func StringToBytes(s string) []byte {
	// TODO: unsafe.Slice(unsafe.StringData(s), len(s)); nil for "".
	panic("not implemented")
}

// Int64At returns xs[i] using pointer arithmetic, with manual bounds checks.
func Int64At(xs []int64, i int) (int64, bool) {
	// TODO: bounds check; unsafe.Add(unsafe.Pointer(unsafe.SliceData(xs)), i*int(unsafe.Sizeof(int64(0)))).
	panic("not implemented")
}
