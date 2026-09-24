/*
LEVEL 07 (advanced) - lifecycle: streaming a large JSON array with Decoder.Token

You will learn
  - json.NewDecoder wraps an io.Reader and can decode without ever holding the
    whole input in memory
  - Token() reads one JSON token at a time (the opening '[', each element,
    the closing ']') - the streaming equivalent of bufio.Scanner for JSON
  - looping Decode() for each array element after consuming the opening '['
    keeps memory bounded to ONE element at a time, not the whole array

Run: go run ./GoStdLib/09_encoding_json/level_07_streaming_decoder_tokens
*/

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
)

type Event struct {
	Seq int    `json:"seq"`
	Msg string `json:"msg"`
}

// buildLargeArray produces a JSON array of n Event objects, as bytes.Buffer
// output feeding an io.Reader - simulating a large response body without
// actually needing gigabytes of RAM for this demo.
func buildLargeArray(n int) []byte {
	var buf bytes.Buffer
	buf.WriteByte('[')
	for i := 0; i < n; i++ {
		if i > 0 {
			buf.WriteByte(',')
		}
		enc, _ := json.Marshal(Event{Seq: i, Msg: fmt.Sprintf("event-%d", i)})
		buf.Write(enc)
	}
	buf.WriteByte(']')
	return buf.Bytes()
}

func main() {
	const n = 10_000
	data := buildLargeArray(n)

	dec := json.NewDecoder(bytes.NewReader(data))

	// Consume the opening '[' as a delimiter token - Token() returns
	// json.Delim, not a decoded value.
	tok, err := dec.Token()
	if err != nil {
		panic(fmt.Sprintf("reading opening token failed: %v", err))
	}
	delim, ok := tok.(json.Delim)
	if !ok || delim != '[' {
		panic(fmt.Sprintf("first token = %v (%T), want json.Delim('[')", tok, tok))
	}

	// Now stream: while more values remain, Decode ONE Event at a time.
	var count int
	var seqSum int64
	for dec.More() {
		var e Event
		if err := dec.Decode(&e); err != nil {
			panic(fmt.Sprintf("Decode element %d failed: %v", count, err))
		}
		if e.Seq != count {
			panic(fmt.Sprintf("element %d has Seq=%d, want %d (out of order)", count, e.Seq, count))
		}
		seqSum += int64(e.Seq)
		count++
	}

	if count != n {
		panic(fmt.Sprintf("streamed %d elements, want %d", count, n))
	}
	wantSum := int64(n) * int64(n-1) / 2
	if seqSum != wantSum {
		panic(fmt.Sprintf("sum of Seq = %d, want %d", seqSum, wantSum))
	}

	// Consume the closing ']'.
	tok, err = dec.Token()
	if err != nil {
		panic(fmt.Sprintf("reading closing token failed: %v", err))
	}
	delim, ok = tok.(json.Delim)
	if !ok || delim != ']' {
		panic(fmt.Sprintf("final token = %v (%T), want json.Delim(']')", tok, tok))
	}

	// The stream is now exhausted.
	if _, err := dec.Token(); err != io.EOF {
		panic(fmt.Sprintf("expected io.EOF after the array, got %v", err))
	}

	fmt.Printf("streamed %d elements token-by-token without buffering the whole %d-byte array as one value\n", count, len(data))
	fmt.Println("OK")
}
