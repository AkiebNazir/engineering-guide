/*
LEVEL 08 (advanced) - os.Pipe, and how umask filters the mode you ask for

You will learn
  - os.Pipe returns a connected (*os.File, *os.File) pair: write end and read end,
    an in-process, in-kernel byte pipe with no filesystem path
  - writes on one end block/queue until read from the other (small enough here
    to not block) - a goroutine writes while the main goroutine reads
  - the mode you pass to Mkdir/OpenFile is ANDed with ~umask before landing on
    disk - 0777 requested under a typical 022 umask becomes 0755

Run: go run ./GoStdLib/01_os/level_08_pipe_and_permissions
*/

package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"syscall"
)

// setUmask sets the process umask and returns the previous value. The os
// package itself has no umask accessor (umask is a process-wide, not a
// file-level, concept), so this reaches one level down to syscall - purely to
// make the demo deterministic, not the focus of this level.
func setUmask(mask int) int {
	return syscall.Umask(mask)
}

func main() {
	// --- os.Pipe: connect a writer goroutine to a reader synchronously ---
	r, w, err := os.Pipe()
	if err != nil {
		panic(fmt.Sprintf("os.Pipe failed: %v", err))
	}

	const message = "piped straight from one goroutine to another\n"
	done := make(chan error, 1)
	go func() {
		_, werr := w.WriteString(message)
		done <- w.Close()
		_ = werr
	}()

	got, err := io.ReadAll(r)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on pipe failed: %v", err))
	}
	if err := <-done; err != nil {
		panic(fmt.Sprintf("writer close failed: %v", err))
	}
	if string(got) != message {
		panic(fmt.Sprintf("pipe content mismatch: got %q, want %q", string(got), message))
	}
	if err := r.Close(); err != nil {
		panic(fmt.Sprintf("read end Close failed: %v", err))
	}

	// --- permission bits vs umask ---
	dir, err := os.MkdirTemp("", "gostdlib-os-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	// Force a known umask (022) so this check is deterministic regardless of
	// what the calling shell had configured, and restore it afterwards.
	oldUmask := setUmask(0o022)
	defer setUmask(oldUmask)

	path := filepath.Join(dir, "wide-open.txt")
	requested := os.FileMode(0o777)
	if err := os.WriteFile(path, []byte("x"), requested); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}
	info, err := os.Stat(path)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	actual := info.Mode().Perm()
	want := os.FileMode(0o755) // 0777 &^ 0022
	if actual != want {
		panic(fmt.Sprintf("expected umask 022 to reduce 0777 to %v, got %v", want, actual))
	}

	fmt.Printf("pipe transferred %d bytes goroutine-to-goroutine\n", len(got))
	fmt.Printf("requested mode %v, umask 022 filtered it down to %v on disk\n", requested, actual)
	fmt.Println("OK")
}
