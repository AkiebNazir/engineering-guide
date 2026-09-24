/*
LEVEL 02 (core) - os.OpenFile flags, os.Create, os.Open, and os.Stat

You will learn
  - os.Create is shorthand for OpenFile(path, O_RDWR|O_CREATE|O_TRUNC, 0666)
  - os.Open is shorthand for OpenFile(path, O_RDONLY, 0)
  - the O_APPEND flag: every Write lands at end-of-file, no manual Seek needed
  - os.Stat returns a FileInfo: Size, Mode, ModTime, IsDir
  - an *os.File is an io.Reader/io.Writer/io.Closer - Close it or leak an fd

Run: go run ./GoStdLib/01_os/level_02_open_flags_and_stat
*/

package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-os-02-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "log.txt")

	// os.Create: truncate-or-create, read-write.
	f, err := os.Create(path)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	if _, err := f.WriteString("line1\n"); err != nil {
		panic(fmt.Sprintf("WriteString failed: %v", err))
	}
	if err := f.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}

	// os.OpenFile with O_APPEND|O_WRONLY: writes always land at EOF.
	af, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		panic(fmt.Sprintf("OpenFile(O_APPEND) failed: %v", err))
	}
	if _, err := af.WriteString("line2\n"); err != nil {
		panic(fmt.Sprintf("append WriteString failed: %v", err))
	}
	if err := af.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}

	// os.Open: read-only.
	rf, err := os.Open(path)
	if err != nil {
		panic(fmt.Sprintf("Open failed: %v", err))
	}
	buf := make([]byte, 64)
	n, _ := rf.Read(buf)
	if err := rf.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}
	got := string(buf[:n])
	want := "line1\nline2\n"
	if got != want {
		panic(fmt.Sprintf("append order wrong: got %q, want %q", got, want))
	}

	// os.Stat: metadata without opening the file.
	info, err := os.Stat(path)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	if info.IsDir() {
		panic("Stat reported a plain file as a directory")
	}
	if info.Size() != int64(len(want)) {
		panic(fmt.Sprintf("Size mismatch: got %d, want %d", info.Size(), len(want)))
	}

	dirInfo, err := os.Stat(dir)
	if err != nil {
		panic(fmt.Sprintf("Stat(dir) failed: %v", err))
	}
	if !dirInfo.IsDir() {
		panic("Stat failed to report the temp dir as a directory")
	}

	fmt.Printf("file size=%d mode=%v isDir=%v\n", info.Size(), info.Mode(), info.IsDir())
	fmt.Println("OK")
}
