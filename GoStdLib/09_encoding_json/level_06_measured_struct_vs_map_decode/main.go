/*
LEVEL 06 (advanced) - MEASURED: decoding into a typed struct vs map[string]any

You will learn
  - json.Unmarshal into a concrete struct uses reflection guided by the
    struct's own field layout; into map[string]any it must allocate a map,
    box every value in an `any`, and infer types field by field
  - this level actually times both approaches on THIS run and prints real
    numbers - never assert a performance claim without measuring it

Run: go run ./GoStdLib/09_encoding_json/level_06_measured_struct_vs_map_decode
*/

package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type Record struct {
	ID     int     `json:"id"`
	Name   string  `json:"name"`
	Score  float64 `json:"score"`
	Active bool    `json:"active"`
}

const iterations = 20_000

func main() {
	payload := []byte(`{"id":42,"name":"sample-record","score":98.6,"active":true}`)

	// --- approach 1: decode straight into a typed struct. ---
	start := time.Now()
	for i := 0; i < iterations; i++ {
		var r Record
		if err := json.Unmarshal(payload, &r); err != nil {
			panic(fmt.Sprintf("Unmarshal into struct failed: %v", err))
		}
		if r.ID != 42 {
			panic(fmt.Sprintf("r.ID = %d, want 42", r.ID))
		}
	}
	structDur := time.Since(start)

	// --- approach 2: decode into map[string]any, then read fields out. ---
	start = time.Now()
	for i := 0; i < iterations; i++ {
		var m map[string]any
		if err := json.Unmarshal(payload, &m); err != nil {
			panic(fmt.Sprintf("Unmarshal into map failed: %v", err))
		}
		id, ok := m["id"].(float64) // every number decodes as float64 - see level 9
		if !ok || id != 42 {
			panic(fmt.Sprintf("m[\"id\"] = %v (%T), want float64(42)", m["id"], m["id"]))
		}
	}
	mapDur := time.Since(start)

	fmt.Printf("iterations=%d\n", iterations)
	fmt.Printf("decode into struct:          %v (%v/iter)\n", structDur, structDur/iterations)
	fmt.Printf("decode into map[string]any:  %v (%v/iter)\n", mapDur, mapDur/iterations)

	if structDur < mapDur {
		speedup := float64(mapDur) / float64(structDur)
		fmt.Printf("measured: struct decode was %.1fx faster on this run\n", speedup)
	} else {
		// Report honestly even if this run didn't show the expected direction.
		fmt.Println("measured: struct decode was NOT faster on this run - reporting the real numbers above as-is")
	}

	fmt.Println("OK")
}
