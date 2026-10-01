/*
Problem 23 — Custom JSON & Protobuf Encoding

WHAT WE'RE BUILDING

An "Order" domain type that must be serialized two ways in production: as
JSON for a public HTTP API (and for ops tooling / logs that want to grep
readable text), and as protobuf for a low-latency internal service boundary
(problem 24's gRPC service consumes exactly this type). Both encodings have
to solve the same three problems that show up in every real API:

 1. Money must never round-trip through float64. A `Money` type wraps an
    integer cents count + an ISO-4217 currency code, and controls its own
    JSON representation via MarshalJSON/UnmarshalJSON (encoded as a decimal
    string like "19.99 USD", never a bare JSON number).

 2. Large batches of orders must stream, not buffer. A NDJSON (newline-
    delimited JSON) reader/writer pair wraps json.Encoder/json.Decoder over
    an io.Writer/io.Reader so an unbounded number of orders can be written
    or read with O(1) memory relative to batch size — the same shape as
    reading a multi-GB log file one line at a time.

 3. The schema must evolve without breaking old readers or writers. A
    `json.RawMessage` "Metadata" field lets producers attach fields the
    current schema doesn't know about yet (deferred parsing, forward
    compatible), and a pointer field (`*string` Notes) distinguishes "field
    absent" from "field present but empty" — both classic optional-field-
    safe evolution techniques. The protobuf half gets the same two
    properties for free from the wire format itself (unknown fields survive
    round-trips by default; `optional` gives explicit presence) — the point
    of building both halves is to see which properties you have to earn by
    hand in JSON and which protobuf gives you structurally.

# WHY THIS MATTERS IN REAL SYSTEMS

Every service that outlives its first schema hits this. A field gets added,
a client is still running the old binary, and the question is: does the old
client silently drop data it doesn't understand, does the new server reject
old payloads, does a float-encoded price silently lose a cent on every
transaction at scale? Getting encode/decode boundaries right — and knowing
exactly which serialization format buys you what compatibility guarantee —
is the difference between a schema change being a non-event and an incident.

# CONCEPTS COVERED

  - Implementing the `json.Marshaler` / `json.Unmarshaler` interfaces on a
    domain type to fully control its wire representation
  - `json.Encoder` / `json.Decoder` over `io.Writer` / `io.Reader` for
    streaming (as opposed to `json.Marshal`/`Unmarshal`, which require the
    whole payload in memory as a single `[]byte`)
  - `json.RawMessage` as a deferred-parsing / forward-compatible escape
    hatch, and pointer fields for optional-vs-empty presence
  - Defining a protobuf message in a real `.proto` file, generating Go code
    with `protoc` + `protoc-gen-go`, and writing conversion functions
    between the hand-written domain type and the generated protobuf type
  - Comparing what each format gives you "for free": protobuf's wire format
    silently preserves unknown fields on every round trip; JSON's
    `encoding/json` silently DROPS unknown fields unless you explicitly
    capture them (there is no automatic equivalent to protobuf's behavior)

# SPEC

	type Money struct {
	    Cents    int64  // 1999 == "19.99"
	    Currency string // ISO-4217, e.g. "USD"
	}
	// MarshalJSON encodes as the JSON string "19.99 USD".
	// UnmarshalJSON parses that string back into Cents/Currency, and
	// rejects malformed input (wrong number of parts, non-numeric amount,
	// more than 2 decimal places, empty currency).

	type Order struct {
	    ID         string
	    CustomerID string
	    Amount     Money
	    Items      []string
	    CreatedAt  time.Time
	    Notes      *string         // optional; nil means "absent", not empty
	    Metadata   json.RawMessage // opaque forward-compat payload
	}

	// Streaming NDJSON encoder/decoder:
	type OrderStreamWriter struct{ ... } // wraps *json.Encoder over an io.Writer
	func NewOrderStreamWriter(w io.Writer) *OrderStreamWriter
	func (w *OrderStreamWriter) WriteOrder(o Order) error

	type OrderStreamReader struct{ ... } // wraps *json.Decoder over an io.Reader
	func NewOrderStreamReader(r io.Reader) *OrderStreamReader
	func (r *OrderStreamReader) ReadOrder() (Order, error) // io.EOF when exhausted

	// Protobuf conversion (against the generated orderpb.Order — see
	// solution/order.proto for the schema and the exact protoc command):
	func ToProto(o Order) *orderpb.Order
	func FromProto(p *orderpb.Order) (Order, error)

# ACCEPTANCE CRITERIA

  - Money round-trips through MarshalJSON/UnmarshalJSON without precision
    loss, for both whole and fractional amounts, and rejects malformed
    encodings (e.g. "19.999 USD", "abc USD", "19.99").
  - OrderStreamWriter/Reader round-trip N orders written one at a time and
    read back one at a time, in order, with ReadOrder returning io.EOF (not
    a wrapped/other error) once the stream is exhausted.
  - An Order encoded under an older schema (missing Notes/Metadata) decodes
    cleanly into the current Order type with those fields at their zero
    value (nil), and an Order encoded under a NEWER, hypothetical schema
    (extra unknown top-level JSON keys) decodes without error, silently
    dropping the unknown keys — demonstrating why fields you want preserved
    forward must live inside a RawMessage, not as ad hoc top-level keys.
  - ToProto/FromProto round-trip an Order's fields exactly (cents, currency,
    items, truncated-to-second timestamp, notes presence/absence, and the
    raw metadata bytes).

# HINTS

  - `strconv.ParseInt` on the fractional part after checking it's exactly 2
    digits avoids float parsing entirely for Money.
  - `json.Decoder.More()` is NOT the right tool for NDJSON (that's for JSON
    arrays); for newline-delimited JSON just call Decode() in a loop and
    stop on io.EOF.
  - time.Time round-trips through JSON as RFC 3339 automatically via
    MarshalJSON/UnmarshalJSON already implemented on time.Time — you don't
    need to touch it. Protobuf has no such convenience; that's why the
    .proto schema stores `created_at_unix` as an int64 and the conversion
    functions do the truncation explicitly.
  - proto3 `optional` on a scalar field generates a Go pointer field (see
    orderpb.Order.Notes, generated as *string) specifically so presence is
    distinguishable — without `optional` a proto3 scalar can never be "unset".

# PITFALLS

  - Forgetting UnmarshalJSON must have a pointer receiver (`*Money`) — a
    value receiver silently never gets called by encoding/json and you get
    a zero-value Money with no error.
  - Reusing a single json.Decoder across unrelated readers, or a single
    json.Encoder's SetIndent state leaking between unrelated writes.
  - Comparing time.Time with `==` or `reflect.DeepEqual` after a JSON round
    trip: the monotonic reading is stripped and the Location may differ
    (UTC vs a fixed offset) even when the instant is identical — compare
    with `.Equal()`.
  - Treating a protobuf `optional string` field's underlying pointer as
    always safe to dereference — always check for nil, exactly like any
    other Go pointer.

# STRETCH GOALS

  - Add a second protobuf message version (e.g. OrderV2 with a new field)
    in a way that stays wire-compatible with OrderV1 clients, and write a
    test that unmarshals OrderV2-encoded bytes with the OrderV1 generated
    struct to observe the unknown field being silently preserved (not
    dropped) on a re-marshal — protobuf's actual forward-compat guarantee,
    as opposed to JSON where you have to build that yourself with RawMessage.
  - Implement a custom `MarshalJSON` for Order itself that omits Notes
    entirely (rather than emitting `"notes":null`) when nil, and contrast
    with the built-in `omitempty` tag's limitations for pointer types.
*/
package explanation

import (
	"encoding/json"
	"io"
	"time"

	"goengineering/23_custom_json_protobuf_encoding/solution/orderpb"
)

// Money represents a monetary amount as integer minor units (cents) plus an
// ISO-4217 currency code, to avoid float64 precision loss on money math.
type Money struct {
	Cents    int64
	Currency string
}

// TODO: implement MarshalJSON on Money (pointer or value receiver — decide
// which and say why in a comment) that encodes as the JSON string
// "19.99 USD".
func (m Money) MarshalJSON() ([]byte, error) {
	panic("TODO: implement Money.MarshalJSON")
}

// TODO: implement UnmarshalJSON on *Money (must be a pointer receiver) that
// parses the "19.99 USD" format back into Cents/Currency and rejects
// malformed input.
func (m *Money) UnmarshalJSON(data []byte) error {
	panic("TODO: implement Money.UnmarshalJSON")
}

// Order is the domain type shared by the JSON and protobuf encodings.
type Order struct {
	ID         string
	CustomerID string
	Amount     Money
	Items      []string
	CreatedAt  time.Time
	Notes      *string
	Metadata   json.RawMessage
}

// OrderStreamWriter writes newline-delimited JSON (NDJSON): one Order per
// line, suitable for streaming an unbounded number of orders without
// buffering the whole batch.
type OrderStreamWriter struct {
	enc *json.Encoder
}

// TODO: implement NewOrderStreamWriter, wrapping json.NewEncoder(w).
func NewOrderStreamWriter(w io.Writer) *OrderStreamWriter {
	panic("TODO: implement NewOrderStreamWriter")
}

// TODO: implement WriteOrder, encoding one Order as a single JSON line.
func (w *OrderStreamWriter) WriteOrder(o Order) error {
	panic("TODO: implement OrderStreamWriter.WriteOrder")
}

// OrderStreamReader reads NDJSON written by OrderStreamWriter.
type OrderStreamReader struct {
	dec *json.Decoder
}

// TODO: implement NewOrderStreamReader, wrapping json.NewDecoder(r).
func NewOrderStreamReader(r io.Reader) *OrderStreamReader {
	panic("TODO: implement NewOrderStreamReader")
}

// TODO: implement ReadOrder, decoding one Order. Must return io.EOF
// (unwrapped) when the stream is exhausted — do not wrap it.
func (r *OrderStreamReader) ReadOrder() (Order, error) {
	panic("TODO: implement OrderStreamReader.ReadOrder")
}

// TODO: implement ToProto, converting an Order into the generated
// *orderpb.Order (see solution/order.proto for the schema).
func ToProto(o Order) *orderpb.Order {
	panic("TODO: implement ToProto")
}

// TODO: implement FromProto, converting a *orderpb.Order back into an
// Order. Return an error for a nil input.
func FromProto(p *orderpb.Order) (Order, error) {
	panic("TODO: implement FromProto")
}
