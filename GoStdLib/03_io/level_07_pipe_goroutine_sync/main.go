/*
LEVEL 07 (advanced) - io.Pipe lifecycle: synchronous, unbuffered, and closable

You will learn
  - io.Pipe returns a connected (*PipeReader, *PipeWriter) with NO internal
    buffer: a Write blocks until a Read consumes it, so each side needs its
    own goroutine or it deadlocks
  - closing the writer with Close() makes pending/future Reads see io.EOF
  - closing the writer with CloseWithError(err) makes Reads see THAT error
    instead of io.EOF - how to propagate a producer's failure to the consumer
  - closing the reader early makes further Writes fail with io.ErrClosedPipe

Run: go run ./GoStdLib/03_io/level_07_pipe_goroutine_sync
*/

package main

import (
	"errors"
	"fmt"
	"io"
)

func main() {
	// --- normal case: writer finishes cleanly, reader sees io.EOF ---
	r, w := io.Pipe()
	go func() {
		fmt.Fprintln(w, "line one")
		fmt.Fprintln(w, "line two")
		w.Close() // reader will see io.EOF right after these bytes
	}()

	got, err := io.ReadAll(r)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on clean pipe failed: %v", err))
	}
	want := "line one\nline two\n"
	if string(got) != want {
		panic(fmt.Sprintf("pipe content mismatch: got %q, want %q", got, want))
	}

	// --- failure propagation: CloseWithError delivers a specific error, not io.EOF ---
	var producerErr = errors.New("upstream source failed")
	r2, w2 := io.Pipe()
	go func() {
		fmt.Fprint(w2, "partial data")
		w2.CloseWithError(producerErr)
	}()

	buf := make([]byte, 64)
	n, rerr := readUntilError(r2, buf)
	if string(buf[:n]) != "partial data" {
		panic(fmt.Sprintf("expected partial data before the error, got %q", buf[:n]))
	}
	if !errors.Is(rerr, producerErr) {
		panic(fmt.Sprintf("expected the reader to observe the producer's error, got %v", rerr))
	}

	// --- closing the READ end early breaks the writer with io.ErrClosedPipe ---
	r3, w3 := io.Pipe()
	if err := r3.Close(); err != nil {
		panic(fmt.Sprintf("closing read end failed: %v", err))
	}
	_, werr := w3.Write([]byte("too late"))
	if !errors.Is(werr, io.ErrClosedPipe) {
		panic(fmt.Sprintf("expected io.ErrClosedPipe after closing the reader, got %v", werr))
	}

	fmt.Println("clean pipe:      ", string(got))
	fmt.Println("failed pipe read:", string(buf[:n]), "| error:", rerr)
	fmt.Println("write after reader closed:", werr)
	fmt.Println("OK")
}

// readUntilError reads everything available until Read returns a non-nil
// error, and returns that error too (io.ReadAll would swallow io.EOF but we
// specifically want to see a NON-EOF error here).
func readUntilError(r io.Reader, buf []byte) (int, error) {
	total := 0
	for {
		n, err := r.Read(buf[total:])
		total += n
		if err != nil {
			return total, err
		}
	}
}
