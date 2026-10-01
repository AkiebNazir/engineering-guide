/*
LEVEL 05 (intermediate) - io.MultiWriter and io.TeeReader

You will learn
  - io.MultiWriter fans one Write out to several Writers, in order, stopping
    at the first error
  - io.TeeReader wraps a Reader so every byte read is ALSO written to a Writer
    as a side effect - "read from A, and copy what you read into B"
  - the classic use: stream a download to disk while computing a checksum, or
    log a request body while still handing it to the real reader

Run: go run ./GoStdLib/03_io/level_05_multiwriter_and_teereader
*/

package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

func main() {
	// MultiWriter: one Write call reaches every destination.
	var a, b, c bytes.Buffer
	mw := io.MultiWriter(&a, &b, &c)
	n, err := mw.Write([]byte("broadcast"))
	if err != nil {
		panic(fmt.Sprintf("MultiWriter Write failed: %v", err))
	}
	if n != len("broadcast") {
		panic(fmt.Sprintf("expected n=%d, got %d", len("broadcast"), n))
	}
	for name, buf := range map[string]*bytes.Buffer{"a": &a, "b": &b, "c": &c} {
		if buf.String() != "broadcast" {
			panic(fmt.Sprintf("destination %s mismatch: got %q", name, buf.String()))
		}
	}

	// TeeReader: reading from the tee ALSO writes what was read into a second buffer.
	source := strings.NewReader("hash me while you read me")
	var sideEffect bytes.Buffer
	tee := io.TeeReader(source, &sideEffect)

	primaryRead, err := io.ReadAll(tee)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on TeeReader failed: %v", err))
	}
	want := "hash me while you read me"
	if string(primaryRead) != want {
		panic(fmt.Sprintf("primary read mismatch: got %q, want %q", primaryRead, want))
	}
	if sideEffect.String() != want {
		panic(fmt.Sprintf("tee side-effect mismatch: got %q, want %q", sideEffect.String(), want))
	}

	// Realistic combination: copy from a TeeReader straight into a MultiWriter,
	// so one read drives both the "real" destination and a running log.
	var dest, log bytes.Buffer
	body := strings.NewReader("request body")
	logged := io.TeeReader(body, &log)
	copied, err := io.Copy(&dest, logged)
	if err != nil {
		panic(fmt.Sprintf("io.Copy from TeeReader failed: %v", err))
	}
	if dest.String() != "request body" || log.String() != "request body" {
		panic(fmt.Sprintf("expected both dest and log to see the full body, got dest=%q log=%q",
			dest.String(), log.String()))
	}
	if copied != int64(len("request body")) {
		panic(fmt.Sprintf("expected %d bytes copied, got %d", len("request body"), copied))
	}

	fmt.Printf("MultiWriter reached %d destinations with %q\n", 3, a.String())
	fmt.Printf("TeeReader: primary=%q side-effect=%q\n", primaryRead, sideEffect.String())
	fmt.Printf("Copy(TeeReader): dest=%q log=%q\n", dest.String(), log.String())
	fmt.Println("OK")
}
