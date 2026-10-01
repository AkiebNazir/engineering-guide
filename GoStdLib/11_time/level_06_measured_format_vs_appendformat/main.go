/*
LEVEL 06 (measured) - Format (allocates a string) vs AppendFormat (reuses a buffer)

You will learn
  - t.Format(layout) always allocates a brand-new string
  - t.AppendFormat(buf, layout) appends the formatted bytes onto a []byte you
    already own, growing it only if it must - reuse the same backing array
    across iterations and allocation drops close to zero
  - this level actually times both, N times, with time.Now()/time.Since and
    prints the real numbers instead of assuming AppendFormat "must" win

Run: go run ./GoStdLib/11_time/level_06_measured_format_vs_appendformat
*/

package main

import (
	"fmt"
	"time"
)

func main() {
	const iterations = 200_000
	const layout = "2006-01-02 15:04:05.000"
	t := time.Date(2024, time.March, 15, 9, 30, 0, 0, time.UTC)

	// --- Format: a new string every call ---
	startFormat := time.Now()
	var lastFormatted string
	for i := 0; i < iterations; i++ {
		lastFormatted = t.Format(layout)
	}
	elapsedFormat := time.Since(startFormat)

	// --- AppendFormat: one buffer, reused and reset every iteration ---
	startAppend := time.Now()
	buf := make([]byte, 0, 32)
	var lastAppended []byte
	for i := 0; i < iterations; i++ {
		buf = buf[:0] // reuse the backing array instead of reallocating
		buf = t.AppendFormat(buf, layout)
		lastAppended = buf
	}
	elapsedAppend := time.Since(startAppend)

	if lastFormatted != string(lastAppended) {
		panic(fmt.Sprintf("Format and AppendFormat disagree: %q vs %q", lastFormatted, lastAppended))
	}

	fmt.Printf("iterations=%d  Format=%v  AppendFormat=%v\n", iterations, elapsedFormat, elapsedAppend)
	if elapsedAppend < elapsedFormat {
		fmt.Println("this run: AppendFormat with a reused buffer was faster, as its avoided allocation predicts")
	} else {
		fmt.Println("this run: Format was as fast or faster here - report the honest number, not the assumption")
	}
	fmt.Println("OK")
}
