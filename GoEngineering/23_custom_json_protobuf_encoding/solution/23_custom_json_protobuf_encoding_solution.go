// Package solution implements problem 23 — custom JSON encoding, streaming
// NDJSON, schema-evolution-safe fields, and a protobuf encoding generated
// from solution/order.proto (see that file's header comment for the exact
// `protoc` command used to produce orderpb/order.pb.go).
package solution

import (
	"encoding/json"
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"goengineering/23_custom_json_protobuf_encoding/solution/orderpb"
)

// Money represents a monetary amount as integer minor units (cents) plus an
// ISO-4217 currency code. Never use float64 for money: 0.1 + 0.2 != 0.3 in
// IEEE-754, and that error compounds across millions of transactions. Cents
// as an int64 is exact for any amount that fits (max ~92 quadrillion major
// units), and all arithmetic on it is ordinary integer arithmetic.
type Money struct {
	Cents    int64
	Currency string
}

// MarshalJSON encodes Money as the string "19.99 USD" — never a bare JSON
// number. A value receiver is enough here (Marshal never needs to mutate
// the receiver), but note UnmarshalJSON below MUST be a pointer receiver:
// encoding/json calls it on a pointer it holds, and a value receiver would
// silently never be invoked (no compile error, no runtime error — the
// field just stays its zero value, which is exactly the kind of bug that's
// invisible until a client complains about missing data).
func (m Money) MarshalJSON() ([]byte, error) {
	sign := ""
	cents := m.Cents
	if cents < 0 {
		sign = "-"
		cents = -cents
	}
	whole := cents / 100
	frac := cents % 100
	s := fmt.Sprintf("%s%d.%02d %s", sign, whole, frac, m.Currency)
	return json.Marshal(s)
}

// UnmarshalJSON parses the "19.99 USD" format back into Cents/Currency,
// rejecting anything that isn't exactly "<amount> <currency>" with an
// amount having 0-2 decimal digits. Rejecting malformed input here — rather
// than silently truncating or defaulting — is the point: a money field
// that fails loudly on "19.999 USD" (three decimal digits: which cent does
// it round to? the API contract never said) is far cheaper than one that
// silently drops precision into production data.
func (m *Money) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("money: not a JSON string: %w", err)
	}

	parts := strings.Fields(s) // splits on any whitespace, collapses runs
	if len(parts) != 2 {
		return fmt.Errorf("money: expected \"<amount> <currency>\", got %q", s)
	}
	amount, currency := parts[0], parts[1]
	if currency == "" {
		return fmt.Errorf("money: empty currency in %q", s)
	}

	neg := false
	if strings.HasPrefix(amount, "-") {
		neg = true
		amount = amount[1:]
	}

	wholeStr, fracStr, hasFrac := strings.Cut(amount, ".")
	if wholeStr == "" {
		return fmt.Errorf("money: missing whole part in %q", s)
	}
	if hasFrac && len(fracStr) > 2 {
		return fmt.Errorf("money: more than 2 decimal places in %q", s)
	}
	whole, err := strconv.ParseInt(wholeStr, 10, 64)
	if err != nil {
		return fmt.Errorf("money: invalid whole part %q: %w", wholeStr, err)
	}
	frac := int64(0)
	if hasFrac {
		// Right-pad "5" -> "50" so ".5" means 50 cents, not 5.
		for len(fracStr) < 2 {
			fracStr += "0"
		}
		frac, err = strconv.ParseInt(fracStr, 10, 64)
		if err != nil {
			return fmt.Errorf("money: invalid fractional part %q: %w", fracStr, err)
		}
	}

	cents := whole*100 + frac
	if neg {
		cents = -cents
	}
	m.Cents = cents
	m.Currency = currency
	return nil
}

// Order is the domain type shared by the JSON and protobuf encodings — the
// same shape problem 24's gRPC service will exchange over the wire.
//
// Two fields exist specifically for schema evolution:
//
//   - Notes *string: a pointer, not a plain string, so nil ("field absent
//     from the payload, or explicitly not provided") is distinguishable
//     from a non-nil pointer to "" ("field present, deliberately empty").
//     A plain `string` with `omitempty` collapses both cases to nothing
//     being emitted, which loses that distinction on the wire.
//   - Metadata json.RawMessage: an escape hatch for fields the CURRENT
//     binary doesn't know about yet. encoding/json defers parsing this
//     field entirely — it's stored as the raw, unparsed bytes of whatever
//     JSON value occupied that key. A producer on a newer schema version
//     can stuff arbitrary structured data in here; an older consumer that
//     doesn't understand the new fields still round-trips them byte-for-
//     byte through Metadata instead of silently discarding them (which is
//     what happens to any field that ISN'T captured by a RawMessage/map —
//     see TestSchemaEvolution_UnknownTopLevelFieldsAreDropped below).
type Order struct {
	ID         string
	CustomerID string
	Amount     Money
	Items      []string
	CreatedAt  time.Time
	Notes      *string         `json:"notes,omitempty"`
	Metadata   json.RawMessage `json:"metadata,omitempty"`
}

// orderV1 is what Order looked like before Notes/Metadata existed — kept
// here purely to exercise "old writer, new reader" and "new writer, old
// reader" schema evolution in tests, standing in for a previous deployed
// binary's type definition.
type orderV1 struct {
	ID         string
	CustomerID string
	Amount     Money
	Items      []string
	CreatedAt  time.Time
}

// OrderStreamWriter writes newline-delimited JSON (NDJSON): one compact
// JSON object per line. This is the streaming shape — json.Marshal on a
// []Order would require the entire batch resident in memory at once (both
// as the Go slice and again as the serialized byte slice); NDJSON over
// json.Encoder lets a producer write orders one at a time as they're
// generated, and a consumer read them one at a time as they arrive, with
// memory use independent of batch size.
type OrderStreamWriter struct {
	enc *json.Encoder
}

// NewOrderStreamWriter wraps w in a json.Encoder. json.Encoder.Encode
// writes the value followed by a single '\n', which is exactly the NDJSON
// framing — no manual newline handling required.
func NewOrderStreamWriter(w io.Writer) *OrderStreamWriter {
	return &OrderStreamWriter{enc: json.NewEncoder(w)}
}

// WriteOrder encodes one Order as a single NDJSON line.
func (w *OrderStreamWriter) WriteOrder(o Order) error {
	if err := w.enc.Encode(o); err != nil {
		return fmt.Errorf("order stream: encode: %w", err)
	}
	return nil
}

// OrderStreamReader reads NDJSON produced by OrderStreamWriter (or any
// compatible producer — the format is just "one JSON object per line").
type OrderStreamReader struct {
	dec *json.Decoder
}

// NewOrderStreamReader wraps r in a json.Decoder.
func NewOrderStreamReader(r io.Reader) *OrderStreamReader {
	return &OrderStreamReader{dec: json.NewDecoder(r)}
}

// ReadOrder decodes the next Order from the stream. It returns io.EOF,
// UNWRAPPED, once the stream is exhausted — json.Decoder.Decode already
// returns exactly io.EOF (not a wrapped error) at end of input, so we pass
// it straight through rather than running it through fmt.Errorf("%w", …),
// which would break callers doing `errors.Is(err, io.EOF)` naively or, worse,
// a plain `err == io.EOF` check (still common and still valid for this one
// specific stdlib sentinel).
func (r *OrderStreamReader) ReadOrder() (Order, error) {
	var o Order
	if err := r.dec.Decode(&o); err != nil {
		if err == io.EOF {
			return Order{}, io.EOF
		}
		return Order{}, fmt.Errorf("order stream: decode: %w", err)
	}
	return o, nil
}

// ToProto converts an Order into the generated protobuf type. Money's
// integer cents map 1:1 onto amount_cents (both are exact integers —
// no precision to lose in this direction, unlike a hypothetical float
// encoding). CreatedAt is truncated to whole seconds because the .proto
// schema stores Unix seconds, not nanoseconds — a deliberate simplification
// documented here so it isn't mistaken for a bug when a round trip drops
// sub-second precision (see FromProto and the test for the exact contract).
func ToProto(o Order) *orderpb.Order {
	p := &orderpb.Order{
		Id:            o.ID,
		CustomerId:    o.CustomerID,
		AmountCents:   o.Amount.Cents,
		Currency:      o.Amount.Currency,
		Items:         append([]string(nil), o.Items...), // defensive copy
		CreatedAtUnix: o.CreatedAt.Unix(),
		MetadataJson:  append([]byte(nil), o.Metadata...), // defensive copy
	}
	if o.Notes != nil {
		p.Notes = o.Notes // proto3 `optional string` generates *string
	}
	return p
}

// FromProto converts a generated protobuf Order back into the domain type.
// Returns an error for a nil input rather than a zero-value Order, so
// callers can't mistake "no message received" for "an order with every
// field at its zero value" — those are different failures with different
// remediations.
func FromProto(p *orderpb.Order) (Order, error) {
	if p == nil {
		return Order{}, fmt.Errorf("order: FromProto: nil input")
	}
	o := Order{
		ID:         p.GetId(),
		CustomerID: p.GetCustomerId(),
		Amount:     Money{Cents: p.GetAmountCents(), Currency: p.GetCurrency()},
		Items:      append([]string(nil), p.GetItems()...),
		CreatedAt:  time.Unix(p.GetCreatedAtUnix(), 0).UTC(),
		Metadata:   append([]byte(nil), p.GetMetadataJson()...),
	}
	if p.Notes != nil {
		notes := *p.Notes
		o.Notes = &notes
	}
	return o, nil
}

/*
BEST PRACTICES

  - Never serialize money as a JSON/protobuf number. Integer minor units
    (cents) plus a currency code, with a custom string encoding on the JSON
    side, is the standard production pattern (Stripe's API does exactly
    this).
  - UnmarshalJSON must be defined on a pointer receiver. This is not a
    style preference — encoding/json specifically looks for the
    Unmarshaler interface on the addressable pointer to your value, and a
    value-receiver method set never satisfies it for decoding.
  - Use json.RawMessage (or, if the whole envelope is unknown, a
    map[string]json.RawMessage) for any field a producer might extend
    before consumers can be redeployed. Anything NOT captured this way is
    silently dropped by encoding/json on decode into a stricter struct —
    "silently" being the operative danger word.
  - For streaming, prefer json.Encoder/Decoder over Marshal/Unmarshal any
    time the data size is unbounded or unknown at the call site. The
    memory-boundedness is not a micro-optimization — it's the difference
    between a service that scales with batch size and one that OOMs on a
    sufficiently large customer export.
  - In protobuf, use `optional` on scalar fields precisely when "unset"
    needs to be distinguishable from "the zero value" — don't reach for it
    reflexively, since it costs you a pointer indirection and a nil check
    on every read.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - A single unified type with protobuf struct tags AND custom JSON methods
    (instead of two separate types + explicit ToProto/FromProto) is
    possible but couples the two wire formats' evolution together — a
    protobuf-only field addition would force a JSON-side decision too.
    Separate types with explicit conversion functions cost more code but
    let each format evolve independently, which is usually what you want
    once both have real external consumers.
  - google.protobuf.Timestamp (via the standard well-known-types import)
    would give nanosecond precision and a stdlib-provided
    time.Time-compatible representation instead of a bare int64 Unix
    seconds field — not used here to keep the generated code to one file
    with no extra imports, but it's the better choice for a
    precision-sensitive real schema.
  - A decimal-string Money encoding ("19.99") instead of "19.99 USD" (with
    currency as a sibling JSON field) is equally valid and arguably more
    conventional for a REST API; the single-string format was chosen here
    specifically to force UnmarshalJSON to parse two pieces of information
    out of one string, which is the more instructive exercise.

TESTING / FAILURE MODES

  - Money's UnmarshalJSON is tested against both valid and deliberately
    malformed input (three decimal digits, non-numeric amount, missing
    currency, missing amount) — a money parser that only tests the happy
    path hasn't earned any confidence.
  - The NDJSON round trip is tested with io.EOF checked via a direct `==`
    comparison (not just errors.Is), since that's the comparison most
    existing call sites actually use for this specific stdlib sentinel and
    the contract explicitly promises the unwrapped value.
  - Schema evolution is tested in both directions: old-shaped JSON into the
    new Order type (new fields land at zero value), and new-shaped JSON
    (with an extra unknown top-level key) into the OLD orderV1 type,
    demonstrating the unknown key is silently dropped — proving why
    anything meant to survive that direction must live inside Metadata.
*/
