/*
LEVEL 06 (advanced) - MEASURED: errors.Is cost on a shallow vs. a deep wrap chain

You will learn
  - errors.Is is not O(1): it calls Unwrap repeatedly until it finds a
    match, so checking a sentinel buried under N layers of wrapping costs
    roughly N Unwrap calls
  - this level builds a 1-layer chain and a 200-layer chain around the SAME
    sentinel and times errors.Is against each, many iterations, with
    time.Now()/time.Since() - real numbers from this run, not a guess

Run: go run ./GoStdLib/13_errors/level_06_measured_is_shallow_vs_deep
*/

package main

import (
	"errors"
	"fmt"
	"time"
)

var ErrSentinel = errors.New("sentinel failure")

// wrapN wraps err in N layers of fmt.Errorf("...: %w", err).
func wrapN(err error, n int) error {
	for i := 0; i < n; i++ {
		err = fmt.Errorf("layer %d: %w", i, err)
	}
	return err
}

func timeIs(err error, iterations int) time.Duration {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		if !errors.Is(err, ErrSentinel) {
			panic("errors.Is returned false during timing loop, want true")
		}
	}
	return time.Since(start)
}

func main() {
	const deepLayers = 200
	const iterations = 200_000

	shallow := wrapN(ErrSentinel, 1)
	deep := wrapN(ErrSentinel, deepLayers)

	// Sanity: both chains actually contain the sentinel before timing them.
	if !errors.Is(shallow, ErrSentinel) {
		panic("shallow chain does not contain ErrSentinel")
	}
	if !errors.Is(deep, ErrSentinel) {
		panic("deep chain does not contain ErrSentinel")
	}

	// Warm up (first calls can include allocator/cache warmup noise).
	timeIs(shallow, 1000)
	timeIs(deep, 1000)

	shallowDur := timeIs(shallow, iterations)
	deepDur := timeIs(deep, iterations)

	shallowPerOp := shallowDur / iterations
	deepPerOp := deepDur / iterations

	fmt.Printf("shallow chain (1 layer):   %v total, %v/op\n", shallowDur, shallowPerOp)
	fmt.Printf("deep chain (%d layers): %v total, %v/op\n", deepLayers, deepDur, deepPerOp)

	// The real claim we can make from THIS run: walking 200 layers is not
	// faster than walking 1. We don't hardcode an exact ratio (that's
	// machine-dependent and flaky) - we only assert the direction, and
	// report the actual numbers above so a reader can see the real gap.
	if deepDur < shallowDur {
		panic(fmt.Sprintf("deep chain (%v) was faster than shallow chain (%v); expected deep >= shallow", deepDur, shallowDur))
	}

	fmt.Println("OK")
}
