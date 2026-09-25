/*
FOUNDATION LEVEL 09 - generated code in a real program
======================================================
Generated struct types are not your domain models. They are data-transfer
objects, and their only job is to be serialized to or parsed from a boundary.
A complete real-world use case involves framing, IO, and handling errors.

You will learn
  * WHY a stream of messages needs framing, demonstrated by letting it corrupt
  * length-prefix framing: write varint length, then the message, repeat
  * that a schema-version field in the payload is cheap and saves you later

Run it   go run ./09_generated_code_in_a_real_program
Or as two real programs, by hand:
         go run ./09_generated_code_in_a_real_program -write /tmp/batches.pb
         go run ./09_generated_code_in_a_real_program -read  /tmp/batches.pb
*/
package main

import (
	"bytes"
	"encoding/binary"
	"flag"
	"fmt"
	
	"os"
	"os/exec"
	"path/filepath"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l09"
)

func must(err error, what string) {
	if err != nil {
		panic(fmt.Sprintf("FAILED %s: %v", what, err))
	}
}
func mustBe(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

type sampleT struct {
	unixMillis int64
	value      float64
}

type batchT struct {
	deviceId string
	samples  []sampleT
}

var BATCHES = []batchT{
	{"sensor-a", []sampleT{{1700000000000, 21.5}, {1700000060000, 21.7}}},
	{"sensor-b", []sampleT{{1700000000000, 48.0}}},
	{"sensor-c", []sampleT{{1700000000000, -3.25}, {1700000060000, -3.5}, {1700000120000, -3.75}}},
}

func writeBatches(path string) {
	f, err := os.Create(path)
	must(err, "create file")
	defer f.Close()

	for _, b := range BATCHES {
		batch := &l09.SensorBatch{DeviceId: b.deviceId}
		for _, s := range b.samples {
			batch.Samples = append(batch.Samples, &l09.Sample{
				UnixMillis: s.unixMillis,
				Value:      s.value,
			})
		}
		
		payload, err := proto.Marshal(batch)
		must(err, "marshal")

		// FRAMING: write length as varint, then payload
		var buf [10]byte
		n := binary.PutUvarint(buf[:], uint64(len(payload)))
		f.Write(buf[:n])
		f.Write(payload)
	}
	st, _ := f.Stat()
	fmt.Printf("  program A wrote %d batches -> %s (%d bytes)\n", len(BATCHES), path, st.Size())
}

func readBatches(path string) []*l09.SensorBatch {
	blob, err := os.ReadFile(path)
	must(err, "read file")

	var out []*l09.SensorBatch
	position := 0
	for position < len(blob) {
		size, n := binary.Uvarint(blob[position:])
		mustBe(n > 0, "read varint")
		position += n
		
		batch := &l09.SensorBatch{}
		err = proto.Unmarshal(blob[position:position+int(size)], batch)
		must(err, "unmarshal")
		
		position += int(size)
		out = append(out, batch)
	}
	return out
}

func demo() {
	workdir, err := os.MkdirTemp("", "proto_demo")
	must(err, "tempdir")
	defer os.RemoveAll(workdir)

	path := filepath.Join(workdir, "batches.pb")
	 // actually if run via `go run`, me might be a temp binary.
	// We'll execute 'go run main.go' instead
	
	fmt.Println("== 1. two genuinely separate processes ==")
	cmdWrite := exec.Command("go", "run", "09_generated_code_in_a_real_program/main.go", "-write", path)
	cmdWrite.Dir = "."
	outW, err := cmdWrite.CombinedOutput()
	must(err, "run write")
	fmt.Print(string(outW))

	cmdRead := exec.Command("go", "run", "09_generated_code_in_a_real_program/main.go", "-read", path)
	cmdRead.Dir = "."
	outR, err := cmdRead.CombinedOutput()
	must(err, "run read")
	fmt.Print(string(outR))
	mustBe(bytes.Contains(outR, []byte("sensor-c")), "sensor-c found in output")

	fmt.Println("\n== 2. the reader reconstructed exactly what the writer built ==")
	batches := readBatches(path)
	mustBe(len(batches) == len(BATCHES), "framing must recover every message")
	for i, batch := range batches {
		b := BATCHES[i]
		mustBe(batch.DeviceId == b.deviceId, "device id matches")
		mustBe(len(batch.Samples) == len(b.samples), "samples length")
		var vals []float64
		for j, s := range batch.Samples {
			mustBe(s.UnixMillis == b.samples[j].unixMillis, "millis matches")
			mustBe(s.Value == b.samples[j].value, "value matches")
			vals = append(vals, s.Value)
		}
		fmt.Printf("  %s: %d samples, values %v\n", batch.DeviceId, len(batch.Samples), vals)
	}
	fmt.Println("  every field, in every message, in order. Nothing was lost or guessed.")

	fmt.Println("\n== 3. WHY the framing was necessary ==")
	one := &l09.SensorBatch{DeviceId: "first"}
	one.Samples = append(one.Samples, &l09.Sample{UnixMillis: 1, Value: 1.0})
	two := &l09.SensorBatch{DeviceId: "second"}
	two.Samples = append(two.Samples, &l09.Sample{UnixMillis: 2, Value: 2.0})
	
	b1, _ := proto.Marshal(one)
	b2, _ := proto.Marshal(two)
	glued := append(b1, b2...)

	merged := &l09.SensorBatch{}
	err = proto.Unmarshal(glued, merged) // no error!
	must(err, "parse merged")
	fmt.Printf("  wrote 'first' then 'second' with no length prefixes (%d bytes)\n", len(glued))
	fmt.Printf("  parsed back as ONE message: device_id=%q, %d samples\n", merged.DeviceId, len(merged.Samples))
	
	mustBe(merged.DeviceId == "second", "last scalar wins")
	mustBe(len(merged.Samples) == 2, "repeated fields concatenate")
	fmt.Println("  the two messages MERGED: the second device_id overwrote the first,")
	fmt.Println("  and both sample lists were appended into one. No exception, no")
	fmt.Println("  warning, just a plausible-looking wrong answer.")
	fmt.Println("  => a protobuf message does not know its own length. If you put")
	fmt.Println("     more than one in a file, a socket or a log, YOU must frame them.")
	fmt.Println("     (This is precisely the job gRPC's 5-byte prefix does - level 12.)")

	fmt.Println("\n== 4. what this looks like in production ==")
	fmt.Println("  The pattern above is the whole idea behind:")
	fmt.Println("    - protobuf records in Kafka / Pub/Sub / SQS message bodies")
	fmt.Println("    - a `bytes` column in Postgres or a value in Redis")
	fmt.Println("    - on-disk formats and write-ahead logs")
	fmt.Println("    - gRPC request/response bodies (level 12)")
	fmt.Println("  In every one of them the code is the same:")
	fmt.Println("    bytesOut, _ := proto.Marshal(msg)   /   proto.Unmarshal(bytesIn, msg)")
	fmt.Println("  One caution worth internalising now:")
	fmt.Println("    * proto.Unmarshal on untrusted bytes can return an error")
	fmt.Println("      - handle it rather than letting it crash")

	err = proto.Unmarshal([]byte{0xff, 0xff, 0xff, 0xff, 0xff}, &l09.SensorBatch{})
	if err == nil {
		panic("expected garbage to be rejected")
	}
	fmt.Printf("  garbage in -> error: %v (an error, never a panic)\n", err)

	fmt.Println("\nOK")
}

func main() {
	writeFlag := flag.String("write", "", "path to write batches")
	readFlag := flag.String("read", "", "path to read batches")
	flag.Parse()

	if *writeFlag != "" {
		writeBatches(*writeFlag)
		os.Exit(0)
	}
	if *readFlag != "" {
		batches := readBatches(*readFlag)
		for _, b := range batches {
			fmt.Printf("  program B read %s with %d samples\n", b.DeviceId, len(b.Samples))
		}
		os.Exit(0)
	}
	
	demo()
}
