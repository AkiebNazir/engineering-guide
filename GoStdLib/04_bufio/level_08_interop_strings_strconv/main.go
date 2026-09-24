/*
LEVEL 08 (advanced) - interop: bufio.Reader over a strings.Reader, parsed with strconv

You will learn
  - bufio.NewReader accepts ANY io.Reader, including strings.NewReader - you
    don't need a file or socket to use bufio's delimiter-aware reads
  - combining ReadString(',') with strconv.Atoi to parse a token stream
  - real error handling: a malformed token stops the parse with a wrapped error

Run: go run ./GoStdLib/04_bufio/level_08_interop_strings_strconv
*/

package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
)

// sumCSVInts reads comma-separated integers from r and returns their sum.
// The final token (no trailing comma) is handled via the io.EOF contract of
// ReadString.
func sumCSVInts(r io.Reader) (sum int, count int, err error) {
	br := bufio.NewReader(r)
	for {
		token, readErr := br.ReadString(',')
		token = strings.TrimSpace(strings.TrimSuffix(token, ","))
		if token != "" {
			n, convErr := strconv.Atoi(token)
			if convErr != nil {
				return sum, count, fmt.Errorf("parsing token %q: %w", token, convErr)
			}
			sum += n
			count++
		}
		if readErr != nil {
			if errors.Is(readErr, io.EOF) {
				break
			}
			return sum, count, readErr
		}
	}
	return sum, count, nil
}

func main() {
	sum, count, err := sumCSVInts(strings.NewReader("10, 20,30 ,40,50"))
	if err != nil {
		panic(fmt.Sprintf("sumCSVInts failed: %v", err))
	}
	if sum != 150 {
		panic(fmt.Sprintf("sum = %d, expected 150", sum))
	}
	if count != 5 {
		panic(fmt.Sprintf("count = %d, expected 5", count))
	}
	fmt.Printf("sum of %d tokens = %d\n", count, sum)

	// A malformed token must produce a real, inspectable error, not a silent 0.
	_, _, err = sumCSVInts(strings.NewReader("1,2,not-a-number,4"))
	if err == nil {
		panic("expected an error for a malformed token, got nil")
	}
	var numErr *strconv.NumError
	if !errors.As(err, &numErr) {
		panic(fmt.Sprintf("expected the error to wrap *strconv.NumError, got %T: %v", err, err))
	}
	fmt.Printf("malformed input correctly rejected: %v (NumError.Num=%q)\n", err, numErr.Num)

	fmt.Println("OK")
}
