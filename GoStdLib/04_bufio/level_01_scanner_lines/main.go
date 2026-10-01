/*
LEVEL 01 (basic) - bufio.Scanner: reading lines, the single most common use

You will learn
  - the smallest way to read text line by line: bufio.NewScanner + Scan()/Text()
  - the default split function (bufio.ScanLines) strips the trailing newline for you
  - Scan() returns false at EOF or on error - Err() tells you which

Run: go run ./GoStdLib/04_bufio/level_01_scanner_lines
*/

package main

import (
	"bufio"
	"fmt"
	"strings"
)

func main() {
	input := "first line\nsecond line\nthird line\n"

	scanner := bufio.NewScanner(strings.NewReader(input))

	var lines []string
	for scanner.Scan() {
		// Text() returns the line WITHOUT the trailing \n - ScanLines already stripped it.
		lines = append(lines, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		panic(fmt.Sprintf("unexpected scanner error: %v", err))
	}

	expected := []string{"first line", "second line", "third line"}
	if len(lines) != len(expected) {
		panic(fmt.Sprintf("got %d lines, expected %d: %v", len(lines), len(expected), lines))
	}
	for i, want := range expected {
		if lines[i] != want {
			panic(fmt.Sprintf("line %d = %q, expected %q", i, lines[i], want))
		}
	}

	fmt.Printf("read %d lines: %v\n", len(lines), lines)
	fmt.Println("OK")
}
