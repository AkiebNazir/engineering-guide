package layering

import (
	"context"
	"errors"
	"testing"
	"time"
)

// repoFactory lets every table-driven test below run unchanged against both
// adapters — proving OrderService is adapter-agnostic by construction, not
// just by convention (see the explanation file's stretch goals).
type repoFactory struct {
	name string
	new  func() OrderRepository
}

func repoFactories() []repoFactory {
	return []repoFactory{
		{"InMemoryOrderRepository", func() OrderRepository { return NewInMemoryOrderRepository() }},
		{"RecordingOrderRepository", func() OrderRepository { return NewRecordingOrderRepository() }},
	}
}

func TestPlaceOrder(t *testing.T) {
	for _, rf := range repoFactories() {
		t.Run(rf.name, func(t *testing.T) {
			ctx := context.Background()
			repo := rf.new()
			clock := FixedClock{At: time.Date(2026, 1, 1, 12, 0, 0, 0, time.UTC)}
			svc := NewOrderService(repo, clock)

			o, err := svc.PlaceOrder(ctx, "cust-1", 1000)
			if err != nil {
				t.Fatalf("PlaceOrder: %v", err)
			}
			if o.CustomerID != "cust-1" {
				t.Fatalf("CustomerID = %q, want %q", o.CustomerID, "cust-1")
			}
			if o.TotalCents != 1000 {
				t.Fatalf("TotalCents = %d, want 1000", o.TotalCents)
			}
			if o.Status != OrderPending {
				t.Fatalf("Status = %v, want OrderPending", o.Status)
			}
			if !o.PlacedAt.Equal(clock.At) {
				t.Fatalf("PlacedAt = %v, want %v (Clock port not honored)", o.PlacedAt, clock.At)
			}
			if o.ID == "" {
				t.Fatal("ID must not be empty")
			}

			// The port's FindByID must return exactly what Save persisted —
			// the whole point of depending on the interface, not a concrete
			// adapter, is that this assertion holds for either adapter.
			got, err := repo.FindByID(ctx, o.ID)
			if err != nil {
				t.Fatalf("FindByID: %v", err)
			}
			if got != o {
				t.Fatalf("FindByID = %+v, want %+v", got, o)
			}
		})
	}
}

func TestPlaceOrderValidation(t *testing.T) {
	tests := []struct {
		name       string
		customerID string
		totalCents int64
		wantErr    bool
	}{
		{"empty customer id", "", 100, true},
		{"negative total", "cust-1", -1, true},
		{"zero total is allowed", "cust-1", 0, false},
		{"valid", "cust-1", 500, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := context.Background()
			svc := NewOrderService(NewInMemoryOrderRepository(), SystemClock{})
			_, err := svc.PlaceOrder(ctx, tt.customerID, tt.totalCents)
			if (err != nil) != tt.wantErr {
				t.Fatalf("PlaceOrder(%q, %d) err = %v, wantErr %v", tt.customerID, tt.totalCents, err, tt.wantErr)
			}
		})
	}
}

func TestConfirmOrder(t *testing.T) {
	for _, rf := range repoFactories() {
		t.Run(rf.name, func(t *testing.T) {
			ctx := context.Background()
			repo := rf.new()
			svc := NewOrderService(repo, SystemClock{})

			o, err := svc.PlaceOrder(ctx, "cust-1", 100)
			if err != nil {
				t.Fatalf("PlaceOrder: %v", err)
			}
			if err := svc.ConfirmOrder(ctx, o.ID); err != nil {
				t.Fatalf("ConfirmOrder: %v", err)
			}

			got, err := repo.FindByID(ctx, o.ID)
			if err != nil {
				t.Fatalf("FindByID: %v", err)
			}
			if got.Status != OrderConfirmed {
				t.Fatalf("Status = %v, want OrderConfirmed", got.Status)
			}

			// Confirming an already-confirmed order is documented as an
			// idempotent no-op, not an error.
			if err := svc.ConfirmOrder(ctx, o.ID); err != nil {
				t.Fatalf("ConfirmOrder (idempotent re-confirm) = %v, want nil", err)
			}
		})
	}
}

func TestCancelOrder(t *testing.T) {
	for _, rf := range repoFactories() {
		t.Run(rf.name, func(t *testing.T) {
			ctx := context.Background()
			repo := rf.new()
			svc := NewOrderService(repo, SystemClock{})

			o, err := svc.PlaceOrder(ctx, "cust-1", 100)
			if err != nil {
				t.Fatalf("PlaceOrder: %v", err)
			}
			if err := svc.CancelOrder(ctx, o.ID); err != nil {
				t.Fatalf("CancelOrder: %v", err)
			}

			got, err := repo.FindByID(ctx, o.ID)
			if err != nil {
				t.Fatalf("FindByID: %v", err)
			}
			if got.Status != OrderCancelled {
				t.Fatalf("Status = %v, want OrderCancelled", got.Status)
			}

			// Idempotent re-cancel.
			if err := svc.CancelOrder(ctx, o.ID); err != nil {
				t.Fatalf("CancelOrder (idempotent re-cancel) = %v, want nil", err)
			}
		})
	}
}

func TestCannotConfirmCancelledOrder(t *testing.T) {
	for _, rf := range repoFactories() {
		t.Run(rf.name, func(t *testing.T) {
			ctx := context.Background()
			repo := rf.new()
			svc := NewOrderService(repo, SystemClock{})

			o, err := svc.PlaceOrder(ctx, "cust-1", 100)
			if err != nil {
				t.Fatalf("PlaceOrder: %v", err)
			}
			if err := svc.CancelOrder(ctx, o.ID); err != nil {
				t.Fatalf("CancelOrder: %v", err)
			}
			if err := svc.ConfirmOrder(ctx, o.ID); err == nil {
				t.Fatal("ConfirmOrder on a cancelled order = nil, want error")
			}
		})
	}
}

func TestFindByIDNotFoundIsErrOrderNotFound(t *testing.T) {
	for _, rf := range repoFactories() {
		t.Run(rf.name, func(t *testing.T) {
			ctx := context.Background()
			repo := rf.new()

			_, err := repo.FindByID(ctx, "does-not-exist")
			if !errors.Is(err, ErrOrderNotFound) {
				t.Fatalf("FindByID(missing) err = %v, want wrapping ErrOrderNotFound", err)
			}
		})
	}
}

func TestConfirmOrderMissingIsNotFound(t *testing.T) {
	ctx := context.Background()
	svc := NewOrderService(NewInMemoryOrderRepository(), SystemClock{})

	err := svc.ConfirmOrder(ctx, "does-not-exist")
	if !errors.Is(err, ErrOrderNotFound) {
		t.Fatalf("ConfirmOrder(missing) err = %v, want wrapping ErrOrderNotFound", err)
	}
}

// TestRecordingOrderRepositoryTracksCalls exercises the second adapter's
// extra behavior (over and above satisfying OrderRepository): it must
// record every call made through it, in order, which is what makes it
// useful as a test double for asserting interaction patterns.
func TestRecordingOrderRepositoryTracksCalls(t *testing.T) {
	ctx := context.Background()
	repo := NewRecordingOrderRepository()
	svc := NewOrderService(repo, SystemClock{})

	o, err := svc.PlaceOrder(ctx, "cust-1", 100)
	if err != nil {
		t.Fatalf("PlaceOrder: %v", err)
	}
	if err := svc.ConfirmOrder(ctx, o.ID); err != nil {
		t.Fatalf("ConfirmOrder: %v", err)
	}

	calls := repo.Calls()
	want := []string{"Save:" + o.ID, "FindByID:" + o.ID, "UpdateStatus:" + o.ID + ":confirmed"}
	if len(calls) != len(want) {
		t.Fatalf("Calls() = %v, want %v", calls, want)
	}
	for i := range want {
		if calls[i] != want[i] {
			t.Fatalf("Calls()[%d] = %q, want %q", i, calls[i], want[i])
		}
	}
}

// TestSwappingAdapterIsOneLine proves the acceptance criterion directly:
// the ONLY difference between these two subtests is which concrete adapter
// is passed to NewOrderService — OrderService's own code path is identical.
func TestSwappingAdapterIsOneLine(t *testing.T) {
	ctx := context.Background()
	clock := FixedClock{At: time.Unix(0, 0)}

	run := func(repo OrderRepository) (Order, error) {
		svc := NewOrderService(repo, clock)
		o, err := svc.PlaceOrder(ctx, "cust-1", 250)
		if err != nil {
			return Order{}, err
		}
		if err := svc.ConfirmOrder(ctx, o.ID); err != nil {
			return Order{}, err
		}
		return o, nil
	}

	if _, err := run(NewInMemoryOrderRepository()); err != nil {
		t.Fatalf("run(InMemoryOrderRepository): %v", err)
	}
	if _, err := run(NewRecordingOrderRepository()); err != nil {
		t.Fatalf("run(RecordingOrderRepository): %v", err)
	}
}

func TestNewOrderServicePanicsOnNilDeps(t *testing.T) {
	assertPanics := func(t *testing.T, fn func()) {
		t.Helper()
		defer func() {
			if r := recover(); r == nil {
				t.Fatal("expected panic, got none")
			}
		}()
		fn()
	}

	t.Run("nil repo", func(t *testing.T) {
		assertPanics(t, func() { NewOrderService(nil, SystemClock{}) })
	})
	t.Run("nil clock", func(t *testing.T) {
		assertPanics(t, func() { NewOrderService(NewInMemoryOrderRepository(), nil) })
	})
}

func TestOrderStatusString(t *testing.T) {
	tests := []struct {
		status OrderStatus
		want   string
	}{
		{OrderPending, "pending"},
		{OrderConfirmed, "confirmed"},
		{OrderCancelled, "cancelled"},
		{OrderStatus(999), "unknown"},
	}
	for _, tt := range tests {
		if got := tt.status.String(); got != tt.want {
			t.Fatalf("OrderStatus(%d).String() = %q, want %q", tt.status, got, tt.want)
		}
	}
}

func TestRunExample(t *testing.T) {
	ctx := context.Background()
	final, err := RunExample(ctx)
	if err != nil {
		t.Fatalf("RunExample: %v", err)
	}
	if final.Status != OrderConfirmed {
		t.Fatalf("RunExample final Status = %v, want OrderConfirmed", final.Status)
	}
	if final.CustomerID != "cust-1" {
		t.Fatalf("RunExample final CustomerID = %q, want %q", final.CustomerID, "cust-1")
	}
}
