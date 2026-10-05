/*
LAB 05 (advanced) - Streams of messages (protodelim) and an honest benchmark against JSON
=========================================================================================
You will learn
  - a serialised message has no length or terminator, so files, sockets and logs need FRAMING:
    [varint length][message][varint length][message] ...
    Go ships this in google.golang.org/protobuf/encoding/protodelim
  - streaming a producer -> consumer over an io.Pipe (stand-in for a TCP connection)
  - defending the reader: MaxSize stops a corrupt or hostile length prefix from allocating gigabytes
  - reading until io.EOF, and telling a CLEAN end from a TRUNCATED stream (io.ErrUnexpectedEOF)
  - benchmarking with testing.Benchmark from a normal main(): ns/op, B/op, allocs/op
  - reading the result honestly: size ratio, speed ratio, and what gzip does to the size gap

Run it   go run ./Protobuf/labs/golang/05_delimited_streams_and_benchmark      (a few seconds)
*/
package main

import (
	"bufio"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"testing"

	"google.golang.org/protobuf/encoding/protodelim"
	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/labs/golang/pb"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func makeUser(i int) *pb.User {
	return &pb.User{
		Id: int64(1_000_000 + i), Name: fmt.Sprintf("user-%d", i), Email: fmt.Sprintf("user%d@example.com", i),
		Role: pb.Role_ROLE_USER, Tags: []string{"alpha", "beta"}, Active: i%2 == 0, Rating: float64(i%50) / 10,
		Scores:  []int32{1, 5, 9, 12, 40, 41, 88, 99, 3, 7, 12, 18, 21, 22, 23, 24, 25, 26, 27, 28},
		Address: &pb.Address{City: "Oslo", Zip: "0150"},
	}
}

// The same data as a plain struct, the way a JSON API would carry it.
type userJSON struct {
	ID     int64    `json:"id"`
	Name   string   `json:"name"`
	Email  string   `json:"email"`
	Role   string   `json:"role"`
	Tags   []string `json:"tags"`
	Active bool     `json:"active"`
	Rating float64  `json:"rating"`
	Scores []int32  `json:"scores"`
	City   string   `json:"city"`
	Zip    string   `json:"zip"`
}

func toJSONStruct(u *pb.User) userJSON {
	return userJSON{u.Id, u.Name, u.Email, u.Role.String(), u.Tags, u.Active, u.Rating, u.Scores, u.Address.City, u.Address.Zip}
}

func main() {
	fmt.Println("== 1. write and read a delimited stream ==")
	var file bytes.Buffer
	for i := 1; i <= 5; i++ {
		_, err := protodelim.MarshalTo(&file, makeUser(i))
		must(err == nil, "write")
	}
	fmt.Println("  5 records ->", file.Len(), "bytes")

	r := bufio.NewReader(bytes.NewReader(file.Bytes())) // protodelim needs an io.ByteReader: bufio provides it
	var names []string
	for {
		var u pb.User
		err := protodelim.UnmarshalFrom(r, &u)
		if errors.Is(err, io.EOF) { // clean end: no bytes left at a record boundary
			break
		}
		must(err == nil, fmt.Sprint(err))
		names = append(names, u.Name)
	}
	fmt.Println("  read back:", names)
	must(len(names) == 5, "all records read")

	fmt.Println("\n== 2. producer -> consumer over a pipe ==")
	pr, pw := io.Pipe()
	go func() { // producer
		for i := 1; i <= 3; i++ {
			protodelim.MarshalTo(pw, makeUser(i))
		}
		pw.Close()
	}()
	count := 0
	br := bufio.NewReader(pr)
	for {
		var u pb.User
		if err := protodelim.UnmarshalFrom(br, &u); err != nil {
			must(errors.Is(err, io.EOF), "stream ends cleanly")
			break
		}
		count++
	}
	fmt.Println("  consumer received", count, "messages as they were produced")
	must(count == 3, "pipe")

	fmt.Println("\n== 3. truncated and hostile streams ==")
	cut := file.Bytes()[:file.Len()-4]
	br = bufio.NewReader(bytes.NewReader(cut))
	n := 0
	var lastErr error
	for {
		var u pb.User
		if lastErr = protodelim.UnmarshalFrom(br, &u); lastErr != nil {
			break
		}
		n++
	}
	fmt.Printf("  truncated: %d complete records, then error: %v (is EOF: %v)\n", n, lastErr, errors.Is(lastErr, io.EOF))
	must(n == 4 && !errors.Is(lastErr, io.EOF) && errors.Is(lastErr, io.ErrUnexpectedEOF), "truncation is NOT a clean EOF")

	hostile := bufio.NewReader(bytes.NewReader([]byte{0xff, 0xff, 0xff, 0xff, 0x07, 'x'})) // claims a 2 GiB message
	var u pb.User
	err := protodelim.UnmarshalOptions{MaxSize: 1 << 20}.UnmarshalFrom(hostile, &u)
	fmt.Println("  length prefix claiming ~2 GiB with MaxSize=1MiB ->", err)
	must(err != nil, "MaxSize protects the reader")

	fmt.Println("\n== 4. benchmark: Protobuf vs encoding/json (same data, 20 scores, 2 tags) ==")
	users := make([]*pb.User, 1000)
	structs := make([]userJSON, 1000)
	for i := range users {
		users[i] = makeUser(i)
		structs[i] = toJSONStruct(users[i])
	}
	protoBlob, _ := proto.Marshal(users[0])
	jsonBlob, _ := json.Marshal(structs[0])
	fmt.Printf("  size per record: JSON %d bytes, Protobuf %d bytes (%.1fx smaller)\n", len(jsonBlob), len(protoBlob), float64(len(jsonBlob))/float64(len(protoBlob)))

	var jsonAll, protoAll bytes.Buffer
	for i := range users {
		b, _ := json.Marshal(structs[i])
		jsonAll.Write(b)
		p, _ := proto.Marshal(users[i])
		protoAll.Write(p)
	}
	gz := func(b []byte) int {
		var out bytes.Buffer
		w := gzip.NewWriter(&out)
		w.Write(b)
		w.Close()
		return out.Len()
	}
	jz, pz := gz(jsonAll.Bytes()), gz(protoAll.Bytes())
	fmt.Printf("  after gzip (1000 records): JSON %d, Protobuf %d (%.1fx) - compression closes most of the size gap\n", jz, pz, float64(jz)/float64(pz))

	bench := func(name string, f func(b *testing.B)) testing.BenchmarkResult {
		res := testing.Benchmark(f)
		fmt.Printf("  %-18s %8d ns/op %8d B/op %4d allocs/op\n", name, res.NsPerOp(), res.AllocedBytesPerOp(), res.AllocsPerOp())
		return res
	}
	pm := bench("proto  marshal", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			proto.Marshal(users[i%1000])
		}
	})
	jm := bench("json   marshal", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			json.Marshal(structs[i%1000])
		}
	})
	pu := bench("proto  unmarshal", func(b *testing.B) {
		var m pb.User
		for i := 0; i < b.N; i++ {
			proto.Unmarshal(protoBlob, &m)
		}
	})
	ju := bench("json   unmarshal", func(b *testing.B) {
		var m userJSON
		for i := 0; i < b.N; i++ {
			json.Unmarshal(jsonBlob, &m)
		}
	})
	fmt.Printf("  => marshal %.1fx, unmarshal %.1fx faster than encoding/json on this machine\n",
		float64(jm.NsPerOp())/float64(pm.NsPerOp()), float64(ju.NsPerOp())/float64(pu.NsPerOp()))
	must(len(protoBlob) < len(jsonBlob), "protobuf is smaller")
	must(pm.NsPerOp() > 0 && jm.NsPerOp() > 0, "benchmarks ran")
	fmt.Println("  (numbers vary by machine; the DIRECTION is stable. Always measure with YOUR payloads.)")
	fmt.Println("\nOK")
}
