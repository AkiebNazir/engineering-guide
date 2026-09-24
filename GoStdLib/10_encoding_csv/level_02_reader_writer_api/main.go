/*
LEVEL 02 (core) - the Reader/Writer knobs that cover most real usage

You will learn
  - Reader.Comment: a leading rune that makes csv.Reader skip whole lines
  - Reader.TrimLeadingSpace: strips spaces after a comma before parsing a field
  - Reader.FieldsPerRecord: 0 (default) locks to the first record's width;
    a positive number enforces that exact width (level 4 breaks this on purpose)
  - Writer.UseCRLF: emit "\r\n" line endings instead of "\n" (network/Excel friendly)
  - Read() reads exactly one record and returns io.EOF when there is no more -
    ReadAll is just this loop, done for you (level 3 writes the loop by hand)

Run: go run ./GoStdLib/10_encoding_csv/level_02_reader_writer_api
*/

package main

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"strings"
)

func main() {
	input := "# a comment line, ignored\n" +
		"id, name\n" +
		"1,  Ada\n" +
		"2,  Grace\n"

	r := csv.NewReader(strings.NewReader(input))
	r.Comment = '#'
	r.TrimLeadingSpace = true

	got, err := r.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("ReadAll failed: %v", err))
	}
	want := [][]string{
		{"id", "name"},
		{"1", "Ada"},
		{"2", "Grace"},
	}
	if len(got) != len(want) {
		panic(fmt.Sprintf("record count mismatch: got %d, want %d", len(got), len(want)))
	}
	for i := range want {
		for j := range want[i] {
			if got[i][j] != want[i][j] {
				panic(fmt.Sprintf("record %d field %d: got %q, want %q", i, j, got[i][j], want[i][j]))
			}
		}
	}

	// Read() one record at a time: same underlying parser, no ReadAll slice.
	r2 := csv.NewReader(strings.NewReader(input))
	r2.Comment = '#'
	r2.TrimLeadingSpace = true
	first, err := r2.Read()
	if err != nil {
		panic(fmt.Sprintf("Read failed: %v", err))
	}
	if first[0] != "id" || first[1] != "name" {
		// the very first Read() must return the header row - the comment
		// line above it must have been skipped entirely, not returned as data.
		panic(fmt.Sprintf("Comment line leaked into output: %v", first))
	}

	// Writer.UseCRLF: emit "\r\n" instead of "\n".
	var buf bytes.Buffer
	w := csv.NewWriter(&buf)
	w.UseCRLF = true
	if err := w.WriteAll([][]string{{"a", "b"}, {"c", "d"}}); err != nil {
		panic(fmt.Sprintf("WriteAll failed: %v", err)) // WriteAll also Flushes for you
	}
	out := buf.String()
	if !strings.Contains(out, "a,b\r\n") {
		panic(fmt.Sprintf("expected CRLF line ending, got %q", out))
	}

	fmt.Printf("comment-skipped, trimmed rows: %v\n", got)
	fmt.Printf("CRLF output: %q\n", out)
	fmt.Println("OK")
}
