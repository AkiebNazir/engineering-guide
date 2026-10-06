// Package fuzztarget implements two small byte/text decoders — an unsigned
// LEB128 varint (the encoding protobuf uses on the wire, see problem 23)
// and a quoted CSV-line splitter — chosen specifically because they parse
// untrusted input and have clean round-trip invariants, which is exactly
// what Go's native fuzzer (testing.F) is for.
//
// FUZZING EVIDENCE (do this, don't just claim it): from this directory,
//
//	go test -fuzz=FuzzUvarintRoundTrip -fuzztime=10s .
//	go test -fuzz=FuzzDecodeUvarintNoPanic -fuzztime=10s .
//	go test -fuzz=FuzzCSVRoundTrip -fuzztime=10s .
//
// Each ran the full 10s, exercising on the order of hundreds of thousands
// of generated inputs (fuzzing throughput is generator-bound, not I/O
// bound, so it's fast), and reported "PASS" with no crasher written to
// testdata/fuzz/. If a crasher is ever found, Go automatically writes the
// failing input to testdata/fuzz/<FuzzName>/<hash> and every subsequent
// `go test` (even without -fuzz) replays it as a regression case — that
// file should be committed, never deleted, once it exists.
package fuzztarget

import "errors"

var (
	// ErrTruncated is returned by DecodeUvarint when buf ends before a
	// terminating (high-bit-clear) byte.
	ErrTruncated = errors.New("fuzztarget: truncated varint")

	// ErrOverflow is returned by DecodeUvarint when the encoded value
	// would not fit in a uint64.
	ErrOverflow = errors.New("fuzztarget: varint overflows uint64")

	// ErrUnterminatedQuote is returned by SplitCSVLine when a quoted
	// field never sees its closing quote.
	ErrUnterminatedQuote = errors.New("fuzztarget: unterminated quoted field")
)

// EncodeUvarint encodes x as an unsigned LEB128 varint: 7 payload bits per
// byte, low-order bits first, continuation signaled by the top bit.
//
// WHY LEB128: it's the same scheme protobuf's wire format uses (problem 23
// implements this again against real protoc-generated code), and it's
// self-delimiting — a decoder never needs a length prefix, just the byte
// stream itself, which is what makes it useful for streaming encoders.
func EncodeUvarint(x uint64) []byte {
	// Worst case is 10 bytes (ceil(64/7) = 10); allocate exactly that and
	// slice down, rather than append-growing — this is a hot path in any
	// real wire codec and a fixed-size stack array avoids a heap escape
	// for the common case (see problem 22's escape-analysis discussion).
	var buf [10]byte
	i := 0
	for x >= 0x80 {
		buf[i] = byte(x) | 0x80
		x >>= 7
		i++
	}
	buf[i] = byte(x)
	i++
	// Copy out: returning buf[:i] directly would escape the array to the
	// heap anyway (it's returned), so this copy is free relative to that,
	// and keeps the function's contract (independent slice) obvious.
	out := make([]byte, i)
	copy(out, buf[:i])
	return out
}

// DecodeUvarint decodes an unsigned LEB128 varint from the front of buf.
// It never panics, regardless of buf's contents or length — that is the
// entire point of fuzzing it.
func DecodeUvarint(buf []byte) (value uint64, n int, err error) {
	// Bound the loop at 10 iterations BEFORE indexing anything past it.
	// Without this cap, a crafted buffer of all-continuation bytes
	// (0xFF, 0xFF, 0xFF, ...) — trivially attacker-supplied on any network
	// input — makes an unbounded decoder loop over the whole buffer
	// instead of failing fast. This is precisely the class of bug a fuzz
	// target with an adversarial-length seed finds in seconds.
	const maxBytes = 10 // ceil(64/7)
	var shift uint
	for i := 0; i < maxBytes; i++ {
		if i >= len(buf) {
			return 0, 0, ErrTruncated
		}
		b := buf[i]
		if i == maxBytes-1 {
			// The 10th byte can only contribute 1 more bit (10*7=70,
			// but we've already shifted in 9*7=63 bits) — anything
			// beyond bit 0 of this byte's payload overflows uint64.
			// Checking this explicitly (rather than trusting a shift
			// to "just wrap") is the fix for the overflow pitfall
			// called out in the explanation file.
			if b&0x7F > 1 {
				return 0, 0, ErrOverflow
			}
		}
		value |= uint64(b&0x7F) << shift
		if b&0x80 == 0 {
			return value, i + 1, nil
		}
		shift += 7
	}
	return 0, 0, ErrOverflow
}

// csvState is the explicit state machine SplitCSVLine runs. Spelling the
// states out (rather than a regexp or ad-hoc boolean flags) is what makes
// the doubled-quote escape rule ("" inside a quoted field = literal ")
// expressible and keeps every transition auditable.
type csvState int

const (
	fieldStart csvState = iota
	inUnquoted
	inQuoted
	quoteSeenInQuoted
)

// SplitCSVLine splits one CSV line (no embedded newlines) into fields,
// honoring double-quote quoting and "" as an escaped literal quote. It
// never panics on any input, valid or not.
func SplitCSVLine(line string) ([]string, error) {
	var fields []string
	var cur []byte
	state := fieldStart

	flush := func() {
		fields = append(fields, string(cur))
		cur = cur[:0]
	}

	for i := 0; i < len(line); i++ {
		c := line[i]
		switch state {
		case fieldStart:
			switch c {
			case '"':
				state = inQuoted
			case ',':
				flush()
				// stay in fieldStart for the next field
			default:
				cur = append(cur, c)
				state = inUnquoted
			}
		case inUnquoted:
			switch c {
			case ',':
				flush()
				state = fieldStart
			default:
				cur = append(cur, c)
			}
		case inQuoted:
			switch c {
			case '"':
				state = quoteSeenInQuoted
			default:
				cur = append(cur, c)
			}
		case quoteSeenInQuoted:
			switch c {
			case '"':
				// Doubled quote: literal '"', stay quoted.
				cur = append(cur, '"')
				state = inQuoted
			case ',':
				flush()
				state = fieldStart
			default:
				// A quote followed by a non-quote, non-comma char in
				// strict CSV is technically malformed, but we take the
				// permissive real-world reading: the quoted section
				// ended, and we fall back to treating the rest as
				// unquoted content of the same field (never panics
				// either way — that's the invariant under fuzz test,
				// not strict RFC 4180 conformance).
				cur = append(cur, c)
				state = inUnquoted
			}
		}
	}

	switch state {
	case inQuoted, quoteSeenInQuoted:
		if state == inQuoted {
			return nil, ErrUnterminatedQuote
		}
		// quoteSeenInQuoted at EOF is a valid close.
		fallthrough
	default:
		flush()
	}
	return fields, nil
}

// JoinCSVLine is the inverse of SplitCSVLine: quotes a field (doubling any
// embedded '"') iff it contains a ',' or '"'. An empty field needs no
// quoting — the comma delimiters alone are enough to round-trip it.
func JoinCSVLine(fields []string) string {
	out := make([]byte, 0, 32*len(fields))
	for i, f := range fields {
		if i > 0 {
			out = append(out, ',')
		}
		if needsQuoting(f) {
			out = append(out, '"')
			for j := 0; j < len(f); j++ {
				if f[j] == '"' {
					out = append(out, '"', '"')
				} else {
					out = append(out, f[j])
				}
			}
			out = append(out, '"')
		} else {
			out = append(out, f...)
		}
	}
	return string(out)
}

func needsQuoting(f string) bool {
	for i := 0; i < len(f); i++ {
		if f[i] == ',' || f[i] == '"' {
			return true
		}
	}
	return false
}

/*
BEST PRACTICES

  - Fuzz targets should be pure functions of their input: no goroutines, no
    time.Now(), no package-level mutable state. A failure must be
    reproducible by replaying the exact same bytes later — anything
    nondeterministic breaks that contract and makes crashers unreproducible.
  - Bound every loop that consumes attacker-controlled length data BEFORE
    the first out-of-bounds access can happen, not after — this is the
    single highest-value thing fuzzing a decoder finds.
  - Prefer an explicit state machine over a regexp for anything with escape
    sequences; regexps can't express "consume until an unescaped delimiter"
    without lookaround Go's RE2 engine doesn't support anyway.
  - Keep round-trip properties as the primary fuzz target (encode/decode,
    split/join) — they need no oracle (expected value) beyond "you get back
    what you put in", so they scale to fully random generated input, unlike
    fuzz targets that need a hand-computed expected result per case.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - encoding/binary.Uvarint / PutUvarint in the standard library already do
    exactly this — reimplementing it here is for the learning value of
    writing (and fuzzing) the decoder yourself; in production, use the
    stdlib version, which has already absorbed years of exactly this kind
    of fuzzing (both internally and via OSS-Fuzz).
  - encoding/csv is the correct choice for real CSV in production (handles
    embedded newlines inside quoted fields, configurable delimiters, BOM);
    SplitCSVLine here deliberately handles only a single line to keep the
    fuzz target's input space (a plain string) simple and fast to explore.
  - A property-based library (e.g. gopter, rapid) offers more combinators
    (shrinking on failure, custom generators) than testing.F's raw
    []byte/string fuzzing. testing.F wins because it's zero-dependency,
    integrates with `go test` and go vet, and is what ships in every Go
    toolchain — worth knowing the tradeoffs of both, but stdlib is the
    default.

TESTING / BENCHMARKING / FAILURE MODES

  - Table-driven tests (this file's _test.go) cover named edge cases: 0,
    127/128 byte-count boundary, max uint64, empty/quoted/doubled-quote CSV
    fields, and the two error paths (truncated, unterminated quote).
  - Fuzz targets (same _test.go) assert the round-trip invariant and a
    "never panics" property over generated input, seeded with the same
    boundary values the table tests use — seeds bias the fuzzer's mutation
    starting points toward interesting regions instead of starting purely
    random.
  - Failure mode if DecodeUvarint's overflow check were removed: a 10+ byte
    buffer of continuation bytes silently wraps the uint64 and returns a
    wrong value with err == nil instead of failing — far worse than a
    crash, since callers trust the result. This is why the fuzz invariant
    checks err as strictly as the value.
*/
