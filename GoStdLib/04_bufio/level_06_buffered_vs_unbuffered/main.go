/*
LEVEL 06 (advanced) - MEASURED: unbuffered vs bufio.Writer over many small writes

You will learn
  - every unbuffered os.File.Write is (at minimum) one syscall
  - bufio.Writer batches many small writes into far fewer syscalls
  - how to time real code with time.Now()/time.Since() and report real numbers,
    honestly, even if the gap is smaller or larger than expected

Run: go run ./GoStdLib/04_bufio/level_06_buffered_vs_unbuffered
*/

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-bufio-06-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	const chunk = "the quick brown fox jumps over the lazy dog\n" // 45 bytes
	const writes = 200_000

	// --- Unbuffered: one os.File.Write (one syscall) per chunk. ---
	unbufPath := filepath.Join(dir, "unbuffered.txt")
	uf, err := os.Create(unbufPath)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	start := time.Now()
	for i := 0; i < writes; i++ {
		if _, err := uf.WriteString(chunk); err != nil {
			panic(fmt.Sprintf("unbuffered WriteString failed: %v", err))
		}
	}
	unbufElapsed := time.Since(start)
	if err := uf.Close(); err != nil {
		panic(fmt.Sprintf("unbuffered Close failed: %v", err))
	}

	// --- Buffered: bufio.Writer batches into far fewer real Write syscalls. ---
	bufPath := filepath.Join(dir, "buffered.txt")
	bf, err := os.Create(bufPath)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	w := bufio.NewWriter(bf)
	start = time.Now()
	for i := 0; i < writes; i++ {
		if _, err := w.WriteString(chunk); err != nil {
			panic(fmt.Sprintf("buffered WriteString failed: %v", err))
		}
	}
	if err := w.Flush(); err != nil {
		panic(fmt.Sprintf("Flush failed: %v", err))
	}
	bufElapsed := time.Since(start)
	if err := bf.Close(); err != nil {
		panic(fmt.Sprintf("buffered Close failed: %v", err))
	}

	// Both files must contain identical, complete content - performance
	// differences must never come at the cost of correctness.
	unbufInfo, err := os.Stat(unbufPath)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	bufInfo, err := os.Stat(bufPath)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	expectedSize := int64(len(chunk) * writes)
	if unbufInfo.Size() != expectedSize {
		panic(fmt.Sprintf("unbuffered file size = %d, expected %d", unbufInfo.Size(), expectedSize))
	}
	if bufInfo.Size() != expectedSize {
		panic(fmt.Sprintf("buffered file size = %d, expected %d", bufInfo.Size(), expectedSize))
	}

	fmt.Printf("unbuffered: %v for %d writes (%v/write)\n", unbufElapsed, writes, unbufElapsed/writes)
	fmt.Printf("buffered:   %v for %d writes (%v/write)\n", bufElapsed, writes, bufElapsed/writes)

	if unbufElapsed <= bufElapsed {
		fmt.Println("NOTE: this run did not show buffered as faster; OS page cache can absorb small " +
			"unbuffered writes cheaply, but bufio.Writer still issues far fewer syscalls in principle.")
	} else {
		fmt.Printf("buffered was %.1fx faster than unbuffered in this run\n",
			float64(unbufElapsed)/float64(bufElapsed))
	}

	fmt.Println("OK")
}
