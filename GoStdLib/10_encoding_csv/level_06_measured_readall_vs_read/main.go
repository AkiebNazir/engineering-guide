/*
LEVEL 06 (measured) - ReadAll vs a Read() loop: what actually differs

You will learn
  - ReadAll parses the whole input and returns [][]string - every record
    lives in memory at once
  - a Read() loop parses one record at a time - you decide what to keep,
    so memory can stay flat regardless of input size
  - this level times BOTH on the same generated data with time.Now()/time.Since
    and prints the real numbers from this run - it does not assume streaming
    "wins": on a fully in-memory []byte source (no disk I/O either way) the
    difference is dominated by ReadAll's slice-of-slices allocation, not by
    which loop shape is "supposed to be" faster

Run: go run ./GoStdLib/10_encoding_csv/level_06_measured_readall_vs_read
*/

package main

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"time"
)

func generateCSV(rows int) []byte {
	var buf bytes.Buffer
	buf.WriteString("id,name,category,amount\n")
	for i := 0; i < rows; i++ {
		buf.WriteString(strconv.Itoa(i))
		buf.WriteString(",user")
		buf.WriteString(strconv.Itoa(i))
		buf.WriteString(",cat")
		buf.WriteString(strconv.Itoa(i % 7))
		buf.WriteString(",12.34\n")
	}
	return buf.Bytes()
}

func main() {
	const rows = 30000
	data := generateCSV(rows)

	// --- ReadAll: everything in memory at once ---
	startAll := time.Now()
	r := csv.NewReader(bytes.NewReader(data))
	all, err := r.ReadAll()
	elapsedAll := time.Since(startAll)
	if err != nil {
		panic(fmt.Sprintf("ReadAll failed: %v", err))
	}

	// --- Read() loop: one record at a time, only a running sum kept ---
	startLoop := time.Now()
	r2 := csv.NewReader(bytes.NewReader(data))
	count := 0
	for {
		_, err := r2.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(fmt.Sprintf("Read failed at record %d: %v", count, err))
		}
		count++
	}
	elapsedLoop := time.Since(startLoop)

	// Correctness must hold regardless of timing: same input, same record count.
	if len(all) != count {
		panic(fmt.Sprintf("record count mismatch: ReadAll=%d, loop=%d", len(all), count))
	}
	if len(all) != rows+1 { // +1 for the header row
		panic(fmt.Sprintf("got %d records, want %d", len(all), rows+1))
	}

	fmt.Printf("rows=%d  ReadAll=%v  Read()-loop=%v\n", rows, elapsedAll, elapsedLoop)
	if elapsedLoop < elapsedAll {
		fmt.Println("this run: the streaming loop was faster (no [][]string retained)")
	} else {
		fmt.Println("this run: ReadAll was as fast or faster - its retained slice cost less than expected here")
	}
	fmt.Println("OK")
}
