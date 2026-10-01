/*
LEVEL 06 (advanced) - MEASURED: os.ReadFile vs a manual small-buffer read loop

You will learn
  - os.ReadFile pre-sizes its buffer using Stat and reads in one or two syscalls
  - a naive loop with a small fixed buffer makes many more Read syscalls for the
    same data, and that cost is measurable, not theoretical
  - how to time real code with time.Now()/time.Since() and report real numbers
  - the discipline of reporting what THIS run measured, not an assumed answer

Run: go run ./GoStdLib/01_os/level_06_measured_readfile_vs_open
*/

package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// readSmallBuffer reads a whole file using a deliberately tiny 64-byte buffer,
// forcing many Read syscalls - the pattern you get if you copy a loop skeleton
// without thinking about buffer size.
func readSmallBuffer(path string) ([]byte, int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, err
	}
	defer f.Close()

	var out bytes.Buffer
	buf := make([]byte, 64)
	calls := 0
	for {
		n, err := f.Read(buf)
		calls++
		if n > 0 {
			out.Write(buf[:n])
		}
		if err != nil {
			break
		}
	}
	return out.Bytes(), calls, nil
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-os-06-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "payload.bin")
	const size = 4 << 20 // 4 MiB, big enough to make the difference measurable
	payload := bytes.Repeat([]byte("gostdlib-benchmark-payload-"), size/27+1)
	payload = payload[:size]
	if err := os.WriteFile(path, payload, 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	const rounds = 20

	start := time.Now()
	var lastReadFile []byte
	for i := 0; i < rounds; i++ {
		lastReadFile, err = os.ReadFile(path)
		if err != nil {
			panic(fmt.Sprintf("ReadFile failed: %v", err))
		}
	}
	readFileElapsed := time.Since(start)

	start = time.Now()
	var lastSmall []byte
	var lastCalls int
	for i := 0; i < rounds; i++ {
		lastSmall, lastCalls, err = readSmallBuffer(path)
		if err != nil {
			panic(fmt.Sprintf("readSmallBuffer failed: %v", err))
		}
	}
	smallElapsed := time.Since(start)

	if !bytes.Equal(lastReadFile, payload) {
		panic("os.ReadFile did not return the expected payload")
	}
	if !bytes.Equal(lastSmall, payload) {
		panic("small-buffer loop did not return the expected payload")
	}

	expectedMinCalls := size/64 + 1 // at least one Read per 64-byte chunk
	if lastCalls < expectedMinCalls {
		panic(fmt.Sprintf("expected at least %d Read calls with a 64-byte buffer, got %d", expectedMinCalls, lastCalls))
	}

	fmt.Printf("os.ReadFile:        %v for %d rounds (%v/round)\n", readFileElapsed, rounds, readFileElapsed/rounds)
	fmt.Printf("64-byte read loop:  %v for %d rounds (%v/round), %d Read() syscalls in the last round\n",
		smallElapsed, rounds, smallElapsed/rounds, lastCalls)

	if smallElapsed <= readFileElapsed {
		// Report honestly even if the "obvious" answer didn't win this run.
		fmt.Println("NOTE: this run did not show the small-buffer loop as slower; " +
			"syscall cost varies by OS/filesystem cache state, but the syscall COUNT above is still real and always larger.")
	} else {
		fmt.Printf("small-buffer loop was %.1fx slower than os.ReadFile in this run\n",
			float64(smallElapsed)/float64(readFileElapsed))
	}

	fmt.Println("OK")
}
