/*
LEVEL 09 (advanced) - RE2's real limitation: no backreferences, no lookaround

You will learn
  - RE2 (Go's engine) guarantees linear-time matching by refusing any
    feature that could require exponential backtracking - backreferences
    (\1) and lookaround ((?=...), (?<=...)) are exactly those features, and
    Go's regexp REJECTS them at Compile time, it does not silently ignore
    them
  - the Go-idiomatic workaround: capture broadly with a plain group, then
    check the extra condition in Go code afterward ("post-filtering")

Run: go run ./GoStdLib/14_regexp/level_09_re2_no_backreference_trap
*/

package main

import (
	"fmt"
	"regexp"
	"strings"
)

func main() {
	// In PCRE, finding an immediately-repeated word ("the the") is one line:
	//   \b(\w+)\s+\1\b
	// \1 is a backreference to whatever group 1 actually matched. RE2 does
	// not support this - it FAILS TO COMPILE, it does not compile and then
	// misbehave.
	_, err := regexp.Compile(`\b(\w+)\s+\1\b`)
	if err == nil {
		panic("regexp.Compile with a backreference unexpectedly succeeded, want an error")
	}
	fmt.Printf("backreference pattern rejected as expected: %v\n", err)

	// Likewise, lookahead - "digits immediately followed by px, without
	// consuming px" - is also unsupported.
	_, err = regexp.Compile(`\d+(?=px)`)
	if err == nil {
		panic("regexp.Compile with a lookahead unexpectedly succeeded, want an error")
	}
	fmt.Printf("lookahead pattern rejected as expected: %v\n", err)

	// The Go-idiomatic workaround for the backreference case: capture
	// "a word, then whitespace, then another word" broadly with a plain
	// (non-backreferenced) pattern, then POST-FILTER in Go code by comparing
	// the two captured words for equality.
	wordPairRe := regexp.MustCompile(`\b(\w+)\s+(\w+)\b`)

	findRepeatedWords := func(text string) []string {
		var repeats []string
		// FindAllStringSubmatchIndex would let us also advance one word at a
		// time for full accuracy on overlapping runs; FindAllStringSubmatch
		// is enough to demonstrate the technique here.
		for _, m := range wordPairRe.FindAllStringSubmatch(text, -1) {
			w1, w2 := strings.ToLower(m[1]), strings.ToLower(m[2])
			if w1 == w2 {
				repeats = append(repeats, w1)
			}
		}
		return repeats
	}

	got := findRepeatedWords("I saw the the cat, and the dog dog ran")
	want := []string{"the", "dog"}
	if len(got) != len(want) {
		panic(fmt.Sprintf("findRepeatedWords = %v, want %v", got, want))
	}
	for i := range want {
		if got[i] != want[i] {
			panic(fmt.Sprintf("findRepeatedWords[%d] = %q, want %q", i, got[i], want[i]))
		}
	}

	// A sentence with no repeats yields none.
	if got := findRepeatedWords("the quick brown fox jumps"); len(got) != 0 {
		panic(fmt.Sprintf("findRepeatedWords on clean text = %v, want empty", got))
	}

	fmt.Printf("found repeated words via post-filtering: %v\n", got)
	fmt.Println("OK")
}
