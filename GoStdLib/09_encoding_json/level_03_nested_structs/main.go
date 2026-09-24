/*
LEVEL 03 (core) - nested structs, slices, and maps

You will learn
  - a struct field that is itself a struct nests as a JSON object automatically
  - a []T field becomes a JSON array; a map[string]T field becomes a JSON object
  - this composes recursively with no extra code - the reflection-based
    encoder walks the whole value graph

Run: go run ./GoStdLib/09_encoding_json/level_03_nested_structs
*/

package main

import (
	"encoding/json"
	"fmt"
)

type Address struct {
	City    string `json:"city"`
	Country string `json:"country"`
}

type Order struct {
	ID       int            `json:"id"`
	Customer string         `json:"customer"`
	Ship     Address        `json:"ship_to"`
	Items    []string       `json:"items"`
	Meta     map[string]int `json:"meta,omitempty"`
}

func main() {
	order := Order{
		ID:       1001,
		Customer: "Ana",
		Ship:     Address{City: "Lisbon", Country: "PT"},
		Items:    []string{"widget", "gadget"},
		Meta:     map[string]int{"weight_g": 450},
	}

	data, err := json.Marshal(order)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want := `{"id":1001,"customer":"Ana","ship_to":{"city":"Lisbon","country":"PT"},"items":["widget","gadget"],"meta":{"weight_g":450}}`
	if string(data) != want {
		panic(fmt.Sprintf("Marshal(order) = %s, want %s", data, want))
	}

	var back Order
	if err := json.Unmarshal(data, &back); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if back.Ship != order.Ship {
		panic(fmt.Sprintf("nested Ship = %+v, want %+v", back.Ship, order.Ship))
	}
	if len(back.Items) != 2 || back.Items[0] != "widget" || back.Items[1] != "gadget" {
		panic(fmt.Sprintf("Items = %v, want [widget gadget]", back.Items))
	}
	if back.Meta["weight_g"] != 450 {
		panic(fmt.Sprintf("Meta[weight_g] = %d, want 450", back.Meta["weight_g"]))
	}

	// A nil slice/map with omitempty vanishes from the output entirely.
	empty := Order{ID: 2, Customer: "Bo", Ship: Address{City: "Porto", Country: "PT"}}
	data2, err := json.Marshal(empty)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want2 := `{"id":2,"customer":"Bo","ship_to":{"city":"Porto","country":"PT"},"items":null}`
	if string(data2) != want2 {
		panic(fmt.Sprintf("Marshal(empty) = %s, want %s (items has no omitempty, so it's null; meta does, so it's gone)", data2, want2))
	}

	fmt.Printf("nested: %s\n", data)
	fmt.Println("OK")
}
