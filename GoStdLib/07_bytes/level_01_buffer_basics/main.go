/*
LEVEL 01 (basic) - bytes.Buffer: Write/String/Bytes/Reset

You will learn
  - bytes.Buffer is a growable buffer of bytes with Read and Write methods
  - the zero value is ready to use - no constructor needed
  - Write/WriteString append; String()/Bytes() read back the accumulated data;
    Reset() empties it for reuse

Run: go run ./GoStdLib/07_bytes/level_01_buffer_basics
*/

package main

import (
	"bytes"
	"fmt"
)

func main() {
	// The zero value is immediately usable - this is the single most common
	// way people meet the bytes package.
	var buf bytes.Buffer

	n, err := buf.Write([]byte("hello"))
	if err != nil {
		panic(fmt.Sprintf("Write failed: %v", err))
	}
	if n != 5 {
		panic(fmt.Sprintf("Write returned n=%d, want 5", n))
	}

	// WriteString avoids a []byte conversion when the source is already a string.
	if _, err := buf.WriteString(", world"); err != nil {
		panic(fmt.Sprintf("WriteString failed: %v", err))
	}

	// WriteByte and WriteRune append a single unit.
	if err := buf.WriteByte('!'); err != nil {
		panic(fmt.Sprintf("WriteByte failed: %v", err))
	}

	got := buf.String()
	want := "hello, world!"
	if got != want {
		panic(fmt.Sprintf("String() = %q, want %q", got, want))
	}

	// Bytes() gives the same content as a []byte without an extra copy.
	if !bytes.Equal(buf.Bytes(), []byte(want)) {
		panic(fmt.Sprintf("Bytes() = %q, want %q", buf.Bytes(), want))
	}

	if buf.Len() != len(want) {
		panic(fmt.Sprintf("Len() = %d, want %d", buf.Len(), len(want)))
	}

	// Reset empties the buffer so it can be reused for the next message.
	buf.Reset()
	if buf.Len() != 0 {
		panic(fmt.Sprintf("Len() after Reset = %d, want 0", buf.Len()))
	}
	if buf.String() != "" {
		panic(fmt.Sprintf("String() after Reset = %q, want empty", buf.String()))
	}

	// Reused for a second message - proves Reset really cleared prior content.
	fmt.Fprintf(&buf, "count=%d", 42)
	if buf.String() != "count=42" {
		panic(fmt.Sprintf("String() after reuse = %q, want %q", buf.String(), "count=42"))
	}

	fmt.Println("OK")
}
