/*
LEVEL 05 (intermediate) - Mkdir vs MkdirAll, Remove vs RemoveAll

You will learn
  - os.Mkdir fails if the parent directory doesn't exist yet
  - os.MkdirAll creates every missing parent, and does not error if the leaf already exists
  - os.Remove fails on a non-empty directory
  - os.RemoveAll recurses through a whole tree and tolerates an already-missing path

Run: go run ./GoStdLib/01_os/level_05_mkdir_tree_and_remove
*/

package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

func main() {
	root, err := os.MkdirTemp("", "gostdlib-os-05-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(root)

	deep := filepath.Join(root, "a", "b", "c")

	// os.Mkdir requires the parent ("a/b") to already exist - it does not here.
	if err := os.Mkdir(deep, 0755); err == nil {
		panic("expected Mkdir to fail when parent directories are missing")
	} else if !errors.Is(err, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected a not-exist error from Mkdir, got %v", err))
	}

	// os.MkdirAll creates every missing directory along the path.
	if err := os.MkdirAll(deep, 0755); err != nil {
		panic(fmt.Sprintf("MkdirAll failed: %v", err))
	}
	if info, err := os.Stat(deep); err != nil || !info.IsDir() {
		panic(fmt.Sprintf("expected %q to exist as a directory, err=%v", deep, err))
	}

	// MkdirAll on an already-existing directory is a no-op, not an error.
	if err := os.MkdirAll(deep, 0755); err != nil {
		panic(fmt.Sprintf("MkdirAll on existing dir should succeed, got %v", err))
	}

	// Put a file inside "a/b" so it's non-empty.
	file := filepath.Join(root, "a", "b", "note.txt")
	if err := os.WriteFile(file, []byte("x"), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}
	nonEmptyDir := filepath.Join(root, "a", "b")

	// os.Remove refuses a non-empty directory.
	if err := os.Remove(nonEmptyDir); err == nil {
		panic("expected Remove to fail on a non-empty directory")
	}

	// os.RemoveAll recurses through the whole subtree.
	if err := os.RemoveAll(nonEmptyDir); err != nil {
		panic(fmt.Sprintf("RemoveAll failed: %v", err))
	}
	if _, err := os.Stat(nonEmptyDir); !errors.Is(err, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected %q to be gone after RemoveAll", nonEmptyDir))
	}

	// RemoveAll on an already-missing path is not an error (Remove would be).
	if err := os.RemoveAll(nonEmptyDir); err != nil {
		panic(fmt.Sprintf("RemoveAll on missing path should succeed, got %v", err))
	}
	if err := os.Remove(nonEmptyDir); !errors.Is(err, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected Remove on missing path to report not-exist, got %v", err))
	}

	fmt.Println("MkdirAll built a/b/c in one call; RemoveAll tore a/b back down")
	fmt.Println("OK")
}
