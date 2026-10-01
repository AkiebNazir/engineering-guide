/*
LEVEL 02 (core) - struct tags: renaming fields and json:"...,omitempty"

You will learn
  - `json:"name"` controls the JSON key used for a field, independent of the
    Go field name
  - `json:"-"` excludes a field from JSON entirely
  - `json:",omitempty"` drops the field from output when it holds its zero
    value (0, "", nil, false, empty slice/map) - it does NOT mean "required"

Run: go run ./GoStdLib/09_encoding_json/level_02_struct_tags_and_omitempty
*/

package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type User struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Nickname string `json:"nickname,omitempty"`
	Password string `json:"-"` // never serialized
}

func main() {
	full := User{ID: 1, Name: "Ana", Nickname: "Ani", Password: "secret"}
	data, err := json.Marshal(full)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want := `{"id":1,"name":"Ana","nickname":"Ani"}`
	if string(data) != want {
		panic(fmt.Sprintf("Marshal(full) = %s, want %s", data, want))
	}

	// With Nickname left at its zero value (""), omitempty drops the key entirely.
	sparse := User{ID: 2, Name: "Bo", Password: "secret2"}
	data2, err := json.Marshal(sparse)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	want2 := `{"id":2,"name":"Bo"}`
	if string(data2) != want2 {
		panic(fmt.Sprintf("Marshal(sparse) = %s, want %s (nickname key must be absent)", data2, want2))
	}

	// Password never appears, no matter what - confirm it can't leak.
	dangerous := User{ID: 3, Name: "Cy", Password: "should-never-appear"}
	data3, _ := json.Marshal(dangerous)
	for _, forbidden := range []string{"Password", "should-never-appear"} {
		if strings.Contains(string(data3), forbidden) {
			panic(fmt.Sprintf("Marshal output leaked %q: %s", forbidden, data3))
		}
	}

	// Unmarshaling JSON with the "-" key back in has no effect on Password -
	// json:"-" blocks both directions.
	var roundTrip User
	if err := json.Unmarshal([]byte(`{"id":4,"name":"Di","-":"ignored"}`), &roundTrip); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if roundTrip.Password != "" {
		panic(fmt.Sprintf("Password = %q, want empty: json:\"-\" must block unmarshal too", roundTrip.Password))
	}

	fmt.Printf("full:   %s\n", data)
	fmt.Printf("sparse: %s\n", data2)
	fmt.Println("OK")
}
