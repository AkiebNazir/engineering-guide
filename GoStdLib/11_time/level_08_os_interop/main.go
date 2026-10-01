/*
LEVEL 08 (interop) - time.Time from os.Stat: checking file freshness

You will learn
  - os.FileInfo.ModTime() returns a real time.Time - the filesystem's
    modification timestamp, usable with every time.Time method
  - combining it with time.Since gives "how long ago was this touched"
  - combining it with Before/After lets you pick the freshest of several
    files without any string parsing of timestamps

Run: go run ./GoStdLib/11_time/level_08_os_interop
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-time-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	older := filepath.Join(dir, "older.txt")
	newer := filepath.Join(dir, "newer.txt")

	if err := os.WriteFile(older, []byte("first"), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile(older) failed: %v", err))
	}
	// A real, if small, gap between modification times - filesystem
	// timestamp resolution on some systems is coarser than a nanosecond.
	time.Sleep(20 * time.Millisecond)
	if err := os.WriteFile(newer, []byte("second"), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile(newer) failed: %v", err))
	}

	olderInfo, err := os.Stat(older)
	if err != nil {
		panic(fmt.Sprintf("Stat(older) failed: %v", err))
	}
	newerInfo, err := os.Stat(newer)
	if err != nil {
		panic(fmt.Sprintf("Stat(newer) failed: %v", err))
	}

	if !newerInfo.ModTime().After(olderInfo.ModTime()) {
		panic(fmt.Sprintf("expected newer.ModTime() after older.ModTime(): newer=%v older=%v", newerInfo.ModTime(), olderInfo.ModTime()))
	}

	age := time.Since(newerInfo.ModTime())
	if age < 0 {
		panic(fmt.Sprintf("a file's age cannot be negative, got %v", age))
	}
	if age > time.Minute {
		panic(fmt.Sprintf("file was just written, age should be well under a minute, got %v", age))
	}

	// Pick the freshest of several files purely with time.Time comparisons.
	candidates := []struct {
		path string
		mod  time.Time
	}{
		{older, olderInfo.ModTime()},
		{newer, newerInfo.ModTime()},
	}
	freshest := candidates[0]
	for _, c := range candidates[1:] {
		if c.mod.After(freshest.mod) {
			freshest = c
		}
	}
	if freshest.path != newer {
		panic(fmt.Sprintf("freshest file should be %q, got %q", newer, freshest.path))
	}

	fmt.Printf("older mod=%v  newer mod=%v  newer age=%v\n", olderInfo.ModTime(), newerInfo.ModTime(), age)
	fmt.Printf("freshest file: %s\n", filepath.Base(freshest.path))
	fmt.Println("OK")
}
