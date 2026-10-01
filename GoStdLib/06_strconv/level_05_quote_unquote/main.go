/*
LEVEL 05 (advanced) - intermediate pattern: Quote/Unquote round-trip

You will learn
  - strconv.Quote(s) produces a Go-syntax double-quoted string literal,
    escaping newlines, tabs, quotes, backslashes and non-printable runes
  - strconv.Unquote reverses it exactly, given a valid Go string literal
  - this is how you make a string with control characters safe to print or
    embed in generated source, without hand-rolling escaping

Run: go run ./GoStdLib/06_strconv/level_05_quote_unquote
*/

package main

import (
	"fmt"
	"strconv"
)

func main() {
	original := "line one\n\tline two with a \"quote\" and a backslash \\ and a bell \a"

	quoted := strconv.Quote(original)
	// The quoted form must be a valid Go literal: starts and ends with `"`.
	if len(quoted) < 2 || quoted[0] != '"' || quoted[len(quoted)-1] != '"' {
		panic(fmt.Sprintf("Quote output is not a valid literal shape: %s", quoted))
	}
	// The raw control characters must not appear literally in the quoted form.
	for _, r := range []rune{'\n', '\t', '\a'} {
		for _, c := range quoted {
			if c == r {
				panic(fmt.Sprintf("Quote left a raw control character %q unescaped in %s", r, quoted))
			}
		}
	}

	back, err := strconv.Unquote(quoted)
	if err != nil {
		panic(fmt.Sprintf("Unquote failed: %v", err))
	}
	if back != original {
		panic(fmt.Sprintf("round trip mismatch:\n  original=%q\n  back    =%q", original, back))
	}

	// Unquote rejects a string that isn't valid Go literal syntax.
	if _, err := strconv.Unquote(`not a literal`); err == nil {
		panic("expected Unquote to fail on an unquoted plain string")
	}

	fmt.Printf("original: %v bytes, %d visible chars\nquoted:   %s\n", len(original), len([]rune(original)), quoted)
	fmt.Println("OK")
}
