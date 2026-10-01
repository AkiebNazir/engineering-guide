/*
LEVEL 04 (core) - real errors: filepath.ErrBadPattern from Match and Glob

You will learn
  - filepath.Match reports whether a name matches a shell-style pattern
    ('*', '?', '[...]') and returns filepath.ErrBadPattern for a malformed one
  - filepath.Glob returns the same error for the same reason - an unterminated
    character class, not a panic
  - check it with errors.Is, exactly like any other sentinel error

Run: go run ./GoStdLib/08_path_filepath/level_04_match_glob_errors
*/

package main

import (
	"errors"
	"fmt"
	"path/filepath"
)

func main() {
	// A well-formed pattern matches or doesn't, with no error.
	matched, err := filepath.Match("*.go", "main.go")
	if err != nil {
		panic(fmt.Sprintf("Match(*.go) failed unexpectedly: %v", err))
	}
	if !matched {
		panic("Match(*.go, main.go) = false, want true")
	}

	matched, err = filepath.Match("*.go", "main.py")
	if err != nil {
		panic(fmt.Sprintf("Match(*.go, main.py) failed unexpectedly: %v", err))
	}
	if matched {
		panic("Match(*.go, main.py) = true, want false")
	}

	// "[" opens a character class that is never closed - a real malformed
	// pattern, not a hypothetical one.
	const badPattern = "[abc"
	_, err = filepath.Match(badPattern, "a")
	if !errors.Is(err, filepath.ErrBadPattern) {
		panic(fmt.Sprintf("Match(%q, ...) error = %v, want ErrBadPattern", badPattern, err))
	}
	fmt.Printf("Match(%q, ...) correctly reported: %v\n", badPattern, err)

	// Glob hits the same validation and surfaces the identical sentinel.
	_, err = filepath.Glob(badPattern)
	if !errors.Is(err, filepath.ErrBadPattern) {
		panic(fmt.Sprintf("Glob(%q) error = %v, want ErrBadPattern", badPattern, err))
	}
	fmt.Printf("Glob(%q) correctly reported: %v\n", badPattern, err)

	// A well-formed but non-matching Glob pattern is NOT an error - it's just
	// an empty (nil) result. Confusing "no matches" with "bad pattern" is a
	// common mistake this contrast guards against.
	matches, err := filepath.Glob("no-such-directory-xyz/*.go")
	if err != nil {
		panic(fmt.Sprintf("Glob with no matches should not error, got: %v", err))
	}
	if matches != nil {
		panic(fmt.Sprintf("Glob with no matches = %v, want nil", matches))
	}

	fmt.Println("OK")
}
