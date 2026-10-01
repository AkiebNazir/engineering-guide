/*
LEVEL 04 (error handling) - triggering and handling csv.ErrFieldCount for real

You will learn
  - by default FieldsPerRecord locks to the width of the FIRST record read;
    every later record with a different width fails
  - the error is a *csv.ParseError wrapping the sentinel csv.ErrFieldCount -
    errors.Is/errors.As both work because ParseError implements Unwrap
  - ParseError carries StartLine/Line/Column - exactly where parsing broke
  - the fix when rows legitimately vary in width: r.FieldsPerRecord = -1
    turns the check off entirely

Run: go run ./GoStdLib/10_encoding_csv/level_04_field_count_error
*/

package main

import (
	"encoding/csv"
	"errors"
	"fmt"
	"strings"
)

const badCSV = "id,name,city\n" +
	"1,Ada,London\n" +
	"2,Grace\n" + // only 2 fields - the first record had 3
	"3,Alan,Bletchley\n"

func main() {
	// --- default behaviour: the short row is a real, triggered error ---
	r := csv.NewReader(strings.NewReader(badCSV))
	if _, err := r.Read(); err != nil { // header: locks width to 3
		panic(fmt.Sprintf("reading header failed: %v", err))
	}
	if _, err := r.Read(); err != nil { // row 1: also width 3, fine
		panic(fmt.Sprintf("reading row 1 failed: %v", err))
	}

	_, err := r.Read() // row 2: width 2 - must fail
	if err == nil {
		panic("FAILED: expected csv.ErrFieldCount, got nil")
	}
	if !errors.Is(err, csv.ErrFieldCount) {
		panic(fmt.Sprintf("errors.Is(err, csv.ErrFieldCount) = false, err was: %v", err))
	}

	var parseErr *csv.ParseError
	if !errors.As(err, &parseErr) {
		panic(fmt.Sprintf("errors.As(err, *csv.ParseError) failed for: %v (%T)", err, err))
	}
	if parseErr.Line != 3 {
		panic(fmt.Sprintf("ParseError.Line = %d, want 3", parseErr.Line))
	}

	// --- the fix: FieldsPerRecord = -1 disables the width check entirely ---
	r2 := csv.NewReader(strings.NewReader(badCSV))
	r2.FieldsPerRecord = -1
	records, err := r2.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("ReadAll with FieldsPerRecord=-1 should not fail: %v", err))
	}
	if len(records) != 4 {
		panic(fmt.Sprintf("got %d records, want 4", len(records)))
	}
	if len(records[2]) != 2 {
		panic(fmt.Sprintf("short row should keep its own width 2, got %d", len(records[2])))
	}

	fmt.Printf("triggered %v at line %d, column %d\n", parseErr.Err, parseErr.Line, parseErr.Column)
	fmt.Printf("with FieldsPerRecord=-1: %d records read, ragged rows allowed\n", len(records))
	fmt.Println("OK")
}
