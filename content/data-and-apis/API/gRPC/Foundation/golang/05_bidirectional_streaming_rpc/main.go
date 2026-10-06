/*
FOUNDATION LEVEL 05 - Bidirectional streaming: both sides stream at once
============================================================================
`stream` on BOTH sides. This is the fourth and last RPC shape, and it is not
"client streaming plus server streaming" - it is genuinely different, because
the two directions are INDEPENDENT. Neither side has to wait for the other.

	rpc Talk(stream ChatMessage) returns (stream ChatMessage);
	         ^^^^^^                       ^^^^^^ both

The four shapes, complete:

	unary              one  -> one    levels 00-02
	server streaming   one  -> many   level 03
	client streaming   many -> one    level 04
	bidirectional      many -> many   this level

This is the closest gRPC gets to a WebSocket (see ../../../WebSockets/Foundation),
with one advantage: every message is still a typed, contract-checked protobuf
message, not an untyped text frame you parse yourself.

You will learn
  - the server method Recv()s and Send()s on the SAME stream, in any order it likes
  - "independent" means the server may Send 5 messages before reading any, or
    read 5 before sending any; the pattern is yours to choose, not gRPC's
  - the Go client usually reads in a separate goroutine, because Recv blocks -
    this is the one place gRPC's Go API needs concurrency to be useful
  - the call is over when BOTH directions close: the client CloseSend()s, then
    the server handler returns, which sends the final status
  - ordering is guaranteed WITHIN each direction, and there is no ordering
    relationship at all BETWEEN the two directions

Run it   go run ./gRPC/Foundation/golang/05_bidirectional_streaming_rpc
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
	"google.golang.org/grpc/credentials/insecure"

	"dsapractice/api/gRPC/Foundation/golang/pb/chatpb"
)

type chatServer struct {
	chatpb.UnimplementedChatServer
}

func (s *chatServer) Talk(stream grpc.BidiStreamingServer[chatpb.ChatMessage, chatpb.ChatMessage]) error {
	// First, one unsolicited message BEFORE reading anything. A unary or
	// client-streaming RPC could not do this - proof the directions are
	// independent rather than strictly alternating.
	fmt.Println("  [server] sending a greeting before reading a single message")
	if err := stream.Send(&chatpb.ChatMessage{Sender: "server", Text: "welcome"}); err != nil {
		return err
	}

	for {
		msg, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			return nil // the client half-closed; end with OK
		}
		if err != nil {
			return err
		}
		fmt.Printf("  [server] read %q from %q\n", msg.GetText(), msg.GetSender())

		if msg.GetText() == "bye" {
			// Answer and then stop reading: the server may end its side of the
			// conversation whenever it likes.
			if err := stream.Send(&chatpb.ChatMessage{Sender: "server", Text: "goodbye"}); err != nil {
				return err
			}
			return nil
		}
		reply := fmt.Sprintf("you said %q", msg.GetText())
		if err := stream.Send(&chatpb.ChatMessage{Sender: "server", Text: reply}); err != nil {
			return err
		}
	}
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	chatpb.RegisterChatServer(srv, &chatServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := chatpb.NewChatClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	stream, err := client.Talk(ctx)
	if err != nil {
		log.Fatal(err)
	}

	// Recv BLOCKS, so reading has to happen in its own goroutine while the main
	// goroutine sends. This is the standard Go bidi shape, and it is why this
	// level is the first one that needs a channel.
	var received []string
	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			msg, err := stream.Recv()
			if errors.Is(err, io.EOF) {
				return
			}
			if err != nil {
				log.Print(err)
				return
			}
			fmt.Printf("  [client] read %q from %q\n", msg.GetText(), msg.GetSender())
			received = append(received, msg.GetText())
		}
	}()

	for _, text := range []string{"hello", "how are you", "bye"} {
		fmt.Printf("  [client] sending %q\n", text)
		if err := stream.Send(&chatpb.ChatMessage{Sender: "client", Text: text}); err != nil {
			log.Fatal(err)
		}
		time.Sleep(20 * time.Millisecond) // just to keep this demo's output readable
	}
	// CloseSend half-closes OUR direction. The server's direction stays open
	// until its handler returns - the two are independent.
	if err := stream.CloseSend(); err != nil {
		log.Fatal(err)
	}
	<-done

	fmt.Printf("\nserver sent %d messages: %v\n", len(received), received)
	// "welcome" arrived before we sent anything, then one reply per message.
	if len(received) != 4 || received[0] != "welcome" || received[3] != "goodbye" {
		panic("FAILED")
	}
	if received[1] != `you said "hello"` {
		panic("FAILED")
	}

	fmt.Println("OK")
}
