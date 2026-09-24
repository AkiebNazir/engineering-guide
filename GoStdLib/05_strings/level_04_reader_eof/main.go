/*
LEVEL 04 (advanced) - error handling: strings.Reader as a real io.Reader, and io.EOF

You will learn
  - strings.NewReader(s) gives you a full io.Reader (and io.ReaderAt, io.Seeker,
    io.ByteReader, io.RuneReader) over an in-memory string, no copying needed
  - Read() returning (0, io.EOF) is not a bug to swallow silently - it's the
    real, documented end-of-stream signal you must check for
  - driving Read() manually in a loop, the way many io.Reader consumers do

Run: go run ./GoStdLib/05_strings/level_04_reader_eof
*/

package main

import (
	"errors"
	"fmt"
	"io"
	"strings"
)

func main() {
	const text = "buffer this"
	r := strings.NewReader(text)

	if r.Len() != len(text) {
		panic(fmt.Sprintf("Len() = %d, expected %d", r.Len(), len(text)))
	}

	// Drive Read() manually with a small buffer, exactly like a real
	// io.Reader consumer would, and handle io.EOF for real.
	buf := make([]byte, 4)
	var collected []byte
	reads := 0
	for {
		n, err := r.Read(buf)
		reads++
		if n > 0 {
			collected = append(collected, buf[:n]...)
		}
		if err != nil {
			if !errors.Is(err, io.EOF) {
				panic(fmt.Sprintf("unexpected read error: %v", err))
			}
			break // EOF is the expected, documented way this loop ends
		}
	}

	if string(collected) != text {
		panic(fmt.Sprintf("collected = %q, expected %q", collected, text))
	}
	if reads < 3 {
		panic(fmt.Sprintf("expected at least 3 Read calls with a 4-byte buffer over %d bytes, got %d", len(text), reads))
	}

	// A Reader that has hit EOF stays at EOF - reading again gives (0, io.EOF) again.
	n, err := r.Read(buf)
	if n != 0 || !errors.Is(err, io.EOF) {
		panic(fmt.Sprintf("expected (0, io.EOF) after exhaustion, got (%d, %v)", n, err))
	}

	fmt.Printf("read %q back in %d Read() calls, final call correctly returned io.EOF\n", collected, reads)
	fmt.Println("OK")
}
