/*
LEVEL 09 (advanced) - correctness trap: an already-open file survives a Rename

You will learn
  - os.Rename over an existing path is how atomic "swap in a new version" works
    (write to a temp file, then Rename it onto the real path)
  - the trap: a file descriptor opened BEFORE the rename keeps reading the OLD
    content forever - on Unix, rename only repoints the directory entry, it does
    not touch already-open file descriptors, which still reference the old inode
  - the fix: re-open the path (or compare ModTime/size via Stat) instead of
    holding a long-lived handle across an expected update

Run: go run ./GoStdLib/01_os/level_09_stale_handle_after_rename
*/

package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-os-09-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	configPath := filepath.Join(dir, "config.json")
	if err := os.WriteFile(configPath, []byte(`{"version":1}`), 0644); err != nil {
		panic(fmt.Sprintf("initial WriteFile failed: %v", err))
	}

	// Simulate a long-lived service that opened the config once at startup
	// and kept the handle around "for performance".
	longLivedHandle, err := os.Open(configPath)
	if err != nil {
		panic(fmt.Sprintf("Open failed: %v", err))
	}
	defer longLivedHandle.Close()

	firstRead, err := io.ReadAll(longLivedHandle)
	if err != nil {
		panic(fmt.Sprintf("first ReadAll failed: %v", err))
	}
	if string(firstRead) != `{"version":1}` {
		panic(fmt.Sprintf("unexpected initial content: %q", firstRead))
	}

	// Somewhere else in the system: an atomic config update via temp+rename,
	// the textbook-correct way to publish a new file version.
	tmpPath := configPath + ".tmp"
	if err := os.WriteFile(tmpPath, []byte(`{"version":2}`), 0644); err != nil {
		panic(fmt.Sprintf("temp WriteFile failed: %v", err))
	}
	if err := os.Rename(tmpPath, configPath); err != nil {
		panic(fmt.Sprintf("Rename failed: %v", err))
	}

	// THE TRAP: seeking back to 0 and reading again on the SAME handle still
	// returns the OLD content. The rename repointed the directory entry, but
	// this fd still refers to the original (now unlinked-from-that-path) inode.
	if _, err := longLivedHandle.Seek(0, io.SeekStart); err != nil {
		panic(fmt.Sprintf("Seek failed: %v", err))
	}
	staleRead, err := io.ReadAll(longLivedHandle)
	if err != nil {
		panic(fmt.Sprintf("stale ReadAll failed: %v", err))
	}
	if string(staleRead) != `{"version":1}` {
		panic(fmt.Sprintf("expected the stale handle to still read the OLD content %q, got %q",
			`{"version":1}`, staleRead))
	}

	// THE FIX: re-open the path to get a handle to the current inode.
	freshHandle, err := os.Open(configPath)
	if err != nil {
		panic(fmt.Sprintf("re-open failed: %v", err))
	}
	defer freshHandle.Close()
	freshRead, err := io.ReadAll(freshHandle)
	if err != nil {
		panic(fmt.Sprintf("fresh ReadAll failed: %v", err))
	}
	if string(freshRead) != `{"version":2}` {
		panic(fmt.Sprintf("expected the fresh handle to read the NEW content %q, got %q",
			`{"version":2}`, freshRead))
	}

	fmt.Printf("stale (pre-rename) handle still reads: %s\n", staleRead)
	fmt.Printf("freshly opened handle reads:            %s\n", freshRead)
	fmt.Println("OK")
}
