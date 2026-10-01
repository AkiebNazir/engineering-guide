/*
FOUNDATION LEVEL 03 - Server streaming: one request, many responses
=======================================================================
Levels 00-02 were unary: one message each way. Adding the word `stream` to the
RETURN type in the .proto changes the shape of both the server method and the
client call - and nothing else. This is gRPC's first genuinely new capability
over plain REST, where you would reach for polling, pagination, chunked
transfer encoding, or Server-Sent Events to get the same effect.

	rpc Countdown(CountdownRequest) returns (stream Tick);
	                                        ^^^^^^ this one word

WHAT CHANGES IN THE CODE

	server: the method loses its return value and gains a STREAM parameter with
	        a Send method; it returns only an error, when it is done
	client: the call returns a stream with a Recv method; each Recv is one
	        message arriving, and io.EOF means "the server finished cleanly"

You will learn
  - stream.Send(msg) puts one message on the wire immediately - it does not
    buffer until the handler returns
  - the client processes message 1 while the server is still producing message 5;
    that is the point, and it is why this is not just "return a slice"
  - io.EOF from Recv is the NORMAL end of a stream, not an error - any other
    error is a real failure, and its status code says why
  - memory: a stream of a million rows never exists in RAM all at once on either
    side, unlike one response holding a million-element repeated field
  - a client that stops early cancels the call, and `stream.Context().Err()`
    on the server is how the handler notices and stops working

Run it   go run ./gRPC/Foundation/golang/03_server_streaming_rpc
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/tickerpb"
)

type tickerServer struct {
	tickerpb.UnimplementedTickerServer
}

// Note the signature: no response return value, and a stream parameter instead.
// protoc-gen-go-grpc generated the Ticker_CountdownServer interface for this.
func (s *tickerServer) Countdown(req *tickerpb.CountdownRequest, stream grpc.ServerStreamingServer[tickerpb.Tick]) error {
	for value := req.GetStart(); value > 0; value-- {
		// A client that hung up (or timed out) cancels the stream's context.
		// Checking it is how you avoid computing 10,000 more rows nobody reads.
		if err := stream.Context().Err(); err != nil {
			fmt.Printf("  [server] client went away at value=%d, stopping early\n", value)
			return status.Error(codes.Canceled, "client cancelled")
		}
		fmt.Printf("  [server] sending value=%d\n", value)
		// Send puts THIS message on the wire right now.
		if err := stream.Send(&tickerpb.Tick{Value: value, Last: value == 1}); err != nil {
			return err // the client is gone; stop
		}
		time.Sleep(10 * time.Millisecond) // stand-in for real work per item
	}
	// Returning nil ends the stream with status OK, sent as HTTP/2 trailers.
	return nil
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	tickerpb.RegisterTickerServer(srv, &tickerServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := tickerpb.NewTickerClient(conn)

	// --- read the whole stream ---
	// The call returns IMMEDIATELY with a stream handle; nothing has been
	// received yet. The server is producing while we are consuming.
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	stream, err := client.Countdown(ctx, &tickerpb.CountdownRequest{Start: 4})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("client got a stream handle back - the server is still working")

	var received []int32
	for {
		tick, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			// The NORMAL end of a server stream. Not a failure.
			break
		}
		if err != nil {
			log.Fatal(err) // any other error IS a failure; status.Code(err) says why
		}
		fmt.Printf("  [client] received value=%d last=%v\n", tick.GetValue(), tick.GetLast())
		received = append(received, tick.GetValue())
	}
	fmt.Printf("stream finished cleanly (io.EOF), got %v\n", received)
	if len(received) != 4 || received[0] != 4 || received[3] != 1 {
		panic("FAILED")
	}

	// --- stopping early cancels the call ---
	fmt.Println("\nnow abandoning a stream after one message:")
	ctx2, cancel2 := context.WithTimeout(context.Background(), 2*time.Second)
	stream, err = client.Countdown(ctx2, &tickerpb.CountdownRequest{Start: 100})
	if err != nil {
		log.Fatal(err)
	}
	first, err := stream.Recv()
	if err != nil || first.GetValue() != 100 {
		panic("FAILED")
	}
	cancel2() // in Go, cancelling the CONTEXT is how a client hangs up
	time.Sleep(50 * time.Millisecond)
	_, err = stream.Recv()
	fmt.Printf("  [client] further reads -> %s\n", status.Code(err))
	if status.Code(err) != codes.Canceled {
		panic("FAILED")
	}

	fmt.Println("OK")
}
