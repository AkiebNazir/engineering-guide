/*
LEVEL 07 (advanced) - lifecycle: Buffer capacity, Grow, and reuse via Reset

You will learn
  - a Buffer grows its backing array automatically, doubling roughly like a
    slice append would - Grow(n) pre-reserves capacity to avoid repeated
    reallocation when you know the approximate final size
  - Cap() exposes the current backing array size, Len() the used portion
  - Reset() empties the buffer for reuse WITHOUT releasing its capacity - this
    is the whole point of reusing a Buffer across many small messages

Run: go run ./GoStdLib/07_bytes/level_07_buffer_reuse_and_growth
*/

package main

import (
	"bytes"
	"fmt"
)

func main() {
	var buf bytes.Buffer

	if buf.Cap() != 0 {
		panic(fmt.Sprintf("fresh Buffer Cap() = %d, want 0", buf.Cap()))
	}

	// Grow(n) guarantees room for n more bytes without another allocation -
	// use it when you know roughly how much you're about to write.
	buf.Grow(1024)
	capAfterGrow := buf.Cap()
	if capAfterGrow < 1024 {
		panic(fmt.Sprintf("Cap() after Grow(1024) = %d, want >= 1024", capAfterGrow))
	}

	// Writing within that reserved capacity must not reallocate: Cap() stays put.
	buf.Write(bytes.Repeat([]byte("a"), 1024))
	if buf.Cap() != capAfterGrow {
		panic(fmt.Sprintf("Cap() changed from %d to %d after writing within reserved space", capAfterGrow, buf.Cap()))
	}
	if buf.Len() != 1024 {
		panic(fmt.Sprintf("Len() = %d, want 1024", buf.Len()))
	}

	// Reset empties the buffer (Len back to 0) but keeps the backing array -
	// this is what makes reuse in a loop cheap.
	buf.Reset()
	if buf.Len() != 0 {
		panic(fmt.Sprintf("Len() after Reset = %d, want 0", buf.Len()))
	}
	if buf.Cap() != capAfterGrow {
		panic(fmt.Sprintf("Cap() after Reset = %d, want unchanged %d (Reset must not shrink capacity)", buf.Cap(), capAfterGrow))
	}

	// Simulate reusing one Buffer to render 100 short messages instead of
	// allocating a new Buffer each time - Cap() should never need to grow
	// past what a single message requires, since Reset gives the space back.
	maxCapSeen := buf.Cap()
	for i := 0; i < 100; i++ {
		buf.Reset()
		fmt.Fprintf(&buf, "message #%d", i)
		if buf.Cap() > maxCapSeen {
			maxCapSeen = buf.Cap()
		}
	}
	if maxCapSeen > capAfterGrow {
		panic(fmt.Sprintf("reuse loop grew capacity past the initial reservation: %d > %d", maxCapSeen, capAfterGrow))
	}

	fmt.Printf("reserved cap=%d up front; reused across 100 messages without regrowing\n", capAfterGrow)
	fmt.Println("OK")
}
