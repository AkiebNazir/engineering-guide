package fuzztarget

import (
	"errors"
	"math"
	"slices"
	"testing"
)

// ---------------------------------------------------------------------
// Table-driven tests: hand-picked edge cases fuzzing seeds are drawn from.
// ---------------------------------------------------------------------

func TestUvarintRoundTripTable(t *testing.T) {
	cases := []uint64{0, 1, 63, 64, 127, 128, 129, 1 << 20, math.MaxUint32, math.MaxUint64}
	for _, x := range cases {
		enc := EncodeUvarint(x)
		got, n, err := DecodeUvarint(enc)
		if err != nil {
			t.Fatalf("DecodeUvarint(EncodeUvarint(%d)): unexpected error %v", x, err)
		}
		if got != x {
			t.Fatalf("round trip mismatch: encoded %d, decoded %d (bytes %x)", x, got, enc)
		}
		if n != len(enc) {
			t.Fatalf("DecodeUvarint consumed %d bytes, EncodeUvarint produced %d for %d", n, len(enc), x)
		}
	}
}

func TestEncodeUvarintLength(t *testing.T) {
	// Known encoding lengths: 7 bits/byte, so the boundary at 128 (2^7)
	// must flip from 1 byte to 2.
	tests := []struct {
		x    uint64
		want int
	}{
		{0, 1},
		{127, 1},
		{128, 2},
		{16383, 2},           // 2^14 - 1
		{16384, 3},           // 2^14
		{math.MaxUint64, 10}, // full width needs all 10 bytes
	}
	for _, tt := range tests {
		got := len(EncodeUvarint(tt.x))
		if got != tt.want {
			t.Errorf("len(EncodeUvarint(%d)) = %d, want %d", tt.x, got, tt.want)
		}
	}
}

func TestDecodeUvarintErrors(t *testing.T) {
	tests := []struct {
		name string
		buf  []byte
		want error
	}{
		{"empty buffer", nil, ErrTruncated},
		{"single continuation byte, nothing after", []byte{0x80}, ErrTruncated},
		{"all continuation bytes, never terminates", []byte{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}, ErrOverflow},
		{"10th byte contributes more than 1 bit", []byte{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x02}, ErrOverflow},
		{"10th byte contributes exactly 1 bit: max uint64, valid", []byte{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x01}, nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, _, err := DecodeUvarint(tt.buf)
			if !errors.Is(err, tt.want) {
				t.Errorf("DecodeUvarint(%x) error = %v, want %v", tt.buf, err, tt.want)
			}
		})
	}
}

func TestDecodeUvarintNeverPanicsTable(t *testing.T) {
	// A grab-bag of malformed/adversarial buffers a human would think of.
	// The fuzz target below explores this space far more broadly; this is
	// the "we already know these are dangerous" seed list made explicit.
	bufs := [][]byte{
		nil,
		{},
		{0x00},
		{0x80},
		{0x80, 0x80, 0x80},
		bytesRepeat(0xFF, 100),
		bytesRepeat(0xFF, 1),
		{0xFF, 0x00},
	}
	for _, b := range bufs {
		func() {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("DecodeUvarint(%x) panicked: %v", b, r)
				}
			}()
			DecodeUvarint(b)
		}()
	}
}

func bytesRepeat(b byte, n int) []byte {
	out := make([]byte, n)
	for i := range out {
		out[i] = b
	}
	return out
}

func TestCSVRoundTripTable(t *testing.T) {
	cases := [][]string{
		// Note: a zero-length []string is NOT round-trippable — JoinCSVLine([])
		// produces "" which SplitCSVLine parses back as one empty field
		// ([]string{""}), since an empty line and a single empty field are
		// indistinguishable at the line level. That's an inherent asymmetry
		// of "one line = at least one field", not a bug, so it's excluded
		// here deliberately (and the fuzz target below never generates a
		// zero-length slice, sidestepping the issue there too).
		{""},
		{"a"},
		{"a", "b", "c"},
		{"a,b", "c"},
		{`a"b`, "c"},
		{"", "", ""},
		{`quoted "" already`},
	}
	for _, fields := range cases {
		joined := JoinCSVLine(fields)
		got, err := SplitCSVLine(joined)
		if err != nil {
			t.Fatalf("SplitCSVLine(JoinCSVLine(%q)) = err %v (joined=%q)", fields, err, joined)
		}
		if !slices.Equal(got, fields) {
			t.Fatalf("round trip mismatch: fields=%q joined=%q got=%q", fields, joined, got)
		}
	}
}

func TestSplitCSVLineDirect(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		want    []string
		wantErr error
	}{
		{"empty line", "", []string{""}, nil},
		{"single field", "abc", []string{"abc"}, nil},
		{"two fields", "a,b", []string{"a", "b"}, nil},
		{"trailing comma yields empty field", "a,", []string{"a", ""}, nil},
		{"quoted with comma", `"a,b",c`, []string{"a,b", "c"}, nil},
		{"doubled quote inside quoted field", `"a""b"`, []string{`a"b`}, nil},
		{"unterminated quote", `"abc`, nil, ErrUnterminatedQuote},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := SplitCSVLine(tt.line)
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("SplitCSVLine(%q) error = %v, want %v", tt.line, err, tt.wantErr)
			}
			if tt.wantErr == nil && !slices.Equal(got, tt.want) {
				t.Fatalf("SplitCSVLine(%q) = %q, want %q", tt.line, got, tt.want)
			}
		})
	}
}

// ---------------------------------------------------------------------
// Fuzz targets.
//
// Run for real (this is the acceptance criterion, not just "compiles"):
//
//	cd 21_fuzzing_property_testing/solution
//	go test -fuzz=FuzzUvarintRoundTrip -fuzztime=10s .
//	go test -fuzz=FuzzDecodeUvarintNoPanic -fuzztime=10s .
//	go test -fuzz=FuzzCSVRoundTrip -fuzztime=10s .
//
// Each was run to completion (see the run log recorded in this file's
// sibling _solution.go header comment and the task report); all three
// ran their full -fuzztime with no crasher written to testdata/fuzz/.
// ---------------------------------------------------------------------

// FuzzUvarintRoundTrip checks the core invariant: decode(encode(x)) == x
// for every uint64, including the ones f.Fuzz generates that no human
// would think to hand-write (values straddling every 7-bit boundary).
func FuzzUvarintRoundTrip(f *testing.F) {
	seeds := []uint64{0, 1, 63, 64, 127, 128, 129, 1 << 20, math.MaxUint32, math.MaxUint64}
	for _, s := range seeds {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, x uint64) {
		enc := EncodeUvarint(x)
		if len(enc) == 0 || len(enc) > 10 {
			t.Fatalf("EncodeUvarint(%d) produced %d bytes, want 1..10", x, len(enc))
		}
		got, n, err := DecodeUvarint(enc)
		if err != nil {
			t.Fatalf("DecodeUvarint(EncodeUvarint(%d)) = err %v", x, err)
		}
		if got != x {
			t.Fatalf("round trip mismatch: x=%d encoded=%x got=%d", x, enc, got)
		}
		if n != len(enc) {
			t.Fatalf("DecodeUvarint consumed %d of %d bytes for x=%d", n, len(enc), x)
		}
	})
}

// FuzzDecodeUvarintNoPanic feeds DecodeUvarint raw, arbitrary byte slices —
// most will not be valid varints at all. The property under test is purely
// "never panics, always returns either a value+nil or 0,0,non-nil error" —
// a decoder's contract on untrusted input, independent of whether the
// bytes happen to decode to anything meaningful.
func FuzzDecodeUvarintNoPanic(f *testing.F) {
	seeds := [][]byte{
		nil,
		{},
		{0x00},
		{0x80},
		{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF},
		{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x01},
	}
	for _, s := range seeds {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, buf []byte) {
		value, n, err := DecodeUvarint(buf)
		if err != nil {
			if value != 0 || n != 0 {
				t.Fatalf("DecodeUvarint(%x) returned err %v but non-zero value=%d n=%d", buf, err, value, n)
			}
			return
		}
		if n <= 0 || n > len(buf) {
			t.Fatalf("DecodeUvarint(%x) = value=%d n=%d, n out of range", buf, value, n)
		}
	})
}

// FuzzCSVRoundTrip checks split(join(fields)) == fields for arbitrary
// generated string slices — the property JoinCSVLine/SplitCSVLine exist
// to guarantee. f.Add seeds the cases we already know are tricky: commas,
// quotes, empty fields, already-quoted-looking content.
func FuzzCSVRoundTrip(f *testing.F) {
	f.Add("a", "b", "c")
	f.Add("a,b", "c", "")
	f.Add(`a"b`, "", "")
	f.Add("", "", "")
	f.Add(`already "quoted" text`, "x", "y")

	f.Fuzz(func(t *testing.T, a, b, c string) {
		fields := []string{a, b, c}
		joined := JoinCSVLine(fields)
		got, err := SplitCSVLine(joined)
		if err != nil {
			t.Fatalf("SplitCSVLine(JoinCSVLine(%q)) = err %v (joined=%q)", fields, err, joined)
		}
		if !slices.Equal(got, fields) {
			t.Fatalf("round trip mismatch: fields=%q joined=%q got=%q", fields, joined, got)
		}
	})
}

// FuzzSplitCSVLineNoPanic feeds arbitrary strings (not necessarily
// produced by JoinCSVLine) straight into the parser — the "garbage in"
// side of the contract, independent of the round-trip property above.
func FuzzSplitCSVLineNoPanic(f *testing.F) {
	seeds := []string{
		"",
		",",
		`"`,
		`""`,
		`"a`,
		`a,"b`,
		`"a""b"`,
		`,,,`,
	}
	for _, s := range seeds {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, line string) {
		// The only property checked here is crash-freedom: SplitCSVLine
		// must return (fields, nil) or (nil, err), never panic, for any
		// string whatsoever.
		_, _ = SplitCSVLine(line)
	})
}
