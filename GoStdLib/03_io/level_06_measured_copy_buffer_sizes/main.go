/*
LEVEL 06 (advanced) - MEASURED: io.CopyBuffer with a tiny buffer vs a large one

You will learn
  - io.Copy allocates its own 32KiB buffer internally when the source isn't
    already able to hand back a slice directly; io.CopyBuffer lets YOU supply
    the buffer instead
  - a small buffer means more Read/Write call round-trips for the same total
    data - real, measurable overhead, not just theory
  - the buffer you pass is SILENTLY IGNORED whenever the destination
    implements io.ReaderFrom (bytes.Buffer does) or the source implements
    io.WriterTo - CopyBuffer takes that fast path instead, which is why this
    level's destination deliberately hides ReadFrom behind a plain io.Writer
  - how to time real code with time.Now()/time.Since() and report exactly what
    THIS run measured

Run: go run ./GoStdLib/03_io/level_06_measured_copy_buffer_sizes
*/

package main

import (
	"bytes"
	"fmt"
	"io"
	"time"
)

// countingReader wraps a bytes.Reader and counts how many times Read is
// called, so the effect of io.CopyBuffer's buffer size on round-trip count
// is directly observable rather than assumed.
type countingReader struct {
	r     *bytes.Reader
	calls int
}

func (c *countingReader) Read(p []byte) (int, error) {
	c.calls++
	return c.r.Read(p)
}

// plainWriter deliberately exposes ONLY io.Writer, hiding bytes.Buffer's own
// ReadFrom method. This matters: io.CopyBuffer skips the caller-supplied
// buffer entirely and calls dst.ReadFrom(src) directly whenever the
// destination implements io.ReaderFrom (or the source implements
// io.WriterTo) - a real, easy-to-miss fast path. Hiding ReadFrom here forces
// io.CopyBuffer to actually use the buffer size we pass it, which is what
// this level is measuring.
type plainWriter struct{ buf *bytes.Buffer }

func (w *plainWriter) Write(p []byte) (int, error) { return w.buf.Write(p) }

// copyWithBuffer drives the REAL io.CopyBuffer with a caller-supplied buffer
// size, returning how many bytes moved and how many Read calls it took.
func copyWithBuffer(data []byte, bufSize int) (int64, int) {
	src := &countingReader{r: bytes.NewReader(data)}
	dst := &plainWriter{buf: &bytes.Buffer{}}
	buf := make([]byte, bufSize)
	total, err := io.CopyBuffer(dst, src, buf)
	if err != nil {
		panic(fmt.Sprintf("io.CopyBuffer failed: %v", err))
	}
	return total, src.calls
}

func main() {
	const size = 4 << 20 // 4 MiB
	data := bytes.Repeat([]byte("x"), size)

	const rounds = 10

	start := time.Now()
	var smallTotal int64
	var smallCalls int
	for i := 0; i < rounds; i++ {
		smallTotal, smallCalls = copyWithBuffer(data, 256)
	}
	smallElapsed := time.Since(start)

	start = time.Now()
	var largeTotal int64
	var largeCalls int
	for i := 0; i < rounds; i++ {
		largeTotal, largeCalls = copyWithBuffer(data, 64*1024)
	}
	largeElapsed := time.Since(start)

	if smallTotal != int64(size) {
		panic(fmt.Sprintf("small-buffer copy lost bytes: got %d, want %d", smallTotal, size))
	}
	if largeTotal != int64(size) {
		panic(fmt.Sprintf("large-buffer copy lost bytes: got %d, want %d", largeTotal, size))
	}
	if smallCalls <= largeCalls {
		panic(fmt.Sprintf("expected the 256-byte buffer to need more Read calls than the 64KiB buffer, got %d vs %d",
			smallCalls, largeCalls))
	}

	fmt.Printf("256B buffer:  %v for %d rounds (%d Read calls/round)\n", smallElapsed, rounds, smallCalls)
	fmt.Printf("64KiB buffer: %v for %d rounds (%d Read calls/round)\n", largeElapsed, rounds, largeCalls)

	if largeElapsed < smallElapsed {
		fmt.Printf("the larger buffer was %.1fx faster in this run\n",
			float64(smallElapsed)/float64(largeElapsed))
	} else {
		fmt.Println("NOTE: the larger buffer was not faster in this run - reporting the actual measurement.")
	}

	fmt.Println("OK")
}
