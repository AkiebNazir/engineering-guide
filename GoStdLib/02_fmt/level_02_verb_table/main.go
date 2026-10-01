/*
LEVEL 02 (core) - the Printf verb table: %v %+v %#v %T %q %x %p

You will learn
  - %v: the default representation; %+v: adds struct field names
  - %#v: a Go-syntax representation, including the type name
  - %T: the value's dynamic type as text
  - %q: a double-quoted, escaped string literal
  - %x: lowercase hexadecimal (of ints or of a string/[]byte's bytes)
  - %p: a pointer's address in hex, prefixed with 0x

Run: go run ./GoStdLib/02_fmt/level_02_verb_table
*/

package main

import (
	"fmt"
	"strings"
)

type Point struct {
	X, Y int
}

func main() {
	p := Point{X: 3, Y: 4}

	v := fmt.Sprintf("%v", p)
	if v != "{3 4}" {
		panic(fmt.Sprintf("%%v mismatch: got %q, want %q", v, "{3 4}"))
	}

	plusV := fmt.Sprintf("%+v", p)
	if plusV != "{X:3 Y:4}" {
		panic(fmt.Sprintf("%%+v mismatch: got %q, want %q", plusV, "{X:3 Y:4}"))
	}

	hashV := fmt.Sprintf("%#v", p)
	want := "main.Point{X:3, Y:4}"
	if hashV != want {
		panic(fmt.Sprintf("%%#v mismatch: got %q, want %q", hashV, want))
	}

	typ := fmt.Sprintf("%T", p)
	if typ != "main.Point" {
		panic(fmt.Sprintf("%%T mismatch: got %q, want %q", typ, "main.Point"))
	}

	quoted := fmt.Sprintf("%q", "line\n\"quoted\"")
	wantQuoted := `"line\n\"quoted\""`
	if quoted != wantQuoted {
		panic(fmt.Sprintf("%%q mismatch: got %q, want %q", quoted, wantQuoted))
	}

	hexInt := fmt.Sprintf("%x", 255)
	if hexInt != "ff" {
		panic(fmt.Sprintf("%%x on int mismatch: got %q, want %q", hexInt, "ff"))
	}

	hexStr := fmt.Sprintf("%x", "AB")
	if hexStr != "4142" { // bytes 'A'=0x41, 'B'=0x42
		panic(fmt.Sprintf("%%x on string mismatch: got %q, want %q", hexStr, "4142"))
	}

	n := 42
	ptr := fmt.Sprintf("%p", &n)
	if !strings.HasPrefix(ptr, "0x") {
		panic(fmt.Sprintf("%%p should be prefixed with 0x, got %q", ptr))
	}

	fmt.Printf("%%v    -> %v\n", p)
	fmt.Printf("%%+v   -> %+v\n", p)
	fmt.Printf("%%#v   -> %#v\n", p)
	fmt.Printf("%%T    -> %T\n", p)
	fmt.Printf("%%q    -> %q\n", "line\n\"quoted\"")
	fmt.Printf("%%x    -> %x (int) / %x (string)\n", 255, "AB")
	fmt.Printf("%%p    -> %s (address, varies per run)\n", ptr)
	fmt.Println("OK")
}
