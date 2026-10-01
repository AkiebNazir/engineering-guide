/*
LEVEL 10 (capstone) - a tiny job scheduler with timeouts and a formatted log

This wires together levels 1-9:
  - Duration arithmetic and time.Now()/time.Since to time each job (1, 3)
  - a per-job deadline via select+time.After, same shape as level 3
  - log lines formatted with the reference-date layout from level 5
  - Before/After comparisons to find the slowest job (2)
  - everything kept to single-digit milliseconds, well under a second total (7)

Run: go run ./GoStdLib/11_time/level_10_capstone_scheduler_log
*/

package main

import (
	"fmt"
	"time"
)

const logLayout = "2006-01-02 15:04:05.000"

type job struct {
	name string
	work time.Duration
}

type result struct {
	name      string
	ok        bool
	elapsed   time.Duration
	startedAt time.Time
}

// runJob runs one job's simulated work against a shared deadline, exactly
// like level 3's runWithTimeout, but also returns the start time for logging.
func runJob(j job, timeout time.Duration) result {
	start := time.Now()
	done := make(chan struct{})
	go func() {
		time.Sleep(j.work)
		close(done)
	}()

	select {
	case <-done:
		return result{name: j.name, ok: true, elapsed: time.Since(start), startedAt: start}
	case <-time.After(timeout):
		return result{name: j.name, ok: false, elapsed: time.Since(start), startedAt: start}
	}
}

func main() {
	jobs := []job{
		{"warmup", 2 * time.Millisecond},
		{"fetch", 4 * time.Millisecond},
		{"stuck-report", 60 * time.Millisecond}, // deliberately exceeds the deadline
		{"cleanup", 1 * time.Millisecond},
	}
	const deadline = 20 * time.Millisecond

	var results []result
	var log []string
	for _, j := range jobs {
		r := runJob(j, deadline)
		results = append(results, r)
		status := "done"
		if !r.ok {
			status = "TIMEOUT"
		}
		log = append(log, fmt.Sprintf("[%s] %-14s %-7s (%v)", r.startedAt.Format(logLayout), r.name, status, r.elapsed))
	}

	completed, timedOut := 0, 0
	var slowestOK result
	for _, r := range results {
		if r.ok {
			completed++
			if slowestOK.name == "" || r.elapsed > slowestOK.elapsed {
				slowestOK = r
			}
		} else {
			timedOut++
		}
	}

	if completed != 3 {
		panic(fmt.Sprintf("completed = %d, want 3", completed))
	}
	if timedOut != 1 {
		panic(fmt.Sprintf("timedOut = %d, want 1", timedOut))
	}
	if slowestOK.name != "fetch" {
		panic(fmt.Sprintf("slowest completed job = %q, want %q", slowestOK.name, "fetch"))
	}
	for _, r := range results {
		if r.name == "stuck-report" && r.elapsed >= 60*time.Millisecond {
			panic(fmt.Sprintf("stuck-report should have been cut off by the deadline, elapsed=%v", r.elapsed))
		}
	}

	for _, line := range log {
		fmt.Println(line)
	}
	fmt.Printf("completed=%d timedOut=%d slowest=%s (%v)\n", completed, timedOut, slowestOK.name, slowestOK.elapsed)
	fmt.Println("OK")
}
