/*
LEVEL 08 (advanced) - os + io interop: files ARE Readers/Writers, nothing special

You will learn
  - *os.File needs no adapter to work with io.Copy, io.TeeReader, io.LimitReader,
    or io.MultiWriter - it already satisfies io.ReadWriteCloser
  - a realistic pipeline: stream from a "source" file through a TeeReader that
    also feeds a byte counter, capped by a LimitReader, into a destination file
  - Seek (from io.Seeker, which *os.File also implements) to re-read a file
    after writing it, without closing and reopening

Run: go run ./GoStdLib/03_io/level_08_os_plus_io_interop
*/

package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-io-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	srcPath := filepath.Join(dir, "source.txt")
	dstPath := filepath.Join(dir, "dest.txt")

	content := "the quick brown fox jumps over the lazy dog, twice for good measure"
	if err := os.WriteFile(srcPath, []byte(content), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	srcFile, err := os.Open(srcPath)
	if err != nil {
		panic(fmt.Sprintf("Open source failed: %v", err))
	}
	defer srcFile.Close()

	dstFile, err := os.Create(dstPath)
	if err != nil {
		panic(fmt.Sprintf("Create dest failed: %v", err))
	}
	defer dstFile.Close()

	// Pipeline: limit the read to 20 bytes, and count every byte that flows
	// through on the way to the destination file - all built from generic
	// io pieces around two concrete *os.File values.
	const readLimit = 20
	limited := io.LimitReader(srcFile, readLimit)
	counter := &byteCounter{}
	tee := io.TeeReader(limited, counter)

	n, err := io.Copy(dstFile, tee)
	if err != nil {
		panic(fmt.Sprintf("io.Copy failed: %v", err))
	}
	if n != readLimit {
		panic(fmt.Sprintf("expected to copy exactly %d bytes, got %d", readLimit, n))
	}
	if counter.total != readLimit {
		panic(fmt.Sprintf("expected the tee side-effect to see %d bytes, got %d", readLimit, counter.total))
	}

	// Flush to disk and Seek the destination back to the start to verify it,
	// without closing and reopening the file.
	if err := dstFile.Sync(); err != nil {
		panic(fmt.Sprintf("Sync failed: %v", err))
	}
	if _, err := dstFile.Seek(0, io.SeekStart); err != nil {
		panic(fmt.Sprintf("Seek failed: %v", err))
	}
	verify, err := io.ReadAll(dstFile)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on dest failed: %v", err))
	}
	want := content[:readLimit]
	if string(verify) != want {
		panic(fmt.Sprintf("dest file content mismatch: got %q, want %q", verify, want))
	}

	fmt.Printf("copied %d bytes through LimitReader+TeeReader into a real file\n", n)
	fmt.Printf("byte counter observed: %d\n", counter.total)
	fmt.Printf("dest file content (via Seek+ReadAll, no reopen): %q\n", verify)
	fmt.Println("OK")
}

// byteCounter is a minimal io.Writer used purely to observe what a TeeReader
// hands it, without duplicating the data anywhere.
type byteCounter struct{ total int }

func (b *byteCounter) Write(p []byte) (int, error) {
	b.total += len(p)
	return len(p), nil
}
