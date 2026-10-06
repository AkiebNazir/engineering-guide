package main

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"net"
	"testing"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"

	"goengineering/24_grpc_service/solution/inventorypb"
)

// testServer starts a real *grpc.Server over an in-memory bufconn listener
// (no real network port — fast, no port-collision flakiness) and returns a
// connected client plus a cleanup func. This exercises the actual
// interceptor chain and handlers, not a fake/mock of the service.
func testServer(t *testing.T, seed map[string]*inventorypb.Item) inventorypb.InventoryServiceClient {
	t.Helper()

	const bufSize = 1024 * 1024
	lis := bufconn.Listen(bufSize)

	logger := slog.New(slog.NewTextHandler(io.Discard, nil)) // silence logs in tests
	srv := newGRPCServer(logger, seed)

	go func() {
		_ = srv.Serve(lis)
	}()
	t.Cleanup(srv.Stop)

	dialer := func(ctx context.Context, _ string) (net.Conn, error) {
		return lis.DialContext(ctx)
	}
	conn, err := grpc.NewClient("passthrough:///bufnet",
		grpc.WithContextDialer(dialer),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("grpc.NewClient: %v", err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	return inventorypb.NewInventoryServiceClient(conn)
}

func TestGetItem_Unary_Success(t *testing.T) {
	client := testServer(t, defaultSeed())

	item, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: "sku-widget"})
	if err != nil {
		t.Fatalf("GetItem: %v", err)
	}
	if item.GetSku() != "sku-widget" || item.GetQuantity() != 100 {
		t.Fatalf("GetItem = %+v, want sku-widget/100", item)
	}
}

func TestGetItem_NotFound(t *testing.T) {
	client := testServer(t, defaultSeed())

	_, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: "sku-does-not-exist"})
	if err == nil {
		t.Fatal("GetItem = nil error, want codes.NotFound")
	}
	if got := status.Code(err); got != codes.NotFound {
		t.Fatalf("status code = %v, want %v", got, codes.NotFound)
	}
}

func TestGetItem_InvalidArgument(t *testing.T) {
	client := testServer(t, defaultSeed())

	_, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: ""})
	if got := status.Code(err); got != codes.InvalidArgument {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.InvalidArgument, err)
	}
}

// TestGetItem_DeadlineExceeded proves the server honors a client deadline
// shorter than the simulated work duration (200ms for skuSlow), rather than
// completing the work anyway and racing the client's own timeout.
func TestGetItem_DeadlineExceeded(t *testing.T) {
	client := testServer(t, defaultSeed())

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()

	_, err := client.GetItem(ctx, &inventorypb.GetItemRequest{Sku: skuSlow})
	if err == nil {
		t.Fatal("GetItem = nil error, want codes.DeadlineExceeded")
	}
	if got := status.Code(err); got != codes.DeadlineExceeded {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.DeadlineExceeded, err)
	}
}

// TestGetItem_PanicRecovery proves the unary interceptor's panic recovery
// works: a handler panic becomes codes.Internal over the wire, and — the
// part that actually matters — the SAME server instance keeps serving
// other requests afterward instead of the process (or even just that
// connection) dying.
func TestGetItem_PanicRecovery(t *testing.T) {
	client := testServer(t, defaultSeed())

	_, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: skuPanic})
	if err == nil {
		t.Fatal("GetItem = nil error, want codes.Internal from recovered panic")
	}
	if got := status.Code(err); got != codes.Internal {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.Internal, err)
	}

	// The server must still be alive and correct for a subsequent call.
	item, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: "sku-widget"})
	if err != nil {
		t.Fatalf("GetItem after panic recovery: %v", err)
	}
	if item.GetSku() != "sku-widget" {
		t.Fatalf("server did not survive the panic cleanly: got %+v", item)
	}
}

func TestWatchStock_ServerStreaming_ReceivesBoundedUpdates(t *testing.T) {
	client := testServer(t, defaultSeed())

	stream, err := client.WatchStock(context.Background(), &inventorypb.WatchStockRequest{Sku: "sku-widget", MaxUpdates: 3})
	if err != nil {
		t.Fatalf("WatchStock: %v", err)
	}

	var updates []*inventorypb.StockUpdate
	for {
		u, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			t.Fatalf("stream.Recv: %v", err)
		}
		updates = append(updates, u)
	}

	if len(updates) != 3 {
		t.Fatalf("received %d updates, want 3", len(updates))
	}
	for i, u := range updates {
		if u.GetSku() != "sku-widget" || u.GetQuantity() != 100 {
			t.Fatalf("update[%d] = %+v, want sku-widget/100", i, u)
		}
	}
}

func TestWatchStock_UnknownSKU(t *testing.T) {
	client := testServer(t, defaultSeed())

	stream, err := client.WatchStock(context.Background(), &inventorypb.WatchStockRequest{Sku: "sku-does-not-exist", MaxUpdates: 1})
	if err != nil {
		t.Fatalf("WatchStock: %v", err)
	}
	_, err = stream.Recv()
	if got := status.Code(err); got != codes.NotFound {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.NotFound, err)
	}
}

// TestWatchStock_ClientCancellation proves the server-side handler exits
// cleanly (no goroutine/ticker leak, no hang) when the CLIENT cancels
// mid-stream rather than the server reaching max_updates on its own.
func TestWatchStock_ClientCancellation(t *testing.T) {
	client := testServer(t, defaultSeed())

	ctx, cancel := context.WithCancel(context.Background())
	stream, err := client.WatchStock(ctx, &inventorypb.WatchStockRequest{Sku: "sku-widget", MaxUpdates: 0}) // unbounded
	if err != nil {
		t.Fatalf("WatchStock: %v", err)
	}

	// Read a couple of updates to confirm the stream is actually flowing,
	// then cancel and confirm Recv unblocks (rather than hanging until a
	// test timeout, which is what a leaked/ignoring-cancellation handler
	// would produce).
	if _, err := stream.Recv(); err != nil {
		t.Fatalf("first Recv: %v", err)
	}
	cancel()

	done := make(chan struct{})
	go func() {
		for {
			if _, err := stream.Recv(); err != nil {
				close(done)
				return
			}
		}
	}()

	select {
	case <-done:
		// good: stream ended promptly after cancellation.
	case <-time.After(2 * time.Second):
		t.Fatal("stream did not end after client cancellation (handler leaked)")
	}
}

func TestRecordSales_ClientStreaming_Aggregates(t *testing.T) {
	client := testServer(t, defaultSeed())

	stream, err := client.RecordSales(context.Background())
	if err != nil {
		t.Fatalf("RecordSales: %v", err)
	}

	sales := []*inventorypb.SaleRecord{
		{Sku: "sku-widget", Quantity: 5},
		{Sku: "sku-widget", Quantity: 3},
		{Sku: "sku-gadget", Quantity: 10},
	}
	for _, s := range sales {
		if err := stream.Send(s); err != nil {
			t.Fatalf("Send(%+v): %v", s, err)
		}
	}

	summary, err := stream.CloseAndRecv()
	if err != nil {
		t.Fatalf("CloseAndRecv: %v", err)
	}
	if summary.GetTotalQuantity() != 18 || summary.GetRecordCount() != 3 {
		t.Fatalf("summary = %+v, want total=18 count=3", summary)
	}

	// Confirm the sales were actually applied to server-side stock, not
	// just summarized.
	item, err := client.GetItem(context.Background(), &inventorypb.GetItemRequest{Sku: "sku-widget"})
	if err != nil {
		t.Fatalf("GetItem after RecordSales: %v", err)
	}
	if item.GetQuantity() != 100-5-3 {
		t.Fatalf("sku-widget quantity = %d, want %d", item.GetQuantity(), 100-5-3)
	}
}

func TestRecordSales_RejectsNonPositiveQuantity(t *testing.T) {
	client := testServer(t, defaultSeed())

	stream, err := client.RecordSales(context.Background())
	if err != nil {
		t.Fatalf("RecordSales: %v", err)
	}
	if err := stream.Send(&inventorypb.SaleRecord{Sku: "sku-widget", Quantity: 0}); err != nil {
		t.Fatalf("Send: %v", err)
	}

	_, err = stream.CloseAndRecv()
	if got := status.Code(err); got != codes.InvalidArgument {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.InvalidArgument, err)
	}
}

func TestRecordSales_UnknownSKU(t *testing.T) {
	client := testServer(t, defaultSeed())

	stream, err := client.RecordSales(context.Background())
	if err != nil {
		t.Fatalf("RecordSales: %v", err)
	}
	if err := stream.Send(&inventorypb.SaleRecord{Sku: "sku-does-not-exist", Quantity: 1}); err != nil {
		t.Fatalf("Send: %v", err)
	}

	_, err = stream.CloseAndRecv()
	if got := status.Code(err); got != codes.NotFound {
		t.Fatalf("status code = %v, want %v (err=%v)", got, codes.NotFound, err)
	}
}
