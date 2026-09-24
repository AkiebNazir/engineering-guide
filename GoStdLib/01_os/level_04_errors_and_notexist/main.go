/*
LEVEL 04 (core) - real os errors: *PathError and errors.Is(err, fs.ErrNotExist)

You will learn
  - os functions return a *fs.PathError (alias os.PathError) wrapping a plain error
  - the idiomatic check is errors.Is(err, fs.ErrNotExist), not string matching
  - the same idiom (errors.Is with fs.ErrExist / fs.ErrPermission) covers other cases
  - a *PathError carries Op/Path/Err, useful for logging without string parsing

Run: go run ./GoStdLib/01_os/level_04_errors_and_notexist
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
	dir, err := os.MkdirTemp("", "gostdlib-os-04-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	missing := filepath.Join(dir, "does-not-exist.txt")

	// Trigger a real not-exist error, don't just describe it.
	_, statErr := os.Stat(missing)
	if statErr == nil {
		panic("expected Stat on a missing file to fail")
	}
	if !errors.Is(statErr, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected errors.Is(err, fs.ErrNotExist) to be true, got err=%v", statErr))
	}

	// Confirm the concrete type is *fs.PathError and inspect its fields.
	var pathErr *fs.PathError
	if !errors.As(statErr, &pathErr) {
		panic(fmt.Sprintf("expected *fs.PathError, got %T", statErr))
	}
	if pathErr.Op != "stat" {
		panic(fmt.Sprintf("expected Op %q, got %q", "stat", pathErr.Op))
	}
	if pathErr.Path != missing {
		panic(fmt.Sprintf("expected Path %q, got %q", missing, pathErr.Path))
	}

	// Same idiom on os.Open.
	_, openErr := os.Open(missing)
	if !errors.Is(openErr, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected Open's error to satisfy fs.ErrNotExist, got %v", openErr))
	}

	// The mirror case: creating something that already exists.
	existing := filepath.Join(dir, "already-here.txt")
	if err := os.WriteFile(existing, []byte("x"), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}
	_, createErr := os.OpenFile(existing, os.O_CREATE|os.O_EXCL, 0644)
	if createErr == nil {
		panic("expected O_CREATE|O_EXCL on an existing file to fail")
	}
	if !errors.Is(createErr, fs.ErrExist) {
		panic(fmt.Sprintf("expected errors.Is(err, fs.ErrExist) to be true, got err=%v", createErr))
	}

	fmt.Printf("Stat error: %v\n", statErr)
	fmt.Printf("classified via errors.Is: not-exist=%v exist=%v\n",
		errors.Is(statErr, fs.ErrNotExist), errors.Is(createErr, fs.ErrExist))
	fmt.Println("OK")
}
