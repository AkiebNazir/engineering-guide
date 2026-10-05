/*
Problem 14 — Concurrent Cache (reference solution)

See explanation/14_concurrent_cache_explanation.go for the full spec and
rationale. This file implements it.

Design summary:
  - Two storage backends (StoreMutex, StoreSyncMap) behind one internal
    `store[K, V]` interface, selected at construction. Both hold entry[V]
    values (value + expiry deadline). Benchmarks at the bottom of the test
    file compare them directly instead of asserting a winner in prose.
  - Single-flight is entirely separate from storage: an `inflight
    map[K]*call[V]` guarded by its own mutex. The first goroutine to miss
    on a key creates the *call[V], releases the inflight lock, runs the
    loader OUTSIDE any lock, then stores the result and closes call.done.
    Every other concurrently-missing goroutine for the same key finds the
    existing *call[V] under the same brief lock and waits on call.done —
    so exactly one loader invocation happens per stampede.
  - Lazy expiry-on-read is the correctness backstop; the background
    sweeper is the memory-bounding mechanism. Either alone is insufficient
    per the explanation file's pitfalls section.
  - Close() stops the sweeper deterministically: closes a stop channel and
    waits on a sync.WaitGroup for the sweeper goroutine to actually exit,
    so Close is synchronous rather than "requested."
*/
package cache

import (
	"context"
	"sync"
	"time"
)

// Loader loads the value for key on a cache miss.
type Loader[K comparable, V any] func(ctx context.Context, key K) (V, error)

// Store selects the internal storage strategy.
type Store string

const (
	// StoreMutex backs the cache with a plain map[K]entry[V] guarded by a
	// sync.Mutex. Default when Options.Store is empty; faster than
	// StoreSyncMap for most cache workloads (read+write mixed on a shared
	// key set) per the stdlib's own sync.Map guidance.
	StoreMutex Store = "mutex"
	// StoreSyncMap backs the cache with sync.Map — optimized for
	// mostly-write-once/read-many or disjoint-key-per-goroutine access
	// patterns, not a general drop-in replacement for a mutex+map cache.
	StoreSyncMap Store = "syncmap"
)

// Options configures a new Cache.
type Options struct {
	// TTL is how long an entry stays valid after being set. Required, > 0.
	TTL time.Duration
	// SweepInterval is how often the background sweeper scans for and
	// removes expired entries. Required, > 0.
	SweepInterval time.Duration
	// Store selects StoreMutex or StoreSyncMap. Zero value defaults to
	// StoreMutex.
	Store Store
}

// entry is one stored value plus its expiry deadline.
type entry[V any] struct {
	value     V
	expiresAt time.Time
}

func (e entry[V]) expired(now time.Time) bool {
	return now.After(e.expiresAt)
}

// store is the storage abstraction the two backends implement. Kept
// intentionally tiny — exactly what Cache needs, nothing mirroring a
// general-purpose map API.
type store[K comparable, V any] interface {
	load(key K) (entry[V], bool)
	store(key K, e entry[V])
	delete(key K)
	// sweep removes every entry for which expired(now) is true and
	// returns how many were removed (used by tests; harmless in prod).
	sweep(now time.Time) int
	// len reports the number of currently live (non-expired) entries.
	len(now time.Time) int
}

// mutexStore is a map[K]entry[V] guarded by a sync.Mutex.
type mutexStore[K comparable, V any] struct {
	mu sync.Mutex
	m  map[K]entry[V]
}

func newMutexStore[K comparable, V any]() *mutexStore[K, V] {
	return &mutexStore[K, V]{m: make(map[K]entry[V])}
}

func (s *mutexStore[K, V]) load(key K) (entry[V], bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	e, ok := s.m[key]
	return e, ok
}

func (s *mutexStore[K, V]) store(key K, e entry[V]) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.m[key] = e
}

func (s *mutexStore[K, V]) delete(key K) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.m, key)
}

func (s *mutexStore[K, V]) sweep(now time.Time) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	n := 0
	for k, e := range s.m {
		if e.expired(now) {
			delete(s.m, k)
			n++
		}
	}
	return n
}

func (s *mutexStore[K, V]) len(now time.Time) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	n := 0
	for _, e := range s.m {
		if !e.expired(now) {
			n++
		}
	}
	return n
}

// syncMapStore wraps sync.Map. Len/sweep necessarily do a full Range scan —
// sync.Map has no size accounting, which is itself part of the trade-off
// the explanation file asks you to weigh.
type syncMapStore[K comparable, V any] struct {
	m sync.Map // K -> entry[V]
}

func newSyncMapStore[K comparable, V any]() *syncMapStore[K, V] {
	return &syncMapStore[K, V]{}
}

func (s *syncMapStore[K, V]) load(key K) (entry[V], bool) {
	v, ok := s.m.Load(key)
	if !ok {
		return entry[V]{}, false
	}
	return v.(entry[V]), true
}

func (s *syncMapStore[K, V]) store(key K, e entry[V]) {
	s.m.Store(key, e)
}

func (s *syncMapStore[K, V]) delete(key K) {
	s.m.Delete(key)
}

func (s *syncMapStore[K, V]) sweep(now time.Time) int {
	n := 0
	s.m.Range(func(k, v any) bool {
		if v.(entry[V]).expired(now) {
			s.m.Delete(k)
			n++
		}
		return true
	})
	return n
}

func (s *syncMapStore[K, V]) len(now time.Time) int {
	n := 0
	s.m.Range(func(_, v any) bool {
		if !v.(entry[V]).expired(now) {
			n++
		}
		return true
	})
	return n
}

// call is one in-flight single-flight load for a given key: the first
// goroutine to miss on a key creates one of these, runs the load, and
// every other concurrently-missing goroutine for the SAME key waits on
// done instead of calling load itself — the classic "future" shape.
type call[V any] struct {
	done  chan struct{}
	value V
	err   error
}

// Cache is a generic, concurrency-safe, TTL-expiring cache with
// single-flight loading. The zero value is not usable; construct with New.
type Cache[K comparable, V any] struct {
	ttl   time.Duration
	store store[K, V]

	inflightMu sync.Mutex
	inflight   map[K]*call[V]

	stop     chan struct{}
	stopOnce sync.Once
	wg       sync.WaitGroup
}

// New constructs a ready-to-use Cache and starts its background sweeper
// goroutine. Panics if opts.TTL <= 0 or opts.SweepInterval <= 0.
func New[K comparable, V any](opts Options) *Cache[K, V] {
	if opts.TTL <= 0 {
		panic("cache: Options.TTL must be > 0")
	}
	if opts.SweepInterval <= 0 {
		panic("cache: Options.SweepInterval must be > 0")
	}

	var st store[K, V]
	switch opts.Store {
	case StoreSyncMap:
		st = newSyncMapStore[K, V]()
	case StoreMutex, "":
		st = newMutexStore[K, V]()
	default:
		panic("cache: unknown Store: " + string(opts.Store))
	}

	c := &Cache[K, V]{
		ttl:      opts.TTL,
		store:    st,
		inflight: make(map[K]*call[V]),
		stop:     make(chan struct{}),
	}

	c.wg.Add(1)
	go c.sweepLoop(opts.SweepInterval)

	return c
}

// sweepLoop periodically removes expired entries until Close stops it.
// Each sweep only holds the store's internal lock for the duration of the
// scan itself (see mutexStore.sweep), never for the full SweepInterval.
func (c *Cache[K, V]) sweepLoop(interval time.Duration) {
	defer c.wg.Done()
	t := time.NewTicker(interval)
	defer t.Stop()
	for {
		select {
		case <-c.stop:
			return
		case now := <-t.C:
			c.store.sweep(now)
		}
	}
}

// Get returns the cached value for key if present and unexpired. On a
// miss, it calls load — collapsing concurrent misses for the same key into
// exactly one loader call (single-flight) — stores the result on success
// with a fresh TTL, and returns it to every waiter. A loader error is
// returned to every waiter and is never cached.
func (c *Cache[K, V]) Get(ctx context.Context, key K, load Loader[K, V]) (V, error) {
	now := time.Now()

	// Fast path: cached and not expired.
	if e, ok := c.store.load(key); ok && !e.expired(now) {
		return e.value, nil
	}

	// Slow path: join-or-create the in-flight call for this key. This
	// whole check-and-maybe-create step is one critical section under the
	// inflight mutex — otherwise two goroutines could both observe "no
	// in-flight call" and both start their own loader, defeating
	// single-flight.
	c.inflightMu.Lock()
	if existing, ok := c.inflight[key]; ok {
		c.inflightMu.Unlock()
		return c.wait(ctx, existing)
	}
	cl := &call[V]{done: make(chan struct{})}
	c.inflight[key] = cl
	c.inflightMu.Unlock()

	// Run the loader OUTSIDE any lock: it may be slow (network/DB call)
	// and must not block Get for unrelated keys, nor hold the inflight
	// lock while other keys try to join-or-create their own calls.
	value, err := load(ctx, key)
	cl.value, cl.err = value, err

	if err == nil {
		c.store.store(key, entry[V]{value: value, expiresAt: time.Now().Add(c.ttl)})
	}

	c.inflightMu.Lock()
	// Only remove our own call — a concurrent Get for the same key that
	// missed again after this one completed (rare, but possible right at
	// the boundary) would have created a NEW *call[V] under the lock, and
	// we must not delete that one.
	if c.inflight[key] == cl {
		delete(c.inflight, key)
	}
	c.inflightMu.Unlock()

	close(cl.done)
	return value, err
}

// wait blocks until the in-flight call cl completes or ctx is canceled.
// Canceling ctx only stops THIS waiter from waiting — it does not cancel
// the load for other waiters, who did not ask to cancel it.
func (c *Cache[K, V]) wait(ctx context.Context, cl *call[V]) (V, error) {
	select {
	case <-cl.done:
		return cl.value, cl.err
	case <-ctx.Done():
		var zero V
		return zero, ctx.Err()
	}
}

// Set unconditionally stores value for key with a fresh TTL, bypassing the
// loader path entirely.
func (c *Cache[K, V]) Set(key K, value V) {
	c.store.store(key, entry[V]{value: value, expiresAt: time.Now().Add(c.ttl)})
}

// Delete removes key immediately, regardless of TTL.
func (c *Cache[K, V]) Delete(key K) {
	c.store.delete(key)
}

// Len reports the number of currently live (non-expired) entries. For the
// StoreSyncMap backend this is an O(n) full-Range scan — sync.Map has no
// cheap size accounting, which is itself part of the mutex-vs-sync.Map
// trade-off.
func (c *Cache[K, V]) Len() int {
	return c.store.len(time.Now())
}

// Close stops the background sweeper goroutine and waits for it to
// actually exit before returning (synchronous, not "requested"). Safe to
// call more than once. Get/Set/Delete remain safe to call afterward — they
// simply no longer benefit from background sweeping; the lazy
// expiry-on-read check in Get still applies.
func (c *Cache[K, V]) Close() {
	c.stopOnce.Do(func() {
		close(c.stop)
	})
	c.wg.Wait()
}

/*
BEST PRACTICES DEMONSTRATED

  - Single-flight bookkeeping (inflightMu/inflight) is a SEPARATE lock from
    storage, and the loader itself runs with NO lock held — the only locked
    sections are the O(1) map operations bracketing it. This is what keeps
    one slow loader from blocking Gets for unrelated keys.
  - The storage backend is an interface (`store[K, V]`) with two
    implementations selected at construction, not a runtime `if` scattered
    through every method — makes both variants independently benchmarkable
    and keeps Cache's own logic backend-agnostic.
  - Lazy expiry-on-read (the `!e.expired(now)` check in the Get fast path)
    plus a background sweeper are BOTH present: the sweeper bounds memory
    over time, the lazy check is the correctness backstop that catches
    anything the sweeper hasn't reached yet (relevant whenever
    SweepInterval > TTL, a legitimate configuration).
  - Close() is synchronous: it waits on a sync.WaitGroup for the sweeper
    goroutine to actually observe the stop channel and return, rather than
    just signaling and hoping — callers can rely on "no goroutine owned by
    this cache is running" being true immediately after Close returns.
  - A loader error is never written to the store — only the success path
    calls c.store.store — so a transient failure doesn't poison the cache
    for a full TTL.

ALTERNATIVE APPROACHES

  - golang.org/x/sync/singleflight provides Group.Do with the same
    join-or-create shape implemented here, plus a Forget method for
    explicitly evicting an in-flight (or just-completed) call — worth
    reaching for in production code once you understand this mechanism;
    reimplementing it here is purely so the mechanism isn't a black box.
  - sync.Map's LoadOrStore could implement the inflight join-or-create step
    atomically without a separate mutex — but LoadOrStore always
    constructs its second argument eagerly even on the Load path, so
    you'd allocate a fresh *call[V] on every single Get, hit or miss; the
    explicit mutex here only allocates a *call[V] when actually needed.
  - An LRU/LFU size-bounded eviction policy layered on top of TTL (stretch
    goal in the explanation file) is a common production addition when
    memory must be bounded by entry count, not just by time.
  - A "loading placeholder" stored directly in the main store (instead of a
    separate inflight map) is another common single-flight shape, but
    requires every store method to understand two entry states (loading vs
    loaded) instead of keeping that state cleanly out of the storage layer.
*/
