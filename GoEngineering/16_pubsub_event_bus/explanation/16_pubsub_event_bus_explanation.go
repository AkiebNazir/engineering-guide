/*
Problem 16 — Pub/Sub Event Bus (subscriber lifecycle, slow-consumer handling)

WHAT WE'RE BUILDING

An in-process, generic publish/subscribe event bus: publishers call Publish
with an event, and every currently-subscribed consumer receives a copy on
its own channel. This is the backbone of most event-driven components
inside a single Go service — a domain-event dispatcher, a "notify all
connected websocket clients" hub, an in-memory fan-out layer in front of a
real message broker (Kafka/NATS) used for unit tests or for low-latency
same-process notifications.

# WHY THIS MATTERS IN REAL SYSTEMS

Every non-trivial pub/sub implementation has to answer three questions that
naive "just range over a slice of channels and send" code gets wrong:

 1. Subscriber lifecycle — how does a consumer stop listening without the
    publisher blocking forever on a channel nobody drains, and without the
    bus leaking a goroutine or a map entry per subscriber that ever
    unsubscribed?
 2. Slow consumers — if one subscriber's channel fills up because that
    consumer is slow (or dead), what happens? Do you block every other
    subscriber and the publisher itself? Drop events? For how long?
 3. Shutdown — when the bus itself closes, how do in-flight publishers and
    all subscribers find out, cleanly, without a panic from a double-close
    or a send on a closed channel?

Get these wrong and you get either an event bus that silently stalls the
whole process because of one misbehaving consumer, or one that panics under
concurrent load, or one that leaks a goroutine per subscriber forever.

CONCEPTS COVERED

  - Generic pub/sub: `Bus[T any]`, `Publish(T)`, `Subscribe() *Subscription[T]`
  - Subscriber lifecycle: clean Subscribe/Unsubscribe with no leaked
    goroutines and no double-close panics
  - Slow-consumer policy: bounded per-subscriber channel + drop-oldest
    (chosen and justified over block-with-timeout — see the solution file)
  - Graceful Close(): stop accepting new publishes/subscribes, close every
    subscriber channel exactly once, safe to call concurrently and multiple
    times
  - Concurrency safety verified with `go test -race`

SPEC

	type Bus[T any] struct { ... }

	func NewBus[T any](bufferSize int) *Bus[T]
	    bufferSize is the *per-subscriber* channel capacity (must be >= 1).

	func (b *Bus[T]) Subscribe() *Subscription[T]
	    Registers a new subscriber and returns a handle exposing:
	      Events() <-chan T   -- receive-only channel of published events
	      Unsubscribe()       -- idempotent; stops delivery and releases
	                              the bus's reference to this subscriber
	    Subscribing after Close has been called returns a Subscription
	    whose Events() channel is already closed (never panics).

	func (b *Bus[T]) Publish(event T)
	    Delivers event to every currently-subscribed subscriber's channel.
	    Never blocks on a slow subscriber: if a subscriber's channel is
	    full, the OLDEST buffered event for that subscriber is dropped to
	    make room for the new one (drop-oldest policy — see spec below).
	    Publish on a closed bus is a safe no-op.

	func (b *Bus[T]) Close()
	    Idempotent, concurrency-safe. After Close returns:
	      - every live subscriber's Events() channel is closed (consumers
	        observe channel closure and can stop their range loops)
	      - no goroutine owned by the bus is still running
	      - further Publish/Subscribe calls are safe no-ops (Subscribe
	        still returns a valid, already-closed Subscription)

	func (b *Bus[T]) SubscriberCount() int
	    Number of currently active subscribers (for tests/observability).

Slow-consumer policy — bounded channel + DROP-OLDEST (not block, not
drop-newest):
  - A publisher must never be made to wait on a consumer it does not
    control — one slow subscriber must not stall delivery to every other
    subscriber, let alone the publisher's own call site.
  - Between "drop the newest (incoming) event" and "drop the oldest
    buffered event," prefer drop-oldest: for most event-bus consumers
    (metrics, cache-invalidation, notifications) the most RECENT state is
    the one worth having if you can only keep N — an old event superseded
    by a newer one is usually worthless once the newer one exists.
  - This is a deliberate, named trade-off, not silent data loss: it must be
    observable (see DroppedCount below) so operators can alert on a
    consumer that's chronically behind.

ACCEPTANCE CRITERIA

  - Multiple publishers and multiple subscribers operating concurrently,
    with subscribers subscribing/unsubscribing throughout, is race-free
    under `go test -race`.
  - A subscriber that never reads its channel does not block Publish for
    other subscribers (bounded delay only, via the drop-oldest policy).
  - Close() is safe to call concurrently from multiple goroutines and more
    than once; it terminates all subscriber channels and every internal
    goroutine (verified in tests by comparing runtime.NumGoroutine before
    vs. after, or by explicit done-channel synchronization).
  - Unsubscribe() is idempotent (safe to call twice, or after Close()).
*/
package eventbus

// Bus is a generic, in-process publish/subscribe event bus for events of
// type T. The zero value is not usable; construct with NewBus.
//
// TODO: fields you'll likely need:
//   - mu sync.Mutex (or RWMutex) guarding the subscriber set
//   - subs map[uint64]*subscriber[T]
//   - nextID uint64
//   - bufferSize int
//   - closed bool
//   - droppedCount atomic counter (see DroppedCount TODO below)
type Bus[T any] struct {
	// TODO: fields
}

// subscriber is the bus's internal bookkeeping for one subscription.
// TODO: fields you'll likely need:
//   - ch chan T             -- the buffered delivery channel
//   - mu sync.Mutex         -- serializes the drop-oldest make-room logic
//     for THIS subscriber against concurrent
//     publishers (channels alone aren't enough:
//     "check len, then send" is a check-then-act
//     race between two goroutines publishing at
//     once)
//   - closed bool           -- guards against double-close on Unsubscribe
//     racing with Close
type subscriber[T any] struct {
	// TODO: fields
}

// Subscription is the handle returned to callers of Bus.Subscribe.
type Subscription[T any] struct {
	// TODO: fields — needs a reference back to the bus (to remove itself
	// on Unsubscribe) and its subscriber id, plus the channel to expose
	// via Events().
}

// NewBus constructs a ready-to-use Bus with the given per-subscriber
// channel capacity. Panics if bufferSize < 1 (a zero-capacity channel
// makes drop-oldest meaningless — there's nothing to drop, every send
// would need to drop the event about to be sent).
//
// TODO: implement.
func NewBus[T any](bufferSize int) *Bus[T] {
	panic("TODO: implement NewBus")
}

// Subscribe registers a new subscriber and returns its Subscription.
//
// TODO: implement. Must be safe to call concurrently with Publish, Close,
// and other Subscribe/Unsubscribe calls. If the bus is already closed,
// return a Subscription wrapping an already-closed channel instead of
// panicking or registering a subscriber that will never receive Close.
func (b *Bus[T]) Subscribe() *Subscription[T] {
	panic("TODO: implement Bus.Subscribe")
}

// Publish delivers event to every currently active subscriber.
//
// TODO: implement the drop-oldest policy: for each subscriber, attempt a
// non-blocking send; on failure (channel full), drop one buffered event
// (non-blocking receive) then send again (still non-blocking — a
// concurrent Unsubscribe/Close could have closed the channel between your
// receive and your send, so guard against sending on a closed channel,
// e.g. by holding that subscriber's own mutex across the whole
// drop-then-send sequence and checking its closed flag under that lock).
// Must be a no-op, not a panic, if the bus is closed.
func (b *Bus[T]) Publish(event T) {
	panic("TODO: implement Bus.Publish")
}

// Close shuts the bus down: closes every subscriber's channel exactly
// once and marks the bus closed so further Publish/Subscribe are no-ops.
//
// TODO: implement. Must be idempotent and safe under concurrent callers
// (use a sync.Once or an explicit closed-flag check under the bus mutex).
func (b *Bus[T]) Close() {
	panic("TODO: implement Bus.Close")
}

// SubscriberCount reports the number of currently active subscribers.
// TODO: implement.
func (b *Bus[T]) SubscriberCount() int {
	panic("TODO: implement Bus.SubscriberCount")
}

// DroppedCount reports how many events have been dropped across all
// subscribers due to the drop-oldest slow-consumer policy, since bus
// creation. Exposed so operators can alert on a chronically slow
// consumer instead of silently losing data.
// TODO: implement with an atomic counter incremented in Publish.
func (b *Bus[T]) DroppedCount() uint64 {
	panic("TODO: implement Bus.DroppedCount")
}

// Events returns the receive-only channel this subscription delivers
// events on. It is closed when Unsubscribe is called or the bus closes.
// TODO: implement.
func (s *Subscription[T]) Events() <-chan T {
	panic("TODO: implement Subscription.Events")
}

// Unsubscribe stops delivery to this subscription and releases the bus's
// reference to it. Idempotent: safe to call more than once, and safe to
// call after the bus has been closed.
// TODO: implement. Must close the subscriber's channel exactly once (a
// second close, or a Close() racing with this Unsubscribe, must not
// panic) and remove the subscriber from the bus's map so Publish stops
// iterating over it (otherwise: goroutine/memory leak — the map entry,
// and everything it references, lives forever).
func (s *Subscription[T]) Unsubscribe() {
	panic("TODO: implement Subscription.Unsubscribe")
}

/*
HINTS

  - You do NOT need a goroutine per subscriber, and you do NOT need a
    goroutine per Publish call. A correct implementation can do all
    delivery synchronously inside Publish, using only non-blocking
    channel operations (select/default). Fewer goroutines means fewer
    places to leak one.
  - The classic "drop-oldest" race: goroutine A checks the channel is
    full and starts draining one item; goroutine B (another publisher)
    does the same thing at the same instant; without per-subscriber
    synchronization you can drop two items and only make room for one
    send, or worse, both try to send into the same freed slot. Guard the
    whole "make room, then send" sequence with the subscriber's own
    mutex, not the bus-wide lock (holding the bus-wide lock across a
    channel send would serialize ALL subscribers behind the slowest one
    doing bus-lock-held work — the opposite of what you want).
  - Closing a channel that a concurrent goroutine might still be sending
    to is the most common source of a "send on closed channel" panic in
    pub/sub code. The fix is ordering: only the code path that holds the
    subscriber's mutex is allowed to close that subscriber's channel, and
    every send path must check the closed flag under the same mutex
    before sending.
  - `sync.Once` is a clean fit for Bus.Close's "run exactly once"
    requirement, but you still need the bus-wide mutex (or the Once
    itself, which is safe for concurrent Do calls) to safely iterate the
    subscriber map while Subscribe/Unsubscribe might be running
    concurrently.

COMMON PITFALLS

  - Ranging over the subscriber map and sending on each channel while
    holding the bus's lock for the entire Publish call — this serializes
    every publisher behind however long each per-subscriber send takes,
    defeating the whole point of a non-blocking bus. Copy out the
    subscriber list (or subscriber pointers) under a brief lock, then do
    delivery lock-free (each subscriber's own mutex still protects its
    channel).
  - Forgetting Unsubscribe must remove the entry from the bus's map, not
    just close the channel — an unremoved entry means Publish keeps
    attempting (fast, no-op) sends into a closed channel's subscriber
    forever, and the map itself grows without bound over the life of a
    long-running process with high subscriber churn.
  - A bufferSize of 0 breaks the drop-oldest policy: there's no buffered
    item to drop to make room, so every Publish on a slow/absent consumer
    would either block or silently drop the newest, incoming event
    instead of an old one.
  - Not distinguishing Subscribe-before-Close (should keep working
    normally) from Subscribe-after-Close (should return something inert,
    not panic and not silently register a subscriber that never learns
    the bus is gone).

STRETCH GOALS

  - Add topic-based routing: `Bus[T]` keyed by a topic string, so
    `Publish(topic, event)` only reaches subscribers of that topic.
  - Add a context-aware Subscribe(ctx) that auto-unsubscribes when ctx is
    canceled, without a leaked goroutine per subscription (hint: this
    genuinely needs one goroutine per context-bound subscription — think
    about how to keep it from leaking when Unsubscribe is called instead
    of ctx being canceled).
  - Replace drop-oldest with a pluggable policy (`type OverflowPolicy int`
    with drop-oldest / drop-newest / block-with-timeout) selected per
    Subscribe call, and write a benchmark comparing publisher latency
    under a stalled subscriber for each policy.
  - Add per-subscriber delivery metrics (delivered/dropped counts) exposed
    via the Subscription handle, not just bus-wide totals.
*/
