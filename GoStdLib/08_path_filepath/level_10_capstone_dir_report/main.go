/*
LEVEL 10 (capstone) - a small directory report using most of levels 1-9 together

You will learn
  - how Join, WalkDir + fs.SkipDir, Ext, Rel and Glob combine into one
    realistic small program: walk a tree, skip a subtree, group files by
    extension, and report paths relative to the tree root

Run: go run ./GoStdLib/08_path_filepath/level_10_capstone_dir_report
*/

package main

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
)

// report walks root, skipping any directory literally named "skip", and
// returns relative paths grouped by extension.
func report(root string) (map[string][]string, error) {
	byExt := make(map[string][]string)
	err := filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if d.Name() == "skip" {
				return fs.SkipDir
			}
			return nil
		}
		rel, err := filepath.Rel(root, p)
		if err != nil {
			return err
		}
		ext := filepath.Ext(p)
		byExt[ext] = append(byExt[ext], filepath.ToSlash(rel))
		return nil
	})
	return byExt, err
}

func main() {
	root, err := os.MkdirTemp("", "gostdlib-filepath-10-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(root)

	tree := []string{
		"main.go", "util.go", "README.md",
		"skip/vendored.go", // must be excluded by fs.SkipDir
		"cmd/app/main.go",
	}
	for _, rel := range tree {
		full := filepath.Join(root, rel)
		if err := os.MkdirAll(filepath.Dir(full), 0755); err != nil {
			panic(fmt.Sprintf("MkdirAll failed: %v", err))
		}
		if err := os.WriteFile(full, []byte("x"), 0644); err != nil {
			panic(fmt.Sprintf("WriteFile(%q) failed: %v", rel, err))
		}
	}

	byExt, err := report(root)
	if err != nil {
		panic(fmt.Sprintf("report failed: %v", err))
	}

	goFiles := byExt[".go"]
	sort.Strings(goFiles)
	wantGo := []string{"cmd/app/main.go", "main.go", "util.go"}
	if len(goFiles) != len(wantGo) {
		panic(fmt.Sprintf("found %d .go files, want %d: %v", len(goFiles), len(wantGo), goFiles))
	}
	for i := range wantGo {
		if goFiles[i] != wantGo[i] {
			panic(fmt.Sprintf(".go[%d] = %q, want %q", i, goFiles[i], wantGo[i]))
		}
	}
	if len(byExt[".md"]) != 1 || byExt[".md"][0] != "README.md" {
		panic(fmt.Sprintf(".md files = %v, want [README.md]", byExt[".md"]))
	}

	// Cross-check with Glob: matching *.go directly under root should find
	// exactly main.go and util.go (Glob is not recursive, unlike WalkDir).
	matches, err := filepath.Glob(filepath.Join(root, "*.go"))
	if err != nil {
		panic(fmt.Sprintf("Glob failed: %v", err))
	}
	if len(matches) != 2 {
		panic(fmt.Sprintf("Glob(root/*.go) found %d, want 2 (non-recursive): %v", len(matches), matches))
	}

	for _, rels := range byExt {
		for _, r := range rels {
			if r == "skip/vendored.go" {
				panic("skip/ subtree should have been pruned by fs.SkipDir")
			}
		}
	}

	fmt.Printf(".go files (%d): %v\n", len(goFiles), goFiles)
	fmt.Printf(".md files (%d): %v\n", len(byExt[".md"]), byExt[".md"])
	fmt.Printf("Glob (non-recursive) found %d top-level .go files\n", len(matches))
	fmt.Println("OK")
}
