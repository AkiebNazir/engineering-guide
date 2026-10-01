/*
LEVEL 06 (advanced) - MEASURED: repeated filepath.Abs vs caching the working directory

You will learn
  - filepath.Abs calls os.Getwd() internally every time the input is relative
  - os.Getwd is a real syscall on most platforms (or at least far from free) -
    calling Abs in a hot loop repeats that cost for every single path
  - this level actually times both approaches on THIS run and prints real
    numbers - never assert a performance claim without measuring it

Run: go run ./GoStdLib/08_path_filepath/level_06_measured_abs_vs_cached
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const iterations = 50_000

func main() {
	names := make([]string, iterations)
	for i := range names {
		names[i] = fmt.Sprintf("file-%d.txt", i)
	}

	// --- approach 1: filepath.Abs per path, each call pays for Getwd. ---
	start := time.Now()
	absResults1 := make([]string, iterations)
	for i, name := range names {
		abs, err := filepath.Abs(name)
		if err != nil {
			panic(fmt.Sprintf("Abs(%q) failed: %v", name, err))
		}
		absResults1[i] = abs
	}
	absLoopDur := time.Since(start)

	// --- approach 2: call Getwd ONCE, then Join+Clean per path. ---
	start = time.Now()
	wd, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd failed: %v", err))
	}
	absResults2 := make([]string, iterations)
	for i, name := range names {
		absResults2[i] = filepath.Join(wd, name)
	}
	cachedDur := time.Since(start)

	// Correctness first: both approaches must produce identical results.
	for i := range names {
		if absResults1[i] != absResults2[i] {
			panic(fmt.Sprintf("mismatch at %d: Abs=%q cached=%q", i, absResults1[i], absResults2[i]))
		}
	}

	fmt.Printf("iterations=%d\n", iterations)
	fmt.Printf("filepath.Abs per call:        %v (%v/iter)\n", absLoopDur, absLoopDur/iterations)
	fmt.Printf("Getwd once + Join per call:   %v (%v/iter)\n", cachedDur, cachedDur/iterations)

	if cachedDur < absLoopDur {
		speedup := float64(absLoopDur) / float64(cachedDur)
		fmt.Printf("measured: caching Getwd was %.1fx faster on this run\n", speedup)
	} else {
		// Report honestly even if this run didn't show the expected direction.
		fmt.Println("measured: caching Getwd was NOT faster on this run - reporting the real numbers above as-is")
	}

	fmt.Println("OK")
}
