/*
LEVEL 01 (basic) - json.Marshal and json.Unmarshal on a simple struct

You will learn
  - json.Marshal converts a Go value to a []byte of JSON text
  - json.Unmarshal parses JSON text into a Go value via a pointer
  - by default, field names in JSON match the Go field name exactly (case-sensitive
    for Marshal's output, case-insensitive for Unmarshal's matching)

Run: go run ./GoStdLib/09_encoding_json/level_01_marshal_unmarshal_basics
*/

package main

import (
	"encoding/json"
	"fmt"
)

type Point struct {
	X int
	Y int
}

// asAny hides the argument's concrete type from static analysis (go vet
// specifically flags an *obviously* non-pointer literal passed to
// json.Unmarshal) so level 1 can demonstrate the real runtime error instead.
func asAny(v any) any { return v }

func main() {
	p := Point{X: 3, Y: 4}

	data, err := json.Marshal(p)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want := `{"X":3,"Y":4}`
	if string(data) != want {
		panic(fmt.Sprintf("Marshal(p) = %s, want %s", data, want))
	}

	var back Point
	if err := json.Unmarshal(data, &back); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if back != p {
		panic(fmt.Sprintf("round trip = %+v, want %+v", back, p))
	}

	// Unmarshal is case-insensitive when matching JSON keys to Go field names.
	var lower Point
	if err := json.Unmarshal([]byte(`{"x": 10, "y": 20}`), &lower); err != nil {
		panic(fmt.Sprintf("Unmarshal (lowercase keys) failed: %v", err))
	}
	if lower != (Point{X: 10, Y: 20}) {
		panic(fmt.Sprintf("case-insensitive unmarshal = %+v, want {10 20}", lower))
	}

	// Unmarshal must be given a pointer for the result to be visible - passing
	// a non-pointer is a common mistake, and it IS a real error. `go vet`
	// catches this exact mistake at compile time when the argument's static
	// type is obviously non-pointer, so the value is routed through an `any`
	// on purpose here to show the RUNTIME error Unmarshal itself reports.
	err = json.Unmarshal(data, asAny(back)) // back, not &back
	if err == nil {
		panic("Unmarshal into a non-pointer should fail, got nil error")
	}
	fmt.Printf("Unmarshal into a non-pointer correctly failed: %v\n", err)

	fmt.Printf("marshaled: %s\n", data)
	fmt.Println("OK")
}
