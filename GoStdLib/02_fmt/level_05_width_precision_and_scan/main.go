/*
LEVEL 05 (intermediate) - reading input with Scan/Scanf/Scanln, non-interactively

You will learn
  - fmt.Fscan/Fscanf/Fscanln read from any io.Reader - here a strings.Reader,
    so the demo needs no real stdin and is fully reproducible
  - Scan/Scanln split on whitespace and ignore newlines vs stop-at-newline
    respectively; Scanf matches literal characters in the format exactly
  - all three return the count of successfully scanned items plus an error

Run: go run ./GoStdLib/02_fmt/level_05_width_precision_and_scan
*/

package main

import (
	"fmt"
	"strings"
)

func main() {
	// Fscan: whitespace-separated, newlines are just more whitespace.
	r1 := strings.NewReader("42 3.5 hello")
	var i int
	var f float64
	var s string
	n, err := fmt.Fscan(r1, &i, &f, &s)
	if err != nil {
		panic(fmt.Sprintf("Fscan failed: %v", err))
	}
	if n != 3 {
		panic(fmt.Sprintf("expected 3 items scanned, got %d", n))
	}
	if i != 42 || f != 3.5 || s != "hello" {
		panic(fmt.Sprintf("Fscan values wrong: i=%d f=%v s=%q", i, f, s))
	}

	// Fscanln: like Fscan but stops at a newline - a second line is untouched.
	r2 := strings.NewReader("1 2\n3 4\n")
	var a, b int
	n2, err := fmt.Fscanln(r2, &a, &b)
	if err != nil {
		panic(fmt.Sprintf("Fscanln failed: %v", err))
	}
	if n2 != 2 || a != 1 || b != 2 {
		panic(fmt.Sprintf("Fscanln first line wrong: n=%d a=%d b=%d", n2, a, b))
	}
	var c, d int
	if _, err := fmt.Fscanln(r2, &c, &d); err != nil {
		panic(fmt.Sprintf("Fscanln second line failed: %v", err))
	}
	if c != 3 || d != 4 {
		panic(fmt.Sprintf("Fscanln second line wrong: c=%d d=%d", c, d))
	}

	// Fscanf: literal text in the format string must match the input exactly.
	r3 := strings.NewReader("name=widget qty=7")
	var name string
	var qty int
	n3, err := fmt.Fscanf(r3, "name=%s qty=%d", &name, &qty)
	if err != nil {
		panic(fmt.Sprintf("Fscanf failed: %v", err))
	}
	if n3 != 2 || name != "widget" || qty != 7 {
		panic(fmt.Sprintf("Fscanf values wrong: n=%d name=%q qty=%d", n3, name, qty))
	}

	// Mismatched literal text makes Fscanf fail with a partial scan count.
	r4 := strings.NewReader("id: 9")
	var id int
	n4, err := fmt.Fscanf(r4, "code=%d", &id)
	if err == nil {
		panic("expected Fscanf to fail when literal text doesn't match input")
	}
	if n4 != 0 {
		panic(fmt.Sprintf("expected 0 items scanned on literal mismatch, got %d", n4))
	}

	fmt.Printf("Fscan:   i=%d f=%.1f s=%s\n", i, f, s)
	fmt.Printf("Fscanln: line1=(%d,%d) line2=(%d,%d)\n", a, b, c, d)
	fmt.Printf("Fscanf:  name=%s qty=%d\n", name, qty)
	fmt.Printf("Fscanf on mismatched literal failed as expected: %v\n", err)
	fmt.Println("OK")
}
