/*
LEVEL 07 (advanced) - design concern: caching compiled patterns that are only known at runtime

You will learn
  - level 6 assumed the pattern was a compile-time constant, so "compile
    once at package scope" was enough - but if the PATTERN ITSELF varies at
    runtime (one per user, one per config entry), there is no single
    package-level var to hoist it into
  - the right design is a small cache keyed by pattern string: compile once
    PER DISTINCT PATTERN, reuse the *Regexp for every later request that
    asks for that same pattern
  - this program is intentionally single-threaded (no concurrency primitives
    - see GoEngineering topics 26/31 for that), so a plain map is enough to
    demonstrate the caching design

Run: go run ./GoStdLib/14_regexp/level_07_pattern_cache
*/

package main

import (
	"fmt"
	"regexp"
)

// patternCache compiles each distinct pattern at most once and remembers it.
type patternCache struct {
	compiled map[string]*regexp.Regexp
	compiles int // how many ACTUAL Compile calls happened - proves the cache works
}

func newPatternCache() *patternCache {
	return &patternCache{compiled: make(map[string]*regexp.Regexp)}
}

func (c *patternCache) get(pattern string) (*regexp.Regexp, error) {
	if re, ok := c.compiled[pattern]; ok {
		return re, nil // cache hit: no compile work at all
	}
	re, err := regexp.Compile(pattern)
	if err != nil {
		return nil, err
	}
	c.compiled[pattern] = re
	c.compiles++
	return re, nil
}

func main() {
	cache := newPatternCache()

	// Simulate a stream of requests, each naming a pattern by string (as if
	// read from a config row or a user's saved search) - several REPEAT an
	// earlier pattern, several are new.
	requests := []struct {
		pattern, input string
		want           bool
	}{
		{`^\d+$`, "123", true},
		{`^[a-z]+$`, "abc", true},
		{`^\d+$`, "456", true},     // repeat of request 1's pattern
		{`^[a-z]+$`, "789", false}, // repeat of request 2's pattern, different input
		{`^\d+$`, "abc", false},    // repeat again
	}

	for i, r := range requests {
		re, err := cache.get(r.pattern)
		if err != nil {
			panic(fmt.Sprintf("request %d: cache.get(%q) failed: %v", i, r.pattern, err))
		}
		got := re.MatchString(r.input)
		if got != r.want {
			panic(fmt.Sprintf("request %d: pattern %q against %q = %v, want %v", i, r.pattern, r.input, got, r.want))
		}
	}

	// 5 requests named only 2 DISTINCT patterns -> exactly 2 real compiles.
	if cache.compiles != 2 {
		panic(fmt.Sprintf("cache performed %d real compiles, want 2 (one per distinct pattern)", cache.compiles))
	}
	if len(cache.compiled) != 2 {
		panic(fmt.Sprintf("cache holds %d entries, want 2", len(cache.compiled)))
	}

	// An unbounded cache is itself a design trade-off worth naming: if
	// patterns come from untrusted, unbounded input (e.g. raw user text
	// rather than a small fixed set of config rows), a cache without an
	// eviction/size limit is a memory-growth risk - out of scope to build
	// here, but worth knowing before shipping this pattern verbatim.
	fmt.Printf("served %d requests with %d real Compile calls\n", len(requests), cache.compiles)
	fmt.Println("OK")
}
