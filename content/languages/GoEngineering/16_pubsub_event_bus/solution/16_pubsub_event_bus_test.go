package eventbus

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

func TestNewBusPanicsOnInvalidBufferSize(t *testing.T) {
	tests := []struct {
		name       string
		bufferSize int
	}{
		{"zero", 0},
		{"negative", -1},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			defer func() {
				if recover() == nil {
					t.Fatalf("NewBus(%d) did not panic", tt.bufferSize)
				}
			}()
			NewBus[int](tt.bufferSize)
		})
	}
}

func TestPublishDeliversToAllSubscribers(t *testing.T) {
	b := NewBus[string](4)
	defer b.Close()

	sub1 := b.Subscribe()
	sub2 := b.Subscribe()

	if got := b.SubscriberCount(); got != 2 {
		t.Fatalf("SubscriberCount() = %d, want 2", got)
	}

	b.Publish("hello")

	select {
	case v := <-sub1.Events():
		if v != "hello" {
			t.Fatalf("sub1 got %q, want %q", v, "hello")
		}
	case <-time.After(time.Second):
		t.Fatal("sub1 timed out waiting for event")
	}

	select {
	case v := <-sub2.Events():
		if v != "hello" {
			t.Fatalf("sub2 got %q, want %q", v, "hello")
		}
	case <-time.After(time.Second):
		t.Fatal("sub2 timed out waiting for event")
	}
}

func TestUnsubscribeStopsDeliveryAndClosesChannel(t *testing.T) {
	b := NewBus[int](4)
	defer b.Close()

	sub := b.Subscribe()
	sub.Unsubscribe()

	if got := b.SubscriberCount(); got != 0 {
		t.Fatalf("SubscriberCount() after Unsubscribe = %d, want 0", got)
	}

	// The channel must be closed, not merely idle.
	select {
	case v, ok := <-sub.Events():
		if ok {
			t.Fatalf("expected closed channel, got value %v", v)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for channel closure")
	}

	// Publishing afterward must not panic (no send on closed channel).
	b.Publish(42)
}

func TestUnsubscribeIsIdempotent(t *testing.T) {
	b := NewBus[int](1)
	defer b.Close()

	sub := b.Subscribe()
	sub.Unsubscribe()
	sub.Unsubscribe() // must not panic
}

func TestUnsubscribeAfterCloseIsSafe(t *testing.T) {
	b := NewBus[int](1)
	sub := b.Subscribe()
	b.Close()
	sub.Unsubscribe() // must not panic (double-close guard)
}

func TestCloseIsIdempotentAndConcurrencySafe(t *testing.T) {
	b := NewBus[int](1)
	b.Subscribe()
	b.Subscribe()

	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			b.Close()
		}()
	}
	wg.Wait() // must not panic
}

func TestCloseClosesAllSubscriberChannels(t *testing.T) {
	b := NewBus[int](1)
	subs := make([]*Subscription[int], 5)
	for i := range subs {
		subs[i] = b.Subscribe()
	}

	b.Close()

	for i, sub := range subs {
		select {
		case _, ok := <-sub.Events():
			if ok {
				t.Fatalf("sub %d: expected closed channel", i)
			}
		case <-time.After(time.Second):
			t.Fatalf("sub %d: timed out waiting for channel closure", i)
		}
	}

	if got := b.SubscriberCount(); got != 0 {
		t.Fatalf("SubscriberCount() after Close = %d, want 0", got)
	}
}

func TestSubscribeAfterCloseReturnsClosedSubscription(t *testing.T) {
	b := NewBus[int](1)
	b.Close()

	sub := b.Subscribe()
	if got := b.SubscriberCount(); got != 0 {
		t.Fatalf("SubscriberCount() = %d, want 0", got)
	}

	select {
	case _, ok := <-sub.Events():
		if ok {
			t.Fatal("expected already-closed channel")
		}
	default:
		t.Fatal("expected channel to be immediately closed, not merely empty")
	}

	// Must not panic.
	sub.Unsubscribe()
}

func TestPublishOnClosedBusIsNoOp(t *testing.T) {
	b := NewBus[int](1)
	sub := b.Subscribe()
	b.Close()

	b.Publish(1) // must not panic

	select {
	case _, ok := <-sub.Events():
		if ok {
			t.Fatal("expected closed channel, got open channel with value")
		}
	default:
		t.Fatal("expected channel already closed")
	}
}

func TestSlowConsumerDropsOldestWithoutBlockingPublisher(t *testing.T) {
	b := NewBus[int](2)
	defer b.Close()

	sub := b.Subscribe() // never drained — the "slow"/absent consumer
	other := b.Subscribe()

	// Publish and immediately receive on `other` in lockstep: this proves
	// delivery to `other` is undisturbed by `sub` never draining, without
	// relying on a separately-scheduled goroutine to race the publish loop
	// (which would make the test's own timing, not the bus, the thing
	// under test). The bus itself does all delivery synchronously inside
	// Publish, so this lockstep pattern exercises the exact same code path
	// a concurrently-running consumer would.
	done := make(chan struct{})
	go func() {
		defer close(done)
		for i := 0; i < 100; i++ {
			b.Publish(i)
			select {
			case v := <-other.Events():
				if v != i {
					t.Errorf("other received %d, want %d", v, i)
				}
			case <-time.After(time.Second):
				t.Errorf("other timed out waiting for event %d", i)
				return
			}
		}
	}()

	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("Publish blocked on a slow consumer — drop-oldest policy failed")
	}

	// The slow subscriber's buffer should hold only the most recent events
	// (drop-oldest), i.e. the last two published: 98, 99.
	var got []int
	for i := 0; i < 2; i++ {
		select {
		case v := <-sub.Events():
			got = append(got, v)
		case <-time.After(time.Second):
			t.Fatalf("timed out reading buffered event %d", i)
		}
	}
	if got[0] != 98 || got[1] != 99 {
		t.Fatalf("slow subscriber buffer = %v, want [98 99]", got)
	}

	if dropped := b.DroppedCount(); dropped == 0 {
		t.Fatal("DroppedCount() = 0, want > 0 after overflowing a slow subscriber")
	}
}

func TestSubscriberCountReflectsLifecycle(t *testing.T) {
	b := NewBus[int](1)
	defer b.Close()

	if got := b.SubscriberCount(); got != 0 {
		t.Fatalf("initial SubscriberCount() = %d, want 0", got)
	}

	sub1 := b.Subscribe()
	if got := b.SubscriberCount(); got != 1 {
		t.Fatalf("SubscriberCount() = %d, want 1", got)
	}

	sub2 := b.Subscribe()
	if got := b.SubscriberCount(); got != 2 {
		t.Fatalf("SubscriberCount() = %d, want 2", got)
	}

	sub1.Unsubscribe()
	if got := b.SubscriberCount(); got != 1 {
		t.Fatalf("SubscriberCount() = %d, want 1", got)
	}

	sub2.Unsubscribe()
	if got := b.SubscriberCount(); got != 0 {
		t.Fatalf("SubscriberCount() = %d, want 0", got)
	}
}

// TestConcurrentPublishSubscribeUnsubscribeClose is the race-detector
// stress test: many publishers, many subscribers subscribing/unsubscribing
// throughout, and a final Close from multiple goroutines. It asserts no
// panic and no deadlock (via an overall timeout) — go test -race asserts
// the rest.
func TestConcurrentPublishSubscribeUnsubscribeClose(t *testing.T) {
	b := NewBus[int](8)

	const (
		publishers  = 8
		subscribers = 8
		eventsEach  = 200
	)

	var wg sync.WaitGroup

	// Publishers hammer Publish concurrently.
	for p := 0; p < publishers; p++ {
		wg.Add(1)
		go func(p int) {
			defer wg.Done()
			for i := 0; i < eventsEach; i++ {
				b.Publish(p*eventsEach + i)
			}
		}(p)
	}

	// Subscribers churn: subscribe, read a few, unsubscribe, repeat.
	for s := 0; s < subscribers; s++ {
		wg.Add(1)
		go func(s int) {
			defer wg.Done()
			for round := 0; round < 20; round++ {
				sub := b.Subscribe()
				drainDeadline := time.After(5 * time.Millisecond)
			drain:
				for {
					select {
					case _, ok := <-sub.Events():
						if !ok {
							break drain
						}
					case <-drainDeadline:
						break drain
					}
				}
				sub.Unsubscribe()
			}
		}(s)
	}

	// Multiple concurrent Close callers, fired partway through.
	for c := 0; c < 4; c++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			time.Sleep(2 * time.Millisecond)
			b.Close()
		}()
	}

	doneCh := make(chan struct{})
	go func() {
		wg.Wait()
		close(doneCh)
	}()

	select {
	case <-doneCh:
	case <-time.After(10 * time.Second):
		t.Fatal("deadlock: goroutines did not finish within timeout")
	}

	b.Close() // final idempotent close must not panic
}

func TestGenericOverArbitraryType(t *testing.T) {
	type event struct {
		Name string
		Seq  int
	}

	b := NewBus[event](4)
	defer b.Close()

	sub := b.Subscribe()
	b.Publish(event{Name: "created", Seq: 1})

	select {
	case got := <-sub.Events():
		want := event{Name: "created", Seq: 1}
		if got != want {
			t.Fatalf("got %+v, want %+v", got, want)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for event")
	}
}

// TestNoGoroutineLeakAfterClose is a best-effort smoke test: it confirms
// that unsubscribing/closing does not require any bus-owned background
// goroutine to still be alive by checking that all subscriber channels
// have observably closed and further operations are pure no-ops within a
// bounded time (the bus documented design has zero background goroutines,
// so there is nothing time-based to poll for — this test instead documents
// and pins that invariant via behavior).
func TestNoGoroutineLeakAfterClose(t *testing.T) {
	b := NewBus[int](1)
	var subs []*Subscription[int]
	for i := 0; i < 50; i++ {
		subs = append(subs, b.Subscribe())
	}
	b.Close()

	for i, sub := range subs {
		select {
		case _, ok := <-sub.Events():
			if ok {
				t.Fatalf("sub %d: channel not closed", i)
			}
		default:
			t.Fatalf("sub %d: channel not yet closed", i)
		}
	}

	// Further calls after Close must remain cheap no-ops, not spin up new
	// work.
	for i := 0; i < 100; i++ {
		b.Publish(i)
	}
	extra := b.Subscribe()
	extra.Unsubscribe()
	b.Close()
}

func ExampleBus() {
	b := NewBus[string](4)
	sub := b.Subscribe()

	b.Publish("event-1")
	fmt.Println(<-sub.Events())

	sub.Unsubscribe()
	b.Close()
	// Output: event-1
}
