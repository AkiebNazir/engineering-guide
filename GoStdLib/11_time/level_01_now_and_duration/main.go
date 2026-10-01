/*
LEVEL 01 (basic) - time.Now() and Duration arithmetic

You will learn
  - time.Now() returns the current instant as a time.Time
  - time.Duration is just an int64 count of nanoseconds with a friendly
    String() - time.Second, time.Millisecond etc. are Duration constants
  - Duration arithmetic is ordinary integer arithmetic: time.Second*5 is a
    valid, idiomatic way to build "5 seconds"
  - time.Time + Duration = time.Time: t.Add(d) moves a point in time forward
    (or backward, with a negative Duration)

Run: go run ./GoStdLib/11_time/level_01_now_and_duration
*/

package main

import (
	"fmt"
	"time"
)

func main() {
	now := time.Now()

	fiveSeconds := 5 * time.Second
	if fiveSeconds != 5_000_000_000*time.Nanosecond {
		panic(fmt.Sprintf("5*time.Second = %d ns, want 5_000_000_000", int64(fiveSeconds)))
	}
	if fiveSeconds.String() != "5s" {
		panic(fmt.Sprintf("Duration.String() = %q, want %q", fiveSeconds.String(), "5s"))
	}

	future := now.Add(fiveSeconds)
	if !future.After(now) {
		panic(fmt.Sprintf("future=%v should be after now=%v", future, now))
	}
	back := future.Add(-fiveSeconds)
	if !back.Equal(now) {
		panic(fmt.Sprintf("adding then subtracting the same Duration should return to now: got %v, want %v", back, now))
	}

	// Duration arithmetic composes like any integer: minutes and seconds combine.
	combo := 2*time.Minute + 30*time.Second
	if combo.Seconds() != 150 {
		panic(fmt.Sprintf("combo.Seconds() = %v, want 150", combo.Seconds()))
	}

	fmt.Printf("now=%v  +5s=%v  combo=%v (%v seconds)\n", now.Format(time.Kitchen), future.Format(time.Kitchen), combo, combo.Seconds())
	fmt.Println("OK")
}
