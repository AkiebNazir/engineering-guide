/*
LEVEL 09 (production trap) - hand-joining fields looks fine until data has a comma

You will learn
  - strings.Join(fields, ",") "works" for every test row that happens not to
    contain a comma or a newline - that is exactly what makes this trap
    dangerous, it ships and passes review
  - the moment a real field contains the delimiter, the hand-joined line
    silently reparsed as MORE fields than were written - no panic, no error,
    just wrong data from that row onward
  - csv.Writer.Write fixes it by quoting any field that needs it (comma,
    quote, or newline) and doubling embedded quotes - the exact RFC 4180 rule
    - so the same data always round-trips correctly

Run: go run ./GoStdLib/10_encoding_csv/level_09_quoting_roundtrip_trap
*/

package main

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"strings"
)

type expense struct {
	category string
	note     string
}

func main() {
	rows := []expense{
		{"food", "lunch"},
		{"food", "team lunch, drinks included"}, // <-- contains a comma
	}

	// --- the trap: naive manual joining ---
	var naive strings.Builder
	naive.WriteString("category,note\n")
	for _, r := range rows {
		naive.WriteString(strings.Join([]string{r.category, r.note}, ","))
		naive.WriteString("\n")
	}

	naiveReader := csv.NewReader(strings.NewReader(naive.String()))
	naiveReader.FieldsPerRecord = -1 // don't let level-4's check hide the symptom
	naiveParsed, err := naiveReader.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("ReadAll on naive output failed: %v", err))
	}
	// The corrupted row now has 3 fields instead of 2 - the embedded comma
	// was silently reinterpreted as a field separator.
	corruptedRow := naiveParsed[2]
	if len(corruptedRow) != 3 {
		panic(fmt.Sprintf("FAILED to reproduce the trap: naive row had %d fields, expected the corrupted width 3", len(corruptedRow)))
	}
	if corruptedRow[1] != "team lunch" {
		panic(fmt.Sprintf("expected the note to be truncated at the comma, got %q", corruptedRow[1]))
	}

	// --- the fix: let csv.Writer do the quoting ---
	var buf bytes.Buffer
	w := csv.NewWriter(&buf)
	if err := w.Write([]string{"category", "note"}); err != nil {
		panic(fmt.Sprintf("Write header failed: %v", err))
	}
	for _, r := range rows {
		if err := w.Write([]string{r.category, r.note}); err != nil {
			panic(fmt.Sprintf("Write failed: %v", err))
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		panic(fmt.Sprintf("Flush reported an error: %v", err))
	}

	fixedReader := csv.NewReader(bytes.NewReader(buf.Bytes()))
	fixedParsed, err := fixedReader.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("ReadAll on fixed output failed: %v", err))
	}
	if len(fixedParsed[2]) != 2 {
		panic(fmt.Sprintf("fixed row should have 2 fields, got %d", len(fixedParsed[2])))
	}
	if fixedParsed[2][1] != rows[1].note {
		panic(fmt.Sprintf("fixed note = %q, want %q", fixedParsed[2][1], rows[1].note))
	}

	fmt.Printf("naive (corrupted) row: %v\n", corruptedRow)
	fmt.Printf("csv.Writer (correct) row: %v\n", fixedParsed[2])
	fmt.Println("OK")
}
