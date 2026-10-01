/*
LEVEL 09 (advanced) - production trap: decoding big integers into any loses precision

You will learn
  - json.Unmarshal into any/map[string]any decodes EVERY JSON number as
    float64, with no exception - there is no int case in that code path
  - float64 only has 53 bits of integer precision (max exact int ~9.007e15);
    a snowflake-style ID or a large database bigint above that silently
    rounds to the nearest representable float64, with no error
  - the fix: json.Decoder.UseNumber() decodes numbers as json.Number (a
    string under the hood) instead, preserving the exact digits

Run: go run ./GoStdLib/09_encoding_json/level_09_any_map_float64_precision_trap
*/

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strconv"
)

func main() {
	// 9007199254740993 is 2^53 + 1 - the smallest positive integer that
	// float64 CANNOT represent exactly (it rounds to 2^53 = 9007199254740992).
	const bigID = "9007199254740993"
	payload := []byte(fmt.Sprintf(`{"id": %s, "name": "widget"}`, bigID))

	// --- the trap: decode into a generic map[string]any ---
	var generic map[string]any
	if err := json.Unmarshal(payload, &generic); err != nil {
		panic(fmt.Sprintf("Unmarshal into map failed: %v", err))
	}
	idFloat, ok := generic["id"].(float64)
	if !ok {
		panic(fmt.Sprintf("generic[\"id\"] has type %T, want float64 (that's the trap itself)", generic["id"]))
	}

	// Prove the corruption for real: converting the float64 back to an exact
	// integer string must NOT match the original digits.
	corrupted := strconv.FormatFloat(idFloat, 'f', 0, 64)
	if corrupted == bigID {
		panic(fmt.Sprintf("expected precision loss decoding %s into float64, but got the exact value back - environment did not reproduce the trap", bigID))
	}
	fmt.Printf("BUG reproduced: %s decoded into map[string]any became %s (not the same number)\n", bigID, corrupted)

	// --- the fix: UseNumber() on a Decoder keeps the raw digits intact ---
	dec := json.NewDecoder(bytes.NewReader(payload))
	dec.UseNumber()
	var precise map[string]any
	if err := dec.Decode(&precise); err != nil {
		panic(fmt.Sprintf("Decode with UseNumber failed: %v", err))
	}
	num, ok := precise["id"].(json.Number)
	if !ok {
		panic(fmt.Sprintf("precise[\"id\"] has type %T, want json.Number", precise["id"]))
	}
	if num.String() != bigID {
		panic(fmt.Sprintf("json.Number.String() = %q, want exact %q", num.String(), bigID))
	}

	// json.Number converts to int64 exactly when it fits, unlike the float path.
	asInt64, err := num.Int64()
	if err != nil {
		panic(fmt.Sprintf("Int64() failed: %v", err))
	}
	if strconv.FormatInt(asInt64, 10) != bigID {
		panic(fmt.Sprintf("int64 round trip = %d, want exact %s", asInt64, bigID))
	}

	fmt.Printf("FIXED: with UseNumber(), %s round-trips exactly as %s\n", bigID, num.String())
	fmt.Println("OK")
}
