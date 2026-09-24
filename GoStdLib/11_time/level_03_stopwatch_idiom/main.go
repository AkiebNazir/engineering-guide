/*
LEVEL 03 (idiom) - timing a function call, and time.After as a select timeout

You will learn
  - the standard "stopwatch" idiom: capture start := time.Now() right before
    the work, then time.Since(start) right after - often wrapped in a defer
    so it measures a whole function including its early returns
  - time.After(d) returns a channel that receives once, after d elapses -
    used inside a select as a timeout arm alongside the real work's channel
  - the two idioms combine naturally: time a piece of work, but give up on it
    if it takes too long

Run: go run ./GoStdLib/11_time/level_03_stopwatch_idiom
*/

package main

import (
	"fmt"
	"time"
)

// timedWork simulates work that takes `d` and reports how long it took via
// the classic defer+time.Since idiom.
func timedWork(d time.Duration) (elapsed time.Duration) {
	start := time.Now()
	defer func() { elapsed = time.Since(start) }()

	time.Sleep(d)
	return
}

// runWithTimeout does work on a background goroutine and races it against
// time.After in a select - whichever fires first wins.
func runWithTimeout(work time.Duration, timeout time.Duration) (done bool, waited time.Duration) {
	start := time.Now()
	result := make(chan struct{})
	go func() {
		time.Sleep(work)
		close(result)
	}()

	select {
	case <-result:
		return true, time.Since(start)
	case <-time.After(timeout):
		return false, time.Since(start)
	}
}

func main() {
	// Sleeps are kept tiny (single-digit milliseconds) so the whole demo
	// stays well under a second of real wall time.
	elapsed := timedWork(5 * time.Millisecond)
	if elapsed < 5*time.Millisecond {
		panic(fmt.Sprintf("timedWork reported %v, want >= 5ms", elapsed))
	}

	// Work finishes well before the timeout: the result channel wins.
	completed, waited1 := runWithTimeout(3*time.Millisecond, 50*time.Millisecond)
	if !completed {
		panic("expected the work to complete before the timeout")
	}
	if waited1 >= 50*time.Millisecond {
		panic(fmt.Sprintf("should not have waited for the full timeout, waited %v", waited1))
	}

	// Work takes longer than the timeout: time.After wins instead.
	completed2, waited2 := runWithTimeout(200*time.Millisecond, 10*time.Millisecond)
	if completed2 {
		panic("expected the timeout to fire before the work completed")
	}
	if waited2 >= 200*time.Millisecond {
		panic(fmt.Sprintf("should have given up at ~10ms, waited %v", waited2))
	}

	fmt.Printf("timedWork elapsed: %v\n", elapsed)
	fmt.Printf("fast work: completed=%v after %v\n", completed, waited1)
	fmt.Printf("slow work: completed=%v after %v (timeout fired)\n", completed2, waited2)
	fmt.Println("OK")
}
