/*
LEVEL 02 (core) - Compile vs MustCompile, FindString, FindAllString

You will learn
  - regexp.Compile returns (*Regexp, error) instead of panicking - the right
    choice whenever the pattern is not a fixed literal you control
  - FindString returns the FIRST match (or "" for no match)
  - FindAllString returns every non-overlapping match, or nil for none; a
    negative limit (-1) means "all of them", a positive n caps the count

Run: go run ./GoStdLib/14_regexp/level_02_compile_vs_mustcompile_and_find
*/

package main

import (
	"fmt"
	"regexp"
)

func main() {
	// Compile: returns an error instead of panicking. Good practice even for
	// a fixed pattern when you want to handle the failure yourself.
	re, err := regexp.Compile(`\b\d{3}-\d{4}\b`) // a bare local phone extension shape
	if err != nil {
		panic(fmt.Sprintf("Compile failed: %v", err))
	}

	text := "call 555-1234 or the backup line 555-5678 during business hours"

	// FindString: the first match only.
	first := re.FindString(text)
	if first != "555-1234" {
		panic(fmt.Sprintf("FindString = %q, want %q", first, "555-1234"))
	}

	// FindAllString with -1: every match.
	all := re.FindAllString(text, -1)
	wantAll := []string{"555-1234", "555-5678"}
	if len(all) != len(wantAll) {
		panic(fmt.Sprintf("FindAllString returned %d matches, want %d: %v", len(all), len(wantAll), all))
	}
	for i := range wantAll {
		if all[i] != wantAll[i] {
			panic(fmt.Sprintf("FindAllString[%d] = %q, want %q", i, all[i], wantAll[i]))
		}
	}

	// FindAllString with a positive limit: capped count.
	limited := re.FindAllString(text, 1)
	if len(limited) != 1 || limited[0] != "555-1234" {
		panic(fmt.Sprintf("FindAllString(text, 1) = %v, want [555-1234]", limited))
	}

	// No match at all: FindString gives "", FindAllString gives nil.
	none := re.FindString("no numbers here")
	if none != "" {
		panic(fmt.Sprintf("FindString on non-matching text = %q, want \"\"", none))
	}
	noneAll := re.FindAllString("no numbers here", -1)
	if noneAll != nil {
		panic(fmt.Sprintf("FindAllString on non-matching text = %v, want nil", noneAll))
	}

	// --- hand-rolled contrast: what "does this contain a run of 3+ digits"
	// looks like scanning byte-by-byte, vs. one regexp.MatchString call.
	// Not claiming identical semantics to the phone pattern above - just
	// illustrating the line-count gap for the same rough idea.
	manualContainsDigitTriplet := func(s string) bool {
		for i := 0; i+3 <= len(s); i++ {
			allDigits := true
			for j := i; j < i+3; j++ {
				if s[j] < '0' || s[j] > '9' {
					allDigits = false
					break
				}
			}
			if allDigits {
				return true
			}
		}
		return false
	} // 10 lines of manual scanning...
	if !manualContainsDigitTriplet("555-1234") {
		panic("manual scan failed to find a 3-digit run in \"555-1234\"")
	}
	if re.MatchString("555-1234") != true { // ...vs 1 line with regexp
		panic("re.MatchString(\"555-1234\") = false, want true")
	}

	fmt.Printf("first=%q all=%v\n", first, all)
	fmt.Println("OK")
}
