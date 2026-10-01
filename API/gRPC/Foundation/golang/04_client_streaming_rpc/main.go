/*
FOUNDATION LEVEL 04 - Client streaming: many requests, one response
=======================================================================
Level 03 put `stream` on the response. This level puts it on the REQUEST, and
everything mirrors: the client sends as many messages as it likes over one open
call, and the server replies exactly once, at the end.

	rpc UploadReadings(stream Reading) returns (UploadSummary);
	                   ^^^^^^ this side now

In REST you would either POST one giant array (and hold it all in memory on
both sides), or POST a thousand small requests (and pay a thousand round trips).
Client streaming is the third option: one call, a thousand messages, one answer.

WHAT CHANGES IN THE CODE

	server: the method takes ONLY a stream (there is no single request to look
	        at); it Recv()s until io.EOF, then calls SendAndClose once
	client: the call returns a stream you Send() into, then CloseAndRecv() to
	        half-close and read the single response

You will learn
  - io.EOF from the server's Recv means "the client half-closed", which is the
    signal to compute and send the one answer
  - SendAndClose is the server's only way to answer - calling it twice, or not
    at all, is a bug
  - the server folds numbers into a running total while the client is still
    sending, so neither side ever holds the whole batch
  - a natural fit for uploads, metrics, batch inserts and log shipping
  - the server can still fail the whole call with a status code (level 06) if one
    message in the middle of the stream is invalid

Run it   go run ./gRPC/Foundation/golang/04_client_streaming_rpc
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

	"dsapractice/api/gRPC/Foundation/golang/pb/uploadpb"
)

type uploaderServer struct {
	uploadpb.UnimplementedUploaderServer
}

// Note the signature: only a stream, and no response return value - the
// response goes out through SendAndClose instead.
func (s *uploaderServer) UploadReadings(stream grpc.ClientStreamingServer[uploadpb.Reading, uploadpb.UploadSummary]) error {
	var count int32
	var total float64

	for {
		reading, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			// The client half-closed: it will send nothing more. THIS is the
			// moment to answer, and the only moment.
			fmt.Printf("  [server] client half-closed after %d messages, answering once\n", count)
			average := 0.0
			if count > 0 {
				average = total / float64(count)
			}
			return stream.SendAndClose(&uploadpb.UploadSummary{
				Count: count, Sum: total, Average: average,
			})
		}
		if err != nil {
			return err // a real failure mid-stream
		}
		fmt.Printf("  [server] received sensor=%q value=%v\n", reading.GetSensor(), reading.GetValue())
		count++
		total += reading.GetValue()
		// Everything we need is in `count` and `total` - the reading itself is
		// already garbage. That is the memory win.
	}
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	uploadpb.RegisterUploaderServer(srv, &uploaderServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := uploadpb.NewUploaderClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// --- a stream of four readings ---
	stream, err := client.UploadReadings(ctx)
	if err != nil {
		log.Fatal(err)
	}
	readings := []struct {
		sensor string
		value  float64
	}{
		{"temp-a", 20.5}, {"temp-a", 21.0}, {"temp-b", 19.0}, {"temp-b", 23.5},
	}
	for _, r := range readings {
		fmt.Printf("  [client] sending sensor=%q value=%v\n", r.sensor, r.value)
		if err := stream.Send(&uploadpb.Reading{Sensor: r.sensor, Value: r.value}); err != nil {
			log.Fatal(err)
		}
	}

	// CloseAndRecv does two things: half-closes our side (which is what makes
	// the server's Recv return io.EOF) and waits for the single response.
	summary, err := stream.CloseAndRecv()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\nsummary  : count=%d sum=%v average=%v\n",
		summary.GetCount(), summary.GetSum(), summary.GetAverage())
	if summary.GetCount() != 4 || summary.GetSum() != 84.0 || summary.GetAverage() != 21.0 {
		panic("FAILED")
	}

	// --- sending nothing at all is legal: zero messages, then half-close ---
	stream, err = client.UploadReadings(ctx)
	if err != nil {
		log.Fatal(err)
	}
	summary, err = stream.CloseAndRecv()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("empty    : count=%d average=%v   (an empty stream is valid)\n",
		summary.GetCount(), summary.GetAverage())
	if summary.GetCount() != 0 || summary.GetAverage() != 0 {
		panic("FAILED")
	}

	fmt.Println("OK")
}
