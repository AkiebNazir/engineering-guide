/*
FOUNDATION LEVEL 12 - The bridge to gRPC (short, on purpose)
=============================================================
You have now learned the whole of protobuf as a data format. gRPC is a
different thing that USES it, and this level exists only to show you the
seam between them clearly, so you can walk into ../../../gRPC/Foundation
knowing exactly which half you already understand.

The seam is narrow. ../../proto/l12_bridge.proto adds one construct you have
not seen - a `service` block - and nothing else:

	service EchoService {
	  rpc Echo(EchoRequest) returns (EchoResponse);
	}

EchoRequest and EchoResponse are ordinary messages, identical in kind to
every message in levels 00-11. gRPC does not extend, wrap or subclass them.
It transports them.

You will learn
  - that gRPC request/response types are just the messages you already know
  - that the generated MESSAGE package (pb/l12) contains no networking at
    all: the service is recorded in the file DESCRIPTOR, but no client or
    server type exists until a second plugin (protoc-gen-go-grpc) runs
  - the one wire detail gRPC adds: a 5-byte length prefix per message, which
    is level 09's framing problem solved once, properly
  - exactly what lives in ../../../gRPC/Foundation and is NOT re-taught here

Run it   go run ./Protobuf/Foundation/golang/12_bridge_to_grpc
Twin     python Protobuf/Foundation/python/12_bridge_to_grpc.py
*/
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l12"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// frame is gRPC's "Length-Prefixed-Message": 1 byte compressed flag, 4 bytes
// big-endian length, then the protobuf bytes untouched.
func frame(payload []byte) []byte {
	out := make([]byte, 5, 5+len(payload))
	out[0] = 0 // 0 = not compressed, 1 = compressed with the negotiated grpc-encoding
	binary.BigEndian.PutUint32(out[1:5], uint32(len(payload)))
	return append(out, payload...)
}

func unframe(b []byte) (compressed bool, payload []byte) {
	size := binary.BigEndian.Uint32(b[1:5])
	return b[0] == 1, b[5 : 5+size]
}

func main() {
	fmt.Println("== 1. the request and response are ordinary messages ==")
	request := &l12.EchoRequest{Text: "hello, gRPC"}
	response := &l12.EchoResponse{Text: request.GetText(), Length: int32(len(request.GetText()))}
	reqBytes, _ := proto.Marshal(request)
	respBytes, _ := proto.Marshal(response)
	fmt.Printf("  EchoRequest  -> %s\n", hex.EncodeToString(reqBytes))
	fmt.Printf("  EchoResponse -> %s\n", hex.EncodeToString(respBytes))
	// Same API as level 00. Nothing here is gRPC-specific.
	roundTripped := &l12.EchoRequest{}
	must(proto.Unmarshal(reqBytes, roundTripped) == nil, "unmarshal")
	must(proto.Equal(roundTripped, request), "round trip")
	fmt.Println("  built, encoded and decoded with the exact API from level 00.")

	fmt.Println("\n== 2. the generated message code knows nothing about networking ==")
	// The service block DID reach the generated file - but only as data inside
	// the embedded file descriptor, which reflection can read.
	fd := request.ProtoReflect().Descriptor().ParentFile()
	services := fd.Services()
	must(services.Len() == 1, "the descriptor records the service")
	svc := services.Get(0)
	m := svc.Methods().Get(0)
	fmt.Printf("  descriptor of %s says: service %s { rpc %s(%s) returns (%s) }\n",
		fd.Path(), svc.Name(), m.Name(), m.Input().Name(), m.Output().Name())
	must(m.Input().FullName() == protoreflect.FullName("found.l12.EchoRequest"), "input type")
	must(!m.IsStreamingClient() && !m.IsStreamingServer(), "unary")
	// What does NOT exist: pb/l12 has only EchoRequest, EchoResponse and
	// File_l12_bridge_proto. There is no EchoServiceClient, no
	// NewEchoServiceClient, no RegisterEchoServiceServer - try referencing
	// l12.NewEchoServiceClient and the program will not compile. Those come
	// from protoc-gen-go-grpc, into a separate l12_bridge_grpc.pb.go file:
	//   protoc --go_out=.              -> messages       (this folder, pb/l12)
	//   protoc --go-grpc_out=.         -> client + server (gRPC folder)
	fmt.Println("  pb/l12 exports: EchoRequest, EchoResponse, File_l12_bridge_proto")
	fmt.Println("  no client, no server interface, no Register func: the service is a")
	fmt.Println("  description waiting for the gRPC plugin to turn it into code.")

	fmt.Println("\n== 3. the one wire detail gRPC adds ==")
	// Level 09 showed that protobuf messages are not self-delimiting and that
	// a stream of them needs framing. gRPC's answer is fixed and simple: every
	// message on the wire is preceded by 5 bytes.
	f := frame(reqBytes)
	fmt.Printf("  protobuf message : %2d bytes  %s\n", len(reqBytes), hex.EncodeToString(reqBytes))
	fmt.Printf("  gRPC frame       : %2d bytes  %s\n", len(f), hex.EncodeToString(f))
	fmt.Println("                               ^^^^^^^^^^")
	fmt.Printf("                               | +-- 4-byte length 0x%08x = %d, big-endian\n", len(reqBytes), len(reqBytes))
	fmt.Println("                               +-- 1-byte compression flag (00 = none)")
	compressed, body := unframe(f)
	must(!compressed && len(f) == 5+len(reqBytes), "5-byte prefix")
	must(bytes.Equal(body, reqBytes), "gRPC carries the protobuf bytes verbatim")
	unframed := &l12.EchoRequest{}
	must(proto.Unmarshal(body, unframed) == nil && proto.Equal(unframed, request), "decode unframed")
	fmt.Println("  the framed payload is byte-for-byte the protobuf message you encoded.")
	fmt.Println("  gRPC then puts these frames in HTTP/2 DATA frames. That is the entire")
	fmt.Println("  relationship: protobuf decides what a message IS, gRPC moves it.")

	// Two messages back to back in one stream: the prefix is what lets the
	// receiver split them (a server-streaming RPC is exactly this).
	stream := append(frame(reqBytes), frame(respBytes)...)
	_, first := unframe(stream)
	_, second := unframe(stream[5+len(first):])
	got := &l12.EchoResponse{}
	must(proto.Unmarshal(second, got) == nil && got.GetLength() == 11, "second message in stream")
	fmt.Printf("  two frames in one %d-byte stream split cleanly: %q, then length=%d\n",
		len(stream), unframed.GetText(), got.GetLength())

	fmt.Println("\n== 4. what you already know, and what is next ==")
	fmt.Println("  ALREADY YOURS (levels 00-11), unchanged inside gRPC:")
	fmt.Println("    message definitions, field numbers, scalars, nested, repeated,")
	fmt.Println("    presence/optional, enums, oneof, schema evolution, codegen, interop")
	fmt.Println("  THE gRPC LAYER - see ../../../gRPC/Foundation, not re-taught here:")
	for _, item := range []string{
		"unary, server-streaming, client-streaming and bidirectional RPCs",
		"channels (grpc.NewClient), generated clients and server interfaces",
		"status codes, error details and deadlines",
		"interceptors (gRPC's middleware), metadata and auth",
		"HTTP/2 multiplexing, keepalive and load balancing",
	} {
		fmt.Println("    - " + item)
	}
	fmt.Println("  Every one of those moves MESSAGES around. None of them changes what")
	fmt.Println("  a message is. You already finished that part.")

	fmt.Println("\nOK")
}
