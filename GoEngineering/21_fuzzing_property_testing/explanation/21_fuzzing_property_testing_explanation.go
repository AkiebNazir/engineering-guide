/*
Problem 21 — Fuzzing & Property Testing (testing.F, invariants, seed corpora)

WHAT WE'RE BUILDING

Two small, hand-rollable encodings that are exactly the kind of code fuzzing
is built for: code that parses/decodes untrusted bytes.

 1. Varint: the LEB128-style variable-length integer encoding protobuf uses
    on the wire (see problem 23). EncodeUvarint/DecodeUvarint.
 2. A tiny CSV-line splitter with quoting (SplitCSVLine) and its inverse
    (JoinCSVLine) — the kind of "looks simple, isn't" text-parsing code
    that silently panics on some adversarial input in every codebase that
    hand-rolls it instead of using encoding/csv.

# WHY THIS MATTERS IN REAL SYSTEMS

Unit tests check the inputs *you* thought of. Fuzzing hands the function
inputs a human would never think to write: truncated buffers, embedded NUL
bytes, huge varints that overflow, quotes that don't close, near-infinite
generated integers. Go 1.18+ ships fuzzing as a first-class `go test`
citizen (`testing.F`) — no external framework needed. It's not optional
polish for a decoder: any function that turns bytes from the network or
disk into structured data should have a fuzz target, because that's
precisely the boundary attackers and buggy peers exercise.

Two things fuzzing checks that ordinary tests don't naturally check:
  - **Crash freedom**: the function must never panic (index out of range,
    slice out of bounds, integer overflow causing a bad allocation) on ANY
    input, valid or not. A parser's job on garbage input is to return an
    error, not to crash the process.
  - **Invariants / round-trip properties**: "decode(encode(x)) == x for all
    x" is a property, not a single test case. Fuzzing explores the input
    space looking for a counter-example to that property far more
    effectively than a human enumerating cases.

CONCEPTS COVERED

  - `testing.F`, `f.Add(...)` seed corpus, `f.Fuzz(func(t *testing.T, ...))`
  - Running a fuzz target for real: `go test -fuzz=FuzzX -fuzztime=10s`
  - Property-based invariants: round-trip, idempotence, no-panic
  - Corpus files Go writes to `testdata/fuzz/<FuzzName>/` on a crasher, and
    how those become permanent regression tests
  - Why fuzz *targets* should be pure and deterministic (no goroutines,
    no global state, no time.Now()) so failures reproduce byte-for-byte

# SPEC

EncodeUvarint(x uint64) []byte
  - LEB128 unsigned varint: 7 bits of payload per byte, low bits first, MSB
    of each byte set iff another byte follows. Same scheme protobuf uses.
  - Output length: 1..10 bytes (10 for the top bit of a full uint64).

DecodeUvarint(buf []byte) (value uint64, n int, err error)
  - n is the number of bytes consumed. err != nil (never panics) when:
  - buf is empty or ends before a terminating byte (ErrTruncated)
  - the encoded value would overflow 64 bits, i.e. more than 10 bytes
    of continuation or the 10th byte has payload bits beyond bit 63
    (ErrOverflow)
  - INVARIANT under test: for every uint64 x,
    v, n, err := DecodeUvarint(EncodeUvarint(x))
    err == nil && v == x && n == len(EncodeUvarint(x))

SplitCSVLine(line string) ([]string, error)
  - Splits one line (no embedded newlines) on commas.
  - A field may be double-quoted: `"a,b"` is one field containing `a,b`.
  - `""` inside a quoted field is a literal `"` (standard CSV escaping).
  - Error (not panic) on an unterminated quote.

JoinCSVLine(fields []string) string
  - Inverse of SplitCSVLine: quotes a field (doubling embedded quotes) iff
    it contains a comma, a quote, or is empty... actually only iff it
    contains a comma or a quote (empty fields don't need quoting since a
    bare comma already delimits them) — see solution for the exact rule.
  - INVARIANT under test: for every []string fields (no element containing
    a literal newline),
    got, err := SplitCSVLine(JoinCSVLine(fields))
    err == nil && slices.Equal(got, fields)

ACCEPTANCE CRITERIA

  - `go test ./21_fuzzing_property_testing/solution/...` passes (regular
    table-driven tests over hand-picked edge cases).
  - `go test -fuzz=FuzzUvarintRoundTrip -fuzztime=10s ./21_fuzzing_property_testing/solution/`
    runs for the full duration and finds no crasher (documented in the
    solution file's header — this is the "actually runs" proof the spec
    asks for).
  - Neither Decode function panics on any byte slice, however malformed.
*/
package fuzztarget

import "errors"

// ErrTruncated is returned by DecodeUvarint when buf ends before a
// terminating (high-bit-clear) byte.
var ErrTruncated = errors.New("fuzztarget: truncated varint")

// ErrOverflow is returned by DecodeUvarint when the encoded value would not
// fit in a uint64.
var ErrOverflow = errors.New("fuzztarget: varint overflows uint64")

// ErrUnterminatedQuote is returned by SplitCSVLine when a quoted field
// never sees its closing quote.
var ErrUnterminatedQuote = errors.New("fuzztarget: unterminated quoted field")

// EncodeUvarint encodes x as an unsigned LEB128 varint.
//
// TODO: emit 7 bits of x per byte, low-order first. Set the top bit of
// every byte except the last to signal "more bytes follow".
func EncodeUvarint(x uint64) []byte {
	panic("TODO: implement EncodeUvarint")
}

// DecodeUvarint decodes an unsigned LEB128 varint from the front of buf.
// It must NEVER panic, regardless of the contents or length of buf.
//
// TODO: read bytes until one has its high bit clear, accumulating 7 bits
// each into value. Return ErrTruncated if buf runs out first. Return
// ErrOverflow if more than 10 bytes would be needed, or the final byte
// contributes bits beyond bit 63.
func DecodeUvarint(buf []byte) (value uint64, n int, err error) {
	panic("TODO: implement DecodeUvarint")
}

// SplitCSVLine splits a single CSV line into fields. It must never panic.
//
// TODO: scan rune by rune. A field starting with '"' is quoted: consume
// until an unescaped closing quote (`""` inside = literal `"`); a field
// not starting with '"' runs to the next ',' verbatim. Return
// ErrUnterminatedQuote instead of panicking if a quote never closes.
func SplitCSVLine(line string) ([]string, error) {
	panic("TODO: implement SplitCSVLine")
}

// JoinCSVLine is the inverse of SplitCSVLine.
//
// TODO: quote a field (doubling any '"') iff it contains ',' or '"'.
func JoinCSVLine(fields []string) string {
	panic("TODO: implement JoinCSVLine")
}

/*
HINTS

  - Varint decode loop bound: cap the loop at 10 iterations (ceil(64/7))
    before declaring overflow — otherwise a crafted buffer of all
    continuation bytes (0xFF, 0xFF, 0xFF, ...) makes you loop over the
    entire (possibly huge, attacker-controlled) buffer.
  - For the 10th byte specifically, only the low bit may be set (64 = 9*7 +
    1) — anything else overflows uint64. Check this explicitly rather than
    relying on a shift to silently wrap.
  - Write the CSV split as an explicit state machine (states: "start of
    field", "in unquoted field", "in quoted field", "quote seen inside
    quoted field") — resist the urge to use a regexp; regexps don't compose
    with the doubled-quote escaping rule cleanly and you lose the ability to
    return a precise "unterminated" error.
  - `f.Add` seeds should include the boundary cases you already know matter:
    0, 1, 127 (1-byte/2-byte boundary), 128, max uint64, for varint; and
    empty string, a single comma, unterminated quote, doubled quotes for
    CSV. Fuzzing explores *around* your seeds, it doesn't replace them.

COMMON PITFALLS

  - Decoding trusting `buf[i]` without checking `i < len(buf)` first — the
    single most common thing a decoder fuzz target finds in ten seconds.
  - An overflow check that only looks at byte count, not at what bits the
    final byte actually contributes — lets a value like `0x92 0x01` chains
    past 64 bits silently wrap instead of erroring.
  - A round-trip fuzz target that calls `t.Fatalf` with `%v` formatting of
    huge byte slices — makes failures unreadable; prefer `%x` for byte data
    and print lengths, not full contents, for large inputs.
  - Fuzz functions that use a package-level `map` or slice as scratch state
    shared across the parallel-ish execution `go test -fuzz` performs —
    fuzzing runs many inputs through the same process; keep fuzz function
    bodies free of shared mutable state.

STRETCH GOALS

  - Add a signed zig-zag varint (protobuf's `sint32`/`sint64` encoding) and
    fuzz its round trip too.
  - Add a fuzz target for JoinCSVLine ∘ SplitCSVLine in the *other*
    direction: for every valid CSV line, splitting then rejoining should
    produce a line that re-splits to the same fields (not necessarily byte-
    identical, since quoting is a choice — this is a weaker but still real
    invariant).
  - Once a fuzz run finds a crasher, the corpus entry Go saves under
    `testdata/fuzz/<Name>/` becomes a permanent regression test on every
    future `go test` — deliberately introduce a bug, run the fuzzer to
    generate a crasher file, fix the bug, and keep the corpus entry.
*/
