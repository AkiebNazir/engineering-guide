/*
LEVEL 09 (advanced) - production trap: importing "path" for OS filesystem paths

You will learn
  - "path" (always uses '/', for URLs/slash-separated keys) and "path/filepath"
    (OS-aware) export functions with identical names and signatures - the
    wrong import still compiles, and on Unix it even still "works"
  - the bug only shows up once real Windows-style paths are involved, because
    "path" never treats '\' as a separator, on ANY platform
  - this is demonstrated directly, with a manually-constructed Windows-style
    path string, since a single run can't switch its own OS

Run: go run ./GoStdLib/08_path_filepath/level_09_path_vs_filepath_windows_trap
*/

package main

import (
	"fmt"
	"path"
	"path/filepath"
	"runtime"
	"strings"
)

func main() {
	// A path as it would appear on a Windows machine - never actually valid
	// on this (Unix-like) build host, which is exactly the point: whatever
	// package is used here treats it purely as a string, no filesystem calls.
	winPath := `C:\Users\njasm\project\main.go`

	// Both "path" and "path/filepath" only recognize '/' as a separator when
	// NOT built for Windows. On this platform, neither package sees a '/' in
	// winPath at all, so both treat the whole string as a single component -
	// the wrong import is invisible here; both give the SAME (wrong) answer.
	filepathBase := filepath.Base(winPath)
	pathBase := path.Base(winPath)

	if runtime.GOOS != "windows" {
		if filepathBase != winPath {
			panic(fmt.Sprintf("on %s, filepath.Base(winPath) = %q, want the unsplit input %q", runtime.GOOS, filepathBase, winPath))
		}
		if pathBase != winPath {
			panic(fmt.Sprintf("on %s, path.Base(winPath) = %q, want the unsplit input %q", runtime.GOOS, pathBase, winPath))
		}
		if filepathBase != pathBase {
			panic(fmt.Sprintf("expected filepath and path to agree (and both be wrong) on %s: %q != %q", runtime.GOOS, filepathBase, pathBase))
		}
	}

	// What the correct answer SHOULD be if this ran on Windows: filepath.Base
	// there would split on '\' and return "main.go". We compute that expected
	// answer manually here (without filepath) purely to state the fact - this
	// is what filepath.Base is written to do once GOOS=="windows", it just
	// cannot be exercised from a single non-Windows run.
	wantOnWindows := "main.go"
	manualWindowsSplit := winPath[strings.LastIndex(winPath, `\`)+1:]
	if manualWindowsSplit != wantOnWindows {
		panic(fmt.Sprintf("manual backslash split = %q, want %q", manualWindowsSplit, wantOnWindows))
	}

	// The trap in one sentence: code that imports "path" for filesystem paths
	// "because it compiled and the tests passed on my Mac" will silently
	// return whole-string garbage like the above the day it runs on Windows -
	// "path/filepath" is written to get manualWindowsSplit's answer there
	// instead, because it is compiled per-target-OS. Never use "path" for
	// anything that touches a real filesystem; reserve it for URL paths.
	fmt.Printf("GOOS=%s: filepath.Base(winPath)=%q path.Base(winPath)=%q (both wrong here)\n", runtime.GOOS, filepathBase, pathBase)
	fmt.Printf("what filepath.Base WOULD return if GOOS were windows: %q\n", manualWindowsSplit)

	fmt.Println("OK")
}
