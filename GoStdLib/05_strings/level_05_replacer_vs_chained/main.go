/*
LEVEL 05 (advanced) - intermediate pattern, MEASURED: strings.NewReplacer vs chained ReplaceAll

You will learn
  - strings.NewReplacer(oldnew...) builds a single Replacer that does ALL
    substitutions in one left-to-right pass over the string
  - chaining several ReplaceAll calls instead makes one full pass PER pair
  - both must produce identical output - only the cost should differ - and we
    time both for real instead of assuming the "obviously better" one wins

Run: go run ./GoStdLib/05_strings/level_05_replacer_vs_chained
*/

package main

import (
	"fmt"
	"strings"
	"time"
)

func replaceChained(s string) string {
	s = strings.ReplaceAll(s, "cat", "dog")
	s = strings.ReplaceAll(s, "red", "blue")
	s = strings.ReplaceAll(s, "fast", "slow")
	s = strings.ReplaceAll(s, "happy", "content")
	return s
}

func main() {
	replacer := strings.NewReplacer(
		"cat", "dog",
		"red", "blue",
		"fast", "slow",
		"happy", "content",
	)

	sample := "the fast red cat is happy; a happy fast cat likes red things"

	viaReplacer := replacer.Replace(sample)
	viaChained := replaceChained(sample)
	if viaReplacer != viaChained {
		panic(fmt.Sprintf("Replacer and chained output differ:\n  replacer=%q\n  chained =%q", viaReplacer, viaChained))
	}
	expected := "the slow blue dog is content; a content slow dog likes blue things"
	if viaReplacer != expected {
		panic(fmt.Sprintf("output = %q, expected %q", viaReplacer, expected))
	}

	const rounds = 200_000

	start := time.Now()
	var lastReplacer string
	for i := 0; i < rounds; i++ {
		lastReplacer = replacer.Replace(sample)
	}
	replacerElapsed := time.Since(start)

	start = time.Now()
	var lastChained string
	for i := 0; i < rounds; i++ {
		lastChained = replaceChained(sample)
	}
	chainedElapsed := time.Since(start)

	if lastReplacer != expected || lastChained != expected {
		panic("timed loop outputs diverged from the expected result")
	}

	fmt.Printf("NewReplacer:    %v for %d rounds (%v/round)\n", replacerElapsed, rounds, replacerElapsed/rounds)
	fmt.Printf("chained ReplaceAll: %v for %d rounds (%v/round)\n", chainedElapsed, rounds, chainedElapsed/rounds)

	if chainedElapsed <= replacerElapsed {
		fmt.Println("NOTE: this run did not show NewReplacer as faster; with only 4 short pairs the gap can be " +
			"small, but NewReplacer still does ONE pass instead of four regardless of timing noise.")
	} else {
		fmt.Printf("NewReplacer was %.1fx faster than chained ReplaceAll in this run\n",
			float64(chainedElapsed)/float64(replacerElapsed))
	}

	fmt.Println("OK")
}
