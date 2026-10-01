/*
Problem 31 — Deadlocks & Sync Primitives (lock ordering, RWMutex traps,
TryLock, Once semantics, lock striping, the race detector)

WHAT WE'RE BUILDING

A set of small, concurrency-safe components — each paired with the broken
version it replaces and a test that FORCES the bug to happen, instead of
hoping a race shows up:

 1. Transfer — money transfer between two mutex-guarded accounts using a
    global lock order. TransferNaive is the classic deadlock; a `between`
    hook lets the test wedge it deterministically.
 2. TransferTry — the alternative strategy: TryLock the second lock and
    back off (with jitter) instead of waiting while holding the first.
 3. Completes — run a function with a timeout to detect a hang in tests.
 4. Registry.GetOrDefault — the RWMutex "recursive read lock" deadlock
    that only happens when a writer arrives at the wrong moment, and the
    ...Locked-helper convention that fixes it.
 5. OnceRetry — lazy initialisation that retries on failure, contrasted
    with sync.OnceValues, which caches the first error forever.
 6. ShardedCounter — lock striping to cut contention, with cache-line
    padding against false sharing, benchmarked against one global mutex.

WHY THIS MATTERS IN REAL SYSTEMS

Deadlocks in Go services rarely crash anything. The runtime's famous
"fatal error: all goroutines are asleep - deadlock!" only fires when EVERY
goroutine is blocked — a server always has something alive (the HTTP
listener, a ticker, the signal handler), so a real deadlock looks like:

  - a handful of requests that never return, then connection pool
    exhaustion, then health checks timing out, then a restart that "fixes it";
  - goroutine count climbing steadily in your metrics;
  - a goroutine dump (SIGQUIT, or /debug/pprof/goroutine?debug=2) showing
    hundreds of goroutines in `sync.(*Mutex).Lock` with the same stack.

Data races are worse: silent wrong answers, corrupted maps, and
"impossible" states. The race detector finds them — but only on code paths
your tests actually execute concurrently.

MENTAL MODEL 1 — THE FOUR COFFMAN CONDITIONS

A deadlock needs ALL FOUR. Remove any one and it cannot happen.

    ┌──────────────────────┬──────────────────────────────────────────────┐
    │ condition            │ how Go code breaks it                        │
    ├──────────────────────┼──────────────────────────────────────────────┤
    │ mutual exclusion     │ avoid shared state: channels, atomics,       │
    │                      │ copy-on-write snapshots (Problem 26)         │
    │ hold and wait        │ acquire all locks at once, or TryLock and    │
    │                      │ release everything on failure (TransferTry)  │
    │ no preemption        │ timeouts / context cancellation on waits     │
    │                      │ (not possible for sync.Mutex itself)         │
    │ circular wait        │ GLOBAL LOCK ORDER (Transfer) ← the default   │
    └──────────────────────┴──────────────────────────────────────────────┘

MENTAL MODEL 2 — THE DEADLY EMBRACE

    goroutine G1: Transfer(A → B)        goroutine G2: Transfer(B → A)

         G1 ──holds──▶ [ A.mu ]  ◀──wants── G2
         G1 ──wants──▶ [ B.mu ]  ◀──holds── G2

    waits-for graph:   G1 ──▶ G2 ──▶ G1        a cycle = deadlock

    With a global order (lower ID first), BOTH goroutines lock A first:

         G1 ──holds──▶ [ A.mu ]  ◀──waits── G2     (G2 holds nothing)
         G1 ──holds──▶ [ B.mu ]
         G1 done, unlocks → G2 proceeds.            no cycle possible

Ordering by a stable, total key (database row ID, account number) also
makes the lock order visible in logs and code review. Rules that follow:
  - Transfer(a, a) must be rejected: sync.Mutex is not reentrant, locking
    it twice in one goroutine deadlocks immediately.
  - Never call out to unknown code (callbacks, interfaces, logging hooks
    that might lock) while holding a lock — you can't know its lock order.
  - Never do network or disk I/O while holding a lock: not a deadlock, but a
    latency amplifier that looks like one.

MENTAL MODEL 3 — RWMUTEX BLOCKS READERS WHILE A WRITER WAITS

To prevent writer starvation, sync.RWMutex makes RLock wait if any writer
has called Lock. That turns a harmless-looking recursive RLock into a
deadlock that needs precise timing — which is why it survives testing and
shows up in production under load:

    time ─────────────────────────────────────────────────────────────▶
    reader R:  RLock ✓ ────────────────────── RLock (inner Get) ✗ waits
                                   │                     │ for W
    writer W:          Lock() ✗ waits for R ────────────┘
                                   ▲
                       W is now "pending": new RLocks queue behind it

    R waits for W, W waits for R → deadlock. Neither ever proceeds.

Fix: take the lock exactly once, at the exported entry point, and have
internal helpers assume it is held (named getLocked, by convention).

Same family: calling a method that takes mu.Lock from inside another
method that already holds mu — Go mutexes are deliberately not reentrant.

MENTAL MODEL 4 — WHAT SYNC.MUTEX ACTUALLY DOES

    Lock():
      fast path: CAS 0 → locked                  (uncontended: a few ns)
      slow path: spin briefly (multicore only) → park goroutine on a
                 semaphore queue

    Normal mode: a woken waiter competes with newly arriving goroutines —
                 new arrivals usually win (they're already on a CPU).
                 Great throughput, possible unfairness.
    Starvation mode: if a waiter has waited > 1 ms, ownership is handed
                 directly to the queue head; newcomers don't spin.
                 Switches back once the queue drains or wait times drop.

  - TryLock (Go 1.18) exists, but its own documentation notes that correct
    uses are rare; frequent use is usually a sign of a deeper design problem.
  - RWMutex only wins when read critical sections are long or reads vastly
    outnumber writes AND there is real parallelism; its bookkeeping is
    heavier than Mutex, and Problem 26 measured RLock scaling far worse
    than atomic.Pointer on 8 cores.
  - Zero values are ready to use; copying a used Mutex copies its state
    (go vet's copylocks check catches `func (s Store) ...` receivers on
    structs containing a mutex).

MENTAL MODEL 5 — THE SYNC.ONCE FAMILY

    sync.Once.Do(f)          runs f once; if f panics, Do considers it done
    sync.OnceFunc(f)         Go 1.21: returns a func calling f once; re-panics
    sync.OnceValue(f)        Go 1.21: caches f's single result
    sync.OnceValues(f)       Go 1.21: caches (value, error) — INCLUDING the error

    first call:  load() → err "dns timeout"   ──▶ cached
    second call: ─────────────────────────────▶ same "dns timeout", load never retried

For lazy initialisation of something that can fail transiently (a DB
connection, fetching a remote config), cache only success — OnceRetry uses
the same double-checked atomic fast path Once uses internally, plus a
mutex so concurrent callers queue behind a single in-flight load instead of
stampeding the backend.

MENTAL MODEL 6 — CONTENTION AND LOCK STRIPING

    one global mutex                     32 shards
    ┌──────────────┐                     ┌────┐┌────┐┌────┐     ┌────┐
    │  mu  map[..] │ ◀── every Inc on    │mu 0││mu 1││mu 2│ ... │mu31│
    └──────────────┘     every core      └────┘└────┘└────┘     └────┘
                         queues here       ▲ hash(key) % 32 picks one

Each shard carries padding so neighbouring shards' mutex words don't share a
64-byte cache line; otherwise one core locking shard 3 invalidates another
core's cached copy of shard 4 (false sharing), and much of the win is lost.
Measured on this machine (Apple M4 Pro, go1.26, 1024 distinct keys,
`go test -bench Counter -cpu 1,4,12`):

    cores   one global mutex   32 padded shards
      1         10.2 ns/op         13.3 ns/op    ← hashing costs more than it saves
      4        113.9 ns/op         17.5 ns/op    ← 6.5x
     12        164.3 ns/op         44.7 ns/op    ← 3.7x

Note the global mutex getting SLOWER per operation as cores are added:
goroutines spend their time parking and waking on a contended lock.
Striping only helps when there are several cores and many distinct keys.

MENTAL MODEL 7 — THE RACE DETECTOR

    go test -race ./...     go run -race .     go build -race

  - Instruments every memory access and tracks "happens-before" edges
    created by locks, channels, WaitGroups and atomics. Two accesses with
    no such edge, at least one a write → report with both stack traces.
  - Finds races that HAPPEN during the run, not races that could happen:
    run realistic concurrent tests, and consider -race in CI for
    integration/load tests, not just unit tests.
  - Cost: CPU roughly 2-20x and memory roughly 5-10x (Go documentation's
    estimates); too heavy for production traffic, fine for a canary.
  - Exit code 66 and "WARNING: DATA RACE" on detection. The test file
    builds a child `go test -race` against a deliberately racy counter.

DEBUGGING A LIVE DEADLOCK

	kill -QUIT <pid>                        # dumps all goroutine stacks, then exits
	curl localhost:6060/debug/pprof/goroutine?debug=2    # same, process keeps running
	GOTRACEBACK=all                         # include runtime goroutines in crash dumps

Look for many goroutines parked in sync.(*Mutex).Lock or
sync.(*RWMutex).RLock with "[N minutes]" wait times, then read which
lock the holder is itself waiting on. runtime.SetMutexProfileFraction +
/debug/pprof/mutex shows where contention (not deadlock) costs time.

SPEC

	var ErrInsufficientFunds, ErrSameAccount, ErrContended error

	type Account struct { ID int; mu sync.Mutex; balance int64 }
	func NewAccount(id int, balance int64) *Account
	func (a *Account) Balance() int64
	func Transfer(from, to *Account, amount int64) error       // lower ID locked first
	func TransferNaive(from, to *Account, amount int64, between func()) error  // lesson: deadlocks
	func TransferTry(from, to *Account, amount int64, attempts int, between func()) error
	    // Lock(from); between(); TryLock(to) or unlock+jittered backoff; ErrContended when out of attempts

	func Completes(timeout time.Duration, fn func()) bool

	type Registry struct { mu sync.RWMutex; m map[string]string }
	func NewRegistry() *Registry
	func (r *Registry) Get(k string) (string, bool)
	func (r *Registry) Set(k, v string)
	func (r *Registry) GetOrDefaultBad(k, def string, between func()) string   // lesson: recursive RLock
	func (r *Registry) GetOrDefault(k, def string, between func()) string      // single RLock

	type OnceRetry[T any] struct { ... }
	func NewOnceRetry[T any](load func() (T, error)) *OnceRetry[T]
	func (o *OnceRetry[T]) Get() (T, error)   // caches only success; concurrent callers share one load

	type ShardedCounter struct { ... }
	func NewShardedCounter() *ShardedCounter
	func (c *ShardedCounter) Inc(key string)
	func (c *ShardedCounter) Get(key string) int64

ACCEPTANCE CRITERIA

  - `go test -v ./31_deadlocks_and_sync_primitives/solution/...` passes:
      - 16 goroutines × 5,000 random bidirectional Transfers finish and
        conserve the total balance;
      - the forced interleaving deadlocks TransferNaive and
        GetOrDefaultBad, and does NOT deadlock Transfer, TransferTry or
        GetOrDefault;
      - a child process shows the runtime detector firing only when every
        goroutine is blocked;
      - a child `go test -race` reports WARNING: DATA RACE.
  - `go test -race` on the solution package itself is clean.

HOW TO RUN

	go test -v ./31_deadlocks_and_sync_primitives/solution/...
	go test -race -short ./31_deadlocks_and_sync_primitives/solution/...
	go test -run '^$' -bench Counter -cpu 1,4,12 ./31_deadlocks_and_sync_primitives/solution/...

HINTS

  - Transfer: pick (first, second) by comparing IDs, then lock in that
    order; the balance check uses from/to, not first/second.
  - TransferTry: after a failed TryLock, Unlock the first lock BEFORE
    sleeping; use rand.N(backoff) jitter.
  - Completes: close a done channel from the goroutine; select on it and
    time.After.
  - OnceRetry: atomic.Bool fast path; mutex slow path; re-check the flag
    after acquiring the mutex; set the flag only after storing the value.

COMMON PITFALLS

  - Choosing lock order by argument position ("from first") — that IS the
    deadlock.
  - Returning while holding a lock on an error path; prefer defer unless
    the critical section is tiny and panic-free.
  - Holding a lock across a channel send: the receiver may be waiting for
    the same lock.
  - Using RWMutex by default "for performance" without measuring.
  - `for { if mu.TryLock() { break } }` — a CPU-burning spin with no
    backoff and no bound.
  - Assuming "no deadlock detected" means "no deadlock": the runtime
    detector is effectively off in any real server.

STRETCH GOALS

  - Write a lock-order checker: wrap sync.Mutex in an OrderedMutex{rank int}
    that panics (in debug builds, via a build tag) when a goroutine locks a
    lower rank while holding a higher one.
  - Add TransferMany(transfers []Tx) that locks every involved account
    in ID order exactly once.
  - Capture /debug/pprof/mutex while running BenchmarkCounterGlobalMutex
    and find the contended line.
*/

package syncprim

import (
	"errors"
	"sync"
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

// Account is a bank account guarded by its own mutex.
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
	// TODO: lock, read, unlock.
	panic("not implemented")
}

// Transfer moves amount atomically, always locking the lower ID first.
func Transfer(from, to *Account, amount int64) error {
	// TODO: reject from == to; order by ID; lock both; check funds; move money.
	panic("not implemented")
}

// TransferNaive locks from then to. It deadlocks; it exists for the lesson.
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

// TransferTry uses TryLock on the second lock with jittered backoff.
func TransferTry(from, to *Account, amount int64, attempts int, between func()) error {
	// TODO: for each attempt: Lock(from); call between if non-nil; TryLock(to)
	// → do transfer, unlock both, return; else Unlock(from), sleep with jitter.
	// Return ErrContended when attempts run out.
	panic("not implemented")
}

// ============================================================================
// 2. Detecting a hang
// ============================================================================

// Completes reports whether fn returns within timeout.
func Completes(timeout time.Duration, fn func()) bool {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 3. RWMutex
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
	v, ok := r.m[k]
	return v, ok
}

// Set stores v under k.
func (r *Registry) Set(k, v string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.m[k] = v
}

// GetOrDefaultBad takes RLock, then calls Get (a second RLock). Lesson only.
func (r *Registry) GetOrDefaultBad(k, def string, between func()) string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if between != nil {
		between()
	}
	if v, ok := r.Get(k); ok {
		return v
	}
	return def
}

// GetOrDefault must take the read lock exactly once.
func (r *Registry) GetOrDefault(k, def string, between func()) string {
	// TODO: RLock once; call between; read r.m directly (or via a getLocked helper).
	panic("not implemented")
}

// ============================================================================
// 4. Once semantics
// ============================================================================

// OnceRetry caches the first SUCCESSFUL result of load.
type OnceRetry[T any] struct {
	// TODO: mu sync.Mutex; done atomic.Bool; val T; load func() (T, error)
}

// NewOnceRetry wraps load.
func NewOnceRetry[T any](load func() (T, error)) *OnceRetry[T] {
	// TODO
	panic("not implemented")
}

// Get returns the cached value or retries load.
func (o *OnceRetry[T]) Get() (T, error) {
	// TODO: fast path atomic check; slow path under mutex with re-check.
	panic("not implemented")
}

// ============================================================================
// 5. Lock striping
// ============================================================================

// ShardedCounter is a string→int64 counter split across locked shards.
type ShardedCounter struct {
	// TODO: seed maphash.Seed; shards [32]struct{ mu sync.Mutex; m map[string]int64; _ [40]byte }
}

// NewShardedCounter returns an empty counter.
func NewShardedCounter() *ShardedCounter {
	// TODO
	panic("not implemented")
}

// Inc adds one to key.
func (c *ShardedCounter) Inc(key string) {
	// TODO: pick shard by maphash.String(seed, key) % 32.
	panic("not implemented")
}

// Get returns key's count.
func (c *ShardedCounter) Get(key string) int64 {
	// TODO
	panic("not implemented")
}
