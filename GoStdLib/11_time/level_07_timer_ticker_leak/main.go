/*
LEVEL 07 (lifecycle) - a real goroutine leak from an unstopped Ticker

You will learn
  - time.NewTicker starts delivering on ticker.C immediately and keeps going
    forever until Stop() is called - Stop() is not "cleanup for tidiness",
    it is required to let a goroutine reading ticker.C ever exit
  - a goroutine that only knows how to "for range ticker.C" has NO way to
    return if nobody also gives it a stop signal - the ticker firing forever
    keeps it alive forever, which runtime.NumGoroutine() makes visible
  - the fix: read the ticker in a select alongside a stop channel, and call
    ticker.Stop() when leaving - the goroutine count actually drops back down

Run: go run ./GoStdLib/11_time/level_07_timer_ticker_leak
*/

package main

import (
	"fmt"
	"runtime"
	"time"
)

const workers = 15

// startLeaky starts a ticker and a goroutine that reads it forever. There is
// no way to make this goroutine return - it leaks for the life of the process.
func startLeaky() {
	ticker := time.NewTicker(2 * time.Millisecond)
	go func() {
		for range ticker.C {
			// pretend to do periodic work - never told to stop
		}
	}()
}

// startFixed starts an equivalent ticker but reads it in a select alongside
// a stop channel, and calls ticker.Stop() on the way out.
func startFixed(stop <-chan struct{}) {
	ticker := time.NewTicker(2 * time.Millisecond)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				// pretend to do periodic work
			case <-stop:
				return
			}
		}
	}()
}

// waitFor polls runtime.NumGoroutine() until cond is true or the deadline passes.
func waitFor(deadline time.Duration, cond func(n int) bool) int {
	end := time.Now().Add(deadline)
	n := runtime.NumGoroutine()
	for time.Now().Before(end) {
		n = runtime.NumGoroutine()
		if cond(n) {
			return n
		}
		time.Sleep(2 * time.Millisecond)
	}
	return n
}

func main() {
	baseline := runtime.NumGoroutine()

	for i := 0; i < workers; i++ {
		startLeaky()
	}
	afterLeaky := waitFor(50*time.Millisecond, func(n int) bool { return n >= baseline+workers })
	if afterLeaky < baseline+workers {
		panic(fmt.Sprintf("expected at least %d new goroutines from the leak, baseline=%d got=%d", workers, baseline, afterLeaky))
	}

	stop := make(chan struct{})
	for i := 0; i < workers; i++ {
		startFixed(stop)
	}
	afterFixed := waitFor(50*time.Millisecond, func(n int) bool { return n >= afterLeaky+workers })
	if afterFixed < afterLeaky+workers {
		panic(fmt.Sprintf("expected %d more goroutines from the fixed workers, got total %d (was %d)", workers, afterFixed, afterLeaky))
	}

	// Signal the fixed workers to stop, and watch the count actually drop.
	close(stop)
	afterStop := waitFor(200*time.Millisecond, func(n int) bool { return n <= afterFixed-workers/2 })
	if afterStop > afterFixed-workers/2 {
		panic(fmt.Sprintf("FAILED: fixed workers should have exited, count stayed at %d (was %d)", afterStop, afterFixed))
	}
	// The leaky workers never got a stop signal - they are still among the living.
	if afterStop < baseline+workers {
		panic(fmt.Sprintf("the leaky goroutines should still be alive: count=%d, baseline+leaky=%d", afterStop, baseline+workers))
	}

	fmt.Printf("baseline=%d  after %d leaky=%d  after %d fixed=%d  after stop=%d\n",
		baseline, workers, afterLeaky, workers, afterFixed, afterStop)
	fmt.Println("the leaky goroutines are still running - unstoppable without a redesign, and they die only when the process exits")
	fmt.Println("OK")
}
