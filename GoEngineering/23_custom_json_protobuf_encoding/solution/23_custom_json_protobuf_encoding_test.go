package solution

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"testing"
	"time"
)

func TestMoney_MarshalUnmarshalRoundTrip(t *testing.T) {
	cases := []struct {
		name string
		m    Money
		want string // exact JSON-encoded string
	}{
		{"whole amount", Money{Cents: 1900, Currency: "USD"}, `"19.00 USD"`},
		{"fractional amount", Money{Cents: 1999, Currency: "USD"}, `"19.99 USD"`},
		{"single-digit cents", Money{Cents: 5, Currency: "USD"}, `"0.05 USD"`},
		{"zero", Money{Cents: 0, Currency: "EUR"}, `"0.00 EUR"`},
		{"negative", Money{Cents: -150, Currency: "GBP"}, `"-1.50 GBP"`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			data, err := json.Marshal(tc.m)
			if err != nil {
				t.Fatalf("Marshal: %v", err)
			}
			if string(data) != tc.want {
				t.Fatalf("Marshal(%+v) = %s, want %s", tc.m, data, tc.want)
			}

			var got Money
			if err := json.Unmarshal(data, &got); err != nil {
				t.Fatalf("Unmarshal(%s): %v", data, err)
			}
			if got != tc.m {
				t.Fatalf("round trip = %+v, want %+v", got, tc.m)
			}
		})
	}
}

func TestMoney_UnmarshalRejectsMalformed(t *testing.T) {
	badInputs := []string{
		`"19.999 USD"`, // 3 decimal digits
		`"abc USD"`,    // non-numeric amount
		`"19.99"`,      // missing currency
		`"USD"`,        // missing amount
		`"19.99 "`,     // empty currency after trim
		`19.99`,        // not a JSON string at all
		`""`,           // empty string
	}
	for _, in := range badInputs {
		var m Money
		if err := json.Unmarshal([]byte(in), &m); err == nil {
			t.Errorf("Unmarshal(%s) = nil error, want error", in)
		}
	}
}

func TestMoney_PrecisionSurvivesManyRoundTrips(t *testing.T) {
	// Guards against any accidental float64 involvement: if MarshalJSON ever
	// routed the amount through a float, repeated round trips of an amount
	// like 1 cent would eventually drift. Integer arithmetic never does.
	m := Money{Cents: 333333333333, Currency: "USD"} // large, awkward value
	for i := 0; i < 1000; i++ {
		data, err := json.Marshal(m)
		if err != nil {
			t.Fatalf("iteration %d: Marshal: %v", i, err)
		}
		var next Money
		if err := json.Unmarshal(data, &next); err != nil {
			t.Fatalf("iteration %d: Unmarshal: %v", i, err)
		}
		if next != m {
			t.Fatalf("iteration %d: drifted from %+v to %+v", i, m, next)
		}
		m = next
	}
}

func sampleOrder() Order {
	notes := "handle with care"
	return Order{
		ID:         "ord_1",
		CustomerID: "cust_1",
		Amount:     Money{Cents: 4599, Currency: "USD"},
		Items:      []string{"widget", "gadget"},
		CreatedAt:  time.Date(2026, 1, 2, 3, 4, 5, 0, time.UTC),
		Notes:      &notes,
		Metadata:   json.RawMessage(`{"source":"web","promo_code":"SPRING26"}`),
	}
}

func TestOrderStream_RoundTripInOrder(t *testing.T) {
	orders := []Order{
		sampleOrder(),
		{ID: "ord_2", CustomerID: "cust_2", Amount: Money{Cents: 100, Currency: "EUR"},
			Items: []string{"thing"}, CreatedAt: time.Date(2026, 2, 1, 0, 0, 0, 0, time.UTC)},
		{ID: "ord_3", CustomerID: "cust_3", Amount: Money{Cents: 0, Currency: "JPY"},
			CreatedAt: time.Date(2026, 3, 1, 0, 0, 0, 0, time.UTC)},
	}

	var buf bytes.Buffer
	w := NewOrderStreamWriter(&buf)
	for _, o := range orders {
		if err := w.WriteOrder(o); err != nil {
			t.Fatalf("WriteOrder(%s): %v", o.ID, err)
		}
	}

	r := NewOrderStreamReader(&buf)
	for i, want := range orders {
		got, err := r.ReadOrder()
		if err != nil {
			t.Fatalf("ReadOrder #%d: %v", i, err)
		}
		if got.ID != want.ID || got.CustomerID != want.CustomerID || got.Amount != want.Amount {
			t.Fatalf("ReadOrder #%d = %+v, want %+v", i, got, want)
		}
		if !got.CreatedAt.Equal(want.CreatedAt) {
			t.Fatalf("ReadOrder #%d CreatedAt = %v, want %v", i, got.CreatedAt, want.CreatedAt)
		}
	}

	// The stream is exhausted: the next read must be exactly io.EOF, not a
	// wrapped error — callers relying on `err == io.EOF` (still a common,
	// valid check for this one stdlib sentinel) must not break.
	if _, err := r.ReadOrder(); !errors.Is(err, io.EOF) || err != io.EOF {
		t.Fatalf("ReadOrder after exhaustion = %v, want io.EOF unwrapped", err)
	}
}

func TestOrderStream_PreservesMetadataAndNotes(t *testing.T) {
	var buf bytes.Buffer
	w := NewOrderStreamWriter(&buf)
	want := sampleOrder()
	if err := w.WriteOrder(want); err != nil {
		t.Fatalf("WriteOrder: %v", err)
	}

	got, err := NewOrderStreamReader(&buf).ReadOrder()
	if err != nil {
		t.Fatalf("ReadOrder: %v", err)
	}
	if got.Notes == nil || *got.Notes != *want.Notes {
		t.Fatalf("Notes = %v, want %q", got.Notes, *want.Notes)
	}
	if !bytes.Equal(got.Metadata, want.Metadata) {
		t.Fatalf("Metadata = %s, want %s", got.Metadata, want.Metadata)
	}
}

// TestSchemaEvolution_OldPayloadIntoNewType: an order encoded under the
// pre-Notes/Metadata schema (orderV1) decodes cleanly into the current
// Order type, with the new fields at their zero value (nil, nil) — an old
// producer's data is never rejected just because the schema grew.
func TestSchemaEvolution_OldPayloadIntoNewType(t *testing.T) {
	old := orderV1{
		ID:         "ord_old",
		CustomerID: "cust_old",
		Amount:     Money{Cents: 1000, Currency: "USD"},
		Items:      []string{"legacy-item"},
		CreatedAt:  time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
	}
	data, err := json.Marshal(old)
	if err != nil {
		t.Fatalf("Marshal(orderV1): %v", err)
	}

	var got Order
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatalf("Unmarshal into current Order: %v", err)
	}
	if got.ID != old.ID || got.Amount != old.Amount {
		t.Fatalf("got = %+v, want fields from %+v", got, old)
	}
	if got.Notes != nil {
		t.Fatalf("Notes = %v, want nil (field absent in old payload)", got.Notes)
	}
	if got.Metadata != nil {
		t.Fatalf("Metadata = %s, want nil (field absent in old payload)", got.Metadata)
	}
}

// TestSchemaEvolution_UnknownTopLevelFieldsAreDropped: the inverse
// direction. A payload with an extra top-level key the OLD type doesn't
// know about decodes into orderV1 WITHOUT ERROR, but the extra key is
// simply gone — encoding/json has no built-in "preserve what I don't
// recognize" behavior for a fixed struct target. This is the exact gap
// json.RawMessage on the *current* Order.Metadata field exists to close:
// anything you want preserved forward has to be explicitly routed into a
// RawMessage/map field by the producer, not left as an ad hoc top-level key.
func TestSchemaEvolution_UnknownTopLevelFieldsAreDropped(t *testing.T) {
	payloadWithExtraField := `{
		"ID": "ord_new",
		"CustomerID": "cust_new",
		"Amount": "10.00 USD",
		"Items": ["item"],
		"CreatedAt": "2026-01-01T00:00:00Z",
		"future_field_v2_doesnt_know_about": "some new data"
	}`

	var old orderV1
	if err := json.Unmarshal([]byte(payloadWithExtraField), &old); err != nil {
		t.Fatalf("Unmarshal with unknown field: %v", err)
	}
	if old.ID != "ord_new" {
		t.Fatalf("known fields not decoded: got %+v", old)
	}

	// Re-marshal old and confirm the unknown field is gone — it was never
	// captured anywhere, unlike a RawMessage field's contents, which are
	// preserved byte-for-byte through exactly this kind of round trip.
	reencoded, err := json.Marshal(old)
	if err != nil {
		t.Fatalf("re-Marshal: %v", err)
	}
	if bytes.Contains(reencoded, []byte("future_field_v2_doesnt_know_about")) {
		t.Fatalf("unknown field unexpectedly survived: %s", reencoded)
	}
}

func TestToProtoFromProto_RoundTrip(t *testing.T) {
	want := sampleOrder()
	// CreatedAt is stored as Unix seconds in the proto schema, so truncate
	// the expectation to whole seconds — this is a documented, intentional
	// precision loss (see ToProto's doc comment), not a bug.
	want.CreatedAt = want.CreatedAt.Truncate(time.Second)

	p := ToProto(want)
	got, err := FromProto(p)
	if err != nil {
		t.Fatalf("FromProto: %v", err)
	}

	if got.ID != want.ID || got.CustomerID != want.CustomerID || got.Amount != want.Amount {
		t.Fatalf("got = %+v, want %+v", got, want)
	}
	if len(got.Items) != len(want.Items) {
		t.Fatalf("Items = %v, want %v", got.Items, want.Items)
	}
	for i := range want.Items {
		if got.Items[i] != want.Items[i] {
			t.Fatalf("Items[%d] = %q, want %q", i, got.Items[i], want.Items[i])
		}
	}
	if !got.CreatedAt.Equal(want.CreatedAt) {
		t.Fatalf("CreatedAt = %v, want %v", got.CreatedAt, want.CreatedAt)
	}
	if got.Notes == nil || *got.Notes != *want.Notes {
		t.Fatalf("Notes = %v, want %q", got.Notes, *want.Notes)
	}
	if !bytes.Equal(got.Metadata, want.Metadata) {
		t.Fatalf("Metadata = %s, want %s", got.Metadata, want.Metadata)
	}
}

func TestToProtoFromProto_NilNotesStaysNil(t *testing.T) {
	o := Order{ID: "ord_no_notes", Amount: Money{Cents: 1, Currency: "USD"}, CreatedAt: time.Now().Truncate(time.Second)}
	p := ToProto(o)
	if p.Notes != nil {
		t.Fatalf("proto Notes = %v, want nil for an Order with no notes", p.Notes)
	}
	got, err := FromProto(p)
	if err != nil {
		t.Fatalf("FromProto: %v", err)
	}
	if got.Notes != nil {
		t.Fatalf("Notes = %v, want nil", got.Notes)
	}
}

func TestFromProto_NilInputErrors(t *testing.T) {
	if _, err := FromProto(nil); err == nil {
		t.Fatal("FromProto(nil) = nil error, want error")
	}
}
