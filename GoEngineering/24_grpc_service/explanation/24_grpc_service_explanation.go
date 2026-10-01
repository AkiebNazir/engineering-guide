/*
Problem 24 — gRPC Service

WHAT WE'RE BUILDING

An InventoryService: a small gRPC service tracking per-SKU stock, exercising
all three RPC shapes a real service typically needs plus the operational
machinery every production gRPC server needs regardless of what it does:

  - GetItem: a plain unary RPC (request in, response out).
  - WatchStock: a SERVER-streaming RPC — one request, a stream of responses
    (think: a live stock ticker a dashboard subscribes to).
  - RecordSales: a CLIENT-streaming RPC — a stream of requests, one
    response (think: a client batching sale events and getting back one
    aggregated summary when it's done sending).
  - A unary AND a streaming server interceptor, chained, providing
    request-ID propagation, structured logging, and panic recovery —
    cross-cutting concerns every RPC gets without each handler re-
    implementing them.
  - Deadline propagation: GetItem honors ctx and returns
    codes.DeadlineExceeded (via status.FromContextError) instead of racing
    a client's timeout with its own unrelated error.
  - A proper error model: every failure path returns a `*status.Status`
    with a specific `codes.Code` (InvalidArgument, NotFound,
    DeadlineExceeded, Internal) and a human-readable message — never a bare
    Go `error` from a handler, which gRPC would otherwise wrap as an opaque
    codes.Unknown on the wire.

The generated contract lives in solution/inventory.proto (with the exact
`protoc` command in its header comment) and solution/inventorypb/
(inventory.pb.go + inventory_grpc.pb.go) — this explanation package imports
that same generated package rather than duplicating it, since regenerating
per-package would produce two incompatible Go types for the same message.

# WHY THIS MATTERS IN REAL SYSTEMS

gRPC is the default choice for internal service-to-service traffic at scale
because it gets you a strongly-typed contract, efficient binary encoding,
and multiplexed streaming over HTTP/2 for free — but none of the
operational concerns (auth, logging, tracing, panic isolation, deadline
propagation, structured error codes clients can branch on) come for free.
Interceptors are how you get them without smearing the same boilerplate
across every RPC handler. A service that doesn't propagate context
deadlines into its handlers will happily keep doing expensive work for a
client that already gave up and disconnected — wasted work that compounds
under load into a pile-up. A service that panics on one bad request and
takes the whole process down (rather than that one RPC failing cleanly) is
an outage waiting to happen; recovery middleware is not optional in
production gRPC servers.

# CONCEPTS COVERED

  - Defining an RPC service in a `.proto` file (unary, server-streaming,
    client-streaming methods) and generating client/server Go stubs with
    `protoc` + `protoc-gen-go` + `protoc-gen-go-grpc`
  - `grpc.UnaryServerInterceptor` / `grpc.StreamServerInterceptor`, chained
    with `grpc.ChainUnaryInterceptor` / `grpc.ChainStreamInterceptor`
  - Wrapping a `grpc.ServerStream` to inject values into the stream's
    context (the streaming equivalent of a unary interceptor rewriting ctx
    before calling the handler)
  - Deadline-aware handlers: `ctx.Done()` / `stream.Context().Done()`
    selected against real work, `status.FromContextError` to convert
    `context.DeadlineExceeded`/`context.Canceled` into the matching gRPC
    code
  - The `google.golang.org/grpc/codes` + `.../status` error model:
    returning `status.Error`/`status.Errorf` with a specific code instead
    of a bare `error`
  - Testing a gRPC service in-process with `google.golang.org/grpc/test/bufconn`
    — no real network port, no flakiness from port collisions, fast

# SPEC (see solution/inventory.proto for the authoritative contract; run its
documented protoc command first — this package imports the generated
inventorypb package and will not build until that code exists)

	service InventoryService {
	    rpc GetItem(GetItemRequest) returns (Item);
	    rpc WatchStock(WatchStockRequest) returns (stream StockUpdate);
	    rpc RecordSales(stream SaleRecord) returns (SalesSummary);
	}

Server behavior to implement:

  - GetItem: codes.InvalidArgument for an empty SKU, codes.NotFound for an
    unknown SKU, codes.DeadlineExceeded if the (simulated slow-path) work
    doesn't finish before ctx is done, else the Item.
  - WatchStock: sends one StockUpdate per tick for the requested SKU, up to
    max_updates ticks (0 means "until cancelled"), stopping cleanly when
    the stream's context is done.
  - RecordSales: decrements stock per SaleRecord received, rejects a
    non-positive quantity or unknown SKU with the matching code, and
    returns one SalesSummary (total quantity, record count) via
    SendAndClose once the client half-closes.
  - A unary interceptor that: reads (or generates) a request ID, stores it
    on the context, logs method name + duration + resulting code via
    log/slog, and recovers from a handler panic by returning
    codes.Internal instead of crashing the server.
  - A streaming interceptor doing the same, wrapping the ServerStream so
    handlers can read the request ID off `stream.Context()`.

# HINTS

  - `status.FromContextError(ctx.Err()).Err()` is the idiomatic one-liner
    for "turn whatever the context's error is into the matching gRPC
    status" — it maps context.DeadlineExceeded to codes.DeadlineExceeded
    and context.Canceled to codes.Canceled, and passes anything else
    through as codes.Unknown.
  - A `defer func() { if r := recover(); r != nil { ... } }()` at the top
    of an interceptor — NOT inside each handler — is what makes panic
    recovery a cross-cutting concern instead of per-handler boilerplate.
  - To inject a value into a streaming handler's context, you cannot just
    mutate `stream.Context()` (there's no setter) — wrap the ServerStream
    in your own type that embeds it and overrides `Context()` to return
    the modified one.
  - bufconn's `Listener.DialContext` becomes a `grpc.WithContextDialer`
    option; dial with `grpc.NewClient("passthrough:///bufnet", ...)` and
    `credentials/insecure.NewCredentials()` (there's no real transport
    security to negotiate over an in-memory pipe).

# PITFALLS

  - Returning a bare `error` (e.g. from `fmt.Errorf`) from a handler
    instead of a `*status.Status` — gRPC still sends *something* over the
    wire, but the client sees `codes.Unknown` and loses any ability to
    branch on the failure type.
  - Forgetting `stream.Context()` inside WatchStock and instead capturing
    the interceptor's original (pre-wrapped) context in a closure — this
    silently defeats both the request-ID propagation AND cancellation
    detection.
  - A panic inside a streaming handler with no recovery: it takes down the
    whole gRPC server process, not just the one RPC — every other in-flight
    RPC on that process dies too.
  - Not calling `ticker.Stop()` (or otherwise leaking the goroutine/timer
    backing a streaming handler) when the stream ends early via client
    cancellation.

# STRETCH GOALS

  - Add a bidirectional-streaming RPC (e.g. a live price-negotiation loop)
    to see the difference from client-streaming + server-streaming
    composed separately.
  - Register `google.golang.org/grpc/health/grpc_health_v1`'s health
    service alongside InventoryService and have a client poll it.
  - Add a client-side unary interceptor that retries codes.Unavailable with
    backoff, and a deadline-per-attempt vs deadline-for-the-whole-call
    distinction.
*/
package main

import (
	"context"
	"net"

	"google.golang.org/grpc"

	"goengineering/24_grpc_service/solution/inventorypb"
)

// inventoryServer implements inventorypb.InventoryServiceServer.
//
// TODO: add an in-memory items map[string]*inventorypb.Item plus a mutex
// guarding it, and a *slog.Logger for the interceptors to use.
type inventoryServer struct {
	inventorypb.UnimplementedInventoryServiceServer
	// TODO: fields
}

// GetItem: unary RPC.
// TODO: codes.InvalidArgument for empty SKU; simulate a deadline-sensitive
// slow path for a sentinel SKU using select{} against ctx.Done(); codes.NotFound
// for unknown SKU; return a defensive copy of the stored Item otherwise.
func (s *inventoryServer) GetItem(ctx context.Context, req *inventorypb.GetItemRequest) (*inventorypb.Item, error) {
	panic("TODO: implement inventoryServer.GetItem")
}

// WatchStock: server-streaming RPC.
// TODO: send one StockUpdate per tick until max_updates is reached or
// stream.Context().Done() fires; return status.FromContextError(...).Err()
// on cancellation, not a bare context error.
func (s *inventoryServer) WatchStock(req *inventorypb.WatchStockRequest, stream inventorypb.InventoryService_WatchStockServer) error {
	panic("TODO: implement inventoryServer.WatchStock")
}

// RecordSales: client-streaming RPC.
// TODO: loop stream.Recv() until io.EOF, validating and applying each
// SaleRecord, then stream.SendAndClose a SalesSummary.
func (s *inventoryServer) RecordSales(stream inventorypb.InventoryService_RecordSalesServer) error {
	panic("TODO: implement inventoryServer.RecordSales")
}

// unaryLoggingInterceptor should: extract/generate a request ID, store it
// on ctx, log method+duration+code via log/slog, and recover from a panic
// in the handler by returning a codes.Internal status instead of crashing.
// TODO: implement.
func unaryLoggingInterceptor() grpc.UnaryServerInterceptor {
	panic("TODO: implement unaryLoggingInterceptor")
}

// streamLoggingInterceptor is the streaming-RPC equivalent of
// unaryLoggingInterceptor: same request-ID + logging + panic recovery, but
// must wrap the grpc.ServerStream to inject the request ID into
// stream.Context() (there's no setter — wrap the stream, override
// Context()).
// TODO: implement.
func streamLoggingInterceptor() grpc.StreamServerInterceptor {
	panic("TODO: implement streamLoggingInterceptor")
}

// newGRPCServer wires the interceptors and registers inventoryServer.
// TODO: grpc.NewServer(grpc.ChainUnaryInterceptor(...), grpc.ChainStreamInterceptor(...)),
// then inventorypb.RegisterInventoryServiceServer(srv, &inventoryServer{...}).
func newGRPCServer() *grpc.Server {
	panic("TODO: implement newGRPCServer")
}

func main() {
	// TODO:
	//  1. lis, err := net.Listen("tcp", ":50051")
	//  2. srv := newGRPCServer()
	//  3. srv.Serve(lis), logging any error that isn't grpc.ErrServerStopped
	//  4. Handle SIGINT/SIGTERM to call srv.GracefulStop() (problem 25 covers
	//     the full signal.NotifyContext + shutdown pattern in more depth for
	//     an HTTP server; the same idea applies here).
	panic("TODO: implement main")
}

var _ = net.Listen // keep net imported for the stub file
