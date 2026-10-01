/*
LEVEL 01 (basic) - io.Copy: the single most common io function

You will learn
  - io.Copy(dst, src) reads from a Reader and writes to a Writer until EOF
  - it returns the number of bytes copied and the first error other than EOF
  - it works between ANY two things that satisfy Reader/Writer - here a
    strings.Reader (source) and a bytes.Buffer (destination)

Run: go run ./GoStdLib/03_io/level_01_copy_basics
*/

package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

func main() {
	src := strings.NewReader("copy me byte for byte\n")
	var dst bytes.Buffer

	n, err := io.Copy(&dst, src)
	if err != nil {
		panic(fmt.Sprintf("io.Copy failed: %v", err))
	}

	want := "copy me byte for byte\n"
	if int(n) != len(want) {
		panic(fmt.Sprintf("expected %d bytes copied, got %d", len(want), n))
	}
	if dst.String() != want {
		panic(fmt.Sprintf("copied content mismatch: got %q, want %q", dst.String(), want))
	}

	// Copying an already-exhausted reader copies zero bytes, no error.
	n2, err := io.Copy(&dst, src)
	if err != nil {
		panic(fmt.Sprintf("second io.Copy failed: %v", err))
	}
	if n2 != 0 {
		panic(fmt.Sprintf("expected 0 bytes on an exhausted reader, got %d", n2))
	}

	fmt.Printf("copied %d bytes: %q\n", n, dst.String())
	fmt.Println("OK")
}
