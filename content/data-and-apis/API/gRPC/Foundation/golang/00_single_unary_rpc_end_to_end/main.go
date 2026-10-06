/*
FOUNDATION LEVEL 00 (start here) - A basic gRPC endpoint, explained end to end
==================================================================================
If someone says "build me a basic gRPC endpoint", THIS is what they mean: one
`.proto` file describing one function, generated code, a server that implements
that function, and a client that calls it. Nothing about streaming, metadata, or
interceptors yet - just enough to see the whole call happen once.

THE MENTAL MODEL (read this before the code)

	gRPC is REST's request/response idea with ONE big swap. In REST you agree on a
	convention - "GET /ping returns text, POST /orders takes this JSON shape" - and
	both sides hand-write code that hopes the other side kept the bargain. In gRPC
	you write that agreement down in a machine-readable file (`../../proto/ping.proto`)
	and a compiler (`protoc`) GENERATES the client and server types from it. So:

	  REST                              gRPC
	  ------------------------------    ------------------------------------------
	  URL + verb picks the operation    the method name picks it: /Greeter/Ping
	  JSON body, parsed at runtime      protobuf bytes, typed at compile time
	  docs/OpenAPI describe the shape   the .proto file IS the shape, enforced
	  HTTP/1.1 text, one req per conn   HTTP/2 binary, many calls multiplexed
	  404/400/500                       status codes: NOT_FOUND/INVALID_ARGUMENT...

	What is IDENTICAL: a server listens on a port; a client opens a connection,
	sends one message, gets one message back. Everything in levels 01-12 is one
	more piece bolted onto that loop.

You will learn
  - the four-step gRPC recipe: write .proto -> run the generator -> implement the
    server interface -> call the client stub (no step where you parse anything)
  - what the generated `pingpb` package gives you: message structs, a
    `GreeterServer` interface, `UnimplementedGreeterServer`, and `NewGreeterClient`
  - why you embed `UnimplementedGreeterServer`: forward compatibility, so adding
    an RPC to the .proto later does not break this build
  - what a ClientConn is: one long-lived HTTP/2 connection you create once and reuse
  - that calling a method the server never implemented is a normal, handled
    outcome (status UNIMPLEMENTED), not a crash - gRPC's equivalent of REST's 404

Run it        go run ./gRPC/Foundation/golang/00_single_unary_rpc_end_to_end
Keep serving  go run ./gRPC/Foundation/golang/00_single_unary_rpc_end_to_end --serve   (127.0.0.1:50051)
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	// This package is GENERATED - you never edit it. `../../generate.sh` made it
	// from ../../proto/ping.proto. Level 13 shows what is inside it.
	"dsapractice/api/gRPC/Foundation/golang/pb/pingpb"
)

// THE SERVER. Embedding UnimplementedGreeterServer is how you promise "I
// implement the Greeter service" while staying forward compatible: if someone
// adds an RPC to ping.proto and regenerates, this struct still satisfies the
// interface (the new RPC just returns UNIMPLEMENTED until you write it).
type greeterServer struct {
	pingpb.UnimplementedGreeterServer
}

// One method per `rpc` line in the .proto, named exactly as the .proto named it.
func (s *greeterServer) Ping(ctx context.Context, req *pingpb.PingRequest) (*pingpb.PongResponse, error) {
	// `req` is already a fully parsed, typed *PingRequest. gRPC read the bytes
	// off the socket and decoded them before calling this - there is no "parse
	// the body" step, and no way to misspell a field without the compiler saying so.
	fmt.Printf("  [server] Ping arrived with name=%q\n", req.GetName())

	// Always use the generated GetX() accessors rather than req.Name directly:
	// they are nil-safe, so a nil message reads as the zero value instead of panicking.

	// `ctx` is the per-call handle: deadlines, metadata (level 07) and
	// cancellation all live on it. Unused at this level.
	return &pingpb.PongResponse{Message: "pong, " + req.GetName()}, nil
}

func startServer(addr string) (*grpc.Server, net.Listener) {
	// "127.0.0.1:0" = "operating system, hand me any free port", so this demo
	// never collides with something already listening on your machine.
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatal(err)
	}

	srv := grpc.NewServer()
	// The generated Register... helper is what wires the wire path
	// "/foundation.ping.v1.Greeter/Ping" to our Go method above.
	pingpb.RegisterGreeterServer(srv, &greeterServer{})
	go srv.Serve(ln)
	return srv, ln
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--serve" {
		srv, ln := startServer("127.0.0.1:50051")
		fmt.Printf("listening on %s  (gRPC is binary - curl will not help; use grpcurl)\n", ln.Addr())
		defer srv.Stop()
		select {} // block forever
	}

	srv, ln := startServer("127.0.0.1:0")
	defer srv.Stop()

	// THE CLIENT. A ClientConn is a managed HTTP/2 connection to one target.
	// Create it ONCE and reuse it for every call - it is not per-request.
	// (grpc.Dial is deprecated; NewClient connects lazily on the first RPC.)
	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	client := pingpb.NewGreeterClient(conn) // the generated typed client

	// ALWAYS call with a context that has a deadline. gRPC has no default
	// timeout, so a call without one can hang until the process dies (level 12).
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// This one line is the whole request/response loop: serialise the request,
	// send HEADERS + DATA over HTTP/2, wait, read DATA + TRAILERS, deserialise
	// the response. It looks like a function call on purpose.
	res, err := client.Ping(ctx, &pingpb.PingRequest{Name: "world"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("request  : /foundation.ping.v1.Greeter/Ping  name=\"world\"")
	fmt.Printf("response : message=%q\n", res.GetMessage())
	if res.GetMessage() != "pong, world" {
		panic("FAILED")
	}

	// Ask for a method this server does not implement. gRPC answers with the
	// status UNIMPLEMENTED - the direct analogue of REST's 404, and just as
	// normal an outcome. conn.Invoke calls a raw method path by hand.
	err = conn.Invoke(ctx, "/foundation.ping.v1.Greeter/DoesNotExist",
		&pingpb.PingRequest{Name: "world"}, &pingpb.PongResponse{})
	fmt.Println("request  : /foundation.ping.v1.Greeter/DoesNotExist")
	// status.Code(err) is how you read a gRPC status in Go. It returns
	// codes.OK for a nil error, so it is always safe to call.
	fmt.Printf("response : %s   (a method this server never agreed to answer - not a crash)\n", status.Code(err))
	if status.Code(err) != codes.Unimplemented {
		panic("FAILED")
	}

	fmt.Println("OK")
}
