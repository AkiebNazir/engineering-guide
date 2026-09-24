/*
LEVEL 04 (advanced) - a real Compile error, handled; why MustCompile suits fixed patterns

You will learn
  - a malformed pattern makes regexp.Compile return a real *syntax.Error,
    not a panic - triggered here for real, not just described
  - regexp.MustCompile wraps Compile and panics on that same error - correct
    when the pattern is a literal in your source (a bug you want caught at
    startup, in tests, or in CI - never in a live request path)
  - when the pattern comes from outside the binary (config, a flag, a
    request), you MUST use Compile and handle the error - a malicious or
    just-wrong user-supplied pattern must never be able to crash the process

Run: go run ./GoStdLib/14_regexp/level_04_compile_error_handling
*/

package main

import (
	"fmt"
	"regexp"
)

// compileUserPattern simulates accepting a regex from outside the program
// (e.g. a search box, a config file). Compile, not MustCompile: a bad
// pattern here is an EXPECTED possible input, not a programmer bug.
func compileUserPattern(pattern string) (*regexp.Regexp, error) {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return nil, fmt.Errorf("invalid search pattern %q: %w", pattern, err)
	}
	return re, nil
}

func main() {
	// An unbalanced group is a real, common malformed pattern.
	_, err := compileUserPattern(`(unclosed`)
	if err == nil {
		panic("compileUserPattern(`(unclosed`) returned nil error, want a real syntax error")
	}
	fmt.Printf("got the expected error: %v\n", err)

	// Compile's error is a real error value every time the pattern is bad,
	// not just this once - confirmed with a second, differently-broken
	// pattern (an invalid repeat count this time).
	if _, err := regexp.Compile(`a{2,1}`); err == nil {
		panic("regexp.Compile(`a{2,1}`) = nil error, want non-nil (invalid repeat range)")
	}

	// A valid user pattern compiles and works normally.
	re, err := compileUserPattern(`^go\d+$`)
	if err != nil {
		panic(fmt.Sprintf("compileUserPattern on a valid pattern failed: %v", err))
	}
	if !re.MatchString("go121") {
		panic("valid compiled pattern failed to match \"go121\"")
	}

	// MustCompile on the SAME bad pattern panics - proven with recover, not
	// just asserted in a comment. This is the behavior you want at package
	// init for a pattern YOU wrote, never for one a user supplied.
	panicked := func() (recovered bool) {
		defer func() {
			if r := recover(); r != nil {
				recovered = true
			}
		}()
		regexp.MustCompile(`(unclosed`)
		return false
	}()
	if !panicked {
		panic("MustCompile on a malformed pattern did not panic, want a panic")
	}

	fmt.Println("Compile handled the bad pattern gracefully; MustCompile panicked as designed")
	fmt.Println("OK")
}
