/*
LEVEL 01 (basic) - os.WriteFile and os.ReadFile: the whole-file shortcuts

You will learn
  - os.WriteFile writes a []byte to a path in one call, creating it if needed
  - os.ReadFile reads a whole file into memory in one call
  - both take/return a permission mode (WriteFile) and are the Go 1.16+
    replacement for the old ioutil.WriteFile/ReadFile pair

Run: go run ./GoStdLib/01_os/level_01_read_write_file
*/

package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	// Never write into the repo tree: use a throwaway temp directory.
	dir, err := os.MkdirTemp("", "gostdlib-os-01-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "greeting.txt")
	want := []byte("hello, os package\n")

	// The single most common use of os: write a file, then read it back.
	if err := os.WriteFile(path, want, 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	got, err := os.ReadFile(path)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}

	if !bytes.Equal(got, want) {
		panic(fmt.Sprintf("round trip mismatch: got %q, want %q", got, want))
	}

	// Writing again with different content overwrites (truncates) the file.
	overwrite := []byte("shorter\n")
	if err := os.WriteFile(path, overwrite, 0644); err != nil {
		panic(fmt.Sprintf("overwrite WriteFile failed: %v", err))
	}
	got2, err := os.ReadFile(path)
	if err != nil {
		panic(fmt.Sprintf("ReadFile after overwrite failed: %v", err))
	}
	if !bytes.Equal(got2, overwrite) {
		panic(fmt.Sprintf("overwrite mismatch: got %q, want %q", got2, overwrite))
	}
	if len(got2) >= len(want) {
		panic(fmt.Sprintf("expected overwrite to truncate: new len %d, old len %d", len(got2), len(want)))
	}

	fmt.Printf("wrote+read %d bytes, then overwrote with %d bytes\n", len(want), len(overwrite))
	fmt.Println("OK")
}
