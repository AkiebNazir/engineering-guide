/*
LEVEL 10 (capstone) - a small record pipeline using most of levels 1-9 together

You will learn
  - how struct tags, a custom json.Marshaler/Unmarshaler, streaming Decode,
    DisallowUnknownFields, and json.Number combine into one realistic small
    program: stream-decode a batch of records, validate strictly, and total
    an exact-precision amount field

Run: go run ./GoStdLib/09_encoding_json/level_10_capstone_record_pipeline
*/

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
)

// Cents is a custom type: JSON sees a decimal string, Go stores exact integer cents.
type Cents int64

func (c Cents) MarshalJSON() ([]byte, error) {
	return json.Marshal(fmt.Sprintf("%d.%02d", c/100, c%100))
}

func (c *Cents) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return err
	}
	var whole, frac int64
	if _, err := fmt.Sscanf(s, "%d.%d", &whole, &frac); err != nil {
		return fmt.Errorf("Cents: %q: %w", s, err)
	}
	*c = Cents(whole*100 + frac)
	return nil
}

// Record is deliberately strict: an unrecognized field must fail decoding.
type Record struct {
	ID     json.Number `json:"id"` // preserves exact digits, unlike float64
	Item   string      `json:"item"`
	Amount Cents       `json:"amount"`
}

func main() {
	// A batch as it might arrive over the wire: a JSON array of records, one
	// with an ID too large for float64 to hold exactly, proving json.Number matters.
	batch := []byte(`[
		{"id": "9007199254740993", "item": "widget", "amount": "19.99"},
		{"id": "2",                "item": "gadget", "amount": "5.50"},
		{"id": "3",                "item": "gizmo",  "amount": "0.75"}
	]`)

	dec := json.NewDecoder(bytes.NewReader(batch))
	dec.DisallowUnknownFields()

	if tok, err := dec.Token(); err != nil {
		panic(fmt.Sprintf("reading opening token failed: %v", err))
	} else if d, ok := tok.(json.Delim); !ok || d != '[' {
		panic(fmt.Sprintf("first token = %v, want '['", tok))
	}

	var records []Record
	var total Cents
	for dec.More() {
		var r Record
		if err := dec.Decode(&r); err != nil {
			panic(fmt.Sprintf("Decode record %d failed: %v", len(records), err))
		}
		records = append(records, r)
		total += r.Amount
	}

	if len(records) != 3 {
		panic(fmt.Sprintf("decoded %d records, want 3", len(records)))
	}
	if records[0].ID.String() != "9007199254740993" {
		panic(fmt.Sprintf("records[0].ID = %s, want exact 9007199254740993", records[0].ID.String()))
	}
	wantTotal := Cents(1999 + 550 + 75)
	if total != wantTotal {
		panic(fmt.Sprintf("total = %d cents, want %d cents", total, wantTotal))
	}

	// A record with a field the schema doesn't know about must be rejected.
	badRecord := []byte(`{"id": "4", "item": "sprocket", "amount": "1.00", "discount": true}`)
	strictDec := json.NewDecoder(bytes.NewReader(badRecord))
	strictDec.DisallowUnknownFields()
	var bad Record
	if err := strictDec.Decode(&bad); err == nil {
		panic("expected DisallowUnknownFields to reject the 'discount' field, got nil error")
	} else {
		fmt.Printf("strict schema correctly rejected an unknown field: %v\n", err)
	}

	fmt.Printf("processed %d records, exact total = %d.%02d\n", len(records), total/100, total%100)
	fmt.Println("OK")
}
