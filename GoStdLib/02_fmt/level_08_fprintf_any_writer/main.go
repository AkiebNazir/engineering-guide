/*
LEVEL 08 (advanced) - Fprintf/Fprintln/Fprint write to ANY io.Writer

You will learn
  - fmt.Printf(...) is just fmt.Fprintf(os.Stdout, ...) under the hood
  - the same call works unchanged against a bytes.Buffer, a file, or any type
    that implements io.Writer - fmt never special-cases stdout
  - writing a five-line custom io.Writer to see exactly what fmt hands it

Run: go run ./GoStdLib/02_fmt/level_08_fprintf_any_writer
*/

package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
)

// countingWriter is a minimal custom io.Writer: it just tallies bytes and
// call counts, proving fmt.Fprintf works against ANY Write(p []byte) (int, error).
type countingWriter struct {
	calls      int
	totalBytes int
}

func (w *countingWriter) Write(p []byte) (int, error) {
	w.calls++
	w.totalBytes += len(p)
	return len(p), nil
}

func main() {
	// 1. Write into an in-memory bytes.Buffer instead of stdout.
	var buf bytes.Buffer
	n, err := fmt.Fprintf(&buf, "%s scored %d points\n", "alice", 42)
	if err != nil {
		panic(fmt.Sprintf("Fprintf to buffer failed: %v", err))
	}
	want := "alice scored 42 points\n"
	if buf.String() != want {
		panic(fmt.Sprintf("buffer content mismatch: got %q, want %q", buf.String(), want))
	}
	if n != len(want) {
		panic(fmt.Sprintf("expected %d bytes written, got %d", len(want), n))
	}

	// 2. Write into a real file on disk - same function, same arguments shape.
	dir, err := os.MkdirTemp("", "gostdlib-fmt-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "report.txt")
	f, err := os.Create(path)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	if _, err := fmt.Fprintf(f, "report generated for %s\n", "bob"); err != nil {
		panic(fmt.Sprintf("Fprintf to file failed: %v", err))
	}
	if err := f.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}
	fileContent, err := os.ReadFile(path)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	if string(fileContent) != "report generated for bob\n" {
		panic(fmt.Sprintf("file content mismatch: got %q", fileContent))
	}

	// 3. Write into a from-scratch custom io.Writer.
	cw := &countingWriter{}
	fmt.Fprintln(cw, "one")
	fmt.Fprintln(cw, "two")
	fmt.Fprintln(cw, "three")
	if cw.calls != 3 {
		panic(fmt.Sprintf("expected 3 Write calls, got %d", cw.calls))
	}
	wantBytes := len("one\n") + len("two\n") + len("three\n")
	if cw.totalBytes != wantBytes {
		panic(fmt.Sprintf("expected %d total bytes, got %d", wantBytes, cw.totalBytes))
	}

	fmt.Println("buffer:", buf.String())
	fmt.Println("file:  ", string(fileContent))
	fmt.Printf("custom writer saw %d calls, %d bytes total\n", cw.calls, cw.totalBytes)
	fmt.Println("OK")
}
