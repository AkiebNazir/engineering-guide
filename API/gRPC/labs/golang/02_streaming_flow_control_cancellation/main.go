/*
LAB 02 (basic) - Streaming in Go: back-pressure, cancellation, and the io.EOF trap
==================================================================================
You will learn
  - server streaming:   the handler calls stream.Send(msg) in a loop; return nil to finish
  - client streaming:   the handler calls stream.Recv() until io.EOF, then SendAndClose(reply)
  - bidirectional:      Recv and Send are independent; use ONE goroutine per direction
    (never two goroutines calling Send on the same stream)
  - BACK-PRESSURE:      HTTP/2 flow control means a slow client makes the server's Send() BLOCK.
    The server cannot flood memory. You will measure this.
  - CANCELLATION:       when the client cancels its context, stream.Context().Done() fires on the
    server - a well-behaved handler stops working immediately
  - THE io.EOF TRAP:    if the server ends a client stream early with an error, the client's Send
    returns plain io.EOF (not the real error). You must call CloseAndRecv (or
    RecvMsg) to fetch the actual status.

Run it   go run ./gRPC/labs/golang/02_streaming_flow_control_cancellation
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/labs/golang/shoppb"
)

type server struct {
	shoppb.UnimplementedCatalogServer
	sent      atomic.Int64 // Sends that COMPLETED (i.e. the transport accepted them)
	stoppedAt atomic.Int64 // how many we had sent when the client cancelled
	cancelled chan struct{}
	once      sync.Once
}

// markStopped records that the handler noticed the client leaving.
func (s *server) markStopped() {
	s.once.Do(func() { s.stoppedAt.Store(s.sent.Load()); close(s.cancelled) })
}

// Server streaming. Big messages so flow control kicks in quickly.
func (s *server) ListProducts(req *shoppb.ListProductsRequest, stream shoppb.Catalog_ListProductsServer) error {
	blob := strings.Repeat("x", 32*1024)
	for i := int64(1); i <= int64(req.GetLimit()); i++ {
		select {
		case <-stream.Context().Done(): // client cancelled or deadline hit: stop, do not keep working
			s.markStopped()
			return status.FromContextError(stream.Context().Err()).Err()
		default:
		}
		if err := stream.Send(&shoppb.Product{Id: i, Name: blob}); err != nil { // BLOCKS when the client is slow;
			s.markStopped() // ... and fails as soon as the client cancels
			return err
		}
		s.sent.Add(1)
	}
	return nil
}

// Client streaming, rejecting bad data early.
func (s *server) UploadMetrics(stream shoppb.Catalog_UploadMetricsServer) error {
	var n int32
	var sum float64
	for {
		m, err := stream.Recv()
		if err == io.EOF { // the client called CloseSend: normal end of input
			return stream.SendAndClose(&shoppb.UploadSummary{Count: n, Sum: sum, Avg: sum / float64(max(n, 1))})
		}
		if err != nil {
			return err
		}
		if m.GetValue() < 0 {
			return status.Errorf(codes.InvalidArgument, "metric %q has negative value after %d good ones", m.GetName(), n)
		}
		n++
		sum += m.GetValue()
	}
}

// Bidirectional: reply to every message in order.
func (s *server) Chat(stream shoppb.Catalog_ChatServer) error {
	for {
		in, err := stream.Recv()
		if err == io.EOF {
			return nil // client closed its side; returning nil closes ours
		}
		if err != nil {
			return err
		}
		if err := stream.Send(&shoppb.ChatMessage{From: "bot", Text: "echo: " + strings.ToUpper(in.GetText())}); err != nil {
			return err
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	lis, _ := net.Listen("tcp", "127.0.0.1:0")
	srv := &server{cancelled: make(chan struct{})}
	s := grpc.NewServer()
	shoppb.RegisterCatalogServer(s, srv)
	go s.Serve(lis)
	defer s.Stop()
	conn, err := grpc.NewClient(lis.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := shoppb.NewCatalogClient(conn)

	fmt.Println("== 1. back-pressure: a SLOW client vs a server that wants to send 200 x 32KB ==")
	ctx, cancel := context.WithCancel(context.Background())
	stream, err := client.ListProducts(ctx, &shoppb.ListProductsRequest{Limit: 200})
	must(err == nil, "open stream")
	received := 0
	for received < 5 {
		if _, err := stream.Recv(); err != nil {
			log.Fatal(err)
		}
		received++
		time.Sleep(60 * time.Millisecond) // slow consumer
	}
	sentNow := srv.sent.Load()
	fmt.Printf("  client has read %d messages; server has completed %d Sends of 200\n", received, sentNow)
	fmt.Printf("  => the server is only %d messages AHEAD: HTTP/2 flow control stopped it (a fast server\n", sentNow-int64(received))
	fmt.Println("     could otherwise have buffered all 6.4 MB in memory for every slow client)")
	must(sentNow < 60, "server was throttled by the slow client")

	fmt.Println("\n== 2. cancellation: the client walks away ==")
	cancel()
	select {
	case <-srv.cancelled:
		fmt.Printf("  server noticed within ms and stopped at %d sent (not 200)\n", srv.stoppedAt.Load())
	case <-time.After(2 * time.Second):
		panic("FAILED: server did not notice the cancellation")
	}
	buffered := 0
	for { // messages already delivered to the client's buffer may still be readable; then the error appears
		if _, err = stream.Recv(); err != nil {
			break
		}
		buffered++
	}
	fmt.Printf("  client drained %d already-buffered messages, then Recv -> %s\n", buffered, status.Code(err))
	must(status.Code(err) == codes.Canceled, "client sees Canceled")

	fmt.Println("\n== 3. client streaming: 1000 metrics, one reply ==")
	up, _ := client.UploadMetrics(context.Background())
	for i := 1; i <= 1000; i++ {
		must(up.Send(&shoppb.Metric{Name: "latency", Value: float64(i)}) == nil, "send")
	}
	sum, err := up.CloseAndRecv() // half-close + wait for the single response
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  count=%d sum=%.0f avg=%.1f\n", sum.Count, sum.Sum, sum.Avg)
	must(sum.Count == 1000 && sum.Sum == 500500, "summary")

	fmt.Println("\n== 4. the io.EOF trap: the server rejects the stream early ==")
	up, _ = client.UploadMetrics(context.Background())
	var sendErr error
	sent := 0
	for i := 0; i < 100000 && sendErr == nil; i++ {
		v := 1.0
		if i == 3 {
			v = -1 // poison
		}
		sendErr = up.Send(&shoppb.Metric{Name: "m", Value: v})
		sent++
	}
	fmt.Printf("  client Send loop stopped after %d sends with error: %v\n", sent, sendErr)
	must(errors.Is(sendErr, io.EOF), "Send reports plain io.EOF")
	_, realErr := up.CloseAndRecv() // <- THIS returns the real status
	fmt.Printf("  real error from CloseAndRecv: code=%s msg=%q\n", status.Code(realErr), status.Convert(realErr).Message())
	must(status.Code(realErr) == codes.InvalidArgument, "real status")

	fmt.Println("\n== 5. bidirectional: one goroutine sends, another receives ==")
	chat, _ := client.Chat(context.Background())
	var wg sync.WaitGroup
	var replies []string
	wg.Add(1)
	go func() { // receiver
		defer wg.Done()
		for {
			m, err := chat.Recv()
			if err != nil { // io.EOF once the server finishes
				return
			}
			replies = append(replies, m.GetText())
		}
	}()
	for _, t := range []string{"hello", "how are you", "bye"} { // sender (this goroutine)
		chat.Send(&shoppb.ChatMessage{From: "me", Text: t})
	}
	chat.CloseSend() // "I have nothing more to say"
	wg.Wait()
	fmt.Println("  replies:", replies)
	must(strings.Join(replies, "|") == "echo: HELLO|echo: HOW ARE YOU|echo: BYE", "ordered echoes")
	fmt.Println("\nOK")
}
