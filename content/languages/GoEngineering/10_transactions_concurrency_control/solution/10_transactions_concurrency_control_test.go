package txnctl

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"sync"
	"testing"
)

// newTestRepo opens a fresh temp-file SQLite database for one test. Same
// ":memory:" + connection-pool footgun rationale as Problem 09: always a
// t.TempDir()-rooted file DSN, never ":memory:", so tests stay hermetic and
// safe under -parallel.
func newTestRepo(t *testing.T) *Repository {
	t.Helper()
	path := filepath.Join(t.TempDir(), "test.db")
	r, err := Open(context.Background(), path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	t.Cleanup(func() { r.Close() })
	return r
}

func TestCreateAndGetAccount(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	created, err := r.CreateAccount(ctx, "alice", 1000)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}
	if created.Version != 1 {
		t.Fatalf("CreateAccount version = %d, want 1", created.Version)
	}

	got, err := r.GetAccount(ctx, created.ID)
	if err != nil {
		t.Fatalf("GetAccount: %v", err)
	}
	if got != created {
		t.Fatalf("GetAccount = %+v, want %+v", got, created)
	}
}

func TestGetAccount_NotFound(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)

	if _, err := r.GetAccount(context.Background(), 999); !errors.Is(err, ErrNotFound) {
		t.Fatalf("GetAccount(999) err = %v, want ErrNotFound", err)
	}
}

func TestUpdateBalanceCAS_Success(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	acc, err := r.CreateAccount(ctx, "bob", 500)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}

	if err := r.UpdateBalanceCAS(ctx, acc.ID, 600, acc.Version); err != nil {
		t.Fatalf("UpdateBalanceCAS: %v", err)
	}

	got, err := r.GetAccount(ctx, acc.ID)
	if err != nil {
		t.Fatalf("GetAccount: %v", err)
	}
	if got.Balance != 600 {
		t.Errorf("Balance = %d, want 600", got.Balance)
	}
	if got.Version != acc.Version+1 {
		t.Errorf("Version = %d, want %d", got.Version, acc.Version+1)
	}
}

func TestUpdateBalanceCAS_StaleVersionConflict(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	acc, err := r.CreateAccount(ctx, "carol", 500)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}

	// First writer succeeds, bumping the version.
	if err := r.UpdateBalanceCAS(ctx, acc.ID, 700, acc.Version); err != nil {
		t.Fatalf("first UpdateBalanceCAS: %v", err)
	}

	// Second writer still holds the STALE (original) version -> must be
	// rejected, not silently overwrite the first writer's update.
	err = r.UpdateBalanceCAS(ctx, acc.ID, 999, acc.Version)
	if !errors.Is(err, ErrVersionConflict) {
		t.Fatalf("stale UpdateBalanceCAS err = %v, want ErrVersionConflict", err)
	}

	// The first writer's value must still stand.
	got, err := r.GetAccount(ctx, acc.ID)
	if err != nil {
		t.Fatalf("GetAccount: %v", err)
	}
	if got.Balance != 700 {
		t.Errorf("Balance = %d, want 700 (stale write must not have applied)", got.Balance)
	}
}

func TestUpdateBalanceCAS_NotFound(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)

	err := r.UpdateBalanceCAS(context.Background(), 999, 100, 1)
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("UpdateBalanceCAS(999) err = %v, want ErrNotFound", err)
	}
}

func TestTransfer_MovesBalance(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	a, err := r.CreateAccount(ctx, "a", 1000)
	if err != nil {
		t.Fatalf("CreateAccount a: %v", err)
	}
	b, err := r.CreateAccount(ctx, "b", 200)
	if err != nil {
		t.Fatalf("CreateAccount b: %v", err)
	}

	if err := r.Transfer(ctx, a.ID, b.ID, 300); err != nil {
		t.Fatalf("Transfer: %v", err)
	}

	gotA, err := r.GetAccount(ctx, a.ID)
	if err != nil {
		t.Fatalf("GetAccount a: %v", err)
	}
	gotB, err := r.GetAccount(ctx, b.ID)
	if err != nil {
		t.Fatalf("GetAccount b: %v", err)
	}
	if gotA.Balance != 700 {
		t.Errorf("account a balance = %d, want 700", gotA.Balance)
	}
	if gotB.Balance != 500 {
		t.Errorf("account b balance = %d, want 500", gotB.Balance)
	}
}

func TestTransfer_InsufficientFundsRollsBack(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	a, err := r.CreateAccount(ctx, "a", 100)
	if err != nil {
		t.Fatalf("CreateAccount a: %v", err)
	}
	b, err := r.CreateAccount(ctx, "b", 100)
	if err != nil {
		t.Fatalf("CreateAccount b: %v", err)
	}

	err = r.Transfer(ctx, a.ID, b.ID, 500)
	if !errors.Is(err, ErrInsufficientFunds) {
		t.Fatalf("Transfer err = %v, want ErrInsufficientFunds", err)
	}

	// Neither balance should have moved.
	gotA, _ := r.GetAccount(ctx, a.ID)
	gotB, _ := r.GetAccount(ctx, b.ID)
	if gotA.Balance != 100 || gotB.Balance != 100 {
		t.Errorf("balances after failed transfer = a:%d b:%d, want a:100 b:100", gotA.Balance, gotB.Balance)
	}
}

func TestTransfer_NotFound(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	a, err := r.CreateAccount(ctx, "a", 100)
	if err != nil {
		t.Fatalf("CreateAccount a: %v", err)
	}

	if err := r.Transfer(ctx, a.ID, 999, 10); !errors.Is(err, ErrNotFound) {
		t.Fatalf("Transfer to missing account err = %v, want ErrNotFound", err)
	}
	if err := r.Transfer(ctx, 999, a.ID, 10); !errors.Is(err, ErrNotFound) {
		t.Fatalf("Transfer from missing account err = %v, want ErrNotFound", err)
	}
}

// TestTransfer_ConcurrentBothDirectionsPreservesTotal hammers the same pair
// of accounts with concurrent transfers in BOTH directions, from many
// goroutines. The fixed ascending-ID lock ordering inside transferOnce is
// what keeps this from deadlocking; the transaction (and retry-on-busy) is
// what keeps the total balance conserved and no account negative. Run
// under -race to also confirm no Go-level data race in the retry/goroutine
// bookkeeping itself.
func TestTransfer_ConcurrentBothDirectionsPreservesTotal(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	const startBalance = 100_000
	a, err := r.CreateAccount(ctx, "a", startBalance)
	if err != nil {
		t.Fatalf("CreateAccount a: %v", err)
	}
	b, err := r.CreateAccount(ctx, "b", startBalance)
	if err != nil {
		t.Fatalf("CreateAccount b: %v", err)
	}
	total := a.Balance + b.Balance

	const goroutines = 20
	const transfersPerGoroutine = 15
	const amount = 10

	var wg sync.WaitGroup
	errCh := make(chan error, goroutines*transfersPerGoroutine)
	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func(g int) {
			defer wg.Done()
			for i := 0; i < transfersPerGoroutine; i++ {
				var err error
				if (g+i)%2 == 0 {
					err = r.Transfer(ctx, a.ID, b.ID, amount)
				} else {
					err = r.Transfer(ctx, b.ID, a.ID, amount)
				}
				// ErrInsufficientFunds is an acceptable, non-retried
				// outcome if a goroutine's account happens to be too low
				// at that moment; anything else is unexpected.
				if err != nil && !errors.Is(err, ErrInsufficientFunds) {
					errCh <- err
				}
			}
		}(g)
	}
	wg.Wait()
	close(errCh)

	for err := range errCh {
		t.Errorf("unexpected transfer error: %v", err)
	}

	gotA, err := r.GetAccount(ctx, a.ID)
	if err != nil {
		t.Fatalf("GetAccount a: %v", err)
	}
	gotB, err := r.GetAccount(ctx, b.ID)
	if err != nil {
		t.Fatalf("GetAccount b: %v", err)
	}
	if gotA.Balance < 0 || gotB.Balance < 0 {
		t.Errorf("negative balance after concurrent transfers: a=%d b=%d", gotA.Balance, gotB.Balance)
	}
	if gotSum := gotA.Balance + gotB.Balance; gotSum != total {
		t.Errorf("total balance changed: got %d, want %d (a=%d b=%d)", gotSum, total, gotA.Balance, gotB.Balance)
	}
}

// TestWithRetry_NonRetryableFailsFast asserts a non-retryable error (a
// business-rule sentinel, not a SQLITE_BUSY-shaped one) propagates on the
// FIRST call to fn — WithRetry must not mask or delay it with retries.
func TestWithRetry_NonRetryableFailsFast(t *testing.T) {
	t.Parallel()
	calls := 0
	err := WithRetry(context.Background(), 5, func() error {
		calls++
		return ErrInsufficientFunds
	})
	if !errors.Is(err, ErrInsufficientFunds) {
		t.Fatalf("WithRetry err = %v, want ErrInsufficientFunds", err)
	}
	if calls != 1 {
		t.Fatalf("fn called %d times, want exactly 1 (non-retryable error must not retry)", calls)
	}
}

// mustBusyErr triggers a genuine SQLITE_BUSY from the real driver (rather
// than fabricating one — *sqlitedrv.Error's fields are unexported, so
// there's no way to construct one from outside modernc.org/sqlite) by
// holding an uncommitted write transaction open on one connection while a
// second, independent connection to the SAME file attempts to write. No
// busy_timeout is configured on either connection, so the second write
// fails immediately with SQLITE_BUSY instead of blocking.
func mustBusyErr(t *testing.T, dir string) error {
	t.Helper()
	path := filepath.Join(dir, "busy.db")

	dbA, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatalf("open dbA: %v", err)
	}
	defer dbA.Close()
	dbA.SetMaxOpenConns(1)
	if _, err := dbA.Exec(`CREATE TABLE t (id INTEGER PRIMARY KEY)`); err != nil {
		t.Fatalf("create table: %v", err)
	}

	dbB, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatalf("open dbB: %v", err)
	}
	defer dbB.Close()
	dbB.SetMaxOpenConns(1)

	txA, err := dbA.Begin()
	if err != nil {
		t.Fatalf("begin txA: %v", err)
	}
	defer txA.Rollback() //nolint:errcheck
	// SQLite's default deferred BEGIN doesn't take the write lock until
	// the first actual write — this INSERT is what grabs it.
	if _, err := txA.Exec(`INSERT INTO t DEFAULT VALUES`); err != nil {
		t.Fatalf("txA insert: %v", err)
	}

	_, err = dbB.Exec(`INSERT INTO t DEFAULT VALUES`)
	if err == nil {
		t.Fatal("expected dbB write to fail with SQLITE_BUSY while txA holds the write lock, got nil")
	}
	if !isRetryable(err) {
		t.Fatalf("triggered error is not classified retryable by isRetryable: %v", err)
	}
	return err
}

func TestIsRetryable_DistinguishesBusyFromOther(t *testing.T) {
	t.Parallel()
	busy := mustBusyErr(t, t.TempDir())
	if !isRetryable(busy) {
		t.Error("isRetryable(SQLITE_BUSY) = false, want true")
	}
	if isRetryable(ErrInsufficientFunds) {
		t.Error("isRetryable(ErrInsufficientFunds) = true, want false")
	}
	if isRetryable(nil) {
		t.Error("isRetryable(nil) = true, want false")
	}
}

// TestWithRetry_SucceedsAfterTransientFailures reuses a single captured
// real SQLITE_BUSY error as the simulated failure for the first few calls
// to fn, then succeeds — WithRetry only inspects the error's
// classification (via isRetryable), so reusing one captured instance
// across simulated attempts is representative of the real retry loop.
func TestWithRetry_SucceedsAfterTransientFailures(t *testing.T) {
	t.Parallel()
	busy := mustBusyErr(t, t.TempDir())

	calls := 0
	const failuresBeforeSuccess = 2
	err := WithRetry(context.Background(), 5, func() error {
		calls++
		if calls <= failuresBeforeSuccess {
			return busy
		}
		return nil
	})
	if err != nil {
		t.Fatalf("WithRetry: %v", err)
	}
	if calls != failuresBeforeSuccess+1 {
		t.Fatalf("fn called %d times, want %d", calls, failuresBeforeSuccess+1)
	}
}

func TestWithRetry_ExhaustsAttempts(t *testing.T) {
	t.Parallel()
	busy := mustBusyErr(t, t.TempDir())

	calls := 0
	const maxAttempts = 3
	err := WithRetry(context.Background(), maxAttempts, func() error {
		calls++
		return busy
	})
	if err == nil {
		t.Fatal("expected WithRetry to return an error after exhausting attempts")
	}
	if calls != maxAttempts {
		t.Fatalf("fn called %d times, want exactly %d", calls, maxAttempts)
	}
}
