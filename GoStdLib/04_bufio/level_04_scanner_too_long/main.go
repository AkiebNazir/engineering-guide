/*
LEVEL 04 (advanced) - error handling: bufio.ErrTooLong and Scanner.Buffer

You will learn
  - Scanner's default max token size is bufio.MaxScanTokenSize (64KB)
  - a line longer than that makes Scan() return false and Err() return
    bufio.ErrTooLong - we trigger this for real, not just describe it
  - the fix: call Scanner.Buffer(buf, max) BEFORE scanning to raise the limit

Run: go run ./GoStdLib/04_bufio/level_04_scanner_too_long
*/

package main

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"strings"
)

func main() {
	// One line well over the default 64KB (bufio.MaxScanTokenSize) limit.
	hugeLine := strings.Repeat("x", bufio.MaxScanTokenSize+1024)
	input := hugeLine + "\nsecond line\n"

	// --- First attempt: default buffer, must fail with bufio.ErrTooLong. ---
	scanner := bufio.NewScanner(strings.NewReader(input))
	scanned := 0
	for scanner.Scan() {
		scanned++
	}
	err := scanner.Err()
	if !errors.Is(err, bufio.ErrTooLong) {
		panic(fmt.Sprintf("expected bufio.ErrTooLong, got %v (scanned %d tokens)", err, scanned))
	}
	if scanned != 0 {
		panic(fmt.Sprintf("expected 0 successful scans before the failure, got %d", scanned))
	}
	fmt.Printf("default buffer: Scan failed as expected with %v\n", err)

	// --- Fix: give the scanner room for the largest line we expect. ---
	const maxLineSize = bufio.MaxScanTokenSize * 2 // headroom above the huge line
	fixedScanner := bufio.NewScanner(strings.NewReader(input))
	fixedScanner.Buffer(make([]byte, 0, 64*1024), maxLineSize)

	var lines []string
	for fixedScanner.Scan() {
		lines = append(lines, fixedScanner.Text())
	}
	if err := fixedScanner.Err(); err != nil {
		panic(fmt.Sprintf("after Buffer(), expected no error, got %v", err))
	}
	if len(lines) != 2 {
		panic(fmt.Sprintf("expected 2 lines after fix, got %d", len(lines)))
	}
	if !bytes.Equal([]byte(lines[0]), []byte(hugeLine)) {
		panic("first line after fix did not match the huge line")
	}
	if lines[1] != "second line" {
		panic(fmt.Sprintf("second line = %q, expected %q", lines[1], "second line"))
	}

	fmt.Printf("with Scanner.Buffer(): read %d lines, first line length=%d\n", len(lines), len(lines[0]))
	fmt.Println("OK")
}
