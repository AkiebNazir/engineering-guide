/*
LEVEL 03 (core) - streaming a CSV with Read() instead of ReadAll

You will learn
  - the realistic idiom for a file too large to hold entirely in memory:
    loop on Read() until io.EOF, processing one record at a time
  - mapping a header row to column indexes so the rest of the code reads by
    name ("amount") instead of by magic index (row[2])
  - io.EOF is the well-known sentinel that means "no more records", not an error

Run: go run ./GoStdLib/10_encoding_csv/level_03_streaming_idiom
*/

package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"strings"
)

func main() {
	input := "category,amount\n" +
		"food,12.50\n" +
		"transport,4.25\n" +
		"food,7.00\n" +
		"entertainment,15.00\n"

	r := csv.NewReader(strings.NewReader(input))

	header, err := r.Read()
	if err != nil {
		panic(fmt.Sprintf("reading header failed: %v", err))
	}
	col := make(map[string]int, len(header))
	for i, name := range header {
		col[name] = i
	}

	totals := make(map[string]float64)
	rowsSeen := 0
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break // the streaming idiom's exit condition - not a real error
		}
		if err != nil {
			panic(fmt.Sprintf("Read failed at row %d: %v", rowsSeen, err))
		}
		rowsSeen++

		amount, err := strconv.ParseFloat(rec[col["amount"]], 64)
		if err != nil {
			panic(fmt.Sprintf("ParseFloat failed on row %d: %v", rowsSeen, err))
		}
		totals[rec[col["category"]]] += amount
	}

	if rowsSeen != 4 {
		panic(fmt.Sprintf("rowsSeen = %d, want 4", rowsSeen))
	}
	if got, want := totals["food"], 19.50; got != want {
		panic(fmt.Sprintf("food total = %.2f, want %.2f", got, want))
	}
	if got, want := totals["transport"], 4.25; got != want {
		panic(fmt.Sprintf("transport total = %.2f, want %.2f", got, want))
	}

	fmt.Printf("streamed %d rows, totals: %v\n", rowsSeen, totals)
	fmt.Println("OK")
}
