package cgounsafe

import (
	"fmt"
	"strings"
	"testing"
	"unsafe"
)

// Test files cannot `import "C"`, so everything goes through the exported
// wrappers — which is also how real code should isolate cgo.

func TestCWrappers(t *testing.T) {
	if got := CAdd(40, 2); got != 42 {
		t.Fatalf("CAdd = %d, want 42", got)
	}

	cases := []struct {
		in   string
		want int
		why  string
	}{
		{"hello", 5, "ASCII: bytes == runes"},
		{"héllo", 6, "é is 2 bytes in UTF-8; C counts bytes"},
		{"", 0, "empty string still gets a NUL-terminated C buffer"},
		{"ab\x00cd", 2, "C stops at the first NUL; Go strings may contain NUL"},
	}
	for _, c := range cases {
		if got := CStrlen(c.in); got != c.want {
			t.Errorf("CStrlen(%q) = %d, want %d (%s)", c.in, got, c.want, c.why)
		}
	}

	if got := CUpper("hello, cgo 123"); got != "HELLO, CGO 123" {
		t.Fatalf("CUpper = %q", got)
	}

	xs := []int32{1, 2, 3, -4, 2147483647, 2147483647}
	if got, want := SumInt32(xs), int64(1+2+3-4)+2*2147483647; got != want {
		t.Fatalf("SumInt32 = %d, want %d (int64 accumulator must not overflow)", got, want)
	}
	if SumInt32(nil) != 0 {
		t.Fatal("SumInt32(nil) must be 0 without touching &xs[0]")
	}
}

func TestPointerPassingRuleIsEnforced(t *testing.T) {
	err := CheckPointerRule()
	if err == nil {
		t.Fatal("expected cgocheck to reject a Go pointer to memory containing a Go pointer (is GODEBUG=cgocheck=0 set?)")
	}
	if !strings.Contains(err.Error(), "Go pointer") {
		t.Fatalf("unexpected error: %v", err)
	}
	t.Logf("runtime said: %v", err)
}

func TestStructLayout(t *testing.T) {
	if PtrSize != 8 {
		t.Skipf("layout numbers below are for 64-bit; PtrSize=%d", PtrSize)
	}

	padded, pf := Layout(Padded{})
	packed, _ := Layout(Packed{})
	if padded != 40 || packed != 24 {
		t.Fatalf("Sizeof(Padded)=%d Sizeof(Packed)=%d, want 40 and 24", padded, packed)
	}
	// Layout must agree with the compiler's own answers.
	if unsafe.Offsetof(Padded{}.Score) != pf[3].Offset || unsafe.Sizeof(Padded{}) != padded {
		t.Fatal("Layout disagrees with unsafe.Offsetof/Sizeof")
	}

	for _, f := range pf {
		t.Logf("Padded.%-6s offset=%2d size=%d align=%d", f.Name, f.Offset, f.Size, f.Align)
	}
	const n = 10_000_000
	t.Logf("%d elements: Padded %d MB vs Packed %d MB (%d MB saved just by reordering)",
		n, padded*n>>20, packed*n>>20, (padded-packed)*n>>20)
}

// TestLesson_ZeroCopyAliasing proves the hazard: the string changes when the
// bytes it was built from change.
func TestLesson_ZeroCopyAliasing(t *testing.T) {
	b := []byte("hello")
	safe := string(b)        // copies
	fast := BytesToString(b) // aliases

	b[0] = 'J'

	if safe != "hello" {
		t.Fatalf("string(b) changed to %q — it should be an independent copy", safe)
	}
	if fast != "Jello" {
		t.Fatalf("BytesToString result = %q; expected it to alias b and read Jello", fast)
	}
	t.Logf("after b[0]='J': string(b)=%q  BytesToString(b)=%q  ← 'immutable' string mutated", safe, fast)

	// Same backing memory, provably.
	if unsafe.StringData(fast) != &b[0] {
		t.Fatal("expected BytesToString to share the backing array")
	}

	// Round trip the other way (read-only use only).
	s := "gopher"
	bs := StringToBytes(s)
	if len(bs) != 6 || bs[0] != 'g' || &bs[0] != unsafe.StringData(s) {
		t.Fatal("StringToBytes should alias s")
	}
	if StringToBytes("") != nil || BytesToString(nil) != "" {
		t.Fatal("empty conversions")
	}
}

func TestZeroCopyAllocations(t *testing.T) {
	b := []byte(strings.Repeat("x", 64))
	var sink string

	copying := testing.AllocsPerRun(1000, func() { sink = string(b) })
	zeroCopy := testing.AllocsPerRun(1000, func() { sink = BytesToString(b) })
	_ = sink

	if zeroCopy != 0 {
		t.Fatalf("BytesToString allocs = %v, want 0", zeroCopy)
	}
	if copying < 1 {
		t.Fatalf("string(b) allocs = %v; expected the escaping copy to allocate", copying)
	}
	t.Logf("allocs/op: string(b)=%v BytesToString=%v", copying, zeroCopy)
}

func TestInt64At(t *testing.T) {
	xs := []int64{10, 20, 30}
	for i, want := range xs {
		if got, ok := Int64At(xs, i); !ok || got != want {
			t.Fatalf("Int64At(%d) = %d,%v want %d,true", i, got, ok, want)
		}
	}
	for _, i := range []int{-1, 3, 100} {
		if _, ok := Int64At(xs, i); ok {
			t.Fatalf("Int64At(%d) should be out of range", i)
		}
	}
}

// ----------------------------------------------------------------------------
// Benchmarks — what does crossing into C cost?
// ----------------------------------------------------------------------------

//go:noinline
func goAdd(a, b int) int { return a + b }

var sinkInt int

func BenchmarkGoAddNoInline(b *testing.B) {
	for i := 0; b.Loop(); i++ {
		sinkInt = goAdd(i, 1)
	}
}

func BenchmarkCAdd(b *testing.B) {
	for i := 0; b.Loop(); i++ {
		sinkInt = CAdd(i, 1)
	}
}

var sinkI64 int64

// One C call for 4096 elements vs 4096 Go iterations. Measured on an Apple
// M4 Pro (go1.26): C 155 ns/op vs Go 3664 ns/op. The ~14 ns crossing cost is
// amortised over the batch, and clang auto-vectorises the C loop while the Go
// compiler emits a scalar loop — so batched C wins by ~24x here, whereas
// per-element CAdd loses ~10x to a plain Go call.
func BenchmarkSumInt32C(b *testing.B) {
	xs := make([]int32, 4096)
	for i := range xs {
		xs[i] = int32(i)
	}
	for b.Loop() {
		sinkI64 = SumInt32(xs)
	}
}

func BenchmarkSumInt32Go(b *testing.B) {
	xs := make([]int32, 4096)
	for i := range xs {
		xs[i] = int32(i)
	}
	for b.Loop() {
		var total int64
		for _, x := range xs {
			total += int64(x)
		}
		sinkI64 = total
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleCUpper() {
	fmt.Println(CUpper("make it loud"))
	fmt.Println(CStrlen("naïve")) // ï is two bytes
	// Output:
	// MAKE IT LOUD
	// 6
}

func ExampleLayout() {
	if PtrSize != 8 {
		fmt.Println("64-bit only example")
		return
	}
	size, fields := Layout(Padded{})
	fmt.Println("Padded size:", size)
	for _, f := range fields {
		fmt.Printf("  %-6s @%-2d size %d\n", f.Name, f.Offset, f.Size)
	}
	size, _ = Layout(Packed{})
	fmt.Println("Packed size:", size)
	// Output:
	// Padded size: 40
	//   Active @0  size 1
	//   ID     @8  size 8
	//   Flags  @16 size 2
	//   Score  @24 size 8
	//   Kind   @32 size 1
	// Packed size: 24
}

func ExampleBytesToString() {
	buf := []byte("cache-key-42")
	key := BytesToString(buf) // no allocation, shares buf
	fmt.Println(key)
	buf[len(buf)-1] = '3' // violating the contract...
	fmt.Println(key)      // ...silently changes the "immutable" string
	// Output:
	// cache-key-42
	// cache-key-43
}
