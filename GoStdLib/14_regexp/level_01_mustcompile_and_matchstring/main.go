/*
LEVEL 01 (basic) - regexp.MustCompile and MatchString: the yes/no check

You will learn
  - regexp.MustCompile(pattern) builds a *Regexp once, panicking if the
    pattern itself is malformed (a programmer error, caught immediately)
  - (*Regexp).MatchString(s) is the simplest operation: does this string
    match the pattern, at all, anywhere - a plain bool
  - the package-level regexp.MatchString(pattern, s) shortcut exists too,
    but it compiles the pattern EVERY call - fine for a one-off, wrong
    inside a loop (level 6 measures exactly how wrong)

Run: go run ./GoStdLib/14_regexp/level_01_mustcompile_and_matchstring
*/

package main

import (
	"fmt"
	"regexp"
)

// A fixed pattern known at compile time: MustCompile is the right call
// here. If this pattern were ever wrong, we want the program to fail loudly
// at startup, not silently misbehave in production.
var digitsOnly = regexp.MustCompile(`^[0-9]+$`)

func main() {
	cases := []struct {
		input string
		want  bool
	}{
		{"12345", true},
		{"007", true},
		{"", false},
		{"12a45", false},
		{"-5", false}, // no sign allowed by this pattern
	}

	for _, c := range cases {
		got := digitsOnly.MatchString(c.input)
		if got != c.want {
			panic(fmt.Sprintf("digitsOnly.MatchString(%q) = %v, want %v", c.input, got, c.want))
		}
	}

	// The package-level shortcut does the same check, compiling the pattern
	// internally on this one call - convenient for a single use, not for
	// repeated use (see level 6).
	got, err := regexp.MatchString(`^[0-9]+$`, "42")
	if err != nil {
		panic(fmt.Sprintf("regexp.MatchString returned error: %v", err))
	}
	if !got {
		panic("regexp.MatchString(`^[0-9]+$`, \"42\") = false, want true")
	}

	fmt.Printf("checked %d inputs against %q\n", len(cases), digitsOnly.String())
	fmt.Println("OK")
}
