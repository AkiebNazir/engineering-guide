/*
LEVEL 07 (advanced) - resource pattern: reusing an Append* buffer instead of reallocating

You will learn
  - strconv's Append* family (AppendInt, AppendQuote, ...) takes a []byte and
    returns the grown slice - the same slice's backing array is reused
  - resetting a buffer with buf = buf[:0] between uses keeps its capacity,
    avoiding a fresh heap allocation on every formatting pass
  - this is the same "own your buffer's lifetime" discipline as bufio.Writer,
    just applied to a plain []byte instead of a wrapped io.Writer

Run: go run ./GoStdLib/06_strconv/level_07_buffer_reuse
*/

package main

import (
	"fmt"
	"runtime"
	"strconv"
)

// formatRow appends "id=<n> ok=<b>\n" into buf and returns the grown slice.
func formatRow(buf []byte, id int64, ok bool) []byte {
	buf = append(buf, "id="...)
	buf = strconv.AppendInt(buf, id, 10)
	buf = append(buf, " ok="...)
	buf = strconv.AppendBool(buf, ok)
	buf = append(buf, '\n')
	return buf
}

func main() {
	const rows = 10_000

	// --- Fresh allocation every row: buf starts from nil each time. ---
	runtime.GC()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	var lastFresh []byte
	for i := 0; i < rows; i++ {
		var buf []byte // no capacity carried over between iterations
		lastFresh = formatRow(buf, int64(i), i%2 == 0)
	}
	runtime.ReadMemStats(&after)
	freshMallocs := after.Mallocs - before.Mallocs

	// --- Reused buffer: reset length to 0 but KEEP the backing array. ---
	runtime.GC()
	runtime.ReadMemStats(&before)
	reused := make([]byte, 0, 64) // sized once, big enough for one row
	var lastReused []byte
	for i := 0; i < rows; i++ {
		reused = reused[:0] // keep capacity, drop contents
		reused = formatRow(reused, int64(i), i%2 == 0)
		lastReused = append(lastReused[:0], reused...) // copy out what we need to keep
	}
	runtime.ReadMemStats(&after)
	reusedMallocs := after.Mallocs - before.Mallocs

	if string(lastFresh) != "id=9999 ok=false\n" {
		panic(fmt.Sprintf("lastFresh = %q, expected %q", lastFresh, "id=9999 ok=false\n"))
	}
	if string(lastReused) != "id=9999 ok=false\n" {
		panic(fmt.Sprintf("lastReused = %q, expected %q", lastReused, "id=9999 ok=false\n"))
	}

	fmt.Printf("fresh []byte each row: %d heap allocations for %d rows\n", freshMallocs, rows)
	fmt.Printf("reused []byte buffer:  %d heap allocations for %d rows\n", reusedMallocs, rows)

	if reusedMallocs >= freshMallocs {
		panic(fmt.Sprintf("expected reuse to allocate fewer times, got reused=%d vs fresh=%d", reusedMallocs, freshMallocs))
	}

	fmt.Println("OK")
}
