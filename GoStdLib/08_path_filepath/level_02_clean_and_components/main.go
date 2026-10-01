/*
LEVEL 02 (core) - the core surface: Clean, Base, Dir, Ext

You will learn
  - Clean lexically normalizes a path: collapses "..", drops "." and doubled
    slashes, without touching the filesystem or resolving symlinks
  - Base returns the last path element, Dir everything before it
  - Ext returns the file extension including the leading dot

Run: go run ./GoStdLib/08_path_filepath/level_02_clean_and_components
*/

package main

import (
	"fmt"
	"path/filepath"
)

func main() {
	// Clean normalizes purely as string manipulation - no syscalls, so it
	// works even for paths that don't exist yet.
	cases := map[string]string{
		"a/./b":       "a/b",
		"a//b":        "a/b",
		"a/b/../c":    "a/c",
		"a/b/../../c": "c",
		"./a/b":       "a/b",
		"a/b/":        "a/b", // trailing slash removed
		"":            ".",
		"../a":        "../a", // leading ".." that escapes cannot be collapsed further
	}
	for in, want := range cases {
		got := filepath.ToSlash(filepath.Clean(in))
		if got != want {
			panic(fmt.Sprintf("Clean(%q) = %q, want %q", in, got, want))
		}
	}

	// Base: the last element of the path.
	if got := filepath.Base("/var/log/app/current.log"); got != "current.log" {
		panic(fmt.Sprintf("Base = %q, want %q", got, "current.log"))
	}
	// Base of a path ending in a separator is the last real element.
	if got := filepath.ToSlash(filepath.Base("/var/log/app/")); got != "app" {
		panic(fmt.Sprintf("Base of trailing-slash path = %q, want %q", got, "app"))
	}

	// Dir: everything before the last element (itself Clean-ed).
	if got := filepath.ToSlash(filepath.Dir("/var/log/app/current.log")); got != "/var/log/app" {
		panic(fmt.Sprintf("Dir = %q, want %q", got, "/var/log/app"))
	}

	// Ext: the suffix starting at the final dot, or "" if there is none.
	if got := filepath.Ext("archive.tar.gz"); got != ".gz" {
		panic(fmt.Sprintf("Ext = %q, want %q", got, ".gz"))
	}
	if got := filepath.Ext("README"); got != "" {
		panic(fmt.Sprintf("Ext of extensionless file = %q, want empty", got))
	}

	// Base(Dir(p)) + "/" + Base(p) style decomposition round-trips via Join.
	full := filepath.Join("/srv", "data", "report.csv")
	rebuilt := filepath.Join(filepath.Dir(full), filepath.Base(full))
	if rebuilt != full {
		panic(fmt.Sprintf("Join(Dir, Base) = %q, want %q", rebuilt, full))
	}

	fmt.Println("Clean/Base/Dir/Ext verified across trailing slashes, '..', and multi-dot extensions")
	fmt.Println("OK")
}
