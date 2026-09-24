/*
LEVEL 05 (advanced) - a custom bufio.SplitFunc

You will learn
  - the SplitFunc signature: func(data []byte, atEOF bool) (advance int, token []byte, err error)
  - how to split on a custom delimiter byte (0x1E, the ASCII "record separator")
    instead of newline, the way bufio.ScanLines splits on '\n'
  - a SplitFunc MUST return the final token when atEOF is true even without a
    trailing delimiter, or the last record is silently dropped

Run: go run ./GoStdLib/04_bufio/level_05_custom_splitfunc
*/

package main

import (
	"bufio"
	"bytes"
	"fmt"
	"strings"
)

const recordSep = 0x1E // ASCII Record Separator

// splitOnRecordSep is a bufio.SplitFunc that splits on recordSep instead of '\n'.
// It mirrors the shape of bufio.ScanLines.
func splitOnRecordSep(data []byte, atEOF bool) (advance int, token []byte, err error) {
	if atEOF && len(data) == 0 {
		return 0, nil, nil
	}
	if i := bytes.IndexByte(data, recordSep); i >= 0 {
		// Found a full record: advance past it, return it without the separator.
		return i + 1, data[:i], nil
	}
	if atEOF {
		// No separator left, but there's a final record before EOF - return it,
		// don't drop it. Returning (0, nil, nil) here would silently lose data.
		return len(data), data, nil
	}
	// Need more data to find the next separator.
	return 0, nil, nil
}

func main() {
	records := []string{"alpha", "beta", "gamma", "delta"}
	input := strings.Join(records, string(rune(recordSep)))

	scanner := bufio.NewScanner(strings.NewReader(input))
	scanner.Split(splitOnRecordSep)

	var got []string
	for scanner.Scan() {
		got = append(got, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		panic(fmt.Sprintf("unexpected scanner error: %v", err))
	}

	if len(got) != len(records) {
		panic(fmt.Sprintf("got %d records, expected %d: %v", len(got), len(records), got))
	}
	for i, want := range records {
		if got[i] != want {
			panic(fmt.Sprintf("record %d = %q, expected %q", i, got[i], want))
		}
	}

	fmt.Printf("split %d records on 0x1E: %v\n", len(got), got)
	fmt.Println("OK")
}
