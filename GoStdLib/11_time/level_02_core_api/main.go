/*
LEVEL 02 (core) - the handful of time functions covering 90% of real usage

You will learn
  - time.Date builds a specific instant from components; the accessors
    Year/Month/Day/Hour/Minute/Second/Weekday read them back
  - Before/After/Equal compare two time.Time values (never use == on them -
    two equal instants in different locations are not == but ARE Equal)
  - time.Since(t) is shorthand for time.Now().Sub(t); time.Until(t) is
    shorthand for t.Sub(time.Now())
  - Truncate/Round snap a time.Time to a Duration boundary (e.g. the nearest
    minute) - Truncate always rounds down, Round rounds to nearest

Run: go run ./GoStdLib/11_time/level_02_core_api
*/

package main

import (
	"fmt"
	"time"
)

func main() {
	// time.Date: year, month, day, hour, min, sec, nsec, location.
	launch := time.Date(2024, time.March, 15, 9, 30, 0, 0, time.UTC)

	if launch.Year() != 2024 || launch.Month() != time.March || launch.Day() != 15 {
		panic(fmt.Sprintf("component mismatch: got %d-%s-%d", launch.Year(), launch.Month(), launch.Day()))
	}
	if launch.Hour() != 9 || launch.Minute() != 30 {
		panic(fmt.Sprintf("time-of-day mismatch: got %02d:%02d", launch.Hour(), launch.Minute()))
	}
	if launch.Weekday() != time.Friday {
		panic(fmt.Sprintf("Weekday() = %v, want Friday", launch.Weekday()))
	}

	earlier := launch.Add(-time.Hour)
	later := launch.Add(time.Hour)
	if !earlier.Before(launch) || !launch.Before(later) {
		panic("Before ordering is wrong")
	}
	if !launch.After(earlier) || !later.After(launch) {
		panic("After ordering is wrong")
	}
	if !launch.Equal(time.Date(2024, time.March, 15, 9, 30, 0, 0, time.UTC)) {
		panic("Equal should hold for the same instant built twice")
	}

	// time.Since / time.Until: shorthand for Sub against time.Now().
	past := time.Now().Add(-2 * time.Hour)
	if since := time.Since(past); since < 2*time.Hour {
		panic(fmt.Sprintf("time.Since(past) = %v, want >= 2h", since))
	}
	futureDeadline := time.Now().Add(3 * time.Hour)
	if until := time.Until(futureDeadline); until <= 0 || until > 3*time.Hour {
		panic(fmt.Sprintf("time.Until(futureDeadline) = %v, want in (0, 3h]", until))
	}

	// Truncate rounds down to the boundary; Round rounds to the nearest.
	messy := time.Date(2024, time.March, 15, 9, 31, 40, 0, time.UTC)
	truncated := messy.Truncate(time.Hour)
	rounded := messy.Round(time.Hour)
	if truncated.Minute() != 0 {
		panic(fmt.Sprintf("Truncate(time.Hour) should zero the minute, got %v", truncated))
	}
	if rounded.Hour() != 10 { // 09:31:40 is more than half an hour into the 09:00 hour
		panic(fmt.Sprintf("Round(time.Hour) should round up to 10:00, got %v", rounded))
	}

	fmt.Printf("launch=%v weekday=%v since(past)=%v until(deadline)=%v\n", launch, launch.Weekday(), time.Since(past), time.Until(futureDeadline))
	fmt.Printf("messy=%v truncated=%v rounded=%v\n", messy, truncated, rounded)
	fmt.Println("OK")
}
