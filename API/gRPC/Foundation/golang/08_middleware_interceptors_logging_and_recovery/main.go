/*
FOUNDATION LEVEL 08 - Middleware, which gRPC calls INTERCEPTORS
===================================================================
Levels 00-07 put everything a call needed inside one handler method. An
INTERCEPTOR is gRPC's name for middleware: a function that wraps every RPC and
gets to run code before and/or after the real handler, without touching the
handler's code at all. Logging, panic recovery, authentication (level 09),
authorization (level 10), tracing, and rate limiting are all just interceptors.

"Interceptor" is the real, named mechanism - not a vague framework concept. Do
not go looking for "gRPC middleware" in the docs; the word is interceptor.

THE GO SHAPE, WHICH IS ALMOST IDENTICAL TO REST MIDDLEWARE

	func(ctx, req any, info *grpc.UnaryServerInfo, next grpc.UnaryHandler) (any, error)

	`next` is the rest of the chain, ending in your real handler. Call it and you
	get the response; do not call it and you have short-circuited the whole call,
	which is exactly what levels 09-10 do on a failed credential check. Compare
	REST's `func(next http.Handler) http.Handler` - same idea, one signature.

You will learn
  - an interceptor sees the request on the way IN and the response or error on
    the way OUT, because `next` is a plain function call in the middle
  - chaining with grpc.ChainUnaryInterceptor: the list order is OUTSIDE-IN, so
    the first interceptor wraps the second, which wraps your handler
  - ORDER MATTERS, and this file proves it: recovery placed INSIDE logging means
    the log line still happens on a panic; swap them and the log line vanishes
  - recovering from a panic in ONE handler so the server stays up and that one
    call becomes a clean INTERNAL status - Go needs this MORE than Python,
    because an unrecovered panic in a handler goroutine kills the process
  - `info.FullMethod` is the full method path
    ("/foundation.interceptor.v1.Work/Do"), which is how levels 09-10 protect
    some RPCs and not others

Run it   go run ./gRPC/Foundation/golang/08_middleware_interceptors_logging_and_recovery
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/interceptorpb"
)

var callLog []string

// ---- the "real" application logic, with zero knowledge of logging/recovery ----
type workServer struct {
	interceptorpb.UnimplementedWorkServer
}

func (s *workServer) Do(ctx context.Context, req *interceptorpb.DoRequest) (*interceptorpb.DoResponse, error) {
	if req.GetTask() == "boom" {
		panic("simulated bug in a handler") // on purpose, to prove recovery works
	}
	return &interceptorpb.DoResponse{Result: "did " + req.GetTask()}, nil
}

// ---- interceptor #1: logs the method, outcome, and how long it took ----
func loggingInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	start := time.Now()
	res, err := next(ctx, req) // `next` is the rest of the chain
	outcome := "OK"
	if err != nil {
		// We do NOT swallow it - logging's job is to log. Recovery is a
		// separate interceptor with a separate job.
		outcome = status.Code(err).String()
	}
	line := fmt.Sprintf("%s -> %s (%.2fms)", info.FullMethod, outcome,
		float64(time.Since(start).Microseconds())/1000)
	callLog = append(callLog, line)
	fmt.Printf("  [log] %s\n", line)
	return res, err
}

// ---- interceptor #2: turns ANY panic into a clean INTERNAL status ----
func recoveryInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (res any, err error) {

	// A NAMED return value is required: the deferred function has to be able to
	// replace `err` after the panic has already unwound past the return.
	defer func() {
		if p := recover(); p != nil {
			fmt.Printf("  [recovery] caught %v - server stays up, this ONE call becomes INTERNAL\n", p)
			// Without this, an unrecovered panic in a handler goroutine takes
			// the WHOLE PROCESS down - every other in-flight call with it.
			// Note the message: the panic text never reaches the caller.
			res, err = nil, status.Error(codes.Internal, "internal error")
		}
	}()
	return next(ctx, req)
}

func main() {
	// Outside-in: loggingInterceptor wraps recoveryInterceptor wraps the handler.
	srv := grpc.NewServer(grpc.ChainUnaryInterceptor(
		loggingInterceptor,
		recoveryInterceptor,
	))
	interceptorpb.RegisterWorkServer(srv, &workServer{})

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := interceptorpb.NewWorkClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	res, err := client.Do(ctx, &interceptorpb.DoRequest{Task: "ok"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Do(task=\"ok\")    -> %q\n", res.GetResult())
	if res.GetResult() != "did ok" {
		panic("FAILED")
	}

	_, err = client.Do(ctx, &interceptorpb.DoRequest{Task: "boom"})
	msg := status.Convert(err).Message()
	fmt.Printf("Do(task=\"boom\")  -> %s %q   (the handler panicked; recovery cleaned it up)\n",
		status.Code(err), msg)
	if status.Code(err) != codes.Internal {
		panic("FAILED")
	}
	// The panic text did NOT leak to the caller.
	if strings.Contains(msg, "simulated bug") {
		panic("FAILED")
	}

	// The panic above must NOT have taken the server down for anyone else.
	res, err = client.Do(ctx, &interceptorpb.DoRequest{Task: "again"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Do(task=\"again\") -> %q   (server is still alive after the panic)\n", res.GetResult())
	if res.GetResult() != "did again" {
		panic("FAILED")
	}

	// ORDER PROOF. Logging is OUTSIDE recovery, so it observed all three calls -
	// including the one that panicked, which it saw as an Internal status.
	// Swap the two interceptors in the ChainUnaryInterceptor call above and the
	// panic would unwind PAST logging's deferred work entirely.
	fmt.Printf("\nwhat the logging interceptor recorded (%d calls):\n", len(callLog))
	for _, line := range callLog {
		fmt.Printf("  %s\n", line)
	}
	if len(callLog) != 3 || !strings.Contains(callLog[1], "Internal") {
		panic("FAILED")
	}
	fmt.Println("  -> logging saw the Internal status because it wraps recovery, not the reverse")

	fmt.Println("OK")
}
