/*
FOUNDATION LEVEL 07 - Metadata: gRPC's headers
==================================================
Everything so far travelled inside the protobuf messages, which are governed by
the .proto contract. METADATA is the other channel: untyped key/value string
pairs that ride ALONGSIDE the messages, in both directions. It is literally
HTTP/2 headers, and it is exactly what HTTP headers are for in REST.

WHAT GOES IN METADATA, AND WHAT DOES NOT

	metadata (cross-cutting, about the CALL)   messages (the DATA of the call)
	----------------------------------------   -------------------------------
	authorization / api keys (levels 09-10)    the order being placed
	x-request-id for tracing                   the user's name
	user-agent, accept-encoding                the search filters
	grpc-timeout (set for you by the context)  anything a client legitimately
	the grpc-status trailer itself               needs to see in the contract

	Rule of thumb: if changing it would change the ANSWER, it is a message field.
	If it is about plumbing - who, when, trace, retry - it is metadata. Notice
	../../proto/metaecho.proto has no request_id field anywhere.

THREE PLACES METADATA APPEARS (this is the bit people miss)

	1 REQUEST metadata  - client -> server, sent before the request message
	2 INITIAL metadata  - server -> client, sent BEFORE the response message
	3 TRAILING metadata - server -> client, sent AFTER it, with the status

	Trailers are the interesting one: HTTP/1.1 cannot really do them, so REST has
	no equivalent. They let a server report something it only learns at the END
	of a call - rows scanned, cache hit, time spent - even mid-stream.

You will learn
  - metadata keys are always lower-cased, and a key may legally repeat, which is
    why `metadata.MD` is a `map[string][]string` and not a `map[string]string`
  - the client SENDS with metadata.NewOutgoingContext, and READS with the
    grpc.Header / grpc.Trailer call options
  - `metadata.FromIncomingContext(ctx)` and `grpc.SendHeader` /
    `grpc.SetTrailer` are the three server-side halves
  - grpc.SetTrailer works even when the handler then returns an ERROR, which is
    how you attach debug info to a failure
  - never put a secret in metadata over an insecure channel - it is plaintext
    (this is exactly why levels 09-10 say "use TLS in production")

Run it   go run ./gRPC/Foundation/golang/07_metadata_headers_and_trailers
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"strconv"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/metaechopb"
)

type metaEchoServer struct {
	metaechopb.UnimplementedMetaEchoServer
}

func (s *metaEchoServer) Echo(ctx context.Context, req *metaechopb.EchoRequest) (*metaechopb.EchoResponse, error) {
	// 1. READ request metadata off the context. MD is map[string][]string
	//    because a key may repeat.
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Error(codes.Internal, "no metadata on the context")
	}
	fmt.Println("  [server] request metadata the client sent:")
	for key, values := range md {
		fmt.Printf("             %s = %v\n", key, values)
	}

	requestID := "none"
	if v := md.Get("x-request-id"); len(v) > 0 {
		requestID = v[0] // .Get returns a slice; take the first
	}

	// gRPC itself adds metadata you never set. `grpc-timeout` is how the
	// client's context deadline reaches the server, so the server knows the
	// deadline too and can give up at the same moment (level 12).
	if len(md.Get("user-agent")) == 0 {
		return nil, status.Error(codes.Internal, "expected a user-agent")
	}

	// 2. SEND initial metadata - goes out BEFORE the response message. Once
	//    sent it cannot be changed, so this is for things known up front.
	if err := grpc.SendHeader(ctx, metadata.Pairs("x-served-by", "metaecho-1")); err != nil {
		return nil, err
	}

	started := time.Now()
	text := strings.ToUpper(req.GetText())
	elapsedMicros := time.Since(started).Microseconds()

	// 3. SET trailing metadata - goes out AFTER the response, with the status.
	//    This is why it can carry something only knowable at the end.
	tenants := md.Get("x-tenant")
	if err := grpc.SetTrailer(ctx, metadata.Pairs(
		"x-request-id", requestID, // echo the caller's trace id back
		"x-handler-micros", strconv.FormatInt(elapsedMicros, 10), // not knowable before the work
		"x-tenants-seen", strconv.Itoa(len(tenants)), // proof duplicate keys survive
	)); err != nil {
		return nil, err
	}

	return &metaechopb.EchoResponse{Text: text, SawRequestId: requestID}, nil
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	metaechopb.RegisterMetaEchoServer(srv, &metaEchoServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := metaechopb.NewMetaEchoClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// SENDING metadata: attach it to the context, not to the request message.
	// metadata.Pairs takes alternating key, value - and repeating a key is legal.
	outCtx := metadata.NewOutgoingContext(ctx, metadata.Pairs(
		"x-request-id", "req-42",
		"x-tenant", "acme",
		"x-tenant", "acme-eu", // legal: keys may repeat
	))

	// READING metadata: pass grpc.Header(&h) / grpc.Trailer(&t) call options and
	// gRPC fills them in. There is no other way to see them on a unary call.
	var header, trailer metadata.MD
	res, err := client.Echo(outCtx, &metaechopb.EchoRequest{Text: "hello"},
		grpc.Header(&header), grpc.Trailer(&trailer))
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("\nresponse message      : text=%q\n", res.GetText())
	fmt.Printf("initial  metadata     : x-served-by=%v\n", header.Get("x-served-by"))
	fmt.Printf("trailing metadata     : x-request-id=%v x-handler-micros=%v x-tenants-seen=%v\n",
		trailer.Get("x-request-id"), trailer.Get("x-handler-micros"), trailer.Get("x-tenants-seen"))
	fmt.Printf("final status          : %s\n", status.Code(err))

	if res.GetText() != "HELLO" {
		panic("FAILED")
	}
	// The server knew our trace id even though NO message field carried it.
	if res.GetSawRequestId() != "req-42" {
		panic("FAILED")
	}
	if len(header.Get("x-served-by")) == 0 || header.Get("x-served-by")[0] != "metaecho-1" {
		panic("FAILED")
	}
	if len(trailer.Get("x-request-id")) == 0 || trailer.Get("x-request-id")[0] != "req-42" {
		panic("FAILED")
	}
	if len(trailer.Get("x-handler-micros")) == 0 {
		panic("FAILED")
	}

	// We sent x-tenant TWICE, and the server received both, because metadata.MD
	// is a map to a SLICE of values - not a plain map[string]string.
	fmt.Printf("\nx-tenant was sent twice; the server counted %v values\n", trailer.Get("x-tenants-seen"))
	if trailer.Get("x-tenants-seen")[0] != "2" {
		panic("FAILED")
	}

	// --- sending no metadata at all is also fine ---
	res, err = client.Echo(ctx, &metaechopb.EchoRequest{Text: "bare"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\ncalling with no metadata: saw_request_id=%q\n", res.GetSawRequestId())
	if res.GetSawRequestId() != "none" {
		panic("FAILED")
	}

	fmt.Println("OK")
}
