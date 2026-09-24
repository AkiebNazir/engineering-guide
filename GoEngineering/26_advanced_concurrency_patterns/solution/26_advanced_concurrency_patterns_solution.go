// Package advconc is the reference solution for Problem 26 — Advanced
// Concurrency Patterns. Read the explanation file first for the mental
// models; this file explains why each line is the way it is.
package advconc

import (
	"context"
	"errors"
	"maps"
	"sync"
	"sync/atomic"

	"golang.org/x/sync/errgroup"
)

// ErrQueueClosed is returned by Put once the queue has been closed.
var ErrQueueClosed = errors.New("advconc: queue closed")

// ============================================================================
// 1. errgroup — bounded, fail-fast, order-preserving fan-out
// ============================================================================

// FetchAll runs fetch for every id with at most limit in flight and returns
// results in input order.
//
// Design notes:
//   - errgroup.WithContext derives gctx and cancels it on the FIRST non-nil
//     error. Every fetch receives gctx, never the caller's ctx, otherwise the
//     fail-fast cancellation would never reach them.
//   - SetLimit must be called before the first g.Go. With a limit, g.Go blocks
//     the *calling* goroutine until a slot frees, so the for-loop below is the
//     backpressure point: we never have more than `limit` goroutines alive, not
//     merely "running". That is cheaper than spawning len(ids) goroutines that
//     all wait on a semaphore.
//   - results[i] is written by exactly one goroutine; different indices are
//     different memory locations, so no mutex is needed. `-race` agrees.
//   - Go 1.22 made loop variables per-iteration, so capturing i and id in the
//     closure is correct without the old `i, id := i, id` shadowing.
func FetchAll(ctx context.Context, ids []int, limit int, fetch func(ctx context.Context, id int) (string, error)) ([]string, error) {
	g, gctx := errgroup.WithContext(ctx)
	if limit > 0 {
		g.SetLimit(limit)
	}

	results := make([]string, len(ids))
	for i, id := range ids {
		g.Go(func() error {
			// A goroutine that obtained its slot after another one failed
			// should not start expensive work at all.
			if err := gctx.Err(); err != nil {
				return err
			}
			v, err := fetch(gctx, id)
			if err != nil {
				return err
			}
			results[i] = v
			return nil
		})
	}

	// Wait returns the first error, but only after EVERY goroutine returned.
	// That is the property that makes errgroup leak-free — as long as each
	// fetch actually honours ctx.Done().
	if err := g.Wait(); err != nil {
		return nil, err
	}
	return results, nil
}

// ============================================================================
// 2. sync.Cond — bounded blocking queue
// ============================================================================

// BlockingQueue is a bounded FIFO whose Put blocks while full and whose Get
// blocks while empty. Construct with NewBlockingQueue; must not be copied.
type BlockingQueue[T any] struct {
	mu       sync.Mutex
	notEmpty *sync.Cond // signalled when an item is added (wakes a getter)
	notFull  *sync.Cond // signalled when an item is removed (wakes a putter)
	items    []T
	head     int // index of the oldest item; avoids O(n) shifting on Get
	capacity int
	closed   bool
}

// NewBlockingQueue returns a queue that holds at most capacity items.
func NewBlockingQueue[T any](capacity int) *BlockingQueue[T] {
	if capacity < 1 {
		panic("advconc: BlockingQueue capacity must be >= 1")
	}
	q := &BlockingQueue[T]{
		items:    make([]T, 0, capacity),
		capacity: capacity,
	}
	// Two Conds, ONE mutex. The predicate for both ("is there room?", "is
	// there an item?") reads the same state, so it must be guarded by the same
	// lock. Two Conds instead of one means Put only wakes getters and Get only
	// wakes putters — with a single Cond a Signal could wake the "wrong" kind
	// of waiter, which would just re-sleep, and the right one would never be
	// told (a lost wakeup).
	q.notEmpty = sync.NewCond(&q.mu)
	q.notFull = sync.NewCond(&q.mu)
	return q
}

func (q *BlockingQueue[T]) lenLocked() int { return len(q.items) - q.head }

// Put appends v, blocking while the queue is full. It returns ErrQueueClosed
// if the queue is (or becomes, while waiting) closed.
func (q *BlockingQueue[T]) Put(v T) error {
	q.mu.Lock()
	defer q.mu.Unlock()

	// `for`, never `if`: between Signal and this goroutine re-acquiring the
	// lock, another putter may have filled the freed slot.
	for q.lenLocked() == q.capacity && !q.closed {
		q.notFull.Wait()
	}
	if q.closed {
		return ErrQueueClosed
	}

	// Compact lazily: once the backing array's tail is reached, slide the
	// live window back to index 0. Amortised O(1) per operation.
	if len(q.items) == cap(q.items) && q.head > 0 {
		n := copy(q.items, q.items[q.head:])
		clear(q.items[n:]) // drop references so the GC can collect them
		q.items = q.items[:n]
		q.head = 0
	}
	q.items = append(q.items, v)

	// Exactly one item appeared, so exactly one getter can make progress.
	q.notEmpty.Signal()
	return nil
}

// Get removes and returns the oldest item, blocking while the queue is empty.
// Once the queue is closed, Get keeps draining buffered items and then returns
// (zero, false).
func (q *BlockingQueue[T]) Get() (T, bool) {
	q.mu.Lock()
	defer q.mu.Unlock()

	for q.lenLocked() == 0 && !q.closed {
		q.notEmpty.Wait()
	}
	var zero T
	if q.lenLocked() == 0 { // therefore closed
		return zero, false
	}

	v := q.items[q.head]
	q.items[q.head] = zero // don't keep a popped pointer alive
	q.head++
	if q.head == len(q.items) { // empty: reset to reuse the array from the start
		q.items = q.items[:0]
		q.head = 0
	}

	q.notFull.Signal()
	return v, true
}

// Close marks the queue closed and wakes every blocked Put and Get.
// It is safe to call more than once and from multiple goroutines.
func (q *BlockingQueue[T]) Close() {
	q.mu.Lock()
	q.closed = true
	q.mu.Unlock()

	// Broadcast, not Signal: closure changes the predicate for EVERY waiter.
	// Broadcasting after Unlock is legal and slightly cheaper (woken waiters
	// don't immediately collide with our still-held lock); it is safe because
	// `closed` is already visible to anyone who re-checks under the lock.
	q.notEmpty.Broadcast()
	q.notFull.Broadcast()
}

// Len reports the number of buffered items.
func (q *BlockingQueue[T]) Len() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	return q.lenLocked()
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

// ConfigStore publishes *Config snapshots that any number of goroutines can
// read without locks. The zero value is not usable; use NewConfigStore.
type ConfigStore struct {
	ptr     atomic.Pointer[Config]
	version atomic.Uint64
}

// NewConfigStore publishes initial as version 0.
func NewConfigStore(initial *Config) *ConfigStore {
	if initial == nil {
		initial = &Config{}
	}
	s := &ConfigStore{}
	s.ptr.Store(initial)
	return s
}

// Load returns the current snapshot. It is a single atomic pointer read —
// no lock, no allocation. Callers must treat the result as read-only.
//
// Measured on this machine (Apple M4 Pro, go1.26, `-bench . -cpu 1,8`):
//
//	BenchmarkConfigReadAtomic      0.83 ns/op   BenchmarkConfigReadAtomic-8    0.18 ns/op
//	BenchmarkConfigReadRWMutex     3.17 ns/op   BenchmarkConfigReadRWMutex-8  64.36 ns/op
//
// Single-threaded the RWMutex is only ~4x slower. With 8 parallel readers it
// is ~350x slower: RLock/RUnlock WRITE the shared reader counter, so every
// reader bounces the same cache line between cores. atomic Load writes nothing.
func (s *ConfigStore) Load() *Config { return s.ptr.Load() }

// Update applies fn to a private deep copy of the current config and
// publishes the copy. If another writer published in between, the work is
// redone on top of the newer snapshot, so no update is ever lost.
//
// fn may run more than once under contention, so it must be a pure function
// of its argument (no side effects like "send an email").
func (s *ConfigStore) Update(fn func(next *Config)) {
	for {
		old := s.ptr.Load()

		next := *old // copies scalar fields and the map HEADER only...
		// ...so the map must be cloned, or fn would mutate the map that
		// readers of `old` are iterating right now → fatal runtime error.
		next.Features = maps.Clone(old.Features)
		if next.Features == nil {
			next.Features = map[string]bool{}
		}

		fn(&next)

		// CompareAndSwap compares POINTERS: it succeeds only if nobody
		// published a different snapshot since our Load. A plain Store here
		// would silently overwrite a concurrent writer's change.
		if s.ptr.CompareAndSwap(old, &next) {
			s.version.Add(1)
			return
		}
	}
}

// Version reports how many updates have been published.
func (s *ConfigStore) Version() uint64 { return s.version.Load() }

// ============================================================================
// 4. First success wins, losers cancelled, no leaks
// ============================================================================

// ErrNoCandidates is returned by FirstSuccess when called with no functions.
var ErrNoCandidates = errors.New("advconc: no candidates")

// FirstSuccess runs every fn concurrently and returns the first result whose
// error is nil, cancelling the rest. If all fail it returns errors.Join of
// every error, in completion order.
func FirstSuccess[T any](ctx context.Context, fns ...func(ctx context.Context) (T, error)) (T, error) {
	var zero T
	if len(fns) == 0 {
		return zero, ErrNoCandidates
	}

	ctx, cancel := context.WithCancel(ctx)
	// Runs on every return path: the winner's return cancels the losers.
	defer cancel()

	type result struct {
		v   T
		err error
	}
	// Buffered to len(fns): every goroutine can complete its single send even
	// after we've returned and nobody is receiving. An unbuffered channel here
	// is the textbook goroutine leak.
	results := make(chan result, len(fns))
	for _, fn := range fns {
		go func() {
			v, err := fn(ctx)
			results <- result{v, err}
		}()
	}

	errs := make([]error, 0, len(fns))
	for range fns {
		select {
		case r := <-results:
			if r.err == nil {
				return r.v, nil
			}
			errs = append(errs, r.err)
		case <-ctx.Done():
			// Parent cancelled: stop waiting. Goroutines still finish into
			// the buffer, so nothing leaks.
			return zero, errors.Join(append(errs, context.Cause(ctx))...)
		}
	}
	return zero, errors.Join(errs...)
}
