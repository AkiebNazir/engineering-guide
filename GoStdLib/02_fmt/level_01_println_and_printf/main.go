/*
LEVEL 01 (basic) - fmt.Println, fmt.Print, and fmt.Printf: the basics

You will learn
  - Println: space-separates its arguments and always adds a trailing newline
  - Print: space-separates arguments only between two non-string operands, no newline
  - Printf: a format string with verbs like %s, %d, %v, plus an explicit \n
  - all three return (int, error): bytes written and any write error

Run: go run ./GoStdLib/02_fmt/level_01_println_and_printf
*/

package main

import "fmt"

func main() {
	n1, err := fmt.Println("hello", "world")
	if err != nil {
		panic(fmt.Sprintf("Println failed: %v", err))
	}
	// "hello world\n" is 12 bytes.
	if n1 != 12 {
		panic(fmt.Sprintf("expected Println to report 12 bytes written, got %d", n1))
	}

	n2, err := fmt.Print("a", "b", 1, 2, "c")
	if err != nil {
		panic(fmt.Sprintf("Print failed: %v", err))
	}
	fmt.Println() // Print adds no trailing newline itself, add one for clean output
	// Print only inserts a space between two operands when NEITHER is a string:
	// "a" "b" -> "ab" (both strings, no space)
	// "b" 1   -> "b1" (one is a string, no space)
	// 1 2     -> "1 2" (neither is a string, space added)
	// 2 "c"   -> "2c" (one is a string, no space)
	if n2 != len("ab1 2c") {
		panic(fmt.Sprintf("expected Print to report %d bytes written, got %d", len("ab1 2c"), n2))
	}

	name, count := "widget", 3
	n3, err := fmt.Printf("%d x %s\n", count, name)
	if err != nil {
		panic(fmt.Sprintf("Printf failed: %v", err))
	}
	want := len("3 x widget\n")
	if n3 != want {
		panic(fmt.Sprintf("expected Printf to report %d bytes written, got %d", want, n3))
	}

	fmt.Println("OK")
}
