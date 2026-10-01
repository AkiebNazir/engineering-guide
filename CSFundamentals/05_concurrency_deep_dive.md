# Concurrency — Locks, Conditions, Deadlocks, and Thread-Safe Design

The moment two things can happen "at the same time," a whole new category of bug
becomes possible — one that doesn't show up in a single-threaded test and can't be
found by reading the code once. This chapter starts from first principles — why
programs run concurrently at all, what the moving parts are, and how they interact —
then goes as deep as Google-style coding interviews expect: **"What if multiple
threads call this at once?"** is the single most common follow-up in this repo's
interview loop, and some loops also include a dedicated concurrency question (bounded
blocking queue, thread-safe rate limiter, concurrent web crawler). This file gives you
the vocabulary, the primitives, the classic bugs, memory-model precision, the
event-loop alternative, and verified implementations in Python and Go. Corrections of
common myths are marked **Precision note**. A side-by-side breakdown of what Junior
through Staff+ engineers are expected to know closes out the chapter, just before the
interview checklist.

## Foundations — What Is Concurrency, and Why Is It Hard?

### Why Concurrency Exists

Two separate pressures push every serious program towards doing several things at
once:

- **Waiting is wasteful.** A web server spends most of each request waiting — for the
  database, for another service, for the client's slow network. A disk read costs
  around 0.1 ms on NVMe and a cross-region call tens of milliseconds, during which a
  CPU core could run millions of instructions (see [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md)
  §4). If the program can only do one thing at a time, it idles. **Concurrency** lets it
  start other work while one task waits.
- **Cores stopped getting faster; they got more numerous.** Around the mid-2000s,
  single-core clock speeds stopped climbing, and chips added cores instead. A program
  that runs on one core uses a fraction of a modern server. **Parallelism** is how it uses
  the rest.

Both are worth having. Both come with the same price: the moment two tasks can touch
the same data at overlapping times, the order of their steps is no longer decided by
your code but by the scheduler, and some orders produce wrong answers.

### What Concurrency Actually Is

**Concurrency vs. parallelism — separate them early.** Concurrency is about
*structuring* a program as independently progressing tasks; parallelism is actually
*running* more than one at the same literal instant, which needs multiple CPU cores.
You can have concurrency without parallelism (many tasks interleaved on one core, like
Python's `asyncio`), and interview answers often conflate the two.

**Where this builds on [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md).** Recall from that file's
Foundations: a **thread** is a unit of execution that shares its process's memory with
other threads. That sharing is exactly what makes concurrency both useful (threads can
cooperate on the same data with no copying) and dangerous (they can corrupt it) — this
file is about managing that danger.

**Why `count += 1` isn't safe with two threads.** It looks like one operation, but the
CPU does three: read `count`, add 1, write it back. If two threads both read `count`
(say it's `5`) before either writes back, both compute `6` and both write `6` — one
increment vanished. This is a **race condition**: the answer depends on the exact
timing of two threads, which is unpredictable and can pass every test you happen to
run. §1 demonstrates it with runnable code.

**Why locks exist.** A **lock** (or **mutex**, mutual exclusion) lets only one thread
run a given piece of code (a **critical section**) at a time — every other thread that
tries must wait. Wrapping the read-add-write above in a lock fixes it. §2 covers locks
and the other tools for the same underlying problem, each with different trade-offs.

### The Core Components of a Concurrent Program

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Tasks** (threads, goroutines, coroutines, processes) | The independently progressing units of work | §5, §6, §10 |
| **Scheduler** (OS kernel, Go runtime, event loop) | Decides which task runs on which core, and when it's paused | [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §1, §10 |
| **Shared state** | Any memory more than one task can read and write: fields, maps, caches | §1, §7 |
| **Synchronization primitives** | Mutexes, condition variables, semaphores, atomics, channels | §2, §4 |
| **Memory model** | The language's rules for when one task's write becomes visible to another | §9 |
| **Coordination & lifecycle** | Starting, joining, cancelling, and shutting down tasks without leaks | §5, §10 |

### How the Pieces Fit Together

```arch
%% caption: Threads in one process each have their own stack and registers but share one heap; the scheduler maps them onto cores, and only synchronization makes their access to the heap safe.
grid 160x105
group proc "One process" color=blue icon=process
node t1 "Thread 1" at 0,0 in proc icon=thread sub="own stack + registers"
node t2 "Thread 2" at 1,0 in proc icon=thread sub="own stack + registers"
node t3 "Thread 3" at 2,0 in proc icon=thread sub="own stack + registers"
node mu "Mutex / atomics" at 1,1 in proc icon=lock sub="guard shared data"
node heap "Shared heap" at 1,2 in proc icon=memory sub="objects, maps, caches"
group os "Kernel / runtime" color=purple icon=shield
node sch "Scheduler" at 3,1 in os icon=scheduler sub="preempts at any instruction"
node cores "CPU cores" at 3,2 in os icon=cpu sub="run threads in parallel"
t1 -> mu
t2 -> mu
t3 -> mu
mu -> heap
sch -> cores
sch ..> t3 : "switches"
```

Every thread can be paused by the scheduler between *any* two machine instructions and
resumed later, possibly on a different core, while other threads keep changing the
heap. Nothing about the source code's line order protects you; only the primitives in
§2 do, and the memory model (§9) is what makes their guarantees precise.

### Why Races, Deadlocks, and Memory Models All Exist

- **Race conditions** exist because the scheduler interleaves steps in orders you
  didn't plan (§1).
- **Deadlocks** exist because the fix for races — locks — makes threads wait for each
  other, and waiting can form a cycle (§3).
- **Visibility bugs** exist because compilers and CPUs reorder and cache memory
  operations for speed; without synchronization, another thread may see a stale value
  or see writes in a different order than you wrote them (§9).
- **Starvation and overload** exist because unbounded concurrency (a thread or task per
  request, an unbounded queue) turns a slow dependency into memory exhaustion; bounded
  queues and semaphores are the defence (§4, §10).

**A first mental model for "what could go wrong."** Any time two tasks touch the same
mutable data, and at least one of them writes, ask: could they interleave in an order
that produces a wrong answer? If yes, that's shared state you need to protect — §7
turns this question into a repeatable checklist for real interview problems (a cache,
a rate limiter, a counter).

**Try it: be the scheduler.** Step T1 and T2 in any order. Most orders give the right answer; find one that doesn't (both threads LOAD before either STOREs), or press “Show me a lost update”. Then run 10,000 random schedules to see how often it goes wrong: rarely enough to pass tests, often enough to page someone. Switch on the mutex (the steps can no longer interleave) and then the atomic add (one indivisible instruction) and try again.

<div class="lab" data-viz="cs-race"></div>

### Concurrency Models, Side by Side

| Model | How tasks cooperate | Where you meet it | Strength | Weakness |
|---|---|---|---|---|
| **Shared memory + locks** | Tasks read/write the same memory, guarded by locks | Java, C++, Python `threading`, Go `sync` | Fast, flexible, familiar | Races and deadlocks are easy to write and hard to find |
| **Message passing (CSP)** | Tasks own their data and send it over channels | Go channels, Python `queue.Queue` pipelines | Ownership is explicit: "share memory by communicating" | Channels can still deadlock; fan-in/out needs care |
| **Actors** | Each actor has private state and a mailbox, handles one message at a time | Erlang/Elixir, Akka | No shared state; natural distribution and supervision | Request/response patterns get verbose; mailboxes can grow unbounded |
| **Event loop (async/await)** | One thread runs many coroutines that yield at every `await` | Python `asyncio`, Node.js, Rust `tokio` | Huge I/O concurrency with no data races between awaits | One blocking call stalls everything; no CPU parallelism on one loop |
| **Data parallelism** | Split data, run the same function on each part, combine | `multiprocessing.Pool`, MapReduce, SIMD, GPUs | Scales with cores and machines | Only fits divisible work |

**Precision note:** message passing and event loops *reduce* shared state, they don't
make concurrency bugs impossible. Two coroutines can still interleave a
read-modify-write across an `await`, and two goroutines can deadlock on channels. What
changes is where you have to look.

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

**See it happen.** In default CPython the GIL makes a lost `+=` rare enough that a
naive demo usually "passes", which is the point: rare is not never. This version
yields between the read and the write — exactly what a preemption at the wrong moment
does — so the race shows up every time (`python3 race.py`):

```python
"""Make the lost-update race visible, then fix it with a lock."""
import threading
import time

count = 0
lock = threading.Lock()

def unsafe_increment(n):
    global count
    for _ in range(n):
        current = count          # 1. read
        time.sleep(0)            # yield the GIL here, like a preemption at the worst moment
        count = current + 1      # 2. write back (another thread's update may be overwritten)

def safe_increment(n):
    global count
    for _ in range(n):
        with lock:               # read-modify-write is now one critical section
            current = count
            time.sleep(0)
            count = current + 1

for fn in (unsafe_increment, safe_increment):
    count = 0
    threads = [threading.Thread(target=fn, args=(1_000,)) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"{fn.__name__:17} expected 4000, got {count}")
```

Output (verified with Python 3.11; the unsafe number varies run to run):

```text
unsafe_increment  expected 4000, got 1004
safe_increment    expected 4000, got 4000
```

Three standard fixes: a **lock** around the read-modify-write (above), an **atomic**
increment (`atomic.AddInt64` in Go, `AtomicLong` in Java; see §9), or **confinement** —
give each thread its own counter and sum them at the end, so nothing is shared.

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
| Latch / WaitGroup / barrier | Wait until N tasks finish (latch, `WaitGroup`) or all reach a point (barrier) | Fan-out/fan-in, phased computations | `Add` before starting the task, never inside it; a missed `Done` hangs forever |

### What a lock actually costs

A mutex is not a system call. Its fast path is one atomic compare-and-swap in user space;
only when the lock is already held does a thread spin briefly and then sleep in the kernel
(a futex on Linux, [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §3). So an **uncontended** lock is
cheap, and a **contended** one is expensive — not because of the lock's code, but because the
cache line holding the lock (and the data it guards) ping-pongs between cores (`01` §2), and
waiting threads get descheduled and rescheduled. The cost of sharing, measured on 4 cores
with Go (`go run .`; each figure is wall time divided by the total number of operations
across the 4 goroutines):

```go
// Four ways to share a counter, and two ways to guard a read-mostly map,
// under 4 goroutines on 4 cores.
package main

import (
	"fmt"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

const workers, perWorker = 4, 2_000_000

func run(name string, body func(w int)) {
	var wg sync.WaitGroup
	t := time.Now()
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(w int) { defer wg.Done(); body(w) }(w)
	}
	wg.Wait()
	ns := float64(time.Since(t).Nanoseconds()) / (workers * perWorker)
	fmt.Printf("  %-38s %6.1f ns/op\n", name, ns)
}

type padded struct {
	n int64
	_ [56]byte // one counter per 64-byte cache line
}

func main() {
	fmt.Println("GOMAXPROCS =", runtime.GOMAXPROCS(0))
	fmt.Println("counter, every operation a write:")
	var mu sync.Mutex
	var n int64
	run("sync.Mutex", func(int) {
		for i := 0; i < perWorker; i++ {
			mu.Lock()
			n++
			mu.Unlock()
		}
	})
	var a atomic.Int64
	run("atomic.Int64.Add", func(int) {
		for i := 0; i < perWorker; i++ {
			a.Add(1)
		}
	})
	shards := make([]padded, workers)
	run("sharded, one padded slot per worker", func(w int) {
		for i := 0; i < perWorker; i++ {
			atomic.AddInt64(&shards[w].n, 1)
		}
	})
	local := make([]int64, workers)
	run("confined: local variable, sum at end", func(w int) {
		var c int64
		for i := 0; i < perWorker; i++ {
			c++
		}
		local[w] = c
	})

	fmt.Println("map lookups, 100% reads:")
	m := map[int]int{}
	for i := 0; i < 1024; i++ {
		m[i] = i
	}
	var rw sync.RWMutex
	var sink atomic.Int64
	run("sync.Mutex around the map", func(int) {
		s := 0
		for i := 0; i < perWorker; i++ {
			mu.Lock()
			s += m[i&1023]
			mu.Unlock()
		}
		sink.Add(int64(s))
	})
	run("sync.RWMutex (RLock) around the map", func(int) {
		s := 0
		for i := 0; i < perWorker; i++ {
			rw.RLock()
			s += m[i&1023]
			rw.RUnlock()
		}
		sink.Add(int64(s))
	})
	var snap atomic.Pointer[map[int]int]
	snap.Store(&m)
	run("atomic.Pointer to an immutable map", func(int) {
		s := 0
		for i := 0; i < perWorker; i++ {
			s += (*snap.Load())[i&1023]
		}
		sink.Add(int64(s))
	})
	fmt.Println("single goroutine, no contention:")
	t := time.Now()
	for i := 0; i < perWorker; i++ {
		mu.Lock()
		n++
		mu.Unlock()
	}
	fmt.Printf("  %-38s %6.1f ns/op\n", "uncontended sync.Mutex", float64(time.Since(t).Nanoseconds())/perWorker)
	_ = n
}
```

```text
GOMAXPROCS = 4
counter, every operation a write:
  sync.Mutex                               75.9 ns/op
  atomic.Int64.Add                         18.9 ns/op
  sharded, one padded slot per worker       2.8 ns/op
  confined: local variable, sum at end      0.2 ns/op
map lookups, 100% reads:
  sync.Mutex around the map                91.8 ns/op
  sync.RWMutex (RLock) around the map      73.1 ns/op
  atomic.Pointer to an immutable map        3.7 ns/op
single goroutine, no contention:
  uncontended sync.Mutex                   16.3 ns/op
```

What the numbers teach:

- **Contention, not locking, is the cost.** The same `Lock/n++/Unlock` takes 16 ns alone and
  76 ns per operation when four goroutines fight over it.
- **An atomic is cheaper than a lock, but still shares a cache line.** 19 ns: no sleeping, but
  every increment still needs exclusive ownership of the one line holding the counter.
- **Sharding removes the sharing.** One counter per worker, each on its own 64-byte line, is 27×
  faster than the mutex — and confinement (each goroutine counts locally, sums once at the end)
  is faster again by an order of magnitude, because nothing is shared at all. This is the
  design behind striped counters (`LongAdder` in Java), per-CPU statistics in the kernel, and
  sharded locks in concurrent hash maps.
- **A read-write lock helps less than people expect.** With 100% reads, `RWMutex` beat `Mutex`
  by only ~1.3×, because `RLock` itself atomically updates a shared reader count — readers still
  contend on that cache line. `RWMutex` pays off when the critical section is long (a scan, a
  copy) rather than a single map lookup.
- **Immutable snapshots beat both for read-mostly data.** Publishing a map through an
  `atomic.Pointer` and replacing the whole map on update (copy-on-write) makes readers
  lock-free: 4 ns. Writers pay a full copy, so this fits configuration, routing tables and
  feature flags — data read millions of times per update.

**Precision note:** "lock-free is faster" is only true under contention, and not always
then. Lock-free structures use CAS retry loops (`01` §3) that burn CPU when many threads
collide; the real win comes from not sharing (sharding, confinement, immutability), which is
why the answer to "make this faster under concurrency" usually starts with "share less."

### Semaphores: bounding concurrency

A semaphore is a counter of permits: `acquire` takes one (waiting if none are left),
`release` returns one. Unlike a mutex it has no owner, so it expresses "at most *N* at a
time" — database connections, concurrent calls to a fragile dependency, in-flight requests:

```python
"""A semaphore bounds concurrency: 10 threads, at most 3 inside at once."""
import threading, time

limit = threading.BoundedSemaphore(3)       # e.g. 3 connections to a fragile service
inside = peak = 0
count_lock = threading.Lock()

def call_service(i):
    global inside, peak
    with limit:                              # blocks while 3 others are inside
        with count_lock:
            inside += 1
            peak = max(peak, inside)
        time.sleep(0.05)                     # the slow call
        with count_lock:
            inside -= 1

t = time.perf_counter()
threads = [threading.Thread(target=call_service, args=(i,)) for i in range(10)]
for th in threads: th.start()
for th in threads: th.join()
print(f"peak concurrency {peak}, total {time.perf_counter() - t:.2f}s (10 calls x 0.05s / 3 at a time)")
try:
    limit.release()                          # one release too many
except ValueError as e:
    print("BoundedSemaphore caught an extra release:", e)
```

```text
peak concurrency 3, total 0.20s (10 calls x 0.05s / 3 at a time)
BoundedSemaphore caught an extra release: Semaphore released too many times
```

Ten calls of 50 ms with three permits need four waves (3 + 3 + 3 + 1), hence 0.20 s. Prefer
`BoundedSemaphore`: a plain `Semaphore` silently accepts an extra `release()` and quietly
raises the limit, which is exactly the kind of bug that surfaces only under load. In Go, a
buffered channel of capacity *N* is the idiomatic semaphore
(`sem <- struct{}{}` to acquire, `<-sem` to release), and `golang.org/x/sync/semaphore`
adds weighted permits.

### Choosing a primitive

Work down this list and stop at the first that fits — each step shares less, and sharing is
where the bugs and the cost are:

1. **Don't share**: confine data to one goroutine/thread and send messages to it (§5's
   worker pool, the actor model).
2. **Share immutable data**: build it, publish it once (atomic pointer, `sync.Once`), never
   mutate it.
3. **Share with one owner-free counter or flag**: an atomic.
4. **Share a structure**: one mutex around it, held briefly, with no calls to unknown code
   inside.
5. **Contention measured and too high**: shard the structure, or switch the lock type (RW for
   long read sections).
6. **Only then** consider lock-free algorithms, with a race detector and stress tests (§11).

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

**Lock ordering, runnable.** Two concurrent transfers in opposite directions. The naive
version locks `src` then `dst`; a timeout stands in for "hangs forever" so the demo
terminates (`python3 transfer.py`):

```python
"""Lock ordering: transfer(a, b) and transfer(b, a) running concurrently."""
import threading

class Account:
    def __init__(self, acct_id, balance):
        self.id, self.balance, self.lock = acct_id, balance, threading.Lock()

def transfer_naive(src, dst, amount, timeout=1.0):
    with src.lock:
        threading.Event().wait(0.01)                 # widen the window so the deadlock is reliable
        if not dst.lock.acquire(timeout=timeout):    # a real system would just hang here forever
            return "DEADLOCK (gave up after timeout)"
        try:
            src.balance -= amount; dst.balance += amount
            return "ok"
        finally:
            dst.lock.release()

def transfer_ordered(src, dst, amount):
    first, second = sorted((src, dst), key=lambda a: a.id)   # one global order breaks circular wait
    with first.lock, second.lock:
        src.balance -= amount; dst.balance += amount
        return "ok"

for fn in (transfer_naive, transfer_ordered):
    a, b = Account(1, 100), Account(2, 100)
    results = []
    t1 = threading.Thread(target=lambda: results.append(fn(a, b, 10)))
    t2 = threading.Thread(target=lambda: results.append(fn(b, a, 20)))
    t1.start(); t2.start(); t1.join(); t2.join()
    print(f"{fn.__name__:16} {sorted(results)}  total={a.balance + b.balance}")
```

Typical output (verified with Python 3.11):

```text
transfer_naive   ['DEADLOCK (gave up after timeout)', 'ok']  total=200
transfer_ordered ['ok', 'ok']  total=200
```

Each naive thread held one lock and waited for the other's: a circular wait. One gave
up after its timeout, which let the other finish — that's the "try-lock with timeout"
escape, and it only works if the loser retries (with jitter, or it can livelock).
Sorting by account ID removes the cycle, so both succeed and money is conserved.

Detection in systems: databases build a waits-for graph and abort a victim transaction (a cycle detection problem, see `PyDSA/14_graphs/011_course_schedule`).

```arch
%% caption: Deadlock occurs when threads hold one resource while waiting for another, forming a circular wait.
node t1 "Thread 1" at 0,0 icon=thread color=blue
node resA "Lock A" at 2,0 icon=lock color=red
node resB "Lock B" at 0,2 icon=lock color=red
node t2 "Thread 2" at 2,2 icon=thread color=blue

t1 -> resA : "holds"
resA -> t2 : "waits for"
t2 -> resB : "holds"
resB -> t1 : "waits for"
```

<div class="lab" data-viz="flow-deadlock"></div>

## 4. Condition Variables Done Right: a Bounded Blocking Queue (Python)

```arch
%% caption: Producers wait on not_full and consumers on not_empty; both conditions share the queue's one lock, and each side notifies the other.
grid 160x100
node p1 "Producers" at 0,0 icon=worker sub="enqueue()"
node c1 "Consumers" at 2,0 icon=worker sub="dequeue()"
group bq "BoundedBlockingQueue" color=blue icon=queue
node nf "not_full" at 0,1 in bq icon=timer sub="wait while full"
node lk "lock" at 1,1 in bq icon=lock sub="one lock for both"
node ne "not_empty" at 2,1 in bq icon=timer sub="wait while empty"
node dq "deque" at 1,2 in bq icon=queue sub="len ≤ capacity"
p1 -> nf
c1 -> ne
nf -- lk
lk -- ne
lk -> dq
nf ..> ne : "notify consumer"
```

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

**Try it: see the queue you just built.** Make the producer faster than the consumers (for example 4 items/s against two consumers at 1.5/s each). With the bounded buffer, it fills and the producer blocks in `put()`: backpressure. Toggle “Unbounded buffer” and the queue grows without limit instead, along with every item's waiting time. Then add consumers until capacity exceeds the arrival rate and watch the buffer drain.

<div class="lab" data-viz="cs-prodcons"></div>

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

## 9. Memory Models and Visibility: Why "It Works on My Laptop" Isn't Proof

**Why this matters:** most people's model of threads is "the steps interleave in some
order". The real model is weaker: without synchronization, a thread may not see
another thread's write *at all*, or may see writes in a different order than they were
made. Compilers keep values in registers and reorder independent operations; CPUs
buffer stores and execute out of order (ARM more aggressively than x86). A **memory
model** is the language's contract for what a read is allowed to return.

**Happens-before** is the key relation. If operation X *happens-before* Y, Y is
guaranteed to see X's effects. You get happens-before edges only from
synchronization:

```arch
%% caption: A write before an unlock happens-before everything after the next lock of the same mutex; without such an edge, thread B may read a stale value of data.
grid 175x95
group w "Goroutine / thread A" color=blue icon=thread
node a1 "data = 42" at 0,0 in w shape=card color=blue sub="plain write"
node a2 "mu.Unlock()" at 0,1 in w shape=card color=blue sub="release"
group r "Goroutine / thread B" color=green icon=thread
node b1 "mu.Lock()" at 2,1 in r shape=card color=green sub="acquire"
node b2 "read data" at 2,2 in r shape=card color=green sub="guaranteed 42"
a1 -> a2 : "program order"
a2 -> b1 : "synchronizes-with"
b1 -> b2 : "program order"
```

Sources of happens-before edges, by language:

| Mechanism | Go | Java | C++ | Python (CPython) |
|---|---|---|---|---|
| Mutex unlock → next lock | `sync.Mutex` | `synchronized`, `Lock` | `std::mutex` | `threading.Lock` |
| Atomic store → atomic load that sees it | `sync/atomic` (sequentially consistent) | `volatile`, `AtomicX` | `std::atomic` (memory orders) | — (no language-level atomics; the GIL/free-threaded runtime keep single bytecodes safe, not your invariants) |
| Channel send → receive completes | yes | — (`BlockingQueue` put → take) | — | `queue.Queue` put → get |
| Start / join | `go` statement; `WaitGroup.Wait` | `Thread.start`, `join` | `std::thread`, `join` | `Thread.start`, `join` |
| Run-once init | `sync.Once` | static initializers, `final` fields | `std::call_once`, function-local statics | module import lock |

**Precision notes worth saying in an interview:**

- **A data race is undefined behaviour in C and C++**, and in Go a racy program has no
  guarantees beyond limited ones for word-sized values ("a racy program can observe
  any of several values, and may crash" is the safe summary). Java defines racy
  behaviour more tightly but still allows surprising results.
- **`volatile` in Java** gives visibility and ordering for that variable; **it does not
  make `count++` atomic**. In C/C++, `volatile` is for memory-mapped I/O and gives no
  thread-safety at all — use `std::atomic`.
- **Double-checked locking** (`if instance == nil { lock; if instance == nil { create } }`)
  is broken without an atomic or `volatile` publication, because another thread can see
  the pointer before the object's fields. Use `sync.Once`, `std::call_once`, or a
  holder class.
- **The GIL is not a memory model for your code.** It makes each bytecode atomic in
  default CPython, which is why lists and dicts don't corrupt, but multi-step operations
  still interleave (§1's demo). Free-threaded CPython (PEP 703) uses per-object locks so
  built-in containers stay internally consistent, and your own invariants still need a
  lock.

### Let the tool find races: Go's race detector

Races rarely show up in tests; tools that instrument memory accesses find them. This
program has one racy counter and two correct ones. Run it with `go run -race .`:

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var wg sync.WaitGroup

	// 1. Data race: plain int, no synchronization. `go run -race .` reports it.
	racy := 0
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				racy++ // read-modify-write from 4 goroutines: undefined under the Go memory model
			}
		}()
	}
	wg.Wait()

	// 2. Mutex: correct, and the unlock happens-before the next lock.
	var mu sync.Mutex
	locked := 0
	// 3. Atomic: correct for a single word, no lock.
	var atomicCount atomic.Int64
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				mu.Lock()
				locked++
				mu.Unlock()
				atomicCount.Add(1)
			}
		}()
	}
	wg.Wait()
	fmt.Println("racy:", racy, "(any value; a data race)")
	fmt.Println("mutex:", locked, "atomic:", atomicCount.Load())
}
```

Verified with Go 1.24: the detector prints `WARNING: DATA RACE` with the two
conflicting stack traces (read at the `racy++` line in one goroutine, previous write in
another), then the program's output, then `Found 2 data race(s)` and exits with status
66. Note that `racy` may well print 4000 on a given run — **a correct-looking result is
not evidence of correctness**, which is exactly why the tool exists. Run CI tests with
`-race`; C/C++/Rust `unsafe` code has ThreadSanitizer (`-fsanitize=thread`), and Java
has tools such as jcstress for memory-model tests.

## 10. Event Loops and Async/Await: Concurrency Without Threads

**Why this matters:** for I/O-heavy services, "a thread per request" wastes memory and
context switches ([Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §1, §4). An **event loop** runs
many tasks on one thread: each task runs until it hits an `await` on I/O, then yields,
and the loop resumes whichever task's I/O is ready (via `epoll`/`kqueue`).

```arch
%% caption: One thread runs the loop; a coroutine runs until it awaits I/O, the loop parks it on the OS readiness API, and resumes it when its socket is ready.
grid 165x100
node rq "Ready queue" at 0,1 icon=queue sub="coroutines ready to run"
node loop "Event loop" at 1,0 icon=sync sub="one thread"
node co "Running coroutine" at 2,0 icon=code sub="until next await"
node wait "Waiting on I/O" at 2,1 icon=timer sub="parked, costs ~KB"
node ep "epoll / kqueue" at 1,1 icon=cpu sub="which fds are ready?"
node pool "Thread pool" at 0,0 icon=thread sub="run_in_executor: blocking calls"
rq -> loop : "pick next"
loop -> co : "resume"
co -> wait : "await socket"
wait -> ep : "register fd"
ep -> rq : "fd ready"
loop ..> pool : "offload"
```

The rules that follow from "one thread":

- **Never block the loop.** A `time.sleep`, a synchronous HTTP client, or a CPU-heavy
  loop stops *every* task. Use async libraries, or offload with `run_in_executor` /
  `asyncio.to_thread`.
- **No data races between awaits, but races across them.** Code between two `await`s
  runs without interruption on that loop, so `self.count += 1` is safe; `value = await
  get(); await set(value + 1)` is a race again, because other tasks run at each
  `await`. `asyncio.Lock` exists for that.
- **Bound concurrency explicitly.** `gather` over 100,000 coroutines opens 100,000
  connections at once. Use a `Semaphore` or a fixed pool of worker tasks.
- **Put timeouts on everything, and handle cancellation.** A cancelled task gets
  `CancelledError` at its current `await`; clean up in `finally`, and don't swallow it.
- **Structured concurrency:** start child tasks inside a scope that waits for all of
  them and cancels the rest if one fails — `asyncio.TaskGroup` (Python 3.11+), Go's
  `errgroup` (in `golang.org/x/sync`), Java's `StructuredTaskScope` (preview). Tasks then
  can't outlive the request that started them.

**A runnable example** — 100 "requests" on one thread, at most 10 in flight, each with
a timeout (`python3 fetch_all.py`):

```python
"""asyncio: 100 concurrent 'requests' on one thread, at most 10 in flight, each with a timeout."""
import asyncio
import random
import time

async def fetch(i, sem):
    async with sem:                                   # bound concurrency (a bulkhead)
        delay = 2.0 if i % 25 == 0 else random.uniform(0.05, 0.15)   # a few are very slow
        try:
            # the timeout covers the call itself, not the time spent queueing for the semaphore
            await asyncio.wait_for(asyncio.sleep(delay), timeout=0.5)  # stands in for a socket read
            return i
        except asyncio.TimeoutError:
            return None                               # cancelled, not awaited forever

async def main():
    sem = asyncio.Semaphore(10)
    start = time.perf_counter()
    results = await asyncio.gather(*(fetch(i, sem) for i in range(100)))
    print(f"{results.count(None)} timed out, {100 - results.count(None)} ok, "
          f"{time.perf_counter() - start:.1f}s on one thread")

asyncio.run(main())
```

Output (verified with Python 3.11; timing varies slightly): `4 timed out, 96 ok, 1.3s
on one thread`. Sequentially the same work would take over 10 seconds; the four slow
calls were cut off at 0.5 s instead of holding a slot for 2 s. An early version of this
example put the timeout *around* the semaphore wait, and most requests "timed out"
while merely queueing — a real production bug worth mentioning when you discuss where
timeouts belong.

| Choose | When |
|---|---|
| Event loop (`asyncio`, Node, `tokio`) | Many concurrent I/O-bound connections; libraries are async all the way down |
| Threads / thread pool | Blocking libraries, moderate concurrency, or CPU work in a language without a GIL |
| Goroutines / virtual threads (Java 21+) | You want blocking-style code with event-loop scalability: the runtime multiplexes them onto few OS threads |
| Processes | CPU-bound Python on the default GIL build; isolation for crash-prone work |

## 11. Testing and Debugging Concurrent Code

Concurrency bugs are timing-dependent, so ordinary tests mostly pass. What works:

- **Race detectors** instrument memory accesses: Go `-race`, ThreadSanitizer for
  C/C++/Rust, and in Java static analyzers plus stress tools. Run them in CI.
- **Stress and repetition**: run the concurrent test thousands of times with many
  threads; inject `sleep(0)`/`yield` or random delays at suspicious points (§1's demo
  does exactly this to make a race visible).
- **Deterministic testing**: control the scheduler so every interleaving is explored
  or reproducible — model checkers (TLA+ for designs, `loom` for Rust), simulation
  testing with a seeded scheduler (the FoundationDB approach), or fake clocks instead of
  real `sleep`s.
- **Invariant checks**: assert what must always hold (no item lost or duplicated in a
  queue; balances sum to a constant) rather than a specific output order — §4's queue
  was verified this way.
- **Diagnosing a hang in production**: take a thread/goroutine dump and look for a
  cycle of "waiting for lock held by …" — `jstack` for the JVM, `SIGQUIT` or
  `/debug/pprof/goroutine?debug=2` for Go, `py-spy dump` for Python. Databases log the
  waits-for cycle when they abort a deadlock victim.
- **Design so there is less to test**: confine state to one owner (a single goroutine
  or actor), prefer immutable data, and keep critical sections small and free of calls
  into unknown code.

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side. The mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it as a syllabus (read down a column) or as a
self-assessment (find the cell that matches where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Concurrency vs. parallelism, models** (Foundations) | Knows threads run "at the same time" and share memory | Separates concurrency from parallelism; knows threads vs. processes vs. async | Chooses between shared memory, channels, actors and event loops for a problem, with reasons | Sets the concurrency model for a platform or language runtime and its failure semantics |
| **Races & primitives** (§1–§2) | Knows a lock prevents two threads changing data at once | Uses mutexes, conditions and semaphores correctly; spots check-then-act | Picks primitives by trade-off (RW lock vs. mutex, CAS vs. lock) and explains each gotcha | Designs lock-free or sharded structures where profiling proves contention matters |
| **Deadlock** (§3) | Knows deadlock means "everyone waits forever" | States the four Coffman conditions | Prevents deadlock by lock ordering, explains livelock and DB victim selection, and diagnoses a hang from a thread dump | Establishes lock-hierarchy conventions and tooling across a large codebase |
| **Blocking queue, worker pools** (§4–§5) | Uses a thread-safe queue from the standard library | Writes a producer-consumer with a library queue | Writes a bounded blocking queue and a cancellable worker pool cold, justifying every line | Designs backpressure and shutdown semantics for a whole pipeline |
| **Language runtimes** (§6, §10) | Knows Python has a GIL | Knows threads help I/O but not CPU in CPython; uses `asyncio` basics | Explains the GIL precisely, free-threaded CPython, event-loop rules, structured concurrency | Picks runtimes (async vs. virtual threads vs. goroutines) for a fleet with migration costs |
| **Memory models** (§9) | Unaware reads can be stale | Knows `volatile`/atomics exist | Explains happens-before, why data races are undefined, and why double-checked locking breaks | Reviews low-level concurrent code for memory-order correctness (acquire/release) |
| **Testing concurrency** (§11) | Runs the tests | Adds stress tests | Runs race detectors in CI and checks invariants rather than outputs | Invests in deterministic simulation or model checking for critical systems |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column, which the numbered sections (1–11) deliver in
full. The Foundations section alone takes you to roughly the "Mid-Level" column. The
"Staff+" column is judgment that mostly comes from operating real systems at scale;
this file gives you the vocabulary to have that conversation, not a substitute for
having had it.

## Interview checklist

- [ ] I can separate concurrency from parallelism and compare shared-memory, message-passing, actor and event-loop models.
- [ ] I can explain the lost-update race on `count += 1` and fix it three ways (lock, atomic, confinement).
- [ ] I can state the four Coffman conditions and prevent deadlock with lock ordering.
- [ ] I can write a bounded blocking queue with conditions and justify `while`, one lock, and which condition to notify.
- [ ] I can write a Go worker pool that closes channels correctly and honors cancellation.
- [ ] I can say what the GIL does and doesn't protect, and what free-threaded CPython changes.
- [ ] I can make an LRU cache thread-safe and explain why `get` needs the lock.
- [ ] I can explain happens-before, why a data race is undefined behaviour, and why double-checked locking needs an atomic publish.
- [ ] I can list the event-loop rules (never block, races across `await`, bound concurrency, timeouts, structured concurrency).
- [ ] I can say how I'd find a race (race detector, stress, invariants) and diagnose a deadlock (thread dump).

Related: [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §1–§4 (scheduler, MESI, CAS, I/O models), [Designing Concurrent Code](../SoftwareDesign/07_designing_concurrent_code.md), [Transactions, Isolation, Locking, and Sagas](../SystemDesign/building_blocks/11_transactions_and_concurrency.md); GoEngineering topics 12, 26, 31, 32; PyEngineering topic 34.
