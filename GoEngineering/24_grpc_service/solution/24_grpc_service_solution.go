// Command 24_grpc_service_solution implements InventoryService (see
// order.proto — sorry, inventory.proto — for the contract) as a real gRPC
// server: a unary RPC, a server-streaming RPC, a client-streaming RPC, and
// a chained unary+streaming interceptor pair providing request-ID
// propagation, structured logging, and panic recovery.
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"goengineering/24_grpc_service/solution/inventorypb"
)

// requestIDKey is an unexported context-key type — the standard Go idiom
// for context values, so a caller using a plain string key from another
// package can never collide with this one.
type requestIDKey struct{}

// requestIDFromContext extracts the request ID an interceptor placed on
// ctx, returning "" if none is present (e.g. in a handler unit-tested
// directly, without going through an interceptor).
func requestIDFromContext(ctx context.Context) string {
	id, _ := ctx.Value(requestIDKey{}).(string)
	return id
}

// nextRequestID is a process-local monotonic counter used when a caller
// doesn't supply its own request ID via metadata. A real production
// service would more likely use a UUID or a trace ID from an upstream
// propagation header; a counter is used here so tests can assert on
// deterministic, human-readable IDs without pulling in a UUID dependency.
var requestIDCounter atomicCounter

type atomicCounter struct {
	mu sync.Mutex
	n  uint64
}

func (c *atomicCounter) next() uint64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.n++
	return c.n
}

// unaryLoggingInterceptor returns a grpc.UnaryServerInterceptor providing
// three cross-cutting concerns every unary RPC gets without the handler
// knowing about any of them:
//
//  1. Request-ID propagation: stamps a request ID onto the context (a real
//     implementation would first check incoming metadata for a client-
//     supplied ID and only generate one if absent — omitted here to keep
//     the exercise focused, noted as a stretch goal).
//  2. Structured logging: one slog record per RPC with method, duration,
//     and the resulting gRPC code — the single most useful line of
//     observability a gRPC server can emit, and it's free once written
//     here instead of once per handler.
//  3. Panic recovery: converts a handler panic into codes.Internal instead
//     of letting it unwind past grpc-go's own stream-handling goroutine,
//     which would take down the whole server process — one bad request
//     must never be able to kill every other in-flight RPC.
func unaryLoggingInterceptor(logger *slog.Logger) grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (resp any, err error) {
		reqID := fmt.Sprintf("req-%d", requestIDCounter.next())
		ctx = context.WithValue(ctx, requestIDKey{}, reqID)
		start := time.Now()

		defer func() {
			if r := recover(); r != nil {
				err = status.Errorf(codes.Internal, "panic recovered: %v", r)
			}
			logger.Info("unary rpc",
				"method", info.FullMethod,
				"request_id", reqID,
				"duration", time.Since(start),
				"code", status.Code(err).String(),
			)
		}()

		return handler(ctx, req)
	}
}

// wrappedServerStream lets a streaming interceptor inject a value (here,
// the request ID) into the context a handler sees via stream.Context().
// grpc.ServerStream has no context setter, so overriding the Context()
// method on an embedding wrapper is the only way to do this — every other
// method is left as the embedded default.
type wrappedServerStream struct {
	grpc.ServerStream
	ctx context.Context
}

func (w *wrappedServerStream) Context() context.Context { return w.ctx }

// streamLoggingInterceptor is the streaming-RPC equivalent of
// unaryLoggingInterceptor: same request ID + logging + panic-recovery
// contract, but request ID has to travel via a wrapped ServerStream rather
// than a returned context, since a streaming handler receives the stream,
// not a context directly.
func streamLoggingInterceptor(logger *slog.Logger) grpc.StreamServerInterceptor {
	return func(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) (err error) {
		reqID := fmt.Sprintf("req-%d", requestIDCounter.next())
		wrapped := &wrappedServerStream{ServerStream: ss, ctx: context.WithValue(ss.Context(), requestIDKey{}, reqID)}
		start := time.Now()

		defer func() {
			if r := recover(); r != nil {
				err = status.Errorf(codes.Internal, "panic recovered: %v", r)
			}
			logger.Info("stream rpc",
				"method", info.FullMethod,
				"request_id", reqID,
				"duration", time.Since(start),
				"code", status.Code(err).String(),
			)
		}()

		return handler(srv, wrapped)
	}
}

// Sentinel SKUs the server treats specially, purely to make the
// deadline-exceeded and panic-recovery paths deterministically testable
// without relying on real timing races or an actually-broken handler.
const (
	skuSlow  = "sku-slow"  // GetItem simulates 200ms of work for this SKU
	skuPanic = "sku-panic" // GetItem panics for this SKU, to exercise recovery
)

// inventoryServer implements inventorypb.InventoryServiceServer.
// Embedding UnimplementedInventoryServiceServer satisfies forward
// compatibility: if the .proto gains a new RPC and this struct isn't
// updated, it still satisfies the (regenerated) interface at compile time,
// failing at runtime with codes.Unimplemented for the new method instead
// of failing to build.
type inventoryServer struct {
	inventorypb.UnimplementedInventoryServiceServer

	mu    sync.Mutex
	items map[string]*inventorypb.Item
}

func newInventoryServer(seed map[string]*inventorypb.Item) *inventoryServer {
	return &inventoryServer{items: seed}
}

// GetItem: unary RPC. Demonstrates the full error-model + deadline
// contract this exercise asks for: InvalidArgument for a bad request,
// DeadlineExceeded if simulated work doesn't finish before ctx is done,
// NotFound for a missing SKU, Internal (via the interceptor) for a panic.
func (s *inventoryServer) GetItem(ctx context.Context, req *inventorypb.GetItemRequest) (*inventorypb.Item, error) {
	sku := req.GetSku()
	if sku == "" {
		return nil, status.Error(codes.InvalidArgument, "sku is required")
	}

	if sku == skuPanic {
		panic("boom: simulated handler panic for sku-panic")
	}

	if sku == skuSlow {
		// Simulate real work (e.g. a slow downstream call) that respects
		// cancellation instead of blocking obliviously. This is the
		// pattern every handler doing non-trivial work should follow:
		// select on the actual work completing vs ctx.Done(), never just
		// time.Sleep the work's duration and check ctx afterward.
		select {
		case <-time.After(200 * time.Millisecond):
		case <-ctx.Done():
			return nil, status.FromContextError(ctx.Err()).Err()
		}
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	item, ok := s.items[sku]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "item %q not found", sku)
	}
	// Defensive copy: never hand out a pointer into server-owned state that
	// a caller (in-process test, or a future in-process caller) could
	// mutate out from under concurrent RPCs.
	return &inventorypb.Item{Sku: item.Sku, Name: item.Name, Quantity: item.Quantity}, nil
}

// WatchStock: server-streaming RPC. Emits a StockUpdate on each tick for
// the requested SKU until max_updates is reached or the stream's context
// is done (client cancellation, deadline, or the connection dropping).
func (s *inventoryServer) WatchStock(req *inventorypb.WatchStockRequest, stream inventorypb.InventoryService_WatchStockServer) error {
	sku := req.GetSku()
	if sku == "" {
		return status.Error(codes.InvalidArgument, "sku is required")
	}
	max := int(req.GetMaxUpdates())

	ticker := time.NewTicker(15 * time.Millisecond)
	defer ticker.Stop() // never leak the ticker's goroutine on early return

	ctx := stream.Context()
	sent := 0
	for {
		select {
		case <-ctx.Done():
			return status.FromContextError(ctx.Err()).Err()
		case <-ticker.C:
			s.mu.Lock()
			item, ok := s.items[sku]
			var qty int64
			if ok {
				qty = item.Quantity
			}
			s.mu.Unlock()
			if !ok {
				return status.Errorf(codes.NotFound, "item %q not found", sku)
			}

			update := &inventorypb.StockUpdate{Sku: sku, Quantity: qty, UnixTime: time.Now().Unix()}
			if err := stream.Send(update); err != nil {
				// Send only fails if the stream is already broken (client
				// gone) — nothing to recover, just propagate.
				return err
			}
			sent++
			if max > 0 && sent >= max {
				return nil
			}
		}
	}
}

// RecordSales: client-streaming RPC. Applies each SaleRecord as it
// arrives (so stock reflects sales incrementally, not only at the end —
// important if the client-streaming call is interrupted partway through:
// sales already received are not lost), then returns one aggregated
// SalesSummary once the client half-closes its send side.
func (s *inventoryServer) RecordSales(stream inventorypb.InventoryService_RecordSalesServer) error {
	var total int64
	var count int32

	for {
		rec, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			return stream.SendAndClose(&inventorypb.SalesSummary{TotalQuantity: total, RecordCount: count})
		}
		if err != nil {
			return err
		}

		if rec.GetQuantity() <= 0 {
			return status.Errorf(codes.InvalidArgument, "quantity must be positive, got %d", rec.GetQuantity())
		}

		s.mu.Lock()
		item, ok := s.items[rec.GetSku()]
		if ok {
			item.Quantity -= rec.GetQuantity()
		}
		s.mu.Unlock()
		if !ok {
			return status.Errorf(codes.NotFound, "item %q not found", rec.GetSku())
		}

		total += rec.GetQuantity()
		count++
	}
}

// newGRPCServer wires the interceptor chain and registers inventoryServer.
// grpc.ChainUnaryInterceptor/ChainStreamInterceptor compose multiple
// interceptors in the order given (outermost first) — here there's only
// one of each, but the chain form is used anyway since a second
// interceptor (e.g. auth, rate limiting) is the first thing a real service
// adds next, and chaining composes without restructuring this call.
func newGRPCServer(logger *slog.Logger, seed map[string]*inventorypb.Item) *grpc.Server {
	srv := grpc.NewServer(
		grpc.ChainUnaryInterceptor(unaryLoggingInterceptor(logger)),
		grpc.ChainStreamInterceptor(streamLoggingInterceptor(logger)),
	)
	inventorypb.RegisterInventoryServiceServer(srv, newInventoryServer(seed))
	return srv
}

func defaultSeed() map[string]*inventorypb.Item {
	return map[string]*inventorypb.Item{
		"sku-widget": {Sku: "sku-widget", Name: "Widget", Quantity: 100},
		"sku-gadget": {Sku: "sku-gadget", Name: "Gadget", Quantity: 50},
		skuSlow:      {Sku: skuSlow, Name: "Slow Item", Quantity: 10},
	}
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		logger.Error("listen failed", "error", err)
		os.Exit(1)
	}

	srv := newGRPCServer(logger, defaultSeed())

	serveErr := make(chan error, 1)
	go func() {
		logger.Info("grpc server listening", "addr", lis.Addr().String())
		serveErr <- srv.Serve(lis)
	}()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	select {
	case err := <-serveErr:
		if err != nil {
			logger.Error("grpc server stopped unexpectedly", "error", err)
			os.Exit(1)
		}
	case <-ctx.Done():
		logger.Info("shutdown signal received, stopping gracefully")
		srv.GracefulStop() // lets in-flight RPCs (including WatchStock streams) finish
		logger.Info("grpc server stopped")
	}
}

/*
BEST PRACTICES

  - Always return `*status.Status`-backed errors (status.Error/Errorf) from
    handlers, with the most specific applicable codes.Code — a bare `error`
    reaches the client as codes.Unknown and forecloses any client-side
    branching on failure type.
  - Put panic recovery, logging, and any per-RPC bookkeeping in
    interceptors, not handlers. Every handler added later gets the same
    guarantees automatically instead of by convention/memory.
  - Select real work against ctx.Done() (or stream.Context().Done())
    instead of doing the work unconditionally and checking the context
    only before/after — the whole point of deadline propagation is to stop
    wasting work the caller no longer wants.
  - Never leak a pointer into server-owned mutable state to a caller;
    return a copy (as GetItem does here) so concurrent RPCs and the
    caller's own use of the returned value can't race.
  - Use grpc.ChainUnaryInterceptor/ChainStreamInterceptor even for a single
    interceptor — it's a drop-in extension point for the next one instead
    of a call-site refactor.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - A real deployment would read the request ID from incoming metadata
    (`metadata.FromIncomingContext`) first and only generate one if absent,
    so a request ID assigned by an upstream gateway/load balancer survives
    end-to-end instead of being replaced at every hop — omitted here to
    keep the interceptor's logic centered on the recovery+logging pattern,
    called out as a stretch goal.
  - RecordSales applies each sale as it's received rather than buffering
    the whole stream and applying atomically at the end. This means a
    client that disconnects partway through leaves partial effects applied
    — the right trade-off for an inventory decrement (each sale is
    independently valid and should count even if a later one in the same
    stream never arrives) but the wrong one for anything requiring
    all-or-nothing semantics, which would need to buffer and apply in one
    critical section (or a real transaction) instead.
  - WatchStock polls a ticker rather than pushing updates on write (e.g.
    via a pub/sub channel per SKU, problem 16's shape). Ticking is simpler
    and sufficient for a demo; a production stock ticker would want
    push-on-write to avoid the tick-interval latency and unnecessary
    identical-value sends when stock hasn't changed.

TESTING / FAILURE MODES

  - The test file drives all three RPCs against a real (bufconn) in-process
    server: a plain unary call, a server-streaming call read to
    completion, and a client-streaming call sending several records before
    closing.
  - GetItem's DeadlineExceeded path is tested with a real context.WithTimeout
    shorter than skuSlow's simulated 200ms work, asserting the returned
    status code is exactly codes.DeadlineExceeded (via status.Code(err)),
    not a generic error.
  - The panic-recovery interceptor is tested by calling GetItem with
    sku-panic and asserting the client sees codes.Internal instead of the
    RPC connection dying — proving one bad request doesn't take down the
    server for other in-flight tests running against the same instance.
  - WatchStock's clean shutdown on client cancellation is tested by
    cancelling the client-side context mid-stream and asserting the server
    handler returns (rather than leaking its ticker/goroutine) — observed
    indirectly via the stream ending instead of blocking the test.
*/
