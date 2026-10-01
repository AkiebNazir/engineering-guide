/*
LEVEL 07 (lifecycle) - forgetting Writer.Flush() silently loses data

You will learn
  - csv.Writer wraps a bufio.Writer internally - Write() only fills that
    buffer, it does not guarantee bytes reach the underlying file
  - closing the *os.File does NOT flush the csv.Writer's buffer - they are
    two independent buffers, and only Flush() drains the csv one
  - this is the exact same lesson bufio teaches: buffered writers need an
    explicit final flush, and "the program didn't crash" is not evidence
    the data was written
  - Writer.Error() must be checked after Flush() - Flush swallows the
    underlying write error into the Writer's state instead of returning it

Run: go run ./GoStdLib/10_encoding_csv/level_07_flush_leak_trap
*/

package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
)

func writeRecords(path string, flush bool) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write([]string{"id", "name"}); err != nil {
		return err
	}
	if err := w.Write([]string{"1", "Ada"}); err != nil {
		return err
	}
	if flush {
		w.Flush()
		if err := w.Error(); err != nil {
			return err
		}
	}
	// f.Close() runs here via defer - it closes the file descriptor, it does
	// NOT touch csv.Writer's own internal bufio buffer.
	return nil
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-csv-07-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	// --- the mistake: no Flush() before the file is closed ---
	lostPath := filepath.Join(dir, "lost.csv")
	if err := writeRecords(lostPath, false); err != nil {
		panic(fmt.Sprintf("writeRecords(flush=false) failed: %v", err))
	}
	lostInfo, err := os.Stat(lostPath)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	if lostInfo.Size() != 0 {
		panic(fmt.Sprintf("expected 0 bytes without Flush, got %d - this Go version may have changed buffering behaviour", lostInfo.Size()))
	}

	// --- the fix: Flush() before the file goes away ---
	savedPath := filepath.Join(dir, "saved.csv")
	if err := writeRecords(savedPath, true); err != nil {
		panic(fmt.Sprintf("writeRecords(flush=true) failed: %v", err))
	}
	savedInfo, err := os.Stat(savedPath)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	if savedInfo.Size() == 0 {
		panic("FAILED: Flush() should have written bytes to disk, got 0")
	}

	got, err := os.ReadFile(savedPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	want := "id,name\n1,Ada\n"
	if string(got) != want {
		panic(fmt.Sprintf("saved content = %q, want %q", got, want))
	}

	fmt.Printf("without Flush: %d bytes on disk (data lost)\n", lostInfo.Size())
	fmt.Printf("with Flush:    %d bytes on disk: %q\n", savedInfo.Size(), got)
	fmt.Println("OK")
}
