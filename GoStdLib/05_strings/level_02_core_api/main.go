/*
LEVEL 02 (core) - the core API: Split/SplitN/Fields, Replace/ReplaceAll, Trim*

You will learn
  - Split(s, sep) vs SplitN(s, sep, n) (n caps the number of pieces)
  - Fields(s) splits on runs of whitespace and drops empty results, unlike Split
  - Replace(s, old, new, n) vs ReplaceAll(s, old, new) (n=-1 means "all")
  - TrimSpace/TrimLeft/TrimRight/TrimFunc for stripping unwanted edges

Run: go run ./GoStdLib/05_strings/level_02_core_api
*/

package main

import (
	"fmt"
	"strings"
	"unicode"
)

func main() {
	csv := "a,b,,c"

	parts := strings.Split(csv, ",")
	if len(parts) != 4 {
		panic(fmt.Sprintf("Split gave %d parts, expected 4: %v", len(parts), parts))
	}
	if parts[2] != "" {
		panic(fmt.Sprintf("Split should keep the empty field, got %q", parts[2]))
	}

	partsN := strings.SplitN(csv, ",", 2)
	if len(partsN) != 2 || partsN[1] != "b,,c" {
		panic(fmt.Sprintf("SplitN(2) = %v, expected [\"a\" \"b,,c\"]", partsN))
	}

	fields := strings.Fields("  the   quick\tbrown  fox  ")
	expectedFields := []string{"the", "quick", "brown", "fox"}
	if len(fields) != len(expectedFields) {
		panic(fmt.Sprintf("Fields gave %d words, expected %d: %v", len(fields), len(expectedFields), fields))
	}
	for i, w := range expectedFields {
		if fields[i] != w {
			panic(fmt.Sprintf("Fields[%d] = %q, expected %q", i, fields[i], w))
		}
	}

	once := strings.Replace("aaaa", "a", "b", 1)
	if once != "baaa" {
		panic(fmt.Sprintf("Replace(n=1) = %q, expected %q", once, "baaa"))
	}
	all := strings.ReplaceAll("aaaa", "a", "b")
	if all != "bbbb" {
		panic(fmt.Sprintf("ReplaceAll = %q, expected %q", all, "bbbb"))
	}

	trimmed := strings.TrimSpace("  \thello world\n  ")
	if trimmed != "hello world" {
		panic(fmt.Sprintf("TrimSpace = %q, expected %q", trimmed, "hello world"))
	}
	leftTrimmed := strings.TrimLeft("000123", "0")
	if leftTrimmed != "123" {
		panic(fmt.Sprintf("TrimLeft = %q, expected %q", leftTrimmed, "123"))
	}
	rightTrimmed := strings.TrimRight("123000", "0")
	if rightTrimmed != "123" {
		panic(fmt.Sprintf("TrimRight = %q, expected %q", rightTrimmed, "123"))
	}
	funcTrimmed := strings.TrimFunc("123abc456", unicode.IsDigit)
	if funcTrimmed != "abc" {
		panic(fmt.Sprintf("TrimFunc = %q, expected %q", funcTrimmed, "abc"))
	}

	fmt.Println("Split/SplitN/Fields, Replace/ReplaceAll, Trim family all behaved as documented")
	fmt.Println("OK")
}
