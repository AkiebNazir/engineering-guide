/*
LEVEL 07 (advanced) - lifecycle: bufio.Writer needs Flush() before the sink closes

You will learn
  - a bufio.Writer holds bytes in memory; Write() does not guarantee they
    reached the underlying io.Writer
  - closing the underlying *os.File WITHOUT flushing silently drops whatever
    was still buffered - we trigger this data loss for real
  - the fix is a Flush() (checked for error!) before the file is closed

Run: go run ./GoStdLib/04_bufio/level_07_flush_lifecycle
*/

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-bufio-07-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	payload := "this line must survive a Close()\n"

	// --- BROKEN: write through a bufio.Writer, close the file, never Flush. ---
	brokenPath := filepath.Join(dir, "broken.txt")
	bf, err := os.Create(brokenPath)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	broken := bufio.NewWriterSize(bf, 4096) // buffer far bigger than the payload
	if _, err := broken.WriteString(payload); err != nil {
		panic(fmt.Sprintf("WriteString failed: %v", err))
	}
	// Bug: closing the file directly, with no Flush() on the bufio.Writer.
	// The payload is sitting in `broken`'s in-memory buffer, not on disk.
	if err := bf.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}

	lostContent, err := os.ReadFile(brokenPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	if len(lostContent) != 0 {
		panic(fmt.Sprintf("expected the broken file to be empty (data lost silently), got %d bytes", len(lostContent)))
	}
	fmt.Printf("BROKEN: forgot Flush() -> file has %d bytes (expected %d) - data silently lost\n",
		len(lostContent), len(payload))

	// --- FIXED: same pattern, but Flush() (and check its error) before Close. ---
	fixedPath := filepath.Join(dir, "fixed.txt")
	ff, err := os.Create(fixedPath)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	fixed := bufio.NewWriterSize(ff, 4096)
	if _, err := fixed.WriteString(payload); err != nil {
		panic(fmt.Sprintf("WriteString failed: %v", err))
	}
	if err := fixed.Flush(); err != nil {
		panic(fmt.Sprintf("Flush failed: %v", err))
	}
	if err := ff.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}

	savedContent, err := os.ReadFile(fixedPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	if string(savedContent) != payload {
		panic(fmt.Sprintf("fixed file = %q, expected %q", savedContent, payload))
	}
	fmt.Printf("FIXED: Flush() before Close() -> file has %d bytes, content intact\n", len(savedContent))

	fmt.Println("OK")
}
