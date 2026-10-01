/*
LEVEL 01 (basic) - filepath.Join: building paths with the OS separator

You will learn
  - filepath.Join concatenates path elements using the current OS's separator
    (filepath.Separator: '/' on Unix/macOS, '\' on Windows)
  - Join also cleans the result (see level 2), so redundant slashes and empty
    elements are handled for you
  - why this beats hand-rolled string concatenation with "/"

Run: go run ./GoStdLib/08_path_filepath/level_01_join_separators
*/

package main

import (
	"fmt"
	"path/filepath"
	"runtime"
)

func main() {
	// Join is the single most common entry point into this package: build a
	// path from parts without worrying about separators or extra slashes.
	got := filepath.Join("var", "log", "app", "current.log")
	want := "var" + string(filepath.Separator) + "log" + string(filepath.Separator) + "app" + string(filepath.Separator) + "current.log"
	if got != want {
		panic(fmt.Sprintf("Join = %q, want %q", got, want))
	}

	// Empty elements are dropped, not turned into doubled separators.
	got2 := filepath.Join("a", "", "b")
	want2 := "a" + string(filepath.Separator) + "b"
	if got2 != want2 {
		panic(fmt.Sprintf("Join with empty element = %q, want %q", got2, want2))
	}

	// On this OS, the separator is whatever runtime.GOOS says it should be -
	// filepath is OS-aware because it reads this constant, fixed at compile time.
	var wantSep byte = '/'
	if runtime.GOOS == "windows" {
		wantSep = '\\'
	}
	if filepath.Separator != rune(wantSep) {
		panic(fmt.Sprintf("filepath.Separator = %q, want %q for GOOS=%s", filepath.Separator, wantSep, runtime.GOOS))
	}

	// Join with zero arguments returns the empty string, not an error.
	if filepath.Join() != "" {
		panic(fmt.Sprintf("Join() = %q, want empty string", filepath.Join()))
	}

	fmt.Printf("GOOS=%s separator=%q Join(...) = %q\n", runtime.GOOS, filepath.Separator, got)
	fmt.Println("OK")
}
