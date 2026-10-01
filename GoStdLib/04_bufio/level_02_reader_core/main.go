/*
LEVEL 02 (core) - bufio.Reader: ReadString, ReadBytes, Peek

You will learn
  - bufio.NewReader wraps any io.Reader with a read buffer
  - ReadString(delim) reads UP TO AND INCLUDING delim, returning io.EOF if the
    delimiter is never found (with whatever bytes it did read)
  - ReadBytes(delim) is the same contract but returns []byte instead of string
  - Peek(n) looks at the next n bytes WITHOUT consuming them

Run: go run ./GoStdLib/04_bufio/level_02_reader_core
*/

package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"strings"
)

func main() {
	r := bufio.NewReader(strings.NewReader("name:Ana;age:30;city:Lisbon"))

	// Peek does not consume - reading the same bytes twice must give the same result.
	peeked, err := r.Peek(4)
	if err != nil {
		panic(fmt.Sprintf("Peek failed: %v", err))
	}
	if string(peeked) != "name" {
		panic(fmt.Sprintf("Peek = %q, expected %q", peeked, "name"))
	}

	// ReadString reads up to and including the delimiter ';'.
	field1, err := r.ReadString(';')
	if err != nil {
		panic(fmt.Sprintf("ReadString failed: %v", err))
	}
	if field1 != "name:Ana;" {
		panic(fmt.Sprintf("field1 = %q, expected %q", field1, "name:Ana;"))
	}
	// Peek proved the buffer still starts with "name" before we consumed it.

	// ReadBytes does the same thing but returns a []byte.
	field2, err := r.ReadBytes(';')
	if err != nil {
		panic(fmt.Sprintf("ReadBytes failed: %v", err))
	}
	if string(field2) != "age:30;" {
		panic(fmt.Sprintf("field2 = %q, expected %q", field2, "age:30;"))
	}

	// The last field has no trailing ';' - ReadString returns what it has
	// PLUS io.EOF, not an empty result.
	field3, err := r.ReadString(';')
	if !errors.Is(err, io.EOF) {
		panic(fmt.Sprintf("expected io.EOF on last field, got %v", err))
	}
	if field3 != "city:Lisbon" {
		panic(fmt.Sprintf("field3 = %q, expected %q", field3, "city:Lisbon"))
	}

	fmt.Printf("fields: %q %q %q\n", field1, field2, field3)
	fmt.Println("OK")
}
