/*
LEVEL 06 (advanced) - MEASURED: compiling once vs. recompiling every loop iteration

You will learn
  - MustCompile does real work: parsing the pattern and building a state
    machine - paying that cost every iteration of a loop is pure waste
  - this level runs the SAME match, iterations times, once with the pattern
    compiled ONCE outside the loop and once recompiled INSIDE the loop, and
    times both with time.Now()/time.Since() - real numbers from this run

Run: go run ./GoStdLib/14_regexp/level_06_measured_compile_once_vs_loop
*/

package main

import (
	"fmt"
	"regexp"
	"time"
)

const pattern = `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
const sample = "user.name+tag@example.co.uk"
const iterations = 20_000

func main() {
	// Compiled once, reused for every iteration - the idiomatic approach.
	reOnce := regexp.MustCompile(pattern)
	startOnce := time.Now()
	for i := 0; i < iterations; i++ {
		if !reOnce.MatchString(sample) {
			panic("reOnce.MatchString returned false during timing loop, want true")
		}
	}
	durOnce := time.Since(startOnce)

	// Recompiled on every single iteration - the mistake this level exists
	// to make visible.
	startLoop := time.Now()
	for i := 0; i < iterations; i++ {
		re := regexp.MustCompile(pattern) // same pattern, but compiled INSIDE the loop
		if !re.MatchString(sample) {
			panic("recompiled re.MatchString returned false during timing loop, want true")
		}
	}
	durLoop := time.Since(startLoop)

	fmt.Printf("compiled once,   %d iterations: %v total, %v/op\n", iterations, durOnce, durOnce/iterations)
	fmt.Printf("recompiled each, %d iterations: %v total, %v/op\n", iterations, durLoop, durLoop/iterations)

	if durLoop < durOnce {
		panic(fmt.Sprintf("recompiling every iteration (%v) was faster than compiling once (%v); expected the opposite", durLoop, durOnce))
	}

	speedup := float64(durLoop) / float64(durOnce)
	fmt.Printf("compiling once was %.1fx faster in this run\n", speedup)
	fmt.Println("OK")
}
