/*
LEVEL 08 (advanced) - interop: reading a real file into a bytes.Buffer via io.Copy

You will learn
  - *os.File implements io.Reader; bytes.Buffer implements io.Writer - io.Copy
    connects any such pair without either side knowing the other's concrete type
  - bytes.Buffer.ReadFrom is what io.Copy actually calls here (Buffer implements
    io.ReaderFrom as an optimization), reading in efficiently sized chunks
  - once collected, the file content lives in memory as a plain []byte via Bytes()

Run: go run ./GoStdLib/07_bytes/level_08_interop_io_copy_file
*/

package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-bytes-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "data.txt")
	want := []byte("line one\nline two\nline three\n")
	if err := os.WriteFile(path, want, 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	f, err := os.Open(path)
	if err != nil {
		panic(fmt.Sprintf("Open failed: %v", err))
	}
	defer f.Close()

	var buf bytes.Buffer
	n, err := io.Copy(&buf, f) // *os.File (io.Reader) -> bytes.Buffer (io.Writer)
	if err != nil {
		panic(fmt.Sprintf("io.Copy failed: %v", err))
	}
	if n != int64(len(want)) {
		panic(fmt.Sprintf("io.Copy copied %d bytes, want %d", n, len(want)))
	}
	if !bytes.Equal(buf.Bytes(), want) {
		panic(fmt.Sprintf("buffered content = %q, want %q", buf.Bytes(), want))
	}

	// Now that it's in memory, use the bytes toolkit on it directly - no need
	// to go back to the filesystem to count lines.
	lineCount := bytes.Count(buf.Bytes(), []byte("\n"))
	if lineCount != 3 {
		panic(fmt.Sprintf("Count(\\n) = %d, want 3", lineCount))
	}

	fmt.Printf("copied %d bytes from disk into memory, counted %d lines\n", n, lineCount)
	fmt.Println("OK")
}
