/*
LEVEL 02 (core) - Reader, Writer, Closer, and ReadWriter: the core abstraction

You will learn
  - io.Reader is `Read(p []byte) (n int, err error)` - fill p, report how much
  - io.Writer is `Write(p []byte) (n int, err error)` - consume p, report how much
  - io.Closer is `Close() error` - release the underlying resource
  - io.ReadWriter/io.ReadWriteCloser compose these with embedding, not new methods
  - *bytes.Buffer, *strings.Reader, and *os.File all satisfy different subsets
    of these - that's WHY io.Copy can work on any pairing of them

Run: go run ./GoStdLib/03_io/level_02_reader_writer_interfaces
*/

package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	// strings.Reader: Reader (and ReaderAt, Seeker) but NOT Writer.
	var _ io.Reader = strings.NewReader("x")

	// bytes.Buffer: both Reader and Writer at once - satisfies io.ReadWriter.
	var _ io.ReadWriter = &bytes.Buffer{}

	// *os.File: Reader, Writer, AND Closer - satisfies io.ReadWriteCloser.
	var _ io.ReadWriteCloser = &os.File{}

	// Prove the interfaces are really just method sets by writing a function
	// that only asks for what it needs: an io.Writer, nothing more specific.
	writeGreeting := func(w io.Writer, name string) (int, error) {
		return w.Write([]byte("hello, " + name + "\n"))
	}

	var buf bytes.Buffer
	n, err := writeGreeting(&buf, "reader")
	if err != nil {
		panic(fmt.Sprintf("Write failed: %v", err))
	}
	want := "hello, reader\n"
	if n != len(want) || buf.String() != want {
		panic(fmt.Sprintf("mismatch: n=%d content=%q want=%q", n, buf.String(), want))
	}

	// And a function that only asks for an io.Reader.
	readAll := func(r io.Reader) string {
		var out bytes.Buffer
		if _, err := io.Copy(&out, r); err != nil {
			panic(fmt.Sprintf("io.Copy in readAll failed: %v", err))
		}
		return out.String()
	}
	got := readAll(strings.NewReader("data flows through the interface\n"))
	if got != "data flows through the interface\n" {
		panic(fmt.Sprintf("readAll mismatch: got %q", got))
	}

	// A Read call directly, by hand, to see the raw contract in action:
	// it returns how many bytes it filled, separate from any error.
	r := strings.NewReader("abc")
	p := make([]byte, 2)
	rn, rerr := r.Read(p)
	if rerr != nil {
		panic(fmt.Sprintf("unexpected error on first Read: %v", rerr))
	}
	if rn != 2 || string(p[:rn]) != "ab" {
		panic(fmt.Sprintf("expected to read 2 bytes \"ab\", got n=%d p=%q", rn, p[:rn]))
	}

	fmt.Println("writeGreeting produced:", buf.String())
	fmt.Println("readAll produced:      ", got)
	fmt.Printf("manual Read: n=%d data=%q\n", rn, p[:rn])
	fmt.Println("OK")
}
