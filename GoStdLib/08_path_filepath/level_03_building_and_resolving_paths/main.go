/*
LEVEL 03 (core) - combining basics: resolve a set of relative inputs to absolute paths

You will learn
  - filepath.Abs joins a relative path onto the current working directory and
    Cleans the result - it's Join(Getwd(), path) plus normalization in one call
  - a realistic idiom: take user-supplied relative paths, filter by extension,
    and resolve each to an absolute path for logging/opening

Run: go run ./GoStdLib/08_path_filepath/level_03_building_and_resolving_paths
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-filepath-03-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	if err := os.Chdir(dir); err != nil {
		panic(fmt.Sprintf("Chdir failed: %v", err))
	}

	inputs := []string{
		"report.csv",
		"notes.txt",
		"./data/../report.csv", // messy but resolves to the same file as the first
		"archive.tar.gz",
	}

	var csvFiles []string
	for _, in := range inputs {
		if filepath.Ext(in) != ".csv" {
			continue
		}
		abs, err := filepath.Abs(in)
		if err != nil {
			panic(fmt.Sprintf("Abs(%q) failed: %v", in, err))
		}
		csvFiles = append(csvFiles, abs)
	}

	if len(csvFiles) != 2 {
		panic(fmt.Sprintf("found %d .csv inputs, want 2: %v", len(csvFiles), csvFiles))
	}
	// The plain path and the messy "./data/../" path must resolve to the SAME
	// absolute, cleaned path - that's exactly what Abs is for.
	if csvFiles[0] != csvFiles[1] {
		panic(fmt.Sprintf("expected both .csv resolutions to match: %q != %q", csvFiles[0], csvFiles[1]))
	}

	wantDir, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd failed: %v", err))
	}
	wantAbs := filepath.Join(wantDir, "report.csv")
	if csvFiles[0] != wantAbs {
		panic(fmt.Sprintf("resolved path = %q, want %q", csvFiles[0], wantAbs))
	}

	// Abs is idempotent: resolving an already-absolute path returns it Cleaned, unchanged in meaning.
	twiceAbs, err := filepath.Abs(csvFiles[0])
	if err != nil {
		panic(fmt.Sprintf("Abs on an absolute path failed: %v", err))
	}
	if twiceAbs != csvFiles[0] {
		panic(fmt.Sprintf("Abs(Abs(p)) = %q, want %q", twiceAbs, csvFiles[0]))
	}

	fmt.Printf("resolved %d .csv path(s), both pointing at %q\n", len(csvFiles), csvFiles[0])
	fmt.Println("OK")
}
