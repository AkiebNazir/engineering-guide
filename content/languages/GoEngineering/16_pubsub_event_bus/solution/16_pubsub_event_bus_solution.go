/*
Problem 16 — Pub/Sub Event Bus (reference solution)

See explanation/16_pubsub_event_bus_explanation.go for the full spec,
rationale, and acceptance criteria. This file implements it.

Design summary:
  - Bus-wide sync.Mutex guards only the subscriber map and the closed flag —
    never held across a channel send, so one slow subscriber cannot stall
    delivery to any other subscriber or the publisher's call site.
  - Each subscriber has its own mutex guarding "make room, then send" and
    its own closed flag, so Close/Unsubscribe racing with Publish can never
    double-close a channel or send on a closed one.
  - Delivery is fully synchronous inside Publish: no goroutine per
    subscriber, no goroutine per publish call. Non-blocking send; on a full
    channel, drop one buffered (oldest) event to make room, then send.
  - Close uses sync.Once for its "run exactly once" contract, combined with
    the bus mutex to safely snapshot and clear the subscriber map.
*/
package eventbus

import "sync"
import "sync/atomic"

// subscriber is the bus's internal bookkeeping for one subscription.
type subscriber[T any] struct {
	id     uint64
	ch     chan T
	mu     sync.Mutex // serializes drop-oldest make-room + send + close for this subscriber
	closed bool
}

// Bus is a generic, in-process publish/subscribe event bus for events of
// type T. The zero value is not usable; construct with NewBus.
type Bus[T any] struct {
	mu         sync.Mutex
	subs       map[uint64]*subscriber[T]
	nextID     uint64
	bufferSize int
	closed     bool
	closeOnce  sync.Once

	dropped atomic.Uint64
}

// Subscription is the handle returned to callers of Bus.Subscribe.
type Subscription[T any] struct {
	bus *Bus[T]
	sub *subscriber[T]
}

// NewBus constructs a ready-to-use Bus with the given per-subscriber
// channel capacity. Panics if bufferSize < 1 (a zero-capacity channel makes
// drop-oldest meaningless — see explanation file for why).
func NewBus[T any](bufferSize int) *Bus[T] {
	if bufferSize < 1 {
		panic("eventbus: bufferSize must be >= 1")
	}
	return &Bus[T]{
		subs:       make(map[uint64]*subscriber[T]),
		bufferSize: bufferSize,
	}
}

// closedSubscription builds a Subscription whose Events() channel is
// already closed — used for Subscribe-after-Close, so callers never block
// forever or need to special-case a nil bus reference.
func closedSubscription[T any]() *Subscription[T] {
	ch := make(chan T)
	close(ch)
	return &Subscription[T]{sub: &subscriber[T]{ch: ch, closed: true}}
}

// Subscribe registers a new subscriber and returns its Subscription. Safe
// to call concurrently with Publish, Close, and other Subscribe/Unsubscribe
// calls. If the bus is already closed, returns a Subscription wrapping an
// already-closed channel instead of registering a subscriber that would
// never learn the bus is gone.
func (b *Bus[T]) Subscribe() *Subscription[T] {
	b.mu.Lock()
	if b.closed {
		b.mu.Unlock()
		return closedSubscription[T]()
	}
	b.nextID++
	id := b.nextID
	sub := &subscriber[T]{id: id, ch: make(chan T, b.bufferSize)}
	b.subs[id] = sub
	b.mu.Unlock()

	return &Subscription[T]{bus: b, sub: sub}
}

// Publish delivers event to every currently active subscriber. Never blocks
// on a slow subscriber: if a subscriber's channel is full, the oldest
// buffered event for that subscriber is dropped to make room. No-op on a
// closed bus.
func (b *Bus[T]) Publish(event T) {
	b.mu.Lock()
	if b.closed {
		b.mu.Unlock()
		return
	}
	// Snapshot subscriber pointers under the brief bus lock, then deliver
	// lock-free with respect to the bus (each subscriber's own mutex still
	// protects its channel). This is what keeps one slow subscriber from
	// serializing every other subscriber or the publisher behind it.
	targets := make([]*subscriber[T], 0, len(b.subs))
	for _, s := range b.subs {
		targets = append(targets, s)
	}
	b.mu.Unlock()

	for _, s := range targets {
		b.deliver(s, event)
	}
}

// deliver performs the drop-oldest send to a single subscriber, guarded by
// that subscriber's own mutex so a concurrent Close/Unsubscribe cannot race
// with the send-on-closed-channel check.
func (b *Bus[T]) deliver(s *subscriber[T], event T) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.closed {
		return
	}

	select {
	case s.ch <- event:
		return
	default:
	}

	// Channel full: drop the oldest buffered event to make room, then try
	// again. The non-blocking receive is safe here because we're the only
	// goroutine allowed to touch this channel while holding s.mu — every
	// other publisher must acquire the same lock first.
	select {
	case <-s.ch:
		b.dropped.Add(1)
	default:
		// Channel was drained concurrently by nothing (we hold the lock,
		// so this branch is unreachable in practice) — fall through to
		// the send attempt regardless.
	}

	select {
	case s.ch <- event:
	default:
		// Extremely unlikely (would require a concurrent send bypassing
		// the lock, which the design forbids), but never block or panic.
		b.dropped.Add(1)
	}
}

// Close shuts the bus down: closes every subscriber's channel exactly once
// and marks the bus closed so further Publish/Subscribe are no-ops.
// Idempotent and safe under concurrent callers.
func (b *Bus[T]) Close() {
	b.closeOnce.Do(func() {
		b.mu.Lock()
		b.closed = true
		subs := b.subs
		b.subs = make(map[uint64]*subscriber[T])
		b.mu.Unlock()

		for _, s := range subs {
			closeSubscriber(s)
		}
	})
}

// closeSubscriber closes a subscriber's channel exactly once, guarded by
// its own mutex so a racing Unsubscribe cannot double-close.
func closeSubscriber[T any](s *subscriber[T]) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return
	}
	s.closed = true
	close(s.ch)
}

// SubscriberCount reports the number of currently active subscribers.
func (b *Bus[T]) SubscriberCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.subs)
}

// DroppedCount reports how many events have been dropped across all
// subscribers due to the drop-oldest slow-consumer policy, since bus
// creation.
func (b *Bus[T]) DroppedCount() uint64 {
	return b.dropped.Load()
}

// Events returns the receive-only channel this subscription delivers events
// on. It is closed when Unsubscribe is called or the bus closes.
func (s *Subscription[T]) Events() <-chan T {
	return s.sub.ch
}

// Unsubscribe stops delivery to this subscription and releases the bus's
// reference to it. Idempotent, and safe to call after the bus has closed.
func (s *Subscription[T]) Unsubscribe() {
	if s.bus == nil {
		// This is the inert Subscription handed out by Subscribe-after-
		// Close; its channel is already closed, nothing to do.
		return
	}
	s.bus.mu.Lock()
	delete(s.bus.subs, s.sub.id)
	s.bus.mu.Unlock()

	closeSubscriber(s.sub)
}

/*
BEST PRACTICES DEMONSTRATED

  - Lock granularity: a coarse bus-wide lock protects only map membership
    (fast, bounded operations); a per-subscriber lock protects the
    "check-drop-send" sequence on that subscriber's channel. Never hold a
    lock across a blocking or even potentially-slow operation performed on
    behalf of a caller.
  - Snapshot-then-act: Publish copies subscriber pointers out from under the
    bus lock before iterating, so the lock's critical section is O(1) map
    reads, not O(n) channel sends.
  - sync.Once for exactly-once shutdown semantics, combined with ordinary
    mutex-guarded state for everything else Close needs to touch.
  - Idempotency by construction: Unsubscribe and Close both route through
    closeSubscriber, which is itself guarded so any interleaving of the two
    is safe — no double-close panic regardless of call order.
  - Zero extra goroutines: the bus owns no background goroutine at all,
    which trivially satisfies "no leaked goroutine" — there is nothing to
    leak.

ALTERNATIVE APPROACHES

  - Goroutine-per-subscriber with an internal unbounded queue (e.g. a
    linked-list-backed channel) would let Publish never drop events, at the
    cost of one goroutine per subscriber and potentially unbounded memory
    growth if a consumer never catches up — worse for the metrics/cache-
    invalidation use case this bus targets, better if durability matters
    more than the bus's own memory footprint (that's what a real broker is
    for).
  - RWMutex instead of Mutex for the bus-wide lock: Publish only needs a
    read lock to snapshot subscribers (Subscribe/Unsubscribe/Close need the
    write lock). Under heavy concurrent Publish with rare
    Subscribe/Unsubscribe churn this reduces contention; omitted here since
    the critical section is already O(1) and RWMutex has higher overhead
    per lock/unlock than Mutex for the uncontended case.
  - Pluggable overflow policy (drop-oldest vs. drop-newest vs.
    block-with-timeout) as a stretch goal — see the explanation file.
*/
