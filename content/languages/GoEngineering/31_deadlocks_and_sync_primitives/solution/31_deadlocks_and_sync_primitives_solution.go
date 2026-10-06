// Package syncprim is the reference solution for Problem 31 — Deadlocks &
// Sync Primitives. Several functions deliberately contain the bug they teach
// (TransferNaive, GetOrDefaultBad); they take a `between` hook so tests can
// force the fatal interleaving deterministically instead of hoping for it.
package syncprim

import (
	"errors"
	"hash/maphash"
	"math/rand/v2"
	"sync"
	"sync/atomic"
	"time"
)

var (
	ErrInsufficientFunds = errors.New("syncprim: insufficient funds")
	ErrSameAccount       = errors.New("syncprim: cannot transfer to the same account")
	ErrContended         = errors.New("syncprim: could not acquire both locks")
)

// ============================================================================
// 1. Lock ordering
// ============================================================================

// Account is a bank account guarded by its own mutex. Must not be copied
// after first use (go vet's copylocks check enforces this).
type Account struct {
	ID      int
	mu      sync.Mutex
	balance int64
}

// NewAccount returns an account with an opening balance.
func NewAccount(id int, balance int64) *Account {
	return &Account{ID: id, balance: balance}
}

// Balance returns the current balance.
func (a *Account) Balance() int64 {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.balance
}

// Transfer moves amount between two accounts atomically.
//
// Deadlock-freedom comes from a GLOBAL LOCK ORDER: every goroutine acquires
// the lower-ID account's mutex first. A cycle in the "waits-for" graph needs
// someone to hold a higher lock while waiting for a lower one, which this
// rule makes impossible. The order must be total and stable — IDs work;
// pointer addresses would too (they don't move for heap objects), but IDs are
// easier to reason about and log.
func Transfer(from, to *Account, amount int64) error {
	if from == to || from.ID == to.ID {
		// Locking the same non-reentrant mutex twice would self-deadlock.
		return ErrSameAccount
	}
	first, second := from, to
	if second.ID < first.ID {
		first, second = second, first
	}
	first.mu.Lock()
	defer first.mu.Unlock()
	second.mu.Lock()
	defer second.mu.Unlock()

	if from.balance < amount {
		return ErrInsufficientFunds
	}
	from.balance -= amount
	to.balance += amount
	return nil
}

// TransferNaive locks `from` then `to`. Two concurrent transfers in opposite
// directions can each take their first lock and wait forever for the other's:
// the deadly embrace. between (may be nil) runs while holding only the first
// lock, which lets a test force that interleaving. DO NOT USE.
func TransferNaive(from, to *Account, amount int64, between func()) error {
	from.mu.Lock()
	defer from.mu.Unlock()
	if between != nil {
		between()
	}
	to.mu.Lock()
	defer to.mu.Unlock()

	if from.balance < amount {
		return ErrInsufficientFunds
	}
	from.balance -= amount
	to.balance += amount
	return nil
}

// TransferTry avoids deadlock without a global order: take the first lock,
// then TryLock the second; on failure release EVERYTHING, back off, retry.
// Breaking "hold and wait" removes one of the four necessary deadlock
// conditions. The costs: possible livelock under heavy contention (hence
// jittered backoff and a bounded attempt count) and unfair scheduling.
// Mutex.TryLock's own docs warn that correct uses are rare; lock ordering
// is almost always the better answer. between runs after the first lock.
func TransferTry(from, to *Account, amount int64, attempts int, between func()) error {
	if from == to || from.ID == to.ID {
		return ErrSameAccount
	}
	backoff := 50 * time.Microsecond
	for range attempts {
		from.mu.Lock()
		if between != nil {
			between()
		}
		if to.mu.TryLock() {
			var err error
			if from.balance < amount {
				err = ErrInsufficientFunds
			} else {
				from.balance -= amount
				to.balance += amount
			}
			to.mu.Unlock()
			from.mu.Unlock()
			return err
		}
		from.mu.Unlock() // release what we hold before waiting: no hold-and-wait
		// Jitter matters: two goroutines backing off by identical durations
		// retry in lock-step and can collide forever (livelock).
		time.Sleep(backoff/2 + rand.N(backoff/2))
		backoff = min(backoff*2, 5*time.Millisecond)
	}
	return ErrContended
}

// ============================================================================
// 2. Detecting a hang
// ============================================================================

// Completes runs fn in a new goroutine and reports whether it returned
// within timeout. If it did not, that goroutine is leaked — there is no way
// to kill a goroutine from outside in Go. Use this in tests and diagnostics,
// never as a production "timeout" for lock acquisition (use context-aware
// designs or TryLock loops for that).
func Completes(timeout time.Duration, fn func()) bool {
	done := make(chan struct{})
	go func() {
		defer close(done)
		fn()
	}()
	select {
	case <-done:
		return true
	case <-time.After(timeout):
		return false
	}
}

// ============================================================================
// 3. RWMutex: recursive read locking deadlocks with a waiting writer
// ============================================================================

// Registry is a read-mostly map guarded by an RWMutex.
type Registry struct {
	mu sync.RWMutex
	m  map[string]string
}

// NewRegistry returns an empty registry.
func NewRegistry() *Registry { return &Registry{m: map[string]string{}} }

// Get returns the value for k.
func (r *Registry) Get(k string) (string, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.getLocked(k)
}

// getLocked requires r.mu to be held (read or write) by the caller. The
// "...Locked" suffix is a common Go convention for exactly this contract.
func (r *Registry) getLocked(k string) (string, bool) {
	v, ok := r.m[k]
	return v, ok
}

// Set stores v under k.
func (r *Registry) Set(k, v string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.m[k] = v
}

// GetOrDefaultBad takes a read lock and then calls Get, which takes the read
// lock AGAIN. That usually works — until a writer calls Lock between the two
// RLocks. sync.RWMutex blocks new readers once a writer is waiting (so writers
// can't starve), so the inner RLock waits for the writer, and the writer waits
// for the outer RLock to be released: deadlock. between runs between the two
// RLocks so a test can force it. DO NOT USE.
func (r *Registry) GetOrDefaultBad(k, def string, between func()) string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if between != nil {
		between()
	}
	if v, ok := r.Get(k); ok { // recursive RLock
		return v
	}
	return def
}

// GetOrDefault is the fix: take the lock once at the public entry point and
// call the unlocked helper internally. The same between hook proves the
// writer can no longer wedge it.
func (r *Registry) GetOrDefault(k, def string, between func()) string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if between != nil {
		between()
	}
	if v, ok := r.getLocked(k); ok {
		return v
	}
	return def
}

// ============================================================================
// 4. Once semantics: errors are cached forever
// ============================================================================

// OnceRetry runs load until it succeeds once, then caches the value.
// Contrast with sync.OnceValues, which caches the FIRST result — including an
// error — forever: a transient failure during lazy init (DNS blip while
// dialing a DB) would poison the process until restart.
type OnceRetry[T any] struct {
	mu   sync.Mutex
	done atomic.Bool
	val  T
	load func() (T, error)
}

// NewOnceRetry wraps load.
func NewOnceRetry[T any](load func() (T, error)) *OnceRetry[T] {
	return &OnceRetry[T]{load: load}
}

// Get returns the cached value, or calls load if no call has succeeded yet.
// Concurrent callers while a load is in flight wait for it (they queue on the
// mutex) rather than stampeding the backend.
func (o *OnceRetry[T]) Get() (T, error) {
	// Fast path: one atomic read, no lock, after the first success. This is
	// the same double-checked pattern sync.Once uses internally.
	if o.done.Load() {
		return o.val, nil
	}
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.done.Load() { // someone else succeeded while we waited for the lock
		return o.val, nil
	}
	v, err := o.load()
	if err != nil {
		var zero T
		return zero, err // not cached: the next Get retries
	}
	o.val = v
	o.done.Store(true) // publish AFTER val is written
	return v, nil
}

// ============================================================================
// 5. Reducing contention: lock striping
// ============================================================================

const counterShards = 32

// ShardedCounter is a map of counters split across independently locked
// shards. One global mutex serialises every Inc on every core; with N shards,
// goroutines touching different keys rarely contend.
//
// Measured (Apple M4 Pro, 1024 keys): global mutex 10.2 / 113.9 / 164.3 ns/op
// at 1 / 4 / 12 cores; sharded 13.3 / 17.5 / 44.7 ns/op. Slightly slower on
// one core (the hash), 3.7-6.5x faster once there is real contention.
type ShardedCounter struct {
	seed   maphash.Seed
	shards [counterShards]counterShard
}

type counterShard struct {
	mu sync.Mutex
	m  map[string]int64
	// Padding so adjacent shards' mutexes don't share a 64-byte cache line;
	// otherwise locking shard 3 still invalidates shard 4's cache line
	// ("false sharing") and much of the benefit evaporates.
	_ [40]byte
}

// NewShardedCounter returns an empty counter.
func NewShardedCounter() *ShardedCounter {
	c := &ShardedCounter{seed: maphash.MakeSeed()}
	for i := range c.shards {
		c.shards[i].m = map[string]int64{}
	}
	return c
}

func (c *ShardedCounter) shard(key string) *counterShard {
	return &c.shards[maphash.String(c.seed, key)%counterShards]
}

// Inc adds one to key.
func (c *ShardedCounter) Inc(key string) {
	s := c.shard(key)
	s.mu.Lock()
	s.m[key]++
	s.mu.Unlock() // no defer on a 3-line hot path; nothing between can panic
}

// Get returns key's count.
func (c *ShardedCounter) Get(key string) int64 {
	s := c.shard(key)
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.m[key]
}
