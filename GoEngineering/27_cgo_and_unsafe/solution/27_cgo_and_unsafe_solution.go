// Package cgounsafe is the reference solution for Problem 27 — cgo and
// unsafe. Build requirement: CGO_ENABLED=1 and a C compiler on PATH.
package cgounsafe

/*
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Functions in a cgo preamble are compiled by the C compiler into this
// package. `static` keeps them file-local so they can't collide with symbols
// from other packages' preambles at link time.
static int add(int a, int b) { return a + b; }

static void upper_inplace(char *s) {
    for (; *s; s++) *s = (char)toupper((unsigned char)*s);
}

static int64_t sum_int32(const int32_t *xs, size_t n) {
    int64_t total = 0;
    for (size_t i = 0; i < n; i++) total += xs[i];
    return total;
}

// touch ignores its argument; it exists so we can pass Go memory to C and let
// cgocheck inspect it.
static void touch(void *p) { (void)p; }
*/
import "C" // must directly follow the preamble — no blank line in between

import (
	"fmt"
	"reflect"
	"unsafe"
)

// PtrSize is the size of a pointer on this platform (8 on 64-bit).
const PtrSize = unsafe.Sizeof(uintptr(0))

// ============================================================================
// 1. cgo wrappers
// ============================================================================

// CAdd calls the C function add. Go's int and C's int are different types
// (Go int is 64-bit on amd64/arm64, C int is 32-bit), so every value crossing
// the boundary is converted explicitly — cgo refuses implicit conversions.
func CAdd(a, b int) int {
	return int(C.add(C.int(a), C.int(b)))
}

// CStrlen returns C's strlen of s. It counts BYTES up to the first NUL, so
// "héllo" is 6, not 5, and a Go string containing "\x00" is truncated.
func CStrlen(s string) int {
	// C.CString mallocs len(s)+1 bytes in the C heap and copies s into it.
	// The Go GC has no idea this memory exists, so we free it ourselves.
	cs := C.CString(s)
	defer C.free(unsafe.Pointer(cs))
	return int(C.strlen(cs))
}

// CUpper upper-cases ASCII letters of s using C. Demonstrates the full
// round trip: Go → C copy → C mutates → copy back to Go → free C memory.
func CUpper(s string) string {
	cs := C.CString(s)
	defer C.free(unsafe.Pointer(cs)) // runs AFTER GoString below has copied

	C.upper_inplace(cs)
	// C.GoString copies into a new Go string, so the result stays valid after
	// the deferred free. Returning a string that aliased cs would be a
	// use-after-free.
	return C.GoString(cs)
}

// SumInt32 sums xs in ONE C call over the Go slice's own memory — no copy.
//
// This is legal under the pointer-passing rules because an []int32's backing
// array contains no Go pointers, and C does not retain the pointer after
// returning. Batching the whole slice into one call amortises the cgo
// crossing cost; calling C once per element would be dominated by overhead.
func SumInt32(xs []int32) int64 {
	if len(xs) == 0 {
		return 0 // &xs[0] would panic with index out of range
	}
	return int64(C.sum_int32((*C.int32_t)(unsafe.Pointer(&xs[0])), C.size_t(len(xs))))
}

// CheckPointerRule passes C a pointer to Go memory that itself contains a Go
// pointer. With the default GODEBUG=cgocheck=1, the runtime detects this
// before entering C and panics; we recover and return that panic as an error
// so the rule can be observed in a test instead of crashing the process.
func CheckPointerRule() (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("cgo rejected call: %v", r)
		}
	}()

	holder := struct{ p *int }{p: new(int)}
	// The GC could move/free *holder.p while C holds it, and C can't tell the
	// GC it's using it — hence the rule. runtime.Pinner is the sanctioned way
	// to make this legal when you genuinely need it.
	C.touch(unsafe.Pointer(&holder))
	return nil
}

// ============================================================================
// 2. Memory layout
// ============================================================================

// Padded declares fields in an order that wastes space: 40 bytes on 64-bit,
// 20 of which are padding. See the explanation file's diagram.
type Padded struct {
	Active bool    // offset 0, then 7 bytes padding so ID aligns to 8
	ID     int64   // offset 8
	Flags  uint16  // offset 16, then 6 bytes padding
	Score  float64 // offset 24
	Kind   uint8   // offset 32, then 7 bytes tail padding (size multiple of 8)
}

// Packed holds the same fields ordered by descending alignment: 24 bytes.
type Packed struct {
	ID     int64   // offset 0
	Score  float64 // offset 8
	Flags  uint16  // offset 16
	Active bool    // offset 18
	Kind   uint8   // offset 19, then 4 bytes tail padding
}

// FieldInfo describes one struct field's placement in memory.
type FieldInfo struct {
	Name   string
	Offset uintptr
	Size   uintptr
	Align  uintptr
}

// Layout reports the size of struct value v and the placement of each field.
// reflect.StructField.Offset is computed by the same rules as
// unsafe.Offsetof; reflect is used here only so Layout works for any struct.
func Layout(v any) (size uintptr, fields []FieldInfo) {
	t := reflect.TypeOf(v)
	if t == nil || t.Kind() != reflect.Struct {
		panic(fmt.Sprintf("cgounsafe.Layout: want struct, got %v", t))
	}
	fields = make([]FieldInfo, 0, t.NumField())
	for i := range t.NumField() {
		f := t.Field(i)
		fields = append(fields, FieldInfo{
			Name:   f.Name,
			Offset: f.Offset,
			Size:   f.Type.Size(),
			Align:  uintptr(f.Type.Align()),
		})
	}
	return t.Size(), fields
}

// ============================================================================
// 3. Zero-copy conversions and pointer arithmetic
// ============================================================================

// BytesToString returns a string that shares b's memory: no allocation, no
// copy. The caller promises never to modify b again — if they do, the
// "immutable" string changes underneath every holder of it.
func BytesToString(b []byte) string {
	if len(b) == 0 {
		return ""
	}
	return unsafe.String(unsafe.SliceData(b), len(b))
}

// StringToBytes returns a []byte that shares s's memory. It must NEVER be
// written to: string data may live in read-only memory (literals), where a
// write is a fatal fault that recover() cannot catch.
func StringToBytes(s string) []byte {
	if s == "" {
		return nil
	}
	return unsafe.Slice(unsafe.StringData(s), len(s))
}

// Int64At returns xs[i] via pointer arithmetic. unsafe.Add does no bounds
// checking at all — reading past the end returns whatever bytes are there
// (another object, or an unmapped page) — so the check is done by hand.
// This is purely instructional: xs[i] compiles to the same load plus a bounds
// check the compiler can often prove away.
func Int64At(xs []int64, i int) (int64, bool) {
	if i < 0 || i >= len(xs) {
		return 0, false
	}
	base := unsafe.Pointer(unsafe.SliceData(xs))
	p := (*int64)(unsafe.Add(base, i*int(unsafe.Sizeof(int64(0)))))
	return *p, true
}
