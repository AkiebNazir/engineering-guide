/*
LEVEL 05 (advanced) - a custom MarshalJSON/UnmarshalJSON pair

You will learn
  - implementing json.Marshaler (MarshalJSON() ([]byte, error)) and
    json.Unmarshaler (UnmarshalJSON([]byte) error) on a type overrides the
    default reflection-based encoding entirely
  - useful when the wire format and the Go representation genuinely differ:
    here, Money stores integer cents internally but reads/writes as a decimal
    string like "19.99" on the wire, so no float rounding ever touches money

Run: go run ./GoStdLib/09_encoding_json/level_05_custom_marshal_unmarshal
*/

package main

import (
	"encoding/json"
	"fmt"
)

// Money stores an exact amount as integer cents; JSON sees a decimal string.
type Money int64 // cents

func (m Money) MarshalJSON() ([]byte, error) {
	s := fmt.Sprintf("%d.%02d", m/100, m%100)
	return json.Marshal(s) // json.Marshal on a string handles quoting/escaping
}

func (m *Money) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("Money: expected a JSON string, got %s: %w", data, err)
	}
	var whole, cents int64
	if _, err := fmt.Sscanf(s, "%d.%d", &whole, &cents); err != nil {
		return fmt.Errorf("Money: cannot parse %q as dollars.cents: %w", s, err)
	}
	*m = Money(whole*100 + cents)
	return nil
}

type Invoice struct {
	ID     int   `json:"id"`
	Amount Money `json:"amount"`
}

func main() {
	inv := Invoice{ID: 1, Amount: 1999} // $19.99

	data, err := json.Marshal(inv)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want := `{"id":1,"amount":"19.99"}`
	if string(data) != want {
		panic(fmt.Sprintf("Marshal(inv) = %s, want %s", data, want))
	}

	var back Invoice
	if err := json.Unmarshal(data, &back); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if back.Amount != 1999 {
		panic(fmt.Sprintf("Amount = %d cents, want 1999", back.Amount))
	}

	// Round-trip an amount with single-digit cents to catch a common padding bug.
	small := Invoice{ID: 2, Amount: 105} // $1.05
	data2, err := json.Marshal(small)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want2 := `{"id":2,"amount":"1.05"}`
	if string(data2) != want2 {
		panic(fmt.Sprintf("Marshal(small) = %s, want %s (cents must be zero-padded)", data2, want2))
	}
	var backSmall Invoice
	if err := json.Unmarshal(data2, &backSmall); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if backSmall.Amount != 105 {
		panic(fmt.Sprintf("Amount = %d cents, want 105", backSmall.Amount))
	}

	// Feeding UnmarshalJSON malformed input produces a real, wrapped error.
	var bad Invoice
	err = json.Unmarshal([]byte(`{"id":3,"amount":"not-money"}`), &bad)
	if err == nil {
		panic("expected an error unmarshaling a malformed Money string, got nil")
	}
	fmt.Printf("malformed Money correctly rejected: %v\n", err)

	fmt.Printf("marshaled: %s\n", data)
	fmt.Println("OK")
}
