/*
LEVEL 05 (intermediate pattern) - LazyQuotes and a custom Comma rune

You will learn
  - by default a `"` appearing outside a quoted field is a hard parse error
    (csv.ErrBareQuote) - real-world exports from other tools do this anyway
  - Reader.LazyQuotes relaxes that rule so malformed-but-recoverable quoting
    parses instead of failing
  - Reader/Writer.Comma is a rune, not just a comma - tab-separated (TSV) data
    is "CSV" with Comma = '\t', same API, same guarantees

Run: go run ./GoStdLib/10_encoding_csv/level_05_lazy_quotes_and_comma
*/

package main

import (
	"encoding/csv"
	"errors"
	"fmt"
	"strings"
)

func main() {
	// A bare quote in the middle of an unquoted field - common in scraped data.
	messy := `id,note
1,he said "hi" to me
`

	strict := csv.NewReader(strings.NewReader(messy))
	if _, err := strict.Read(); err != nil {
		panic(fmt.Sprintf("reading header failed: %v", err))
	}
	_, err := strict.Read()
	if err == nil {
		panic("FAILED: expected a bare-quote parse error in strict mode")
	}
	var parseErr *csv.ParseError
	if !errors.As(err, &parseErr) {
		panic(fmt.Sprintf("expected *csv.ParseError, got %T: %v", err, err))
	}

	// Same input, LazyQuotes = true: the quote is treated as a literal character.
	lazy := csv.NewReader(strings.NewReader(messy))
	lazy.LazyQuotes = true
	if _, err := lazy.Read(); err != nil {
		panic(fmt.Sprintf("reading header failed (lazy): %v", err))
	}
	row, err := lazy.Read()
	if err != nil {
		panic(fmt.Sprintf("LazyQuotes should have tolerated the bare quote: %v", err))
	}
	if want := `he said "hi" to me`; row[1] != want {
		panic(fmt.Sprintf("row[1] = %q, want %q", row[1], want))
	}

	// A custom Comma: tab-separated values, same Reader/Writer types.
	tsv := "id\tname\tcity\n1\tAda\tLondon\n"
	tr := csv.NewReader(strings.NewReader(tsv))
	tr.Comma = '\t'
	tabRecords, err := tr.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("TSV ReadAll failed: %v", err))
	}
	if !(len(tabRecords) == 2 && tabRecords[1][1] == "Ada") {
		panic(fmt.Sprintf("unexpected TSV parse result: %v", tabRecords))
	}

	var buf strings.Builder
	tw := csv.NewWriter(&buf)
	tw.Comma = '\t'
	if err := tw.WriteAll(tabRecords); err != nil {
		panic(fmt.Sprintf("TSV WriteAll failed: %v", err))
	}
	if buf.String() != tsv {
		panic(fmt.Sprintf("TSV round trip mismatch: got %q, want %q", buf.String(), tsv))
	}

	fmt.Printf("strict mode error: %v\n", parseErr.Err)
	fmt.Printf("lazy mode row: %q\n", row[1])
	fmt.Printf("TSV round trip: %q\n", buf.String())
	fmt.Println("OK")
}
