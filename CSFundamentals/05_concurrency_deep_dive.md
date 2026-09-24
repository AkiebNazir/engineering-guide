# Concurrency — Locks, Conditions, Deadlocks, and Thread-Safe Design

The moment two things can happen "at the same time," a whole new category of bug
becomes possible — one that doesn't show up in a single-threaded test and can't be
found by reading the code once. This file starts with why that happens at all, then
goes as deep as Google-style coding interviews expect: **"What if multiple threads
call this at once?"** is the single most common follow-up in this repo's interview
loop, and some loops also include a dedicated concurrency question (bounded blocking
queue, thread-safe rate limiter, concurrent web crawler). This file gives you the
vocabulary, the primitives, the classic bugs, and two verified implementations
(Python and Go).

## Foundations — Start Here If You're New to Concurrency

**Where this builds on `01_operating_systems_deep_dive.md`.** Recall from that
file's Foundations: a **thread** is a unit of execution that shares its process's
memory with other threads. That sharing is exactly what makes concurrency both
useful (threads can cooperate on the same data with no copying) and dangerous (they
can corrupt it) — this file is entirely about managing that danger.

**Why `count += 1` isn't safe with two threads.** It looks like one operation, but
the CPU actually does three: read `count`, add 1, write it back. If two threads both
read `count` (say it's `5`) before either writes back, both compute `6` and both
write `6` — one increment vanished. This is a **race condition**: the answer depends
on the exact timing of two threads, which is unpredictable and can pass every test
you happen to run. §1 gives you the precise vocabulary for this and related bugs.

**Why locks exist.** A **lock** (or **mutex**, mutual exclusion) is a tool that lets
only one thread run a given piece of code (a **critical section**) at a time — every
other thread that tries must wait. Wrapping the read-add-write above in a lock fixes
it: no other thread can read `count` mid-update. §2 covers locks and several other
tools for the same underlying problem, each with different trade-offs.

**Concurrency vs. parallelism — worth separating early.** Concurrency is about
*structuring* a program as independently-progressing tasks; parallelism is actually
*running* more than one at the same literal instant, which needs multiple CPU cores.
You can have concurrency without parallelism (many tasks interleaved on one core) —
§1's table makes this precise, because interview answers often conflate the two.

**A first mental model for "what could go wrong."** Any time two threads touch the
same mutable data, and at least one of them writes, ask: could they interleave in an
order that produces a wrong answer? If yes, that's the shared state you need to
protect — §7 turns this question into a repeatable checklist for real interview
problems (a cache, a rate limiter, a counter).

With that mental model, the rest of this file is the precise, interview-depth
vocabulary, primitives, and worked implementations for managing it correctly.

## 1. Vocabulary You Must Use Precisely

| Term | Meaning |
|---|---|
| Concurrency | Structuring a program as independently progressing tasks (may interleave on one core) |
| Parallelism | Executing multiple tasks at the same instant on multiple cores |
| Race condition | Correctness depends on the timing of uncontrolled interleavings |
| Data race | Two threads access the same memory, at least one writes, without synchronization (undefined behavior in C/C++/Go) |
| Critical section | Code that must not run concurrently with itself on the same data |
| Atomic | Observed by others as all-or-nothing |
| Thread-safe | Correct under any interleaving of calls from multiple threads |
| Linearizable | Each operation appears to take effect at a single instant between its start and end |
| Deadlock | Threads each wait for something another holds; nobody progresses |
| Livelock | Threads keep reacting to each other and make no progress (both keep stepping aside) |
| Starvation | A thread never gets the resource because others keep winning |

**The canonical race:** `count += 1` is read, add, write. Two threads both read 5, both write 6: one increment is lost.

## 2. Primitives

| Primitive | Guarantees | Use it for | Gotcha |
|---|---|---|---|
| Mutex / lock | One holder at a time | Protecting shared state | Hold it briefly; never call unknown code (callbacks, I/O) while holding it |
| Reentrant lock (RLock) | Same thread may re-acquire | Recursive code paths | Hides design problems; prefer non-reentrant |
| Read-write lock | Many readers OR one writer | Read-heavy shared maps | Writer starvation; often slower than a mutex for short sections |
| Condition variable | Sleep until notified, releasing the lock atomically | "Wait until queue non-empty" | **Always wait in a `while` loop** (spurious wakeups, stolen wakeups) |
| Semaphore | At most N concurrent holders | Connection pools, concurrency limits | Not ownership-based; any thread can release |
| Atomic variables / CAS | Lock-free single-word updates | Counters, flags, lock-free structures | ABA problem; hard to compose |
| Channel (Go) / queue | Ownership transfer between tasks | Pipelines, worker pools | Unbuffered channels block both sides; forgetting to close leaks goroutines |
| Once | Run initialization exactly once | Lazy singletons | Double-checked locking without it is a classic bug |
| Context / cancellation | Propagate deadlines and cancellation | Every request-scoped goroutine/task | Must be checked; cancellation is cooperative |

## 3. Deadlock

### The four Coffman conditions (all four are required)
1. **Mutual exclusion** — resources can't be shared.
2. **Hold and wait** — a thread holds one resource while waiting for another.
3. **No preemption** — resources can't be forcibly taken.
4. **Circular wait** — a cycle of threads each waiting on the next.

Break any one and deadlock is impossible. The practical ones:
- **Lock ordering** (breaks circular wait): always acquire locks in a global order, e.g. by account ID. A `transfer(a, b)` that locks `a` then `b` deadlocks against `transfer(b, a)`; locking `min(a, b)` first doesn't.
- **Try-lock with timeout and back-off** (breaks hold-and-wait). Beware livelock; add jitter.
- **Hold one lock at a time**; copy data out, release, then work.

Detection in systems: databases build a waits-for graph and abort a victim transaction (a cycle detection problem, see `PyDSA/14_graphs/011_course_schedule`).

## 4. Condition Variables Done Right: a Bounded Blocking Queue (Python)

This is the most common "implement it" concurrency question (LeetCode 1188). Verified: 4 producers and 4 consumers moving 40,000 items through a capacity-8 queue lose and duplicate nothing.

```python
import threading
from collections import deque


class BoundedBlockingQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items = deque()
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)    # both conditions share ONE lock
        self.not_empty = threading.Condition(self.lock)

    def enqueue(self, item) -> None:
        with self.not_full:
            while len(self.items) >= self.capacity:      # while, never if
                self.not_full.wait()
            self.items.append(item)
            self.not_empty.notify()                       # wake one waiting consumer

    def dequeue(self):
        with self.not_empty:
            while not self.items:
                self.not_empty.wait()
            item = self.items.popleft()
            self.not_full.notify()                        # wake one waiting producer
            return item

    def size(self) -> int:
        with self.lock:
            return len(self.items)
```

Why each detail matters:
- **One lock, two conditions:** the size check and the mutation must be under the same lock, or a producer can check "not full", get preempted, and overfill.
- **`while` instead of `if`:** after waking, another thread may have taken the slot first (or the wakeup was spurious). Re-check.
- **`notify` the *other* condition:** producers wake consumers and vice versa. Notifying the same condition can wake the wrong kind of waiter and stall.
- **`notify` vs `notify_all`:** `notify` is enough here because each operation frees exactly one unit of the other resource. With a single shared condition you'd need `notify_all`.

## 5. Go: Worker Pool With Context Cancellation

Verified: 1,000 jobs, 8 workers, results summed correctly; cancelling the context stops workers without leaking goroutines.

```go
package main

import (
	"context"
	"fmt"
	"sync"
)

func worker(ctx context.Context, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case j, ok := <-jobs:
			if !ok {
				return // jobs closed: no more work
			}
			select {
			case results <- j * j:
			case <-ctx.Done():
				return // don't block forever sending if nobody reads
			}
		}
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	jobs := make(chan int)
	results := make(chan int)
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go worker(ctx, jobs, results, &wg)
	}

	go func() {
		defer close(jobs) // the SENDER closes the channel
		for i := 1; i <= 1000; i++ {
			select {
			case jobs <- i:
			case <-ctx.Done():
				return // workers are gone; don't block forever on send
			}
		}
	}()
	go func() {
		wg.Wait()
		close(results) // close results only after every worker has exited
	}()

	sum := 0
	for r := range results {
		sum += r
	}
	fmt.Println(sum) // 333833500
}
```

Go rules this demonstrates: the **sender closes** a channel; close `results` only after `wg.Wait()`; every blocking send/receive in a goroutine has a cancellation path; run tests with **`go test -race`**. Deeper material: GoEngineering topics 12 (worker pool), 26 (advanced concurrency), 31 (deadlocks and sync primitives), 32 (context).

## 6. Python's Concurrency Model in One Table

| Tool | Parallel CPU? | Best for | Notes |
|---|---|---|---|
| `threading` | No on the default (GIL) build | Blocking I/O: network calls, disk | The GIL protects interpreter state, **not your data**: `count += 1` still races |
| `multiprocessing` / `ProcessPoolExecutor` | Yes | CPU-bound work | Pickling overhead; no shared memory by default |
| `asyncio` | No | Many concurrent I/O tasks in one thread | One blocking call stalls every task; use `run_in_executor` for blocking code |
| Free-threaded CPython (3.13+ `python3.13t`, PEP 703) | Yes | CPU-bound threads | Experimental in 3.13, officially supported from 3.14; some C extensions not yet compatible |
| Subinterpreters (PEP 734) | Yes, isolated | Isolation + parallelism | See PyEngineering topic 34 |

Interview line: **"In CPython the GIL makes threads useless for CPU-bound speedups but fine for I/O; for CPU work I'd use processes. The GIL does not make my own read-modify-write operations atomic, so I still need a lock."**

## 7. Making Common Interview Structures Thread-Safe

| Structure | Simple, correct answer | Better under contention |
|---|---|---|
| Counter / hit counter | Mutex around increment | Atomic counters; per-thread counters merged periodically |
| LRU cache (hash map + DLL) | One mutex around `get` and `put` (a `get` mutates recency, so it needs the lock too) | Lock striping by key hash with per-shard LRUs; or approximate LRU (CLOCK) with fewer writes |
| Rate limiter (token bucket) | Mutex around refill + take | Per-key buckets in a sharded map; atomic CAS on (tokens, timestamp) |
| Hash map | Mutex or RW lock | Lock striping (N shards, each with its own lock) — the idea behind Java's `ConcurrentHashMap` and Go's sharded caches; `sync.Map` for append-mostly keys |
| Singleton / lazy init | `sync.Once`, a module-level instance in Python | — |
| Web crawler (LC 1242) | Shared `seen` set under a lock + worker threads + in-flight counter to know when to stop | Per-host queues (see SystemDesign problem 011) |

**What to say when asked "what needs locking?"**
1. Identify shared mutable state (fields, collections, caches).
2. Identify **invariants spanning multiple fields** (map and linked list in an LRU must change together) — those need one lock around the whole update, not a lock per field.
3. Identify check-then-act sequences (`if key not in cache: cache[key] = compute()`) — those are races even if each step is individually thread-safe.
4. Choose granularity: one coarse lock first (simple, correct), then shard if profiling shows contention.
5. Keep slow work (I/O, computing a cached value) outside the lock; use per-key "in-flight" futures (single-flight) to avoid thundering herds.

## 8. Classic Problems to Practice

| Problem | Concept |
|---|---|
| LC 1114 Print in Order | Events / conditions to sequence threads |
| LC 1115 Print FooBar Alternately | Two semaphores handing off turns |
| LC 1116 Print Zero Even Odd | Coordinating three threads |
| LC 1117 Building H2O | Semaphores + barrier |
| LC 1188 Design Bounded Blocking Queue | Conditions (section 4) |
| LC 1226 The Dining Philosophers | Deadlock avoidance via lock ordering |
| LC 1242 Web Crawler Multithreaded | Shared visited set, worker pool, termination |
| Producer-consumer with shutdown | Poison pills or closed channels |

## Interview checklist

- [ ] I can explain the lost-update race on `count += 1` and fix it three ways (lock, atomic, confinement).
- [ ] I can state the four Coffman conditions and prevent deadlock with lock ordering.
- [ ] I can write a bounded blocking queue with conditions and justify `while`, one lock, and which condition to notify.
- [ ] I can write a Go worker pool that closes channels correctly and honors cancellation.
- [ ] I can say what the GIL does and doesn't protect.
- [ ] I can make an LRU cache thread-safe and explain why `get` needs the lock.
