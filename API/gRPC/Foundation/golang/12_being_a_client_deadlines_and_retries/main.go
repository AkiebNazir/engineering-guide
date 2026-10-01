/*
FOUNDATION LEVEL 12 - Every service you write is also somebody's client
===========================================================================
Levels 00-11 were all SERVER code. But you spend at least as much real-world
time writing CLIENTS: code that calls someone else's service. This level flips
the lens - a small server plays "someone else's flaky service", and the
interesting code is the client calling it.

TWO THINGS EVERY gRPC CLIENT MUST DO

	1 SET A DEADLINE. Every single call. gRPC has no default timeout, so a call
	  with context.Background() can hang until the process dies. The deadline
	  becomes `grpc-timeout` metadata (level 07), which means the SERVER knows it
	  too and stops working the moment it passes - unlike REST, where a client
	  timeout leaves the server churning on work nobody will read.

	2 RETRY ONLY THE RETRYABLE. The status code (level 06) tells you which:
	  UNAVAILABLE and RESOURCE_EXHAUSTED are transient, INVALID_ARGUMENT and
	  NOT_FOUND will be exactly as wrong next time.

You will learn
  - exponential backoff: wait longer after each failure, so a struggling server
    is not hammered harder while it is already struggling
  - why the retry decision is a switch on `status.Code(err)`, never on a message
  - DEADLINE_EXCEEDED is the client's own clock firing, and it is the one status
    where "safe to retry" depends on whether the call is idempotent - the server
    may well have completed the work before you gave up
  - deadlines are ABSOLUTE and propagate: a context with 2s left passed to a
    downstream call gives that call 2s, not a fresh 2s - which is what stops a
    chain of five services from taking 5 x 2s
  - gRPC also has a built-in, config-driven retry policy (a JSON service config)
    for exactly this - hand-rolling it once first makes that config readable

Run it   go run ./gRPC/Foundation/golang/12_being_a_client_deadlines_and_retries
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"sync/atomic"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/flakypb"
)

// atomic because gRPC handlers run concurrently on many goroutines.
var attempts atomic.Int32

type flakyServer struct {
	flakypb.UnimplementedFlakyServer
}

// Fetch fails the first 2 calls with UNAVAILABLE, then succeeds. Simulates a
// real service warming up or briefly overloaded - not actually broken.
func (s *flakyServer) Fetch(ctx context.Context, req *flakypb.FetchRequest) (*flakypb.FetchResponse, error) {
	n := attempts.Add(1)
	if n <= 2 {
		return nil, status.Error(codes.Unavailable, "warming up, try again")
	}
	return &flakypb.FetchResponse{Status: "ready", Attempt: n}, nil
}

func (s *flakyServer) Slow(ctx context.Context, req *flakypb.SlowRequest) (*flakypb.SlowResponse, error) {
	// The server can SEE the client's deadline, because it travelled as
	// grpc-timeout metadata and became this context's deadline. A well-behaved
	// server checks it instead of doing work whose result cannot be delivered.
	if deadline, ok := ctx.Deadline(); ok {
		fmt.Printf("  [server] the client gave me %.2fs; this work needs 1.00s\n",
			time.Until(deadline).Seconds())
	}

	select {
	case <-time.After(1 * time.Second):
		return &flakypb.SlowResponse{Status: "finished"}, nil
	case <-ctx.Done():
		// The deadline passed (or the client cancelled). Stop immediately; the
		// response could never be delivered anyway.
		fmt.Println("  [server] deadline passed, abandoning the work")
		return nil, status.Error(codes.DeadlineExceeded, "took too long")
	}
}

// Only these two mean "the same request might work if you ask again".
func retryable(c codes.Code) bool {
	return c == codes.Unavailable || c == codes.ResourceExhausted
}

func fetchWithRetries(client flakypb.FlakyClient, maxAttempts int) (*flakypb.FetchResponse, error) {
	var lastErr error
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		// A deadline on EVERY call, including every retry. Note each retry gets
		// its own 1s here; a stricter client would budget ONE overall deadline
		// across all attempts so the total is bounded.
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		res, err := client.Fetch(ctx, &flakypb.FetchRequest{})
		cancel()
		if err == nil {
			return res, nil
		}
		lastErr = err

		code := status.Code(err)
		if !retryable(code) || attempt == maxAttempts {
			// Not retryable, or out of attempts: give up honestly and let the
			// caller see the real status.
			return nil, err
		}
		wait := time.Duration(50<<(attempt-1)) * time.Millisecond // 50ms, 100ms, 200ms, ...
		fmt.Printf("  attempt %d got %s, backing off %v before retrying\n", attempt, code, wait)
		time.Sleep(wait)
	}
	return nil, lastErr
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	flakypb.RegisterFlakyServer(srv, &flakyServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := flakypb.NewFlakyClient(conn)

	fmt.Println("== retrying a transient UNAVAILABLE with exponential backoff ==")
	res, err := fetchWithRetries(client, 5)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("final result -> status=%q on server attempt %d\n", res.GetStatus(), res.GetAttempt())
	if res.GetStatus() != "ready" || attempts.Load() != 3 {
		panic("FAILED: expected exactly 2 failures then 1 success")
	}

	fmt.Println("\n== a deadline the server cannot meet ==")
	started := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
	_, err = client.Slow(ctx, &flakypb.SlowRequest{})
	cancel()
	elapsed := time.Since(started)
	fmt.Printf("  client gave up after %.2fs -> %s\n", elapsed.Seconds(), status.Code(err))
	if status.Code(err) != codes.DeadlineExceeded {
		panic("FAILED")
	}
	// The client's own clock fired at ~0.3s; it did NOT wait the full 1.0s.
	if elapsed > 900*time.Millisecond {
		panic("FAILED")
	}

	// The server's handler goroutine for that abandoned call may still be
	// unwinding right now. Waiting here just keeps this demo's output in order;
	// it is also a real lesson: a client giving up does not instantly free the
	// server's resources.
	time.Sleep(200 * time.Millisecond)

	fmt.Println("\n== the same call with a deadline that fits ==")
	ctx, cancel = context.WithTimeout(context.Background(), 3*time.Second)
	slowRes, err := client.Slow(ctx, &flakypb.SlowRequest{})
	cancel()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  -> status=%q\n", slowRes.GetStatus())
	if slowRes.GetStatus() != "finished" {
		panic("FAILED")
	}

	fmt.Println("\n== never retry a non-retryable status ==")
	// Calling a method that does not exist is UNIMPLEMENTED - permanent. A retry
	// loop that ignored the code would burn 5 attempts to learn this.
	before := attempts.Load()
	ctx, cancel = context.WithTimeout(context.Background(), 1*time.Second)
	err = conn.Invoke(ctx, "/foundation.flaky.v1.Flaky/Nope",
		&flakypb.FetchRequest{}, &flakypb.FetchResponse{})
	cancel()
	fmt.Printf("  -> %s is permanent; retrying it would waste everyone's time\n", status.Code(err))
	if status.Code(err) != codes.Unimplemented || retryable(status.Code(err)) {
		panic("FAILED")
	}
	if attempts.Load() != before {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
