package repository

import (
	"context"
	"errors"
	"path/filepath"
	"sync"
	"testing"
)

// newTestRepo opens a fresh temp-file SQLite database for one test. Per the
// ":memory:" + connection-pool footgun documented in the explanation file,
// tests always use a t.TempDir()-rooted file DSN, never ":memory:" — this
// keeps every test hermetic and safe to run with -parallel, and exercises
// the same code path a real file-backed deployment would take.
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

func TestOpen_PingsAndCreatesSchema(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)

	// Schema should already exist: a query against it should succeed with
	// zero rows, not fail with "no such table".
	accounts, err := r.ListAccounts(context.Background(), "")
	if err != nil {
		t.Fatalf("ListAccounts on fresh DB: %v", err)
	}
	if len(accounts) != 0 {
		t.Fatalf("ListAccounts on fresh DB = %v, want empty", accounts)
	}
}

func TestCreateAndGetAccount(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	created, err := r.CreateAccount(ctx, "alice", 1000)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}
	if created.ID == 0 {
		t.Fatal("CreateAccount returned zero ID")
	}
	if created.Owner != "alice" || created.Balance != 1000 {
		t.Fatalf("CreateAccount = %+v, want Owner=alice Balance=1000", created)
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

	_, err := r.GetAccount(context.Background(), 999)
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("GetAccount(999) err = %v, want ErrNotFound", err)
	}
}

func TestListAccounts_AllVsFiltered(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	owners := []string{"alice", "alicia", "bob"}
	for _, o := range owners {
		if _, err := r.CreateAccount(ctx, o, 100); err != nil {
			t.Fatalf("CreateAccount(%q): %v", o, err)
		}
	}

	all, err := r.ListAccounts(ctx, "")
	if err != nil {
		t.Fatalf("ListAccounts(\"\"): %v", err)
	}
	if len(all) != len(owners) {
		t.Fatalf("ListAccounts(\"\") returned %d accounts, want %d", len(all), len(owners))
	}

	filtered, err := r.ListAccounts(ctx, "ali%")
	if err != nil {
		t.Fatalf("ListAccounts(\"ali%%\"): %v", err)
	}
	if len(filtered) != 2 {
		t.Fatalf("ListAccounts(\"ali%%\") returned %d accounts, want 2", len(filtered))
	}
	for _, a := range filtered {
		if a.Owner != "alice" && a.Owner != "alicia" {
			t.Errorf("ListAccounts(\"ali%%\") unexpectedly matched owner %q", a.Owner)
		}
	}

	none, err := r.ListAccounts(ctx, "zzz%")
	if err != nil {
		t.Fatalf("ListAccounts(\"zzz%%\"): %v", err)
	}
	if len(none) != 0 {
		t.Fatalf("ListAccounts(\"zzz%%\") = %v, want empty", none)
	}
}

func TestUpdateBalance(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	acc, err := r.CreateAccount(ctx, "carol", 500)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}

	if err := r.UpdateBalance(ctx, acc.ID, 750); err != nil {
		t.Fatalf("UpdateBalance: %v", err)
	}

	got, err := r.GetAccount(ctx, acc.ID)
	if err != nil {
		t.Fatalf("GetAccount: %v", err)
	}
	if got.Balance != 750 {
		t.Fatalf("Balance after update = %d, want 750", got.Balance)
	}
}

func TestUpdateBalance_NotFound(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)

	err := r.UpdateBalance(context.Background(), 999, 100)
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("UpdateBalance(999) err = %v, want ErrNotFound", err)
	}
}

func TestDeleteAccount(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	acc, err := r.CreateAccount(ctx, "dave", 200)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}

	if err := r.DeleteAccount(ctx, acc.ID); err != nil {
		t.Fatalf("DeleteAccount: %v", err)
	}

	if _, err := r.GetAccount(ctx, acc.ID); !errors.Is(err, ErrNotFound) {
		t.Fatalf("GetAccount after delete err = %v, want ErrNotFound", err)
	}
}

func TestDeleteAccount_NotFound(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)

	err := r.DeleteAccount(context.Background(), 999)
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("DeleteAccount(999) err = %v, want ErrNotFound", err)
	}
}

func TestClose_SafeToCallTwice(t *testing.T) {
	t.Parallel()
	path := filepath.Join(t.TempDir(), "test.db")
	r, err := Open(context.Background(), path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	if err := r.Close(); err != nil {
		t.Fatalf("first Close: %v", err)
	}
	if err := r.Close(); err != nil {
		t.Fatalf("second Close: %v", err)
	}
}

// TestConcurrentAccess exercises the repository from many goroutines at
// once. With SetMaxOpenConns(1) inside Open, SQLite-level access is fully
// serialized, but this test is run under -race specifically to prove there
// is no *Go-level* data race in this package's own code (e.g. shared state
// on *Repository itself), independent of whatever guarantees SQLite's file
// locking provides.
func TestConcurrentAccess(t *testing.T) {
	t.Parallel()
	r := newTestRepo(t)
	ctx := context.Background()

	acc, err := r.CreateAccount(ctx, "shared", 0)
	if err != nil {
		t.Fatalf("CreateAccount: %v", err)
	}

	const goroutines = 16
	const itersPerGoroutine = 10

	var wg sync.WaitGroup
	errCh := make(chan error, goroutines*itersPerGoroutine)
	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func(g int) {
			defer wg.Done()
			for i := 0; i < itersPerGoroutine; i++ {
				if err := r.UpdateBalance(ctx, acc.ID, int64(g*itersPerGoroutine+i)); err != nil {
					errCh <- err
					continue
				}
				if _, err := r.GetAccount(ctx, acc.ID); err != nil {
					errCh <- err
				}
			}
		}(g)
	}
	wg.Wait()
	close(errCh)

	for err := range errCh {
		t.Errorf("concurrent operation failed: %v", err)
	}
}
