/*
LEVEL 09 (advanced) - production trap: Buffer.Bytes() aliases internal storage

You will learn
  - Buffer.Bytes() does NOT copy - it returns a slice over the buffer's own
    backing array
  - reusing that same Buffer (Reset + Write again) can silently overwrite data
    a caller thinks it still owns, with no error, no panic, just wrong data
  - the fix: copy out immediately if the slice needs to outlive the next write

Run: go run ./GoStdLib/07_bytes/level_09_bytes_aliasing_trap
*/

package main

import (
	"bytes"
	"fmt"
)

func main() {
	// --- demonstrate the bug for real ---
	var buf bytes.Buffer
	buf.Grow(64) // guarantee enough capacity that neither write below reallocates

	buf.WriteString("original")
	snapshot := buf.Bytes() // BUG: this aliases buf's backing array, no copy taken

	if string(snapshot) != "original" {
		panic(fmt.Sprintf("snapshot right after write = %q, want %q", snapshot, "original"))
	}

	// Somewhere else in the program, this same Buffer gets reused...
	buf.Reset()
	buf.WriteString("mutated!") // same length, fits in the already-grown capacity

	// The "snapshot" a caller took earlier has been corrupted in place - no
	// error was ever returned. This is the trap: it works fine in every test
	// where you don't reuse the Buffer, then breaks in production once you do.
	if string(snapshot) == "original" {
		panic("expected the aliasing trap to corrupt snapshot, but it still reads \"original\" - environment did not reproduce the trap")
	}
	if string(snapshot) != "mutated!" {
		panic(fmt.Sprintf("snapshot after reuse = %q, want it corrupted to %q", snapshot, "mutated!"))
	}
	fmt.Printf("BUG reproduced: snapshot silently became %q after the buffer was reused\n", snapshot)

	// --- the fix: copy the bytes out the moment you need them to survive ---
	var buf2 bytes.Buffer
	buf2.Grow(64)
	buf2.WriteString("original")

	safeCopy := bytes.Clone(buf2.Bytes()) // Go 1.20+: allocates a fresh backing array
	if &safeCopy[0] == &buf2.Bytes()[0] {
		panic("safeCopy shares a backing array with the buffer - Clone did not copy")
	}

	buf2.Reset()
	buf2.WriteString("mutated!")

	if string(safeCopy) != "original" {
		panic(fmt.Sprintf("safeCopy = %q, want it UNAFFECTED by buffer reuse: %q", safeCopy, "original"))
	}

	fmt.Printf("FIXED: safeCopy still reads %q after the same reuse pattern\n", safeCopy)
	fmt.Println("OK")
}
