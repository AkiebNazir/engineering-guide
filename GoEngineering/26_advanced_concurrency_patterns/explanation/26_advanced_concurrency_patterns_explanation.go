/*
Problem 26 — Advanced Concurrency Patterns (context trees, errgroup,
sync.Cond, atomic.Pointer, hedged requests)

WHAT WE'RE BUILDING

Four small, production-shaped concurrency primitives that show up again and
again inside real Go services once you move past "spawn a goroutine, send on
a channel":

 1. FetchAll        — bounded, fail-fast, order-preserving fan-out built on
                      golang.org/x/sync/errgroup.
 2. BlockingQueue   — a bounded FIFO whose Put blocks when full and whose
                      Get blocks when empty, built on sync.Cond.
 3. ConfigStore     — a lock-free, copy-on-write configuration holder for
                      hot reloading, built on atomic.Pointer[T] with a
                      CompareAndSwap retry loop.
 4. FirstSuccess    — "hedged requests": run N equivalent calls, return the
                      first success, cancel the losers, never leak a
                      goroutine.

Each one is short. What makes them "advanced" is that each has exactly one
subtle rule that, if you break it, gives you a bug that only shows up under
load: a goroutine leak, a lost wakeup, a lost update, or a hang on shutdown.

WHY THIS MATTERS IN REAL SYSTEMS

A request handler in a backend service typically fans out to several
dependencies (DB, cache, two internal RPCs), must stop all of them the
moment one fails or the client disconnects, and must never run more than N
of them at once or it will melt the dependency. Meanwhile the process
reloads feature flags every 30 seconds while 10k goroutines read them per
request. Those are exactly the four primitives above.

The failure modes are expensive precisely because they are silent:

  - A leaked goroutine per request is ~2-8 KB of stack plus whatever it
    references. At 1k req/s that is an OOM kill within hours, and pprof's
    goroutine profile is the only place it shows up.
  - A fan-out without a limit turns a traffic spike into a thundering herd
    against your database's connection pool.
  - A config reload that mutates a map in place while readers iterate it is
    a fatal "concurrent map read and map write" crash — not a panic you can
    recover, the runtime aborts the process.

MENTAL MODEL 1 — THE CONTEXT CANCELLATION TREE

Every context.With* call creates a child node. Cancellation flows DOWN the
tree only, never up. A child can shorten a parent's deadline, never extend it.

    context.Background()
            │
            ▼
    ┌────────────────────────┐   cancel() or deadline
    │ request ctx (5s)       │─────────────────────────┐
    └────────────────────────┘                         │
            │                                          │ propagates
     ┌──────┴───────────────┬───────────────┐          ▼ to every child
     ▼                      ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
    │ errgroup ctx│  │ db ctx (1s)  │  │ WithoutCancel ctx│  ◀── detached:
    └─────────────┘  └──────────────┘  └──────────────────┘      NOT cancelled
       │   │   │
       ▼   ▼   ▼   goroutines select on ctx.Done()

The rule that matters: cancelling a node closes its Done() channel and the
Done() channel of every descendant, and every CancelFunc you create must be
called (usually via defer) or the child stays registered in the parent until
the parent itself ends — that is the classic "context leak".

MENTAL MODEL 2 — ERRGROUP: FAIL-FAST WITH A CONCURRENCY LIMIT

errgroup.WithContext gives you a Group plus a derived ctx. The FIRST
goroutine that returns a non-nil error cancels that ctx; Wait() returns
that first error after ALL goroutines have returned. SetLimit(n) makes
g.Go block the caller until a slot frees up.

    limit = 2        time ───────────────────────────────────────▶

    slot A:  [ fetch id=0 ─────── ok ][ fetch id=2 ── ERROR ✗ ]
    slot B:  [ fetch id=1 ───────────────────── ctx.Done ⊘ ]
                                                  ▲
    g.Go(id=3) blocked waiting for a slot ...     │ first error cancels ctx
                                 ... gets a slot, sees ctx.Err(), returns
    g.Wait() ────────────────────────────────────────────▶ returns ERROR

Order preservation trick: pre-allocate results := make([]T, len(ids)) and
have goroutine i write ONLY to results[i]. Distinct slice elements are
distinct memory locations, so this is race-free without a mutex.

	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(limit)
	results := make([]string, len(ids))
	for i, id := range ids {
	    g.Go(func() error {           // Go 1.22+: i and id are per-iteration
	        v, err := fetch(ctx, id)
	        if err != nil {
	            return err
	        }
	        results[i] = v
	        return nil
	    })
	}
	if err := g.Wait(); err != nil {
	    return nil, err
	}

MENTAL MODEL 3 — SYNC.COND: WAIT RELEASES THE LOCK ATOMICALLY

A condition variable lets a goroutine sleep until "some predicate over
shared state" might have become true. cond.Wait() does three things as one
atomic step from the point of view of other goroutines:

    goroutine G (holds q.mu)
          │
          │ for len(q.items) == 0 {      ◀── ALWAYS a loop, never an if
          ▼
    ┌──────────────────────────────┐
    │ cond.Wait():                 │
    │   1. unlock q.mu             │  ── other goroutines may now Put
    │   2. park G until Signal /   │
    │      Broadcast               │
    │   3. re-lock q.mu before     │
    │      returning               │
    └──────────────────────────────┘
          │
          ▼  re-check predicate (another Get may have stolen the item,
             or it was a Broadcast from Close)

Signal wakes ONE waiter; Broadcast wakes ALL. Use Signal when any single
waiter can make progress with the change (one item was added → one getter).
Use Broadcast when the change affects every waiter (Close → everyone must
wake up and observe closed == true). Using Signal on Close strands every
waiter except one forever — the test file demonstrates this live.

Why not just channels? A buffered channel IS a bounded blocking queue, and
you should prefer it when it fits. sync.Cond earns its place when the
predicate is not "channel has room": wait until "at least K items", "the
queue is drained", "total bytes buffered < limit", or when you need Len(),
PeekFront(), or priority ordering that a channel cannot give you.

MENTAL MODEL 4 — ATOMIC.POINTER: COPY-ON-WRITE SNAPSHOTS

Readers must never see a half-updated config. Instead of locking, treat a
*Config as IMMUTABLE once published and swap the pointer:

    readers (10k goroutines)                writer (reload loop)
    cfg := store.Load()  ───────┐
                                ▼
                     ┌───────────────────┐        1. old := p.Load()
    p ─────────────▶ │ Config v7 (frozen)│        2. next := deep copy of *old
                     └───────────────────┘        3. mutate next
                                                  4. p.CompareAndSwap(old, &next)
                     ┌───────────────────┐           ├─ true  → published
                     │ Config v8 (frozen)│ ◀──────── └─ false → someone else won,
                     └───────────────────┘              retry from step 1

Readers that already hold v7 keep a perfectly valid, consistent snapshot;
the GC frees v7 when the last reader drops it. Two traps:

  - Store(new) without CAS is a lost update if two writers race: both load
    v7, both build v8, the second Store silently discards the first
    writer's change. CompareAndSwap in a retry loop fixes it.
  - A "copy" of a struct containing a map or slice copies the map HEADER,
    not the entries. Mutating next.Features mutates v7's map that readers
    are iterating → fatal error: concurrent map read and map write. Clone
    reference-typed fields (maps.Clone, slices.Clone) before mutating.

MENTAL MODEL 5 — HEDGED REQUESTS WITHOUT LEAKS

Send the same idempotent request to several replicas; take the first
success. The leak trap is the result channel: if it is unbuffered and you
return after the first result, every loser blocks forever on its send.

	results := make(chan result, len(fns))  // buffered: losers never block
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()                          // tells losers to stop working

    replica A ─────── ok ───▶ ┐
    replica B ── err ──▶      ├─▶ chan (cap 3) ─▶ first ok wins, cancel()
    replica C ───────────────▶┘      losers: send into buffer, exit

If every call fails, return errors.Join of all errors so the caller sees
the full picture, not just the last one.

SPEC

	func FetchAll(ctx context.Context, ids []int, limit int,
	    fetch func(ctx context.Context, id int) (string, error)) ([]string, error)
	  - Runs fetch for every id with at most `limit` running concurrently
	    (limit <= 0 means unlimited).
	  - Returns results in the SAME ORDER as ids.
	  - The first error cancels the ctx passed to every other fetch and is
	    the error returned. On error the result slice is nil.

	type BlockingQueue[T any] struct { ... }
	func NewBlockingQueue[T any](capacity int) *BlockingQueue[T]   // capacity >= 1
	func (q *BlockingQueue[T]) Put(v T) error    // blocks while full; ErrQueueClosed if closed
	func (q *BlockingQueue[T]) Get() (T, bool)   // blocks while empty; (zero, false) once closed AND drained
	func (q *BlockingQueue[T]) Close()           // idempotent; wakes every blocked Put and Get
	func (q *BlockingQueue[T]) Len() int

	type Config struct { LogLevel string; MaxConns int; Features map[string]bool }
	func NewConfigStore(initial *Config) *ConfigStore
	func (s *ConfigStore) Load() *Config                       // lock-free, never nil
	func (s *ConfigStore) Update(fn func(next *Config))        // CAS loop; fn mutates a private deep copy
	func (s *ConfigStore) Version() uint64                     // number of successful updates

	func FirstSuccess[T any](ctx context.Context,
	    fns ...func(ctx context.Context) (T, error)) (T, error)
	  - Returns the first nil-error result and cancels the others.
	  - If all fail, returns errors.Join of every error.
	  - Every goroutine it starts has exited or is guaranteed to exit
	    without blocking once FirstSuccess returns.

ACCEPTANCE CRITERIA

  - `go test -race ./26_advanced_concurrency_patterns/solution/...` passes.
  - FetchAll never exceeds its limit (measured with an atomic high-water
    mark) and returns within a fraction of the slow calls' duration once
    one call fails.
  - 50 concurrent ConfigStore.Update calls that each increment MaxConns
    produce exactly +50 — no lost updates.
  - Close() on a BlockingQueue with several blocked getters wakes all of
    them.

HOW TO RUN

	go test -race -v ./26_advanced_concurrency_patterns/solution/...
	go test -run Example -v ./26_advanced_concurrency_patterns/solution/...
	go test -bench . -benchmem ./26_advanced_concurrency_patterns/solution/...

HINTS

  - errgroup: after g.Wait() returns an error, do not look at results.
  - BlockingQueue: two Conds (notEmpty, notFull) sharing ONE mutex keep
    getters from waking getters. Signal notEmpty after Put, notFull after
    Get, Broadcast both on Close.
  - Update: Load → copy (clone the map!) → fn(&copy) → CompareAndSwap.
    Only bump the version counter when CAS succeeds.
  - FirstSuccess: count results received, not goroutines finished.

COMMON PITFALLS

  - `if len(q.items) == 0 { cond.Wait() }` — spurious/stolen wakeups make
    this return with an empty queue. Always `for`.
  - Calling cond.Wait() without holding the lock → runtime panic
    "sync: unlock of unlocked mutex".
  - Copying a struct that contains sync.Mutex / sync.Cond / atomic.* after
    first use. `go vet` (copylocks) catches most of these.
  - Forgetting `defer cancel()` in FirstSuccess — the losers keep burning
    CPU/network until their own timeouts.
  - Writing to a shared map or appending to a shared slice from errgroup
    goroutines. Index-per-goroutine writes are safe; append is not.

STRETCH GOALS

  - Add PutContext/GetContext that also return when a ctx is cancelled.
    (Hint: context.AfterFunc(ctx, func(){ q.mu.Lock(); q.notEmpty.Broadcast(); q.mu.Unlock() }).)
  - Make FirstSuccess actually HEDGE: start fns[i] only after fns[i-1] has
    not answered within a delay, like Google's "The Tail at Scale".
  - Replace the Features map with an immutable persistent structure and
    benchmark Update cost.
*/

package advconc

import (
	"context"
	"errors"
	"sync/atomic"
)

// ErrQueueClosed is returned by Put once the queue has been closed.
var ErrQueueClosed = errors.New("advconc: queue closed")

// ============================================================================
// 1. errgroup — bounded, fail-fast, order-preserving fan-out
// ============================================================================

// FetchAll runs fetch for every id with at most limit in flight and returns
// results in input order. See SPEC.
func FetchAll(ctx context.Context, ids []int, limit int, fetch func(ctx context.Context, id int) (string, error)) ([]string, error) {
	// TODO: g, gctx := errgroup.WithContext(ctx); g.SetLimit(limit) when > 0.
	// TODO: pre-size results; goroutine i writes only results[i].
	// TODO: return nil, err if g.Wait() fails.
	panic("not implemented")
}

// ============================================================================
// 2. sync.Cond — bounded blocking queue
// ============================================================================

// BlockingQueue is a bounded FIFO. Construct with NewBlockingQueue.
type BlockingQueue[T any] struct {
	// TODO: mu sync.Mutex; notEmpty, notFull *sync.Cond; items []T;
	// capacity int; closed bool
}

// NewBlockingQueue returns a queue that holds at most capacity items.
func NewBlockingQueue[T any](capacity int) *BlockingQueue[T] {
	// TODO: validate capacity >= 1 (panic on misuse is fine — programmer error).
	// TODO: both Conds must share the SAME mutex: sync.NewCond(&q.mu).
	panic("not implemented")
}

// Put appends v, blocking while the queue is full.
func (q *BlockingQueue[T]) Put(v T) error {
	// TODO: lock; for full && !closed { notFull.Wait() }; if closed return ErrQueueClosed;
	// append; notEmpty.Signal(); unlock.
	panic("not implemented")
}

// Get removes the oldest item, blocking while the queue is empty.
func (q *BlockingQueue[T]) Get() (T, bool) {
	// TODO: lock; for empty && !closed { notEmpty.Wait() };
	// if empty (therefore closed) return zero, false;
	// pop front (zero the vacated slot so the GC can free it); notFull.Signal().
	panic("not implemented")
}

// Close marks the queue closed and wakes every waiter. Idempotent.
func (q *BlockingQueue[T]) Close() {
	// TODO: set closed under the lock, then Broadcast BOTH conds.
	panic("not implemented")
}

// Len reports the number of buffered items.
func (q *BlockingQueue[T]) Len() int {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 3. atomic.Pointer — copy-on-write hot-reloadable config
// ============================================================================

// Config is treated as immutable once published through a ConfigStore.
type Config struct {
	LogLevel string
	MaxConns int
	Features map[string]bool
}

// ConfigStore publishes *Config snapshots without locks.
type ConfigStore struct {
	ptr     atomic.Pointer[Config]
	version atomic.Uint64
}

// NewConfigStore publishes initial as version 0.
func NewConfigStore(initial *Config) *ConfigStore {
	// TODO: store initial (treat nil as &Config{}).
	panic("not implemented")
}

// Load returns the current snapshot. Callers must not mutate it.
func (s *ConfigStore) Load() *Config {
	// TODO
	panic("not implemented")
}

// Update applies fn to a private deep copy and publishes it atomically,
// retrying if another writer published first.
func (s *ConfigStore) Update(fn func(next *Config)) {
	// TODO: for { old := Load(); next := *old; next.Features = maps.Clone(old.Features);
	// fn(&next); if CompareAndSwap(old, &next) { version.Add(1); return } }
	panic("not implemented")
}

// Version reports how many updates have been published.
func (s *ConfigStore) Version() uint64 {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 4. First success wins, losers cancelled, no leaks
// ============================================================================

// FirstSuccess returns the first successful result among fns.
func FirstSuccess[T any](ctx context.Context, fns ...func(ctx context.Context) (T, error)) (T, error) {
	// TODO: ctx, cancel := context.WithCancel(ctx); defer cancel()
	// TODO: buffered channel of len(fns); one goroutine per fn.
	// TODO: receive len(fns) times; return on first nil error; collect errors.
	// TODO: zero fns → return zero value and an error.
	panic("not implemented")
}
