/*
LEVEL 01 (basic) - encoding/csv: writing and reading a real CSV file

You will learn
  - csv.NewWriter wraps any io.Writer; Write takes one record ([]string)
  - Writer buffers internally - Flush() sends the buffered bytes out (level 7
    shows what happens if you forget this)
  - csv.NewReader wraps any io.Reader; ReadAll returns every record as
    [][]string in one call
  - why encoding/csv exists at all: a field containing a comma or a newline
    is automatically quoted on write and correctly un-quoted on read - hand
    rolled strings.Join(fields, ",") cannot do this safely (level 9 proves it)

Run: go run ./GoStdLib/10_encoding_csv/level_01_write_read_basics
*/

package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-csv-01-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "contacts.csv")

	records := [][]string{
		{"name", "email", "city"},
		{"Ada Lovelace", "ada@example.com", "London"},
		{"Grace Hopper", "grace@example.com", "New York"},
	}

	// --- write ---
	f, err := os.Create(path)
	if err != nil {
		panic(fmt.Sprintf("Create failed: %v", err))
	}
	w := csv.NewWriter(f)
	for _, rec := range records {
		if err := w.Write(rec); err != nil {
			panic(fmt.Sprintf("Write failed: %v", err))
		}
	}
	// The writer buffers records; nothing is guaranteed on disk until Flush.
	w.Flush()
	if err := w.Error(); err != nil {
		panic(fmt.Sprintf("Flush reported an error: %v", err))
	}
	if err := f.Close(); err != nil {
		panic(fmt.Sprintf("Close failed: %v", err))
	}

	// --- read ---
	rf, err := os.Open(path)
	if err != nil {
		panic(fmt.Sprintf("Open failed: %v", err))
	}
	defer rf.Close()

	r := csv.NewReader(rf)
	got, err := r.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("ReadAll failed: %v", err))
	}

	if !reflect.DeepEqual(got, records) {
		panic(fmt.Sprintf("round trip mismatch: got %v, want %v", got, records))
	}

	fmt.Printf("wrote+read %d records (%d fields each)\n", len(got), len(got[0]))
	fmt.Println("OK")
}
