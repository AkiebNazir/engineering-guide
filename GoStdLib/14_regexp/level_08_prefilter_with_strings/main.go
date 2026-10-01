/*
LEVEL 08 (advanced) - regexp + strings interop: a cheap pre-filter before an expensive match

You will learn
  - strings.Contains is a simple substring scan; a regexp match, even a
    "fast" RE2 one, does more work per byte (state machine transitions)
  - when most inputs can be rejected by a fast literal check, guard the
    regex behind it: only pay for the regex on inputs that could possibly
    match
  - this level MEASURES the combined pre-filter+regex approach against
    running the regex on every input unconditionally, over a batch that is
    mostly non-matching - real numbers from this run

Run: go run ./GoStdLib/14_regexp/level_08_prefilter_with_strings
*/

package main

import (
	"fmt"
	"regexp"
	"strings"
	"time"
)

// Real matches must contain "ERROR" - a cheap, mandatory literal substring
// the regex also requires. Any line without it can be rejected instantly.
var errorLineRe = regexp.MustCompile(`ERROR\s+code=(\d+)`)

func matchDirect(line string) (string, bool) {
	m := errorLineRe.FindStringSubmatch(line)
	if m == nil {
		return "", false
	}
	return m[1], true
}

func matchPrefiltered(line string) (string, bool) {
	if !strings.Contains(line, "ERROR") { // cheap literal scan first
		return "", false
	}
	m := errorLineRe.FindStringSubmatch(line)
	if m == nil {
		return "", false
	}
	return m[1], true
}

func main() {
	// A batch that's mostly non-matching lines, as a real log stream is.
	lines := make([]string, 0, 10_000)
	for i := 0; i < 10_000; i++ {
		if i%50 == 0 {
			lines = append(lines, fmt.Sprintf("INFO some ERROR code=%d happened", i))
		} else {
			lines = append(lines, fmt.Sprintf("INFO request %d handled ok in normal operation without any issues", i))
		}
	}

	// Correctness first: both approaches must agree on every line.
	matches := 0
	for _, line := range lines {
		codeDirect, okDirect := matchDirect(line)
		codePre, okPre := matchPrefiltered(line)
		if okDirect != okPre || codeDirect != codePre {
			panic(fmt.Sprintf("mismatch on %q: direct=(%q,%v) prefiltered=(%q,%v)", line, codeDirect, okDirect, codePre, okPre))
		}
		if okDirect {
			matches++
		}
	}
	if matches != 200 { // 10000/50
		panic(fmt.Sprintf("matches = %d, want 200", matches))
	}

	// Now measure both approaches over the whole batch.
	startDirect := time.Now()
	for i := 0; i < 20; i++ { // repeat the batch to get a stable duration
		for _, line := range lines {
			matchDirect(line)
		}
	}
	durDirect := time.Since(startDirect)

	startPre := time.Now()
	for i := 0; i < 20; i++ {
		for _, line := range lines {
			matchPrefiltered(line)
		}
	}
	durPre := time.Since(startPre)

	fmt.Printf("regex on every line:            %v\n", durDirect)
	fmt.Printf("strings.Contains pre-filtered:  %v\n", durPre)

	if durPre > durDirect {
		fmt.Println("note: pre-filter was not faster in this run (small/fast pattern, JIT/cache noise) - reporting the real numbers regardless")
	} else {
		speedup := float64(durDirect) / float64(durPre)
		fmt.Printf("pre-filtering was %.1fx faster in this run\n", speedup)
	}

	fmt.Println("OK")
}
