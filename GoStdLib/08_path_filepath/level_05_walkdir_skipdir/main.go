/*
LEVEL 05 (advanced) - filepath.WalkDir and fs.SkipDir

You will learn
  - WalkDir (Go 1.16+, preferred over the deprecated Walk) walks a directory
    tree depth-first, calling back with an fs.DirEntry per file/dir
  - fs.DirEntry gets its type from the directory read itself - no per-entry
    os.Lstat like the old Walk needed
  - returning fs.SkipDir from the callback when it's a directory prunes that
    whole subtree without aborting the rest of the walk

Run: go run ./GoStdLib/08_path_filepath/level_05_walkdir_skipdir
*/

package main

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-filepath-05-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	// Build a small tree:
	//   dir/
	//     app.go
	//     README.md
	//     vendor/            <- to be skipped entirely
	//       thirdparty.go
	//     internal/
	//       helper.go
	files := map[string]string{
		"app.go":               "package main\n",
		"README.md":            "# demo\n",
		"vendor/thirdparty.go": "package vendor\n",
		"internal/helper.go":   "package internal\n",
	}
	for rel, content := range files {
		full := filepath.Join(dir, rel)
		if err := os.MkdirAll(filepath.Dir(full), 0755); err != nil {
			panic(fmt.Sprintf("MkdirAll failed: %v", err))
		}
		if err := os.WriteFile(full, []byte(content), 0644); err != nil {
			panic(fmt.Sprintf("WriteFile(%q) failed: %v", rel, err))
		}
	}

	var visited []string
	err = filepath.WalkDir(dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err // a real error reading this entry - propagate it
		}
		rel, relErr := filepath.Rel(dir, path)
		if relErr != nil {
			return relErr
		}
		if rel == "." {
			return nil // the root itself
		}
		if d.IsDir() && d.Name() == "vendor" {
			return fs.SkipDir // prune: don't descend, and don't report vendor itself further
		}
		visited = append(visited, filepath.ToSlash(rel))
		return nil
	})
	if err != nil {
		panic(fmt.Sprintf("WalkDir failed: %v", err))
	}

	sort.Strings(visited)
	want := []string{"README.md", "app.go", "internal", "internal/helper.go"}
	if len(visited) != len(want) {
		panic(fmt.Sprintf("visited %d entries, want %d: %v", len(visited), len(want), visited))
	}
	for i := range want {
		if visited[i] != want[i] {
			panic(fmt.Sprintf("visited[%d] = %q, want %q (full list: %v)", i, visited[i], want[i], visited))
		}
	}
	for _, v := range visited {
		if v == "vendor" || v == "vendor/thirdparty.go" {
			panic(fmt.Sprintf("vendor subtree should have been pruned by fs.SkipDir, found %q", v))
		}
	}

	fmt.Printf("walked %d entries, vendor/ pruned via fs.SkipDir: %v\n", len(visited), visited)
	fmt.Println("OK")
}
