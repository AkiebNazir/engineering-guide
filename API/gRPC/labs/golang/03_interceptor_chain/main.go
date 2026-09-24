/*
LAB 03 (advanced) - Interceptor chains: recovery, logging, auth with per-method policy, stream wrapping
======================================================================================================
You will learn

  - interceptors are gRPC's middleware, in two flavours:
    UnaryServerInterceptor   func(ctx, req, info, handler) (resp, err)
    StreamServerInterceptor  func(srv, stream, info, handler) error
    You need BOTH: a unary-only auth check leaves every streaming method wide open.

  - chaining:  grpc.ChainUnaryInterceptor(a, b, c)   -> a runs first (outermost)

    request -> Recovery -> Logging -> Auth -> handler
    panic->INTERNAL  timings   token + role per METHOD

  - a per-method policy table: "GetProduct needs role=reader, UploadMetrics needs role=writer"

  - how an interceptor passes the authenticated user down: context.WithValue for unary;
    for streams you must WRAP the ServerStream to override Context()

  - wrapping a stream to COUNT messages (RecvMsg / SendMsg) for metrics

  - a CLIENT interceptor that attaches the token to every call, unary and streaming

  - converting a panic into codes.Internal so one bad request cannot kill the server

Run it   go run ./gRPC/labs/golang/03_interceptor_chain
*/
package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"runtime/debug"
	"strings"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/labs/golang/shoppb"
)

// ------------------------------------------------------------- auth data ----
type user struct{ Name, Role string }

var tokens = map[string]user{
	"tok-reader": {"rita", "reader"},
	"tok-writer": {"walt", "writer"},
}

// Which role a method requires. A method missing from this table is DENIED (secure by default).
var policy = map[string]string{
	"/shop.v1.Catalog/GetProduct":    "reader",
	"/shop.v1.Catalog/ListProducts":  "reader",
	"/shop.v1.Catalog/UploadMetrics": "writer",
}

type userKey struct{}

func authorize(ctx context.Context, fullMethod string) (context.Context, error) {
	role, known := policy[fullMethod]
	if !known {
		return ctx, status.Errorf(codes.PermissionDenied, "%s is not in the access policy", fullMethod)
	}
	md, _ := metadata.FromIncomingContext(ctx)
	auth := md.Get("authorization")
	if len(auth) == 0 {
		return ctx, status.Error(codes.Unauthenticated, "missing authorization metadata")
	}
	u, ok := tokens[strings.TrimPrefix(auth[0], "Bearer ")]
	if !ok {
		return ctx, status.Error(codes.Unauthenticated, "invalid token")
	}
	if u.Role != role && u.Role != "admin" {
		return ctx, status.Errorf(codes.PermissionDenied, "%s requires role %q, you are %q", fullMethod, role, u.Role)
	}
	return context.WithValue(ctx, userKey{}, u), nil
}

// ------------------------------------------------------ server interceptors --
var (
	logMu  sync.Mutex
	logBuf []string
)

func logf(format string, a ...any) {
	logMu.Lock()
	logBuf = append(logBuf, fmt.Sprintf(format, a...))
	logMu.Unlock()
}

func recoveryUnary(ctx context.Context, req any, info *grpc.UnaryServerInfo, h grpc.UnaryHandler) (resp any, err error) {
	defer func() {
		if r := recover(); r != nil {
			logf("PANIC in %s: %v (stack has %d bytes)", info.FullMethod, r, len(debug.Stack()))
			err = status.Error(codes.Internal, "internal error") // details stay in the log
		}
	}()
	return h(ctx, req)
}

func recoveryStream(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, h grpc.StreamHandler) (err error) {
	defer func() {
		if r := recover(); r != nil {
			logf("PANIC in %s: %v", info.FullMethod, r)
			err = status.Error(codes.Internal, "internal error")
		}
	}()
	return h(srv, ss)
}

type whoKey struct{}

func loggingUnary(ctx context.Context, req any, info *grpc.UnaryServerInfo, h grpc.UnaryHandler) (any, error) {
	start := time.Now()
	who := new(string) // inner interceptors fill this in; we read it after the call
	resp, err := h(context.WithValue(ctx, whoKey{}, who), req)
	if *who == "" {
		*who = "-"
	}
	logf("unary  %-32s %-18s user=%-5s %s", info.FullMethod, status.Code(err), *who, time.Since(start).Round(time.Microsecond))
	return resp, err
}

// countingStream wraps a ServerStream to count messages and to carry a new context.
type countingStream struct {
	grpc.ServerStream
	ctx        context.Context
	recv, sent int
}

func (c *countingStream) Context() context.Context { return c.ctx } // how a stream interceptor injects the user
func (c *countingStream) RecvMsg(m any) error {
	err := c.ServerStream.RecvMsg(m)
	if err == nil {
		c.recv++
	}
	return err
}
func (c *countingStream) SendMsg(m any) error {
	err := c.ServerStream.SendMsg(m)
	if err == nil {
		c.sent++
	}
	return err
}

func loggingStream(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, h grpc.StreamHandler) error {
	cs := &countingStream{ServerStream: ss, ctx: ss.Context()}
	err := h(srv, cs)
	logf("stream %-32s %-18s recv=%d sent=%d", info.FullMethod, status.Code(err), cs.recv, cs.sent)
	return err
}

func authUnary(ctx context.Context, req any, info *grpc.UnaryServerInfo, h grpc.UnaryHandler) (any, error) {
	ctx, err := authorize(ctx, info.FullMethod)
	if err != nil {
		return nil, err // the handler is NEVER called
	}
	if who, ok := ctx.Value(whoKey{}).(*string); ok {
		*who = userName(ctx) // tell the (outer) logging interceptor who this was
	}
	return h(ctx, req)
}

func authStream(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, h grpc.StreamHandler) error {
	ctx, err := authorize(ss.Context(), info.FullMethod)
	if err != nil {
		return err
	}
	// The handler reads ss.Context(); to change it we must wrap the stream.
	return h(srv, &ctxStream{ServerStream: ss, ctx: ctx})
}

type ctxStream struct {
	grpc.ServerStream
	ctx context.Context
}

func (c *ctxStream) Context() context.Context { return c.ctx }

func userName(ctx context.Context) string {
	if u, ok := ctx.Value(userKey{}).(user); ok {
		return u.Name
	}
	return "-"
}

// ---------------------------------------------------------- business logic --
type server struct {
	shoppb.UnimplementedCatalogServer
}

func (server) GetProduct(ctx context.Context, r *shoppb.GetProductRequest) (*shoppb.Product, error) {
	if r.Id == 666 {
		var m map[string]int
		m["boom"] = 1 // panics
	}
	return &shoppb.Product{Id: r.Id, Name: "Keyboard (viewed by " + userName(ctx) + ")"}, nil
}

func (server) ListProducts(r *shoppb.ListProductsRequest, s shoppb.Catalog_ListProductsServer) error {
	for i := 1; i <= 3; i++ {
		s.Send(&shoppb.Product{Id: int64(i), Name: fmt.Sprint("p", i)})
	}
	return nil
}

func (server) UploadMetrics(s shoppb.Catalog_UploadMetricsServer) error {
	n := int32(0)
	for {
		if _, err := s.Recv(); err == io.EOF {
			return s.SendAndClose(&shoppb.UploadSummary{Count: n})
		} else if err != nil {
			return err
		}
		n++
	}
}

// ------------------------------------------------------ client interceptors --
func tokenClient(token string) []grpc.DialOption {
	attach := func(ctx context.Context) context.Context {
		if token == "" {
			return ctx
		}
		return metadata.AppendToOutgoingContext(ctx, "authorization", "Bearer "+token)
	}
	return []grpc.DialOption{
		grpc.WithChainUnaryInterceptor(func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, inv grpc.UnaryInvoker, opts ...grpc.CallOption) error {
			return inv(attach(ctx), method, req, reply, cc, opts...)
		}),
		grpc.WithChainStreamInterceptor(func(ctx context.Context, d *grpc.StreamDesc, cc *grpc.ClientConn, method string, str grpc.Streamer, opts ...grpc.CallOption) (grpc.ClientStream, error) {
			return str(attach(ctx), d, cc, method, opts...)
		}),
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	lis, _ := net.Listen("tcp", "127.0.0.1:0")
	s := grpc.NewServer(
		grpc.ChainUnaryInterceptor(loggingUnary, recoveryUnary, authUnary),     // first listed = outermost
		grpc.ChainStreamInterceptor(loggingStream, recoveryStream, authStream), // do not forget the stream side!
	)
	shoppb.RegisterCatalogServer(s, server{})
	go s.Serve(lis)
	defer s.Stop()

	dial := func(token string) shoppb.CatalogClient {
		opts := append([]grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}, tokenClient(token)...)
		conn, err := grpc.NewClient(lis.Addr().String(), opts...)
		if err != nil {
			log.Fatal(err)
		}
		return shoppb.NewCatalogClient(conn)
	}
	ctx := func() context.Context { // a 2s deadline for each call; cancel releases the timer
		c, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		time.AfterFunc(2*time.Second, cancel)
		return c
	}

	anon, reader, writer := dial(""), dial("tok-reader"), dial("tok-writer")

	fmt.Println("== unary: authentication and per-method roles ==")
	_, err := anon.GetProduct(ctx(), &shoppb.GetProductRequest{Id: 1})
	fmt.Println("  no token            ->", status.Code(err))
	must(status.Code(err) == codes.Unauthenticated, "no token")
	p, err := reader.GetProduct(ctx(), &shoppb.GetProductRequest{Id: 1})
	must(err == nil, fmt.Sprint(err))
	fmt.Println("  reader GetProduct   ->", p.Name, "(user injected into ctx by the interceptor)")
	_, err = writer.GetProduct(ctx(), &shoppb.GetProductRequest{Id: 1})
	fmt.Println("  writer GetProduct   ->", status.Code(err), "-", status.Convert(err).Message())
	must(status.Code(err) == codes.PermissionDenied, "role mismatch")

	fmt.Println("\n== the SAME rules on streaming methods ==")
	st, _ := anon.ListProducts(ctx(), &shoppb.ListProductsRequest{})
	_, err = st.Recv()
	fmt.Println("  anon ListProducts   ->", status.Code(err))
	must(status.Code(err) == codes.Unauthenticated, "stream auth")
	st, _ = reader.ListProducts(ctx(), &shoppb.ListProductsRequest{})
	n := 0
	for {
		if _, err := st.Recv(); err != nil {
			break
		}
		n++
	}
	fmt.Println("  reader ListProducts -> received", n, "products")
	must(n == 3, "reader can list")
	up, _ := writer.UploadMetrics(ctx())
	for i := 0; i < 5; i++ {
		up.Send(&shoppb.Metric{Name: "m", Value: 1})
	}
	sum, err := up.CloseAndRecv()
	must(err == nil && sum.Count == 5, "writer can upload")
	fmt.Println("  writer UploadMetrics-> count", sum.Count)

	fmt.Println("\n== secure by default: a method missing from the policy is denied ==")
	chat, _ := writer.Chat(ctx())
	chat.Send(&shoppb.ChatMessage{Text: "hi"})
	_, err = chat.Recv()
	fmt.Println("  writer Chat         ->", status.Code(err), "-", status.Convert(err).Message())
	must(status.Code(err) == codes.PermissionDenied, "unlisted method denied")

	fmt.Println("\n== a panic becomes INTERNAL; the server keeps running ==")
	_, err = reader.GetProduct(ctx(), &shoppb.GetProductRequest{Id: 666})
	fmt.Println("  id=666              ->", status.Code(err), "-", status.Convert(err).Message())
	must(status.Code(err) == codes.Internal, "panic recovered")
	_, err = reader.GetProduct(ctx(), &shoppb.GetProductRequest{Id: 1})
	must(err == nil, "server still serving")

	fmt.Println("\n== server-side log (what the interceptors recorded) ==")
	logMu.Lock()
	for _, l := range logBuf {
		fmt.Println("  ", l)
	}
	logMu.Unlock()
	fmt.Println("\nOK")
}
