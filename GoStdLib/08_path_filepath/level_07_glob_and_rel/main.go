/*
LEVEL 07 (advanced) - a second core pattern: Glob pattern matching and Rel

You will learn
  - filepath.Glob finds files matching a shell-style pattern against the real
    filesystem (Match works on names, Glob actually looks on disk)
  - filepath.Rel computes the relative path needed to get from a base
    directory to a target - the inverse operation of Join

Run: go run ./GoStdLib/08_path_filepath/level_07_glob_and_rel
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-filepath-07-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	names := []string{"a.log", "b.log", "c.txt", "notes.md"}
	for _, n := range names {
		if err := os.WriteFile(filepath.Join(dir, n), []byte("x"), 0644); err != nil {
			panic(fmt.Sprintf("WriteFile(%q) failed: %v", n, err))
		}
	}

	// Glob matches against the real filesystem, so results come back as full paths.
	matches, err := filepath.Glob(filepath.Join(dir, "*.log"))
	if err != nil {
		panic(fmt.Sprintf("Glob failed: %v", err))
	}
	sort.Strings(matches)
	if len(matches) != 2 {
		panic(fmt.Sprintf("Glob(*.log) found %d matches, want 2: %v", len(matches), matches))
	}
	for i, want := range []string{"a.log", "b.log"} {
		if filepath.Base(matches[i]) != want {
			panic(fmt.Sprintf("match %d base = %q, want %q", i, filepath.Base(matches[i]), want))
		}
	}

	// Rel computes the path FROM a base TO a target - here, relative to dir itself.
	rel, err := filepath.Rel(dir, matches[0])
	if err != nil {
		panic(fmt.Sprintf("Rel failed: %v", err))
	}
	if rel != "a.log" {
		panic(fmt.Sprintf("Rel(dir, a.log) = %q, want %q", rel, "a.log"))
	}

	// Rel between two sibling subdirectories walks up and back down with "..".
	sub1 := filepath.Join(dir, "reports", "2026")
	sub2 := filepath.Join(dir, "archive")
	if err := os.MkdirAll(sub1, 0755); err != nil {
		panic(fmt.Sprintf("MkdirAll failed: %v", err))
	}
	relBetween, err := filepath.Rel(sub1, sub2)
	if err != nil {
		panic(fmt.Sprintf("Rel(sub1, sub2) failed: %v", err))
	}
	wantRel := filepath.Join("..", "..", "archive")
	if relBetween != wantRel {
		panic(fmt.Sprintf("Rel(sub1, sub2) = %q, want %q", relBetween, wantRel))
	}

	// Rel is the inverse of Join: Join(base, Rel(base, target)) == Clean(target).
	rejoined := filepath.Join(sub1, relBetween)
	if rejoined != filepath.Clean(sub2) {
		panic(fmt.Sprintf("Join(sub1, Rel(sub1, sub2)) = %q, want %q", rejoined, filepath.Clean(sub2)))
	}

	fmt.Printf("Glob found %d *.log files; Rel(sub1, sub2) = %q\n", len(matches), relBetween)
	fmt.Println("OK")
}
