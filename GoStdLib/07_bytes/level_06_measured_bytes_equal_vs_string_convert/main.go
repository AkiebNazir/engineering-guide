/*
LEVEL 06 (advanced) - MEASURED: bytes.Equal vs converting to string first

You will learn
  - string(b) for a []byte b copies the bytes - it is not free
  - comparing []byte directly with bytes.Equal skips that copy entirely
  - this level actually times both approaches on THIS run and prints real
    numbers - never assert a performance claim without measuring it

Run: go run ./GoStdLib/07_bytes/level_06_measured_bytes_equal_vs_string_convert
*/

package main

import (
	"bytes"
	"fmt"
	"time"
)

// payloadSize and iterations are large enough to make the copy cost visible
// above measurement noise, small enough to run in well under a second.
const (
	payloadSize = 64 * 1024
	iterations  = 20_000
)

func main() {
	a := bytes.Repeat([]byte("x"), payloadSize)
	b := bytes.Repeat([]byte("x"), payloadSize)
	// One differing byte at the very end forces a full scan in both approaches
	// (best case for Equal would be an early mismatch, which we deliberately avoid).
	c := bytes.Repeat([]byte("x"), payloadSize)
	c[len(c)-1] = 'y'

	// --- approach 1: convert both sides to string, THEN compare. ---
	// Assigning to a variable (rather than comparing the conversion expressions
	// inline) forces the real copy - Go's compiler only skips the copy for the
	// narrow case of comparing two conversion expressions directly.
	start := time.Now()
	equalCount := 0
	for i := 0; i < iterations; i++ {
		sa := string(a)
		sb := string(b)
		if sa == sb {
			equalCount++
		}
	}
	stringConvertDur := time.Since(start)

	// --- approach 2: bytes.Equal directly on the []byte, no conversion. ---
	start = time.Now()
	equalCount2 := 0
	for i := 0; i < iterations; i++ {
		if bytes.Equal(a, b) {
			equalCount2++
		}
	}
	bytesEqualDur := time.Since(start)

	if equalCount != iterations || equalCount2 != iterations {
		panic(fmt.Sprintf("sanity check failed: equalCount=%d equalCount2=%d, want %d both", equalCount, equalCount2, iterations))
	}

	// Confirm bytes.Equal still correctly reports inequality (not just fast).
	if bytes.Equal(a, c) {
		panic("bytes.Equal(a, c) = true, want false: c differs in its last byte")
	}

	fmt.Printf("payload=%d bytes, iterations=%d\n", payloadSize, iterations)
	fmt.Printf("string(a)==string(b) in a loop: %v (%v/iter)\n", stringConvertDur, stringConvertDur/iterations)
	fmt.Printf("bytes.Equal(a, b) in a loop:    %v (%v/iter)\n", bytesEqualDur, bytesEqualDur/iterations)

	if bytesEqualDur < stringConvertDur {
		speedup := float64(stringConvertDur) / float64(bytesEqualDur)
		fmt.Printf("measured: bytes.Equal was %.1fx faster on this run (avoids the string-copy)\n", speedup)
	} else {
		// Report honestly even if this run didn't show the expected direction -
		// never fabricate a number that contradicts what actually happened.
		fmt.Println("measured: string-convert was NOT slower on this run - reporting the real numbers above as-is")
	}

	fmt.Println("OK")
}
