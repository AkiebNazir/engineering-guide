/*
LEVEL 08 (advanced) - errors + fmt interop: multiple %w verbs in one Errorf (Go 1.20+)

You will learn
  - since Go 1.20, fmt.Errorf accepts MORE THAN ONE %w verb in a single call,
    producing one error that wraps several children at once
  - such an error implements Unwrap() []error (the same shape errors.Join
    produces), so errors.Is/As check every child, not just one
  - this is the direct fmt-package counterpart to errors.Join from level 5 -
    same result, different spelling, useful when you already have a format
    string and don't want a separate Join call

Run: go run ./GoStdLib/13_errors/level_08_fmt_multi_verb_wrap
*/

package main

import (
	"errors"
	"fmt"
)

var (
	ErrTimeout    = errors.New("upstream timeout")
	ErrRateLimit  = errors.New("rate limit exceeded")
	ErrCacheStale = errors.New("cache entry stale")
)

// fetchWithFallback simulates a call where two independent problems were
// both true at once: the upstream timed out AND the cache we'd fall back to
// was stale. Neither one alone tells the full story.
func fetchWithFallback() error {
	// A single fmt.Errorf call, two %w verbs: both errors become children of
	// the returned error's Unwrap() []error.
	return fmt.Errorf("fetch failed: %w; fallback failed: %w", ErrTimeout, ErrCacheStale)
}

func main() {
	err := fetchWithFallback()
	if err == nil {
		panic("fetchWithFallback returned nil, want a multi-wrapped error")
	}

	wantMsg := "fetch failed: upstream timeout; fallback failed: cache entry stale"
	if err.Error() != wantMsg {
		panic(fmt.Sprintf("err.Error() = %q, want %q", err.Error(), wantMsg))
	}

	// Both wrapped sentinels are independently visible to errors.Is.
	if !errors.Is(err, ErrTimeout) {
		panic("errors.Is(err, ErrTimeout) = false, want true")
	}
	if !errors.Is(err, ErrCacheStale) {
		panic("errors.Is(err, ErrCacheStale) = false, want true")
	}
	// A sentinel that was never part of this call is correctly absent.
	if errors.Is(err, ErrRateLimit) {
		panic("errors.Is(err, ErrRateLimit) = true, want false")
	}

	// Confirm the shape is really Unwrap() []error, same as errors.Join
	// from level 5, not a single-child chain.
	type multiUnwrapper interface{ Unwrap() []error }
	mu, ok := err.(multiUnwrapper)
	if !ok {
		panic("multi-%w error does not implement Unwrap() []error")
	}
	children := mu.Unwrap()
	if len(children) != 2 {
		panic(fmt.Sprintf("len(children) = %d, want 2", len(children)))
	}
	if children[0] != ErrTimeout || children[1] != ErrCacheStale {
		panic(fmt.Sprintf("children = %v, want [ErrTimeout ErrCacheStale] in call order", children))
	}

	// A single-%w Errorf, for contrast, still produces a plain single-child
	// chain (Unwrap() error, not Unwrap() []error).
	single := fmt.Errorf("single: %w", ErrTimeout)
	if _, ok := single.(multiUnwrapper); ok {
		panic("single-%w error unexpectedly implements Unwrap() []error")
	}
	if errors.Unwrap(single) != ErrTimeout {
		panic("single-%w error did not unwrap to ErrTimeout")
	}

	fmt.Printf("multi-wrapped: %v\n", err)
	fmt.Println("OK")
}
