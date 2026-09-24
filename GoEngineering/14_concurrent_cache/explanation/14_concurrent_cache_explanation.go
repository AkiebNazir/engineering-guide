/*
Problem 14 — Concurrent Cache (sync.Map vs mutex, single-flight, TTL eviction)

# WHAT WE'RE BUILDING

A generic, concurrency-safe, in-process cache with:
  - TTL-based expiry (entries become invisible/collectible after their
    time-to-live elapses, with a background sweeper reclaiming memory
    instead of relying purely on lazy get-time checks),
  - single-flight loading (concurrent Gets for the same missing key
    collapse into exactly one call to the loader function, not N),
  - a choice of two internal storage strategies (mutex-protected map vs
    sync.Map) selectable at construction, so the trade-off is something you
    can benchmark, not just read about.

This is the cache shape that sits in front of an expensive operation inside
a single Go process — a DB row, a computed aggregate, a downstream API
response — where the goal is "never do the expensive work twice
concurrently for the same key, and never serve stale data past its TTL."

# WHY THIS MATTERS IN REAL SYSTEMS

Three failure modes show up constantly in hand-rolled caches:

 1. **Cache stampede / thundering herd.** A popular key expires (or is
    never populated) and 500 concurrent requests all miss at once, all call
    the expensive loader at once, and the backing store that the cache was
    protecting gets hit with 500x its normal load simultaneously. This is
    one of the most common real production incidents caused by caching
    code. Single-flight collapses those 500 calls into 1: the other 499
    goroutines block briefly and then receive the same result the 1
    in-flight call produced.
 2. **Unbounded growth from lazy-only expiry.** If entries are only checked
    "is this expired?" when read, a key that stops being read (e.g. a user
    who never comes back) stays in memory forever — the map only shrinks on
    access, never on time passing. A background sweeper (or an eviction
    check woven into every operation, if you choose to avoid a goroutine)
    is what actually bounds memory over the life of a long-running process.
 3. **Choosing sync.Map by default.** sync.Map is optimized for a specific
    access pattern (keys mostly written once and read many times by many
    goroutines, or disjoint key sets per goroutine) and is a Pessimization
    for a general-purpose read-write-heavy cache — the stdlib docs say this
    explicitly. A mutex-protected map[K]V is faster for most cache
    workloads. This exercise makes you implement both and benchmark them so
    the trade-off is measured, not assumed.

# CONCEPTS COVERED

  - Generic cache: `Cache[K comparable, V any]`
  - sync.Map vs sync.Mutex+map: two Store implementations behind one
    interface, benchmarked against each other
  - Hand-rolled single-flight (do NOT import golang.org/x/sync/singleflight
    — implement the mechanism yourself so you understand what it does: a
    map of in-flight calls keyed by K, each guarded so concurrent callers
    for the same key wait on the SAME loader invocation's result instead of
    starting their own)
  - TTL eviction: per-entry expiry timestamp + a background sweeper
    goroutine with clean shutdown (no goroutine leak)
  - Context-aware loading: the loader function accepts a context so a
    caller's cancellation/timeout propagates into (or at least bounds) the
    single-flight-shared load
  - Race safety verified with `go test -race`

# SPEC

	type Loader[K comparable, V any] func(ctx context.Context, key K) (V, error)

	type Cache[K comparable, V any] struct { ... }

	type Store string // "mutex" or "syncmap" — selects internal storage strategy

	type Options struct {
	    TTL             time.Duration // required, > 0
	    SweepInterval   time.Duration // how often the background sweeper runs; > 0
	    Store           Store         // defaults to "mutex" if empty
	}

	func New[K comparable, V any](opts Options) *Cache[K, V]
	    Constructs a ready-to-use cache and starts its background sweeper
	    goroutine.

	func (c *Cache[K, V]) Get(ctx context.Context, key K, load Loader[K, V]) (V, error)
	    Returns the cached value for key if present and not expired.
	    Otherwise calls load exactly once per set of concurrently-missing
	    callers for that key (single-flight), stores the result (only on
	    success — a loader error is never cached) with a fresh TTL, and
	    returns it to every waiter.

	func (c *Cache[K, V]) Set(key K, value V)
	    Unconditionally stores value for key with a fresh TTL, bypassing
	    the loader path entirely (for pre-warming or explicit writes).

	func (c *Cache[K, V]) Delete(key K)
	    Removes key immediately, regardless of TTL.

	func (c *Cache[K, V]) Len() int
	    Number of currently live (non-expired) entries. For the sync.Map
	    backend this necessarily means a full scan — document that cost.

	func (c *Cache[K, V]) Close()
	    Stops the background sweeper goroutine. Idempotent. After Close,
	    Get/Set/Delete remain safe to call (they just won't benefit from
	    background sweeping — lazy expiry-on-read still applies) — Close
	    is a resource-cleanup operation, not a hard shutdown gate.

ACCEPTANCE CRITERIA

  - N concurrent Get calls for the same missing key result in exactly ONE
    call to the loader function (verified in tests with an atomic call
    counter).
  - An expired entry is never returned by Get: a lazy check-on-read backstop
    catches anything the background sweeper hasn't gotten to yet.
  - The background sweeper does not leak: Close() stops it, verified with a
    done-channel or similar deterministic synchronization (not a sleep).
  - Race-free under `go test -race` with concurrent Get/Set/Delete/Close
    from many goroutines against the same cache, for both Store variants.
  - A loader error is propagated to all waiters for that single-flight call
    and is NOT cached — the next Get retries the loader.
*/
package cache

import (
	"context"
	"time"
)

// Loader loads the value for key on a cache miss.
type Loader[K comparable, V any] func(ctx context.Context, key K) (V, error)

// Store selects the internal storage strategy.
type Store string

const (
	// StoreMutex backs the cache with a plain map[K]entry[V] guarded by a
	// sync.Mutex. TODO: this is the default when Options.Store is empty.
	StoreMutex Store = "mutex"
	// StoreSyncMap backs the cache with sync.Map.
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

// Cache is a generic, concurrency-safe, TTL-expiring cache with
// single-flight loading. The zero value is not usable; construct with New.
//
// TODO: fields you'll likely need:
//   - opts Options
//   - a storage abstraction (interface or two concrete implementations
//     selected at construction time) holding entry[V] per key
//   - inflight map[K]*call[V] + a mutex guarding it, for single-flight
//   - a stop channel + sync.WaitGroup (or similar) for Close() to
//     shut down the sweeper goroutine deterministically
type Cache[K comparable, V any] struct {
	// TODO: fields
}

// entry is one stored value plus its expiry deadline.
// TODO: fields: value V, expiresAt time.Time.
type entry[V any] struct {
	// TODO: fields
}

// call is one in-flight single-flight load for a given key: the first
// goroutine to miss on a key creates one of these, does the actual load,
// and every other concurrently-missing goroutine for the SAME key waits on
// it via done instead of calling load itself.
// TODO: fields: done chan struct{} (closed when the load finishes), value
// V, err error — the classic "future" shape.
type call[V any] struct {
	// TODO: fields
}

// New constructs a ready-to-use Cache and starts its background sweeper
// goroutine. Panics if opts.TTL <= 0 or opts.SweepInterval <= 0.
//
// TODO: implement.
func New[K comparable, V any](opts Options) *Cache[K, V] {
	panic("TODO: implement New")
}

// Get returns the cached value for key if present and unexpired. On a
// miss, it calls load — collapsing concurrent misses for the same key into
// exactly one loader call (single-flight) — stores the result on success
// with a fresh TTL, and returns it to every waiter. A loader error is
// returned to every waiter and is never cached.
//
// TODO: implement:
//  1. Fast path: look up key; if present and not expired, return it.
//  2. Slow path: join or create the in-flight call for key under the
//     inflight-map's own lock (NOT the storage lock — see hints).
//     - If you created it: run load, store on success, close done,
//     release the inflight-map entry.
//     - If you joined an existing one: wait on done (respecting ctx
//     cancellation via select), then read the shared result.
func (c *Cache[K, V]) Get(ctx context.Context, key K, load Loader[K, V]) (V, error) {
	panic("TODO: implement Cache.Get")
}

// Set unconditionally stores value for key with a fresh TTL.
// TODO: implement.
func (c *Cache[K, V]) Set(key K, value V) {
	panic("TODO: implement Cache.Set")
}

// Delete removes key immediately, regardless of TTL.
// TODO: implement.
func (c *Cache[K, V]) Delete(key K) {
	panic("TODO: implement Cache.Delete")
}

// Len reports the number of currently live (non-expired) entries.
// TODO: implement. For the sync.Map backend this requires a full Range
// scan — document that cost at the call site or in the method doc.
func (c *Cache[K, V]) Len() int {
	panic("TODO: implement Cache.Len")
}

// Close stops the background sweeper goroutine. Idempotent; safe to call
// more than once. Get/Set/Delete remain safe to call afterward.
// TODO: implement using a sync.Once plus closing a stop channel, and wait
// (via sync.WaitGroup or a done channel) for the sweeper goroutine to
// actually exit before returning — Close should be synchronous, not
// "requested and hopefully done eventually."
func (c *Cache[K, V]) Close() {
	panic("TODO: implement Cache.Close")
}

/*
HINTS

  - Single-flight needs its OWN lock, separate from whatever protects the
    storage map. If you reuse the storage lock for the inflight bookkeeping
    too, you'll either deadlock (holding the storage lock while waiting on
    a load that itself wants the storage lock to Set the result) or
    serialize unrelated keys behind one key's slow load.
  - The "join or create" step for single-flight must be atomic: two
    goroutines checking "is there an inflight call for key?" and both
    finding none, then both creating one, defeats the entire point. Do the
    check-and-maybe-create under the inflight mutex as one critical
    section.
  - For sync.Map: LoadOrStore is your friend for atomic check-and-set of
    the *call[V] entry itself — but note sync.Map's LoadOrStore always
    evaluates its second argument eagerly (you're constructing a fresh
    *call[V] every time even when it won't be used) which is a real,
    measurable cost the mutex+map version doesn't pay; worth noting when
    you benchmark.
  - Context cancellation while WAITING on someone else's in-flight call
    should return ctx.Err() to the waiter that gave up, WITHOUT canceling
    the load for the other waiters still waiting on it — the load isn't
    "yours" to cancel just because you stopped waiting.
  - The background sweeper should hold its lock only long enough to scan
    and delete expired keys, never for the whole SweepInterval — a
    sweep is a bounded, fast operation; don't let it block Get/Set for
    unrelated keys any longer than necessary.

COMMON PITFALLS

  - Caching a loader error — the acceptance criteria explicitly forbid
    this: a transient failure (backing store hiccup) must not poison the
    cache for the full TTL; the next Get should retry.
  - Forgetting the lazy expiry-on-read backstop and relying only on the
    sweeper — with a SweepInterval longer than TTL (a legitimate config,
    e.g. sweep every minute, TTL 10s), Get would return stale data for up
    to a minute without the read-time check.
  - Closing the `done` channel on a *call[V] more than once (if load
    somehow runs twice for the same call — shouldn't happen with correct
    single-flight, but guard it) — panics.
  - Leaking the sweeper goroutine because Close() only sets a flag/closes a
    channel without waiting for the goroutine to observe it and exit —
    tests that check goroutine counts before/after Close will catch this,
    but only if you write that test.
  - Using time.Now() directly scattered through the code instead of
    capturing it once per operation — makes expiry-boundary tests flaky
    (two time.Now() calls microseconds apart can straddle the TTL boundary
    differently than intended).

STRETCH GOALS

  - Add an eviction policy on top of TTL (LRU or LFU with a max entry
    count) so the cache is bounded by size, not just by time.
  - Add per-key TTL overrides (Set taking an optional ttl parameter distinct
    from the cache-wide default).
  - Write a benchmark (`go test -bench`) comparing StoreMutex vs
    StoreSyncMap under: (a) read-heavy/write-rare workload, (b) balanced
    read/write, (c) write-heavy workload — confirm or refute the stdlib's
    documented sync.Map sweet spot on this machine.
  - Implement a real golang.org/x/sync/singleflight-style Do/Forget API
    surface (separate group keyed independently of the cache) and compare
    it against your hand-rolled version's behavior under cancellation.
*/
