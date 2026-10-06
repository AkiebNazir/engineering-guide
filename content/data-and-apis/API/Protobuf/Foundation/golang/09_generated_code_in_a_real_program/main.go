/*
FOUNDATION LEVEL 09 - Using generated code in a real program
=============================================================
Every level so far encoded and decoded in the same breath, in one process,
which is not what protobuf is for. This level is the smallest HONEST example:
two separate programs, started separately, sharing nothing but a file on disk
and ../../proto/l09_batch.proto.

Deliberately there is NO gRPC, no service, no network. Protobuf is a
serialization format; the transport is your choice. A file is a transport,
and it is the one that makes the separation impossible to fake - the writer
has already exited by the time the reader starts.

The one genuinely new problem: protobuf messages are NOT self-delimiting.
An encoded message does not record its own length, and the parser reads until
the bytes run out. That is fine for ONE message in a file, but if you
concatenate two, they silently merge into one corrupt value. The fix is
length-prefix framing, which this level implements in a dozen lines and which
is exactly what gRPC does for you on the wire.

(Go ships this framing ready-made as google.golang.org/protobuf/encoding/
protodelim - see ../../../labs/golang/05_delimited_streams_and_benchmark. It
is written out by hand here so that nothing is hidden. The bytes are the
same: a varint length, then the message.)

You will learn
  - the real shape of a protobuf program: build -> proto.Marshal -> write bytes
  - that the reader needs only the same .proto, not the same language or process
  - WHY a stream of messages needs framing, demonstrated by letting it corrupt
  - length-prefix framing: write varint length, then the message, repeat
  - that proto.Unmarshal on untrusted bytes returns an error you must handle

Run it   go run ./Protobuf/Foundation/golang/09_generated_code_in_a_real_program
Or as two real programs, by hand:

	go run ./Protobuf/Foundation/golang/09_generated_code_in_a_real_program -write /tmp/batches.pb
	go run ./Protobuf/Foundation/golang/09_generated_code_in_a_real_program -read  /tmp/batches.pb
*/
package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"google.golang.org/protobuf/encoding/protowire"
	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l09"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

type sample struct {
	unixMillis int64
	value      float64
}

// The three batches program A writes and program B expects to read back.
var batches = []struct {
	deviceID string
	samples  []sample
}{
	{"sensor-a", []sample{{1700000000000, 21.5}, {1700000060000, 21.7}}},
	{"sensor-b", []sample{{1700000000000, 48.0}}},
	{"sensor-c", []sample{{1700000000000, -3.25}, {1700000060000, -3.5}, {1700000120000, -3.75}}},
}

// writeFramed writes one message as <varint length><message bytes>.
// protowire.AppendVarint is protobuf's own varint encoder (level 13 builds
// one from scratch): lengths under 128 cost a single byte.
func writeFramed(w io.Writer, m proto.Message) error {
	payload, err := proto.Marshal(m)
	if err != nil {
		return err
	}
	if _, err := w.Write(protowire.AppendVarint(nil, uint64(len(payload)))); err != nil {
		return err
	}
	_, err = w.Write(payload)
	return err
}

// readFramed reads one <varint length><message> record. It returns io.EOF
// only on a clean boundary between records.
func readFramed(r *bufio.Reader, m proto.Message) error {
	var size uint64
	for shift := 0; ; shift += 7 {
		b, err := r.ReadByte()
		if err != nil {
			if shift == 0 && errors.Is(err, io.EOF) {
				return io.EOF // clean end of file
			}
			return io.ErrUnexpectedEOF
		}
		size |= uint64(b&0x7F) << shift
		if b&0x80 == 0 { // continuation bit clear -> last byte
			break
		}
		if shift > 63 {
			return errors.New("length varint too long")
		}
	}
	buf := make([]byte, size)
	if _, err := io.ReadFull(r, buf); err != nil {
		return io.ErrUnexpectedEOF
	}
	return proto.Unmarshal(buf, m)
}

// writeBatches is PROGRAM A: build messages and write them to a file.
func writeBatches(path string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	for _, b := range batches {
		batch := &l09.SensorBatch{DeviceId: b.deviceID}
		for _, s := range b.samples {
			batch.Samples = append(batch.Samples, &l09.Sample{UnixMillis: s.unixMillis, Value: s.value})
		}
		// FRAMING: length first, then payload. Without it the three messages
		// would merge into one on the way back in (section 3).
		if err := writeFramed(w, batch); err != nil {
			return err
		}
	}
	if err := w.Flush(); err != nil {
		return err
	}
	info, _ := f.Stat()
	fmt.Printf("  program A wrote %d batches -> %s (%d bytes)\n", len(batches), path, info.Size())
	return nil
}

// readBatches is PROGRAM B: it knows only the .proto, not program A.
func readBatches(path string) ([]*l09.SensorBatch, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := bufio.NewReader(f)
	var out []*l09.SensorBatch
	for {
		batch := &l09.SensorBatch{}
		err := readFramed(r, batch)
		if errors.Is(err, io.EOF) {
			return out, nil
		}
		if err != nil {
			return nil, err
		}
		out = append(out, batch)
	}
}

func runSelf(args ...string) string {
	// Not a function call - a real child process: this same compiled binary,
	// started again with a flag. Program A runs to completion and exits
	// before program B is even started.
	exe, err := os.Executable()
	must(err == nil, "find own executable")
	out, err := exec.Command(exe, args...).CombinedOutput()
	if err != nil {
		panic(fmt.Sprintf("child %v failed: %v\n%s", args, err, out))
	}
	return strings.TrimRight(string(out), "\n")
}

func demo() {
	// A temp directory, so the two programs share nothing but this one path.
	workdir, err := os.MkdirTemp("", "protobuf_foundation_l09_")
	must(err == nil, "temp dir")
	defer os.RemoveAll(workdir)
	path := filepath.Join(workdir, "batches.pb")

	fmt.Println("== 1. two genuinely separate processes ==")
	fmt.Println(runSelf("-write", path))
	readOut := runSelf("-read", path)
	fmt.Println(readOut)
	must(strings.Contains(readOut, "sensor-c"), "program B saw the last batch")

	fmt.Println("\n== 2. the reader reconstructed exactly what the writer built ==")
	got, err := readBatches(path)
	must(err == nil, "read back")
	must(len(got) == len(batches), "framing must recover every message")
	for i, batch := range got {
		want := batches[i]
		must(batch.GetDeviceId() == want.deviceID, "device id")
		must(len(batch.GetSamples()) == len(want.samples), "sample count")
		var values []float64
		for j, s := range batch.GetSamples() {
			must(s.GetUnixMillis() == want.samples[j].unixMillis && s.GetValue() == want.samples[j].value,
				"sample content")
			values = append(values, s.GetValue())
		}
		fmt.Printf("  %s: %d samples, values %v\n", batch.GetDeviceId(), len(batch.GetSamples()), values)
	}
	fmt.Println("  every field, in every message, in order. Nothing was lost or guessed.")

	fmt.Println("\n== 3. WHY the framing was necessary ==")
	// Concatenate two messages with no length prefixes and read them back as
	// one. This does not return an error - which is what makes it dangerous.
	one, _ := proto.Marshal(&l09.SensorBatch{DeviceId: "first", Samples: []*l09.Sample{{UnixMillis: 1, Value: 1}}})
	two, _ := proto.Marshal(&l09.SensorBatch{DeviceId: "second", Samples: []*l09.Sample{{UnixMillis: 2, Value: 2}}})
	glued := append(append([]byte{}, one...), two...)
	merged := &l09.SensorBatch{}
	must(proto.Unmarshal(glued, merged) == nil, "no error!")
	fmt.Printf("  wrote 'first' then 'second' with no length prefixes (%d bytes)\n", len(glued))
	fmt.Printf("  parsed back as ONE message: device_id=%q, %d samples\n",
		merged.GetDeviceId(), len(merged.GetSamples()))
	// The documented merge rules bite here: the last scalar wins and the
	// repeated field is APPENDED.
	must(merged.GetDeviceId() == "second", "last scalar wins")
	must(len(merged.GetSamples()) == 2, "repeated fields concatenate")
	fmt.Println("  the two messages MERGED: the second device_id overwrote the first,")
	fmt.Println("  and both sample lists were appended into one. No error, no warning,")
	fmt.Println("  just a plausible-looking wrong answer.")
	fmt.Println("  => a protobuf message does not know its own length. If you put more")
	fmt.Println("     than one in a file, a socket or a log, YOU must frame them.")
	fmt.Println("     (This is precisely the job gRPC's 5-byte prefix does - level 12.)")

	fmt.Println("\n== 4. what this looks like in production ==")
	fmt.Println("  The pattern above is the whole idea behind:")
	fmt.Println("    - protobuf records in Kafka / Pub/Sub / SQS message bodies")
	fmt.Println("    - a `bytea` column in Postgres or a value in Redis")
	fmt.Println("    - on-disk formats and write-ahead logs")
	fmt.Println("    - gRPC request/response bodies (level 12)")
	fmt.Println("  In every one of them the code is the same two calls you saw:")
	fmt.Println("    data, err := proto.Marshal(msg)   /   err := proto.Unmarshal(data, msg)")
	fmt.Println("  and proto.Unmarshal on untrusted bytes returns an ERROR - check it:")
	bad := proto.Unmarshal([]byte{0xff, 0xff, 0xff, 0xff, 0xff}, &l09.SensorBatch{})
	must(bad != nil, "garbage is rejected")
	fmt.Printf("  garbage in -> err = %v\n", bad)
	fmt.Println("  (an error value, never a panic - but only if you look at it.)")

	fmt.Println("\nOK")
}

func main() {
	// The two "program" entry points, so you can run them separately by hand.
	write := flag.String("write", "", "PROGRAM A: write framed batches to this file")
	read := flag.String("read", "", "PROGRAM B: read framed batches from this file")
	flag.Parse()
	switch {
	case *write != "":
		if err := writeBatches(*write); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case *read != "":
		got, err := readBatches(*read)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		for _, b := range got {
			fmt.Printf("  program B read %s with %d samples\n", b.GetDeviceId(), len(b.GetSamples()))
		}
	default:
		demo()
	}
}
