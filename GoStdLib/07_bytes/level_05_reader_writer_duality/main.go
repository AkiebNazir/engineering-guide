/*
LEVEL 05 (advanced) - reader/writer duality: bytes.NewReader over a []byte

You will learn
  - bytes.NewReader wraps an existing []byte as an io.Reader (read-only, no
    copy of the data) - the standard way to hand a []byte to any API that
    wants an io.Reader (http.NewRequest body, io.Copy, json.NewDecoder, ...)
  - bytes.Reader also implements io.Seeker and io.ReaderAt, unlike bytes.Buffer
  - io.Copy driving data from a bytes.Reader into a bytes.Buffer

Run: go run ./GoStdLib/07_bytes/level_05_reader_writer_duality
*/

package main

import (
	"bytes"
	"fmt"
	"io"
)

func main() {
	source := []byte("the quick brown fox jumps over the lazy dog")
	reader := bytes.NewReader(source)

	if reader.Len() != len(source) {
		panic(fmt.Sprintf("reader.Len() = %d, want %d", reader.Len(), len(source)))
	}

	// io.Copy pulls from the Reader (io.Reader) and pushes into the Buffer
	// (io.Writer) - neither side knows the concrete type of the other.
	var dest bytes.Buffer
	n, err := io.Copy(&dest, reader)
	if err != nil {
		panic(fmt.Sprintf("io.Copy failed: %v", err))
	}
	if n != int64(len(source)) {
		panic(fmt.Sprintf("io.Copy copied %d bytes, want %d", n, len(source)))
	}
	if !bytes.Equal(dest.Bytes(), source) {
		panic(fmt.Sprintf("copied content = %q, want %q", dest.Bytes(), source))
	}

	// The reader is now exhausted (position at the end)...
	if reader.Len() != 0 {
		panic(fmt.Sprintf("reader.Len() after full copy = %d, want 0", reader.Len()))
	}

	// ...but unlike bytes.Buffer, a Reader supports Seek, so it can be rewound
	// and read again without re-wrapping the original []byte.
	if _, err := reader.Seek(0, io.SeekStart); err != nil {
		panic(fmt.Sprintf("Seek failed: %v", err))
	}
	if reader.Len() != len(source) {
		panic(fmt.Sprintf("reader.Len() after Seek(0) = %d, want %d", reader.Len(), len(source)))
	}

	// ReadAt reads from an arbitrary offset without disturbing the current
	// position - useful for random access into a large in-memory blob.
	word := make([]byte, 5)
	if _, err := reader.ReadAt(word, 10); err != nil {
		panic(fmt.Sprintf("ReadAt failed: %v", err))
	}
	if string(word) != "brown" {
		panic(fmt.Sprintf("ReadAt(10) = %q, want %q", word, "brown"))
	}
	// Position for sequential Read is unaffected by ReadAt.
	if reader.Len() != len(source) {
		panic(fmt.Sprintf("reader.Len() after ReadAt = %d, want unchanged %d", reader.Len(), len(source)))
	}

	fmt.Println("copied via io.Copy, rewound with Seek, random-read with ReadAt")
	fmt.Println("OK")
}
