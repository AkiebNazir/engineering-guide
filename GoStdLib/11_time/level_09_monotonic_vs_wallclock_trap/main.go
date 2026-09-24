/*
LEVEL 09 (production trap) - the monotonic reading silently disappears

You will learn
  - time.Now() returns a time.Time carrying BOTH a wall-clock reading and a
    monotonic reading; t.String() shows the monotonic part as a trailing
    "m=+..." offset - Format() never prints it, only the default String()/%v does
  - Sub()/Since() between two time.Time values that both still carry a
    monotonic reading use IT, not the wall clock - that is what makes
    elapsed-time measurement immune to the wall clock being adjusted
  - the trap: Round, Truncate, AddDate, and round-tripping through
    Parse/Format/marshalling all strip the monotonic reading, silently and
    without error - a time.Time that LOOKS the same now computes Sub() using
    wall-clock math instead, which IS vulnerable to a clock step
  - this environment cannot safely adjust the system wall clock to PROVE a
    divergent result, so this level demonstrates the mechanism that is
    honestly measurable: whether the monotonic reading is present at all,
    and that Since()-with-monotonic and Sub()-after-stripping agree under
    normal conditions but are computed by genuinely different code paths

Run: go run ./GoStdLib/11_time/level_09_monotonic_vs_wallclock_trap
*/

package main

import (
	"fmt"
	"strings"
	"time"
)

func hasMonotonic(t time.Time) bool {
	return strings.Contains(t.String(), " m=")
}

func main() {
	start := time.Now()
	if !hasMonotonic(start) {
		panic(fmt.Sprintf("time.Now() should carry a monotonic reading, String()=%q", start.String()))
	}

	time.Sleep(15 * time.Millisecond)
	end := time.Now()

	// Both start and end still carry monotonic readings: Sub() uses them.
	elapsedMono := end.Sub(start)
	if elapsedMono < 15*time.Millisecond {
		panic(fmt.Sprintf("elapsedMono = %v, want >= 15ms", elapsedMono))
	}

	// The trap: round-tripping through Format/Parse (what you'd do to log or
	// persist a timestamp) produces a time.Time with NO monotonic reading -
	// nothing errors, nothing warns, it just silently becomes wall-clock-only.
	const layout = "2006-01-02 15:04:05.000000000"
	startPersisted, err := time.Parse(layout, start.Format(layout))
	if err != nil {
		panic(fmt.Sprintf("Parse failed: %v", err))
	}
	if hasMonotonic(startPersisted) {
		panic("FAILED: a value round-tripped through Format/Parse should have LOST its monotonic reading")
	}

	// Same trap via Round(0), the documented way to strip it deliberately.
	startStripped := start.Round(0)
	if hasMonotonic(startStripped) {
		panic("FAILED: Round(0) should strip the monotonic reading")
	}

	// Under normal conditions (no wall-clock step happened), the wall-clock-only
	// computation and the monotonic one still agree closely - they are computed
	// differently, but nothing perturbed the wall clock during this run.
	elapsedWall := end.Sub(startStripped)
	diff := elapsedMono - elapsedWall
	if diff < 0 {
		diff = -diff
	}
	if diff > 5*time.Millisecond {
		panic(fmt.Sprintf("mono vs wall elapsed should be close absent a clock step: mono=%v wall=%v diff=%v", elapsedMono, elapsedWall, diff))
	}

	fmt.Printf("start has monotonic: %v   after Round(0): %v\n", hasMonotonic(start), hasMonotonic(startStripped))
	fmt.Printf("elapsed via monotonic Sub(): %v\n", elapsedMono)
	fmt.Printf("elapsed via wall-clock-only Sub() (post round-trip): %v\n", elapsedWall)
	fmt.Println("both agree here because nothing stepped the wall clock during this run -")
	fmt.Println("only the monotonic path is IMMUNE to that ever happening")
	fmt.Println("OK")
}
