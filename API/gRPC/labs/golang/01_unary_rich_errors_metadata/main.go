/*
LAB 01 (basic) - Unary gRPC in Go: status codes, rich error details, metadata
=============================================================================
You will learn
  - the Go gRPC shape:  embed UnimplementedCatalogServer, implement methods, Register, Serve
  - the client:         grpc.NewClient(target, creds)  ->  shoppb.NewCatalogClient(conn)
    (grpc.Dial is deprecated; NewClient connects lazily)
  - ALWAYS call with a context that has a deadline
  - errors: return status.Error(codes.X, "message"). The client reads status.Code(err).
  - RICH errors: attach machine-readable details (errdetails.BadRequest lists WHICH field failed)
    so clients can highlight the right input without parsing message strings
  - metadata: request metadata from the client, header + trailer metadata from the server
  - never return a plain error from a handler: it becomes codes.Unknown, which tells the caller nothing

Wire picture (one unary call):

	client -> HEADERS(:path=/shop.v1.Catalog/GetProduct, metadata)  DATA(request)
	client <- HEADERS(initial metadata)  DATA(response)  TRAILERS(grpc-status, trailing metadata)

Run it   go run ./gRPC/labs/golang/01_unary_rich_errors_metadata
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/labs/golang/shoppb"
)

type server struct {
	shoppb.UnimplementedCatalogServer // forward compatibility: new RPCs added to the .proto will not break the build
	products                          map[int64]*shoppb.Product
}

func (s *server) GetProduct(ctx context.Context, req *shoppb.GetProductRequest) (*shoppb.Product, error) {
	// 1. request metadata (the gRPC word for HTTP headers). Keys are lower-cased.
	requestID := "none"
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if v := md.Get("x-request-id"); len(v) > 0 {
			requestID = v[0]
		}
	}

	// 2. validation error with structured details
	if req.GetId() <= 0 {
		st := status.New(codes.InvalidArgument, "invalid request")
		st, err := st.WithDetails(&errdetails.BadRequest{FieldViolations: []*errdetails.BadRequest_FieldViolation{
			{Field: "id", Description: "must be a positive integer"},
		}})
		if err != nil {
			return nil, status.Error(codes.Internal, "could not attach details")
		}
		return nil, st.Err()
	}

	// 3. not found
	p, ok := s.products[req.GetId()]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "product %d does not exist", req.GetId())
	}

	// 4. respond with metadata: header BEFORE the response, trailer AFTER it
	grpc.SendHeader(ctx, metadata.Pairs("x-served-by", "catalog-1"))
	grpc.SetTrailer(ctx, metadata.Pairs("x-request-id", requestID))
	return p, nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	s := grpc.NewServer()
	shoppb.RegisterCatalogServer(s, &server{products: map[int64]*shoppb.Product{
		1: {Id: 1, Name: "Keyboard", PriceCents: 4999, Stock: 12},
	}})
	go s.Serve(lis)
	defer s.Stop()

	// ONE connection for the life of the program. NewClient does not dial until the first call.
	conn, err := grpc.NewClient(lis.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := shoppb.NewCatalogClient(conn)

	newCtx := func() (context.Context, context.CancelFunc) {
		return context.WithTimeout(context.Background(), 2*time.Second) // ALWAYS a deadline
	}

	fmt.Println("== a successful call, reading header and trailer metadata ==")
	ctx, cancel := newCtx()
	ctx = metadata.AppendToOutgoingContext(ctx, "x-request-id", "req-42")
	var header, trailer metadata.MD
	p, err := client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1}, grpc.Header(&header), grpc.Trailer(&trailer))
	cancel()
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  %s $%.2f | header x-served-by=%v | trailer x-request-id=%v\n",
		p.GetName(), float64(p.GetPriceCents())/100, header.Get("x-served-by"), trailer.Get("x-request-id"))
	must(trailer.Get("x-request-id")[0] == "req-42", "trailer metadata")

	fmt.Println("\n== NOT_FOUND ==")
	ctx, cancel = newCtx()
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 99})
	cancel()
	st, _ := status.FromError(err)
	fmt.Printf("  code=%s message=%q\n", st.Code(), st.Message())
	must(status.Code(err) == codes.NotFound, "not found")

	fmt.Println("\n== INVALID_ARGUMENT with structured details ==")
	ctx, cancel = newCtx()
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: -1})
	cancel()
	st, _ = status.FromError(err)
	fmt.Printf("  code=%s message=%q\n", st.Code(), st.Message())
	for _, d := range st.Details() { // details are typed messages, not strings to parse
		if br, ok := d.(*errdetails.BadRequest); ok {
			for _, v := range br.GetFieldViolations() {
				fmt.Printf("  -> highlight field %q: %s\n", v.GetField(), v.GetDescription())
			}
			must(br.GetFieldViolations()[0].GetField() == "id", "field violation")
		}
	}

	fmt.Println("\n== the client's own deadline ==")
	ctx, cancel = context.WithTimeout(context.Background(), time.Nanosecond)
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1})
	cancel()
	fmt.Println("  code =", status.Code(err))
	must(status.Code(err) == codes.DeadlineExceeded, "deadline")

	fmt.Println("\n== the server is gone ==")
	s.Stop()
	ctx, cancel = newCtx()
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1})
	cancel()
	fmt.Println("  code =", status.Code(err), "(UNAVAILABLE = transient: safe to retry with backoff)")
	must(status.Code(err) == codes.Unavailable, "unavailable")

	fmt.Println("\ngRPC code -> nearest HTTP status (what a REST gateway would return)")
	for _, c := range []struct {
		code codes.Code
		http int
	}{{codes.InvalidArgument, 400}, {codes.Unauthenticated, 401}, {codes.PermissionDenied, 403}, {codes.NotFound, 404},
		{codes.AlreadyExists, 409}, {codes.ResourceExhausted, 429}, {codes.Internal, 500}, {codes.Unavailable, 503}, {codes.DeadlineExceeded, 504}} {
		fmt.Printf("  %-18s %d\n", c.code, c.http)
	}
	fmt.Println("\nOK")
}
