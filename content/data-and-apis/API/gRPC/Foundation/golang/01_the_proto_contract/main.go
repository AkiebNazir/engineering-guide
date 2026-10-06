/*
FOUNDATION LEVEL 01 - The .proto file IS the contract
=========================================================
Level 00 treated `ping.proto` as a magic incantation. This level treats it as
what it is: the single source of truth that both sides are generated from.
`../../proto/contract.proto` is level 00's proto after exactly two edits - one
new FIELD on an existing message, one new RPC on the existing service - and this
file shows what each edit bought you.

THE WORKFLOW, AND IT IS NOT OPTIONAL

	step one   edit the .proto
	step two   run ../../generate.sh  (protoc rewrites the generated package)
	step three THEN write code against the new generated types

	Doing it in any other order means writing code that cannot compile yet. In
	REST you would just start sending a new JSON key and hope; here the contract
	moves first, on purpose. That is the entire trade: less freedom, no drift.

You will learn
  - field NUMBERS (`= 1`, `= 2`) are the wire identity, not field names - renaming
    a field is safe, renumbering or reusing a number is a breaking change
  - adding a field is backward compatible: an old client that never sets it sends
    nothing, and the server reads the Go zero value ("" / 0 / false)
  - adding an RPC is backward compatible too: old clients simply never call it
  - an empty request message (`message VersionRequest {}`) is normal and correct -
    every RPC takes exactly one message so the contract can grow later
  - proto3 makes "absent" and "zero" the same bytes for a plain scalar, which is
    why `proto.Marshal` of an unset field and an explicit 0 are byte-identical
  - the .proto is carried INSIDE the generated package as a descriptor, which is
    why gRPC's implementation can never drift from its documentation

Run it   go run ./gRPC/Foundation/golang/01_the_proto_contract
*/
package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/proto"

	"dsapractice/api/gRPC/Foundation/golang/pb/contractpb"
)

const version = "1.1.0"

type greeterServer struct {
	contractpb.UnimplementedGreeterServer
}

func (s *greeterServer) Ping(ctx context.Context, req *contractpb.PingRequest) (*contractpb.PongResponse, error) {
	// `Times` is the field EDIT #1 added. A client generated from the old proto
	// cannot set it, so we read 0 - and 0 has to mean "not specified". This
	// "zero means absent" ambiguity is the price of proto3 scalars.
	times := req.GetTimes()
	if times <= 0 {
		times = 1
	}
	words := make([]string, times)
	for i := range words {
		words[i] = "pong"
	}
	out := words[0]
	for _, w := range words[1:] {
		out += " " + w
	}
	return &contractpb.PongResponse{Message: out, Count: times}, nil
}

// `Version` is the RPC EDIT #2 added. Before regenerating, this method name
// meant nothing to gRPC; after regenerating, the generated GreeterServer
// interface has it and gRPC routes to it.
func (s *greeterServer) Version(ctx context.Context, req *contractpb.VersionRequest) (*contractpb.VersionResponse, error) {
	return &contractpb.VersionResponse{Version: version}, nil
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	contractpb.RegisterGreeterServer(srv, &greeterServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := contractpb.NewGreeterClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// --- the old call, unchanged. Adding things did not break it. ---
	res, err := client.Ping(ctx, &contractpb.PingRequest{Name: "world"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Ping(name=\"world\")            -> message=%q count=%d\n", res.GetMessage(), res.GetCount())
	if res.GetMessage() != "pong" || res.GetCount() != 1 {
		panic("FAILED")
	}

	// --- the same RPC, now using the field that edit #1 added ---
	res, err = client.Ping(ctx, &contractpb.PingRequest{Name: "world", Times: 3})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Ping(name=\"world\", times=3)   -> message=%q count=%d\n", res.GetMessage(), res.GetCount())
	if res.GetMessage() != "pong pong pong" || res.GetCount() != 3 {
		panic("FAILED")
	}

	// --- the RPC that edit #2 added ---
	vres, err := client.Version(ctx, &contractpb.VersionRequest{})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Version()                     -> version=%q\n", vres.GetVersion())
	if vres.GetVersion() != version {
		panic("FAILED")
	}

	// --- what the contract itself says, read back out of the generated code ---
	// The descriptor is the .proto, parsed, carried inside the generated
	// package. This is why gRPC can never drift from its docs: the docs are the input.
	fmt.Println("\nthe contract, read back out of the generated code:")
	fileDesc := (&contractpb.PingRequest{}).ProtoReflect().Descriptor().ParentFile()
	msgs := fileDesc.Messages()
	for i := 0; i < msgs.Len(); i++ {
		md := msgs.Get(i)
		line := "(none - an empty message is legal)"
		fields := md.Fields()
		for j := 0; j < fields.Len(); j++ {
			if j == 0 {
				line = ""
			} else {
				line += ", "
			}
			line += fmt.Sprintf("%s=%d", fields.Get(j).Name(), fields.Get(j).Number())
		}
		fmt.Printf("  message %-16s fields: %s\n", md.Name(), line)
	}
	methods := fileDesc.Services().Get(0).Methods()
	names := ""
	for i := 0; i < methods.Len(); i++ {
		if i > 0 {
			names += ", "
		}
		names += string(methods.Get(i).Name())
	}
	fmt.Printf("  service %-16s rpcs:   %s\n", fileDesc.Services().Get(0).Name(), names)
	if names != "Ping, Version" {
		panic("FAILED")
	}

	// Field numbers are the wire identity. Assert them, because changing one is
	// a silent, data-corrupting break that no compiler will catch for you.
	pingFields := (&contractpb.PingRequest{}).ProtoReflect().Descriptor().Fields()
	if pingFields.Get(0).Number() != 1 || pingFields.Get(1).Number() != 2 {
		panic("FAILED")
	}

	// The struct tags protoc-gen-go emitted encode exactly those rules:
	fmt.Println("\nthe generated Go struct carries the wire rules as struct tags:")
	fmt.Println("  Name  string `protobuf:\"bytes,1,opt,name=name,proto3\"`")
	fmt.Println("  Times int32  `protobuf:\"varint,2,opt,name=times,proto3\"`")
	fmt.Println("           wire type ^      ^ field number")

	// Proof of the proto3 rule above: an unset scalar is indistinguishable from
	// an explicit zero, because a zero-valued field is simply not written at all.
	a, _ := proto.Marshal(&contractpb.PingRequest{Name: "x"})
	b, _ := proto.Marshal(&contractpb.PingRequest{Name: "x", Times: 0})
	fmt.Println("\nPingRequest{Times unset} and PingRequest{Times: 0} serialise identically")
	fmt.Println("  -> in proto3, 'absent' and 'zero' are the same bytes for a plain scalar")
	if !bytes.Equal(a, b) {
		panic("FAILED")
	}

	fmt.Println("OK")
}
