/*
LEVEL 10 (capstone) - a small report printer using most of levels 1-9 together

You will learn
  - combining Stringer, Fprintf-to-any-writer, width/precision, %+v/%T
    debugging output, and %w error wrapping in one realistic small program:
    render a list of line items into an aligned text report, and reject
    invalid input with a wrapped, inspectable error

Run: go run ./GoStdLib/02_fmt/level_10_capstone_report_printer
*/

package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
)

var ErrInvalidItem = errors.New("invalid line item")

// Cents implements Stringer so %v renders it as currency automatically.
type Cents int64

func (c Cents) String() string {
	return fmt.Sprintf("%.2f", float64(c)/100)
}

type lineItem struct {
	name  string
	qty   int
	price Cents
}

func (li lineItem) validate() error {
	if li.qty <= 0 {
		return fmt.Errorf("%w: %q has non-positive qty %d", ErrInvalidItem, li.name, li.qty)
	}
	if li.price < 0 {
		return fmt.Errorf("%w: %q has negative price %v", ErrInvalidItem, li.name, li.price)
	}
	return nil
}

// writeReport renders items to any io.Writer as an aligned table, returning
// the total. It stops and returns a wrapped error on the first invalid item.
func writeReport(w io.Writer, items []lineItem) (Cents, error) {
	var total Cents
	fmt.Fprintf(w, "%-12s %5s %10s\n", "ITEM", "QTY", "PRICE")
	for _, li := range items {
		if err := li.validate(); err != nil {
			return 0, fmt.Errorf("writeReport: %w", err)
		}
		fmt.Fprintf(w, "%-12s %5d %10s\n", li.name, li.qty, li.price)
		total += li.price * Cents(li.qty)
	}
	fmt.Fprintf(w, "%-12s %5s %10s\n", "TOTAL", "", total)
	return total, nil
}

func main() {
	good := []lineItem{
		{"widget", 2, 350},
		{"gadget", 1, 1999},
	}

	var buf bytes.Buffer
	total, err := writeReport(&buf, good)
	if err != nil {
		panic(fmt.Sprintf("unexpected error on valid items: %v", err))
	}
	if total != 350*2+1999 {
		panic(fmt.Sprintf("total mismatch: got %d, want %d", total, 350*2+1999))
	}
	wantReport := "ITEM           QTY      PRICE\n" +
		"widget           2       3.50\n" +
		"gadget           1      19.99\n" +
		"TOTAL                   26.99\n"
	if buf.String() != wantReport {
		panic(fmt.Sprintf("report mismatch:\ngot:\n%q\nwant:\n%q", buf.String(), wantReport))
	}

	// A bad item: qty is zero. writeReport must fail with a wrapped, inspectable error.
	bad := []lineItem{{"broken", 0, 100}}
	var buf2 bytes.Buffer
	_, err = writeReport(&buf2, bad)
	if err == nil {
		panic("expected writeReport to fail on an invalid item")
	}
	if !errors.Is(err, ErrInvalidItem) {
		panic(fmt.Sprintf("expected errors.Is(err, ErrInvalidItem) to be true, got %v", err))
	}

	// %+v and %T for debugging the failing item itself.
	badItem := bad[0]
	debug := fmt.Sprintf("%+v (%T)", badItem, badItem)
	want := "{name:broken qty:0 price:100} (main.lineItem)"
	if debug != want {
		panic(fmt.Sprintf("debug form mismatch: got %q, want %q", debug, want))
	}

	fmt.Print(buf.String())
	fmt.Println("total:", total)
	fmt.Println("rejected item error:", err)
	fmt.Println("debug form:", debug)
	fmt.Println("OK")
}
