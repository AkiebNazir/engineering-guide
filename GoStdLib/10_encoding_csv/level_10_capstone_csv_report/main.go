/*
LEVEL 10 (capstone) - an expense report: write, flush, reread, validate, sum

You will learn nothing new here - this wires together levels 1-9:
  - csv.Writer with proper Flush()+Error() (levels 1, 7)
  - fields containing a comma, written safely instead of hand-joined (level 9)
  - a real file on disk via os.MkdirTemp/os.Create/os.Open (levels 1, 8)
  - FieldsPerRecord catching a corrupt row for real (level 4)
  - the streaming Read() loop to aggregate without holding everything (level 3)

Run: go run ./GoStdLib/10_encoding_csv/level_10_capstone_csv_report
*/

package main

import (
	"encoding/csv"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
)

type expense struct {
	category string
	note     string
	amount   float64
}

func writeReport(path string, rows []expense) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write([]string{"category", "note", "amount"}); err != nil {
		return err
	}
	for _, r := range rows {
		rec := []string{r.category, r.note, strconv.FormatFloat(r.amount, 'f', 2, 64)}
		if err := w.Write(rec); err != nil {
			return err
		}
	}
	w.Flush()
	return w.Error()
}

// sumByCategory streams the file back and enforces a consistent column count.
func sumByCategory(path string) (map[string]float64, int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, err
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.FieldsPerRecord = 3 // this report always has exactly 3 columns
	if _, err := r.Read(); err != nil {
		return nil, 0, fmt.Errorf("reading header: %w", err)
	}

	totals := make(map[string]float64)
	rowsSeen := 0
	for {
		rec, err := r.Read()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return nil, rowsSeen, fmt.Errorf("row %d: %w", rowsSeen, err)
		}
		amount, err := strconv.ParseFloat(rec[2], 64)
		if err != nil {
			return nil, rowsSeen, fmt.Errorf("row %d amount %q: %w", rowsSeen, rec[2], err)
		}
		totals[rec[0]] += amount
		rowsSeen++
	}
	return totals, rowsSeen, nil
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-csv-10-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)
	path := filepath.Join(dir, "report.csv")

	rows := []expense{
		{"food", "lunch", 12.50},
		{"food", "team lunch, drinks included", 45.00}, // comma in the field, on purpose
		{"transport", "taxi \"receipt #4\"", 18.75},    // quote in the field, on purpose
		{"food", "coffee", 3.50},
	}

	if err := writeReport(path, rows); err != nil {
		panic(fmt.Sprintf("writeReport failed: %v", err))
	}

	totals, rowsSeen, err := sumByCategory(path)
	if err != nil {
		panic(fmt.Sprintf("sumByCategory failed: %v", err))
	}

	if rowsSeen != len(rows) {
		panic(fmt.Sprintf("rowsSeen = %d, want %d", rowsSeen, len(rows)))
	}
	if got, want := totals["food"], 61.00; got != want {
		panic(fmt.Sprintf("food total = %.2f, want %.2f", got, want))
	}
	if got, want := totals["transport"], 18.75; got != want {
		panic(fmt.Sprintf("transport total = %.2f, want %.2f", got, want))
	}

	fmt.Printf("report at %s: %d rows, totals by category: %v\n", path, rowsSeen, totals)
	fmt.Println("OK")
}
