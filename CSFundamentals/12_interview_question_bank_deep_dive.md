# Interview Question Bank — Every Topic, Every Level

The other chapters teach the material. This one tests it the way an interviewer
does: a question, a short answer expected first, then a push for the mechanism
underneath, then a follow-up that checks whether you really understand it or have
only memorised it. Every question is tagged with the level it usually shows up at,
and every answer is hidden until you have tried it yourself.

## How to Use This Bank

**Answer out loud before you open anything.** Give yourself about 30 seconds for the
short answer and two minutes for the full one. Then open the answer and compare the
*content*, not the wording. Anything you missed goes on a list you retest in 1, 3 and
10 days.

Each answer has the same four layers, because that is how a real interview unfolds:

| Layer | What it is | Why it matters |
|---|---|---|
| **Say this first** | The 30-second answer: the definition and the one idea that matters | Interviewers decide early whether you know the topic at all |
| **Then explain** | The mechanism, the trade-off, and where it goes wrong | This is where levels separate: juniors define, seniors explain *why* and *when not* |
| **Next follow-up** | The question a strong interviewer asks next, with its answer | Follow-ups test understanding; a memorised answer runs out here |
| **Go deeper** | The chapter section or live lab that covers it | Where to go when the answer surprised you |

**What each level is expected to show.** The same question is asked at every level;
what changes is how far the answer has to go.

| Tag | Typical title | A passing answer shows |
|---|---|---|
| **L3 · Junior** | New grad, Software Engineer I | Correct definitions, one concrete example, knows when to reach for it |
| **L4 · Mid** | Software Engineer II | The mechanism inside, the main trade-off, and the common bug |
| **L5 · Senior** | Senior Software Engineer | Failure modes, numbers, what you would monitor, alternatives compared, production scars |
| **L6+ · Staff** | Staff / Principal | Consequences across systems and teams, when the textbook answer is wrong, migration and cost |

A useful habit at every level: **end each answer with a trade-off sentence.** "I'd
use X; we give up A, which is fine here because B." That one sentence is the most
reliable seniority signal in both coding and design rounds.

## 1. Complexity and Data Structures

### Q1.1 · L3 — What does "O(n)" promise, and what doesn't it?

<details>
<summary>Open the answer</summary>

**Say this first.** It is an upper bound on how the work grows: for large enough `n`,
the algorithm does at most `c·n` steps for some constant `c`. It says nothing about
the constant, about small inputs, or about the actual running time.

**Then explain.**
- Big-O drops constants and lower-order terms because, at scale, the *shape* of the
  growth dominates: no constant factor rescues `n²` against `n log n` at a million items.
- In interviews "O(n)" usually means a tight bound (Θ). Say which case you mean —
  worst, average, expected or amortized — and what `n` is (length of the input? the
  number of distinct keys? both `n` and `m`?).
- Constants still matter in practice: a C-implemented `O(n log n)` sort often beats a
  pure-Python `O(n)` loop at realistic sizes. Say "O(n), but with heavy work per element"
  when it's true.

**Next follow-up: "So is a hash-map lookup O(1)?"** Expected O(1), given a good hash
and a bounded load factor. The worst case is O(n) when keys collide; Java turns long
buckets into trees to cap it at O(log n), and Python and Go randomise string hashing
so attackers cannot craft colliding keys (hash flooding).

**Go deeper.** `07` §1 and §3, and the growth-rate lab at the top of `07`.

</details>

### Q1.2 · L3 — Why is appending to a dynamic array O(1) if it sometimes copies everything?

<details>
<summary>Open the answer</summary>

**Say this first.** It is O(1) *amortized*: capacity grows geometrically, so the
copies over n appends add up to less than 2n, which is under three steps per append.

**Then explain.**
- With doubling, copies happen at lengths 1, 2, 4, 8, … and sum to less than 2n. The
  total for n appends is under 3n, so the average per append is constant.
- Amortized is a guarantee over *every* sequence of operations, unlike average-case,
  which depends on the input distribution.
- A single append can still cost O(n). For latency-sensitive code, preallocate:
  `make([]T, 0, n)` in Go, `new ArrayList<>(n)` in Java.
- Growing by a *constant* (say +4) makes append O(n) amortized and building a list
  O(n²).

**Next follow-up: "Why not grow by 10× and copy even less?"** Memory: right after a
resize up to 90% of the block is empty. Real runtimes pick modest factors — Java
1.5×, CPython about 1.125× plus a constant, Go 2× for small slices easing towards
1.25× — trading a few more copies for less waste.

**Go deeper.** `07` §6 and `06` §2, with the append lab in both.

</details>

### Q1.3 · L4 — How does a hash map work inside, and what happens as it fills up?

<details>
<summary>Open the answer</summary>

**Say this first.** The key's hash picks a slot. Collisions are resolved by chaining
(a list per slot) or open addressing (probe other slots). When the load factor passes
a threshold, the table doubles and every key is re-inserted, which keeps operations
O(1) expected.

**Then explain.**
- Slot = `hash(key) mod capacity`, often a bit-mask with power-of-two capacities.
- Chaining (Java `HashMap`: resize at 0.75, a bucket of 8+ entries becomes a red-black
  tree) versus open addressing (CPython `dict`: perturbed probing, resize at ⅔ full;
  Go 1.24+ and Rust use Swiss tables that probe groups of slots with SIMD).
- Open addressing needs **tombstones** on delete, or lookups for keys placed past the
  deleted slot would stop early and miss.
- Keys must not change while stored: mutating a key changes its hash, and the entry
  becomes unreachable.
- Iteration order: Python preserves insertion order (a language guarantee since
  3.7); Go deliberately randomises map iteration.

**Next follow-up: "Why must equal objects have equal hashes?"** Lookup finds the
bucket by hash and only then compares with equality. Two equal keys with different
hashes land in different buckets, so the second lookup misses. Override `__eq__` and
`__hash__` (or `equals` and `hashCode`) together.

**Go deeper.** `06` §1, §10 and §11, and the hash-table lab in `06`.

</details>

### Q1.4 · L4 — When would you choose a heap over a sorted array or a balanced BST?

<details>
<summary>Open the answer</summary>

**Say this first.** When all you need is the minimum (or maximum), again and again. A
heap gives O(log n) push and pop, O(1) peek, O(n) build, and it is a plain array —
simple and cache-friendly.

**Then explain.**
- Sorted array: O(1) min and O(log n) search, but O(n) insert.
- Balanced BST (`TreeMap`, `std::map`): O(log n) for everything, plus ordered
  iteration, floor/ceiling, range queries and arbitrary delete.
- Heap: no search, no ordered iteration, no efficient arbitrary delete — use lazy
  deletion or an indexed heap when you need decrease-key (Dijkstra).
- Top-k of a stream: a size-k **min**-heap, O(n log k) time and O(k) space.

**Next follow-up: "Find the running median of a stream."** Two heaps: a max-heap for
the lower half and a min-heap for the upper half, rebalanced so their sizes differ by
at most one. Insert is O(log n) and the median is O(1). If values are small integers,
counting buckets are simpler; at huge scale, an approximate sketch (t-digest) is fine.

**Go deeper.** `06` §5 and §12, and the heap lab in `06`.

</details>

### Q1.5 · L5 — Two algorithms are both O(n log n). Why might one be 10× faster?

<details>
<summary>Open the answer</summary>

**Say this first.** Once Big-O ties, constants decide: cache misses, branch
mispredictions, allocation, and language overhead.

**Then explain.**
- Memory access dominates. An L1 hit is about 1 ns; a RAM access about 100 ns.
  Scanning an array streams through cache lines; walking a tree or linked list chases
  pointers, and each hop can be a miss.
- Quicksort sorts in place with good locality; merge sort needs O(n) extra memory but
  is stable and predictable. Timsort exploits existing runs (O(n) on sorted input).
- Per-element allocation (boxed integers in Java, every Python int is an object) costs
  memory and cache.
- In Python, built-ins run in C; each iteration of a Python-level loop costs tens of
  nanoseconds of interpreter overhead.

**Next follow-up: "How would you prove which is faster?"** Benchmark with realistic
sizes and data distributions, warm up, repeat, and report percentiles rather than one
number. Then profile (`perf`, `pprof`, `py-spy`) to see *where* the time goes;
`perf stat` shows cache misses directly.

**Go deeper.** `06` §13 and `07` §10, and the cache-line and latency labs in `06` and `01`.

</details>

### Q1.6 · L5 — Why do databases index with B+ trees rather than binary trees or hash tables?

<details>
<summary>Open the answer</summary>

**Say this first.** Storage is read in pages. A B+ tree packs hundreds of keys into
each page, so even a billion-row table is 3–4 levels deep, and its linked leaves make
range scans sequential. A hash index cannot answer range or ordering queries at all.

**Then explain.**
- A binary tree over a billion keys is about 30 levels: 30 random page reads.
- With a fan-out of a few hundred, the tree is 4 levels, and the top levels stay in the
  buffer pool, so a lookup usually costs one or two real reads.
- Splits propagate upwards and the tree grows at the root, so it stays balanced
  without rotations.
- LSM trees are the write-optimised alternative: sequential writes, but reads may
  check several files and compaction rewrites data in the background.

**Next follow-up: "Why is a random UUID primary key bad in MySQL InnoDB?"** InnoDB
stores rows in primary-key order (a clustered index). Random keys insert all over the
tree: constant page splits, half-empty pages, poor cache locality and more write
amplification. Use a sequential key, or a time-ordered UUID (UUIDv7, ULID).

**Go deeper.** `03` §1 and `06` §6, and the B+ tree lab in both.

</details>

### Q1.7 · L6+ — You have 10 TB of log lines. Find the 100 most frequent URLs.

<details>
<summary>Open the answer</summary>

**Say this first.** Don't sort 10 TB. Partition by `hash(url)` so each URL lands on
exactly one worker, count locally, keep a top-100 per worker with a min-heap, and merge
the candidates. If an approximate answer is acceptable, one streaming pass with a
count-min sketch plus a heap (or Misra–Gries) needs tiny memory.

**Then explain.**
- First estimate: how many distinct URLs? (HyperLogLog gives this cheaply.) That
  decides whether one machine's memory is enough.
- Exact, distributed: a MapReduce or Spark job keyed by URL. Correct because each URL's
  *entire* count lives in one partition, so a local top-k contains every possible
  global winner from that partition.
- The classic bug: splitting the data arbitrarily, taking the top-k of each piece, and
  merging. A URL that is moderately frequent everywhere never makes any local list.
- Cost: reading 10 TB is bandwidth-bound — at about 1 GB/s per worker, 100 workers
  take under two minutes. Pre-aggregate (combiners) before the shuffle to handle hot
  URLs.

**Next follow-up: "Now keep it live: top 100 over the last 5 minutes, updated every 10
seconds."** A streaming job with hopping windows: keep a small sketch per 10-second
bucket, merge the last 30 buckets for each answer, and pre-aggregate hot keys in two
stages so one popular URL does not overload one worker.

**Go deeper.** `10` §2, §13 and §15, SD problem 028, and the sketch lab in `10`.

</details>

## 2. Operating Systems

### Q2.1 · L3 — What is the difference between a process and a thread?

<details>
<summary>Open the answer</summary>

**Say this first.** A process is a running program with its own address space, file
descriptors and resources. Threads are separate execution paths inside one process:
each has its own stack and registers, but they share the heap and everything else.

**Then explain.**
- Processes are isolated: one crashing or misbehaving cannot corrupt another's memory,
  but sharing data needs IPC (pipes, sockets, shared memory).
- Threads share memory for free, which is fast and also why they need synchronisation.
- On Linux both are "tasks" created by `clone()`; what differs is how much they share.
- Goroutines, green threads and async tasks are scheduled in user space on top of a few
  OS threads.

**Next follow-up: "Why does a browser run each tab in its own process?"** Isolation and
security: a crash or an exploited renderer in one tab cannot read another tab's memory,
and the OS sandbox can restrict what that process may do. The cost is memory.

**Go deeper.** `01` Foundations and §6.

</details>

### Q2.2 · L4 — What happens in a context switch, and why is it expensive?

<details>
<summary>Open the answer</summary>

**Say this first.** The kernel saves the running thread's registers, picks the next
thread, and restores that one's state — switching page tables if it belongs to another
process. The direct cost is a few microseconds; the bigger cost is the cold caches and
TLB the new thread starts with.

**Then explain.**
- Triggers: the timer interrupt ending a time slice, a blocking system call, or a
  voluntary yield.
- Switching address spaces changes the page-table root, which invalidates TLB entries
  (tagged TLBs, PCID on x86, reduce this).
- This is why 10,000 threads doing blocking I/O scale badly: stack memory for each, and
  the scheduler constantly switching between them.
- Event loops and goroutines avoid most of it: a goroutine switch happens in user space
  and costs on the order of a few hundred nanoseconds.

**Next follow-up: "How does Go run a million goroutines on eight threads?"** M:N
scheduling. The runtime multiplexes goroutines onto OS threads (up to `GOMAXPROCS`
running at once), switches between them in user space on channel operations and
blocking calls, and parks network I/O on its netpoller (epoll/kqueue). Stacks start at
a few KB and grow on demand. A goroutine stuck in a blocking system call has its
thread handed off so the others keep running.

**Go deeper.** `01` §1 and §4, and the scheduling lab in `01`.

</details>

### Q2.3 · L4 — What is virtual memory, and what is a page fault?

<details>
<summary>Open the answer</summary>

**Say this first.** Every process sees its own private address space. The MMU
translates virtual pages to physical frames through page tables, cached in the TLB. A
page fault is the trap when a page isn't currently mapped: the kernel either fixes it
(allocate a frame, read it from disk) or kills the process (segmentation fault).

**Then explain.**
- It gives isolation, lets files be mapped into memory (`mmap`), makes `fork()` cheap
  via copy-on-write, and allows overcommit and swap.
- A **minor** fault just maps a page that is already in RAM (microseconds). A **major**
  fault reads from disk (roughly 100 µs on an SSD, milliseconds on a spinning disk).
- TLB misses force a page-table walk; huge pages (2 MB, 1 GB) cut TLB misses for large
  heaps and databases.

**Next follow-up: "How can a process allocate more memory than the machine has?"**
Overcommit. `malloc` reserves virtual address space; physical frames are assigned only
when a page is first touched. If processes touch more than RAM plus swap, Linux's OOM
killer picks a process to kill.

**Go deeper.** `01` §5 and the page-fault flow there.

</details>

### Q2.4 · L5 — select vs epoll vs io_uring: how does one server thread handle 10,000 connections?

<details>
<summary>Open the answer</summary>

**Say this first.** Put the sockets in non-blocking mode and ask the kernel which ones
are ready. `select`/`poll` rescan every descriptor on every call (O(n)); `epoll`
registers interest once and returns only the ready ones; `io_uring` goes further and
submits and completes the I/O itself through shared ring buffers, with very few system
calls.

**Then explain.**
- Thread-per-connection wastes memory on stacks and time on context switches.
- Readiness model (`epoll`, `kqueue`): "tell me when I can read". Completion model
  (`io_uring`, Windows IOCP): "do this read and tell me when it's done" — which also
  works for regular files, where readiness is meaningless (a file is always "ready").
- Level-triggered vs edge-triggered notification: edge-triggered requires draining the
  socket until `EAGAIN`.
- Node's libuv, Go's netpoller and Python's asyncio are all built on these calls.

**Next follow-up: "What goes wrong if one handler does heavy CPU work?"** It blocks the
loop, so every other connection on that thread stalls. Move CPU-heavy work to a worker
pool (or a process pool, in Python) and monitor event-loop lag.

**Go deeper.** `01` §4 and `05` §10.

</details>

### Q2.5 · L5 — What is false sharing, and how do you find and fix it?

<details>
<summary>Open the answer</summary>

**Say this first.** Two cores write *different* variables that happen to sit on the same
64-byte cache line. The coherence protocol moves the whole line back and forth between
the cores on every write, so independent work runs as if it were serialised. Fix it by
padding or aligning hot per-thread data onto separate cache lines.

**Then explain.**
- Symptom: adding threads makes the program *slower*, with a high cache-miss rate.
- Finding it: `perf c2c` on Linux reports contended cache lines and the code touching
  them.
- Fixes: padding (`alignas(64)` in C++, `@Contended` in Java, a `[56]byte` pad in a Go
  struct), or per-thread data merged at the end.

**Next follow-up: "One atomic counter incremented by 64 threads is slow too — is that
false sharing?"** No, that is *true* sharing: every increment needs exclusive ownership
of the same line, so increments queue up. Shard the counter per core or thread and sum
on read (Java's `LongAdder`, the Linux kernel's per-CPU counters).

**Go deeper.** `01` §2 and the false-sharing lab there.

</details>

### Q2.6 · L6+ — p99 latency spikes every few minutes, yet CPU is only 40%. Investigate from the OS up.

<details>
<summary>Open the answer</summary>

**Say this first.** Averages hide spikes. Line the spikes up against the things that
pause a process: CPU throttling by the container's quota, garbage-collection pauses,
page reclaim or swap, disk flushes, noisy neighbours, periodic jobs, and retries. Look
at per-second data and traces, not one-minute averages.

**Then explain.**
- **CPU throttling:** a cgroup quota is enforced per 100 ms period. A multithreaded
  burst can spend the whole quota in 20 ms and then be frozen for 80 ms — tail latency
  with a healthy-looking average. Check `nr_throttled` in `cpu.stat`.
- **GC:** JVM and Go GC logs; allocation spikes.
- **Memory:** major faults, swap-ins, transparent huge page compaction.
- **Disk:** dirty-page writeback or `fsync` storms (`biolatency`).
- **Neighbours:** CPU steal time on VMs.
- **Periodic work:** cron jobs, compaction, log rotation, cache expiry herds.
- **Network:** TCP retransmits (`ss -ti`, `nstat`).
- Tools: eBPF (`runqlat` for scheduler delay, `offcputime`), flame graphs, tracing to
  find which span grows.

**Next follow-up: "Why would removing the CPU limit help if average use is 40%?"**
Because the limit is applied per 100 ms period, not per minute. Bursty, parallel
request handling hits the quota early in a period and is throttled for the rest of it.

**Go deeper.** `01` §1, and SD building blocks 15 and 28.

</details>

## 3. Concurrency

### Q3.1 · L3 — Concurrency vs parallelism?

<details>
<summary>Open the answer</summary>

**Say this first.** Concurrency is structuring a program as several tasks whose
progress overlaps in time. Parallelism is actually executing at the same instant on
several cores. Concurrency is about *dealing with* many things; parallelism is about
*doing* many things at once.

**Then explain.**
- One core can be concurrent (interleaving) but never parallel.
- CPython's GIL lets only one thread execute Python bytecode at a time: threads help
  with I/O, not with pure-Python CPU work (use processes, native extensions that
  release the GIL, or the free-threaded 3.13t build).
- Go runs goroutines concurrently and in parallel up to `GOMAXPROCS`.

**Next follow-up: "When do threads speed up a Python program?"** When the threads spend
time waiting — on the network, disk, or a subprocess — because blocking I/O releases the
GIL; and in C extensions such as NumPy that release it during heavy work. Not for
pure-Python loops.

**Go deeper.** `05` Foundations and §6.

</details>

### Q3.2 · L3 — What is a race condition? Give an example and a fix.

<details>
<summary>Open the answer</summary>

**Say this first.** The result depends on the timing of threads touching shared state
when at least one of them writes. Two threads doing `counter += 1` can lose updates,
because it is really three steps: load, add, store.

**Then explain.**
- A **data race** is unsynchronised concurrent access to memory (undefined behaviour in
  C/C++, a bug the Go race detector reports). A **race condition** is the broader logic
  bug — check-then-act, like `if key not in cache: cache[key] = compute()`.
- Fixes: a mutex around the critical section, atomics for single-word updates,
  confinement (one goroutine owns the data, others send it messages), immutability, or
  database constraints and transactions for races between processes.
- Find them with `go run -race` and ThreadSanitizer.

**Next follow-up: "Is `if not os.path.exists(p): open(p, 'w')` safe?"** No — it's a
time-of-check-to-time-of-use race: another process can create the file between the two
calls. Make it one atomic operation: `open(p, 'x')` (`O_CREAT | O_EXCL`).

**Go deeper.** `05` §1 and §9, and the race lab in `05`.

</details>

### Q3.3 · L4 — What are the conditions for deadlock, and how do you prevent it?

<details>
<summary>Open the answer</summary>

**Say this first.** Four conditions must all hold: mutual exclusion, hold-and-wait, no
preemption, and circular wait. Break any one; in practice, break circular wait by
always acquiring locks in one global order.

**Then explain.**
- Other preventions: try-lock with a timeout and back off, acquire everything at once,
  keep critical sections short, and never call unknown code (callbacks, I/O) while
  holding a lock.
- Detection instead of prevention: databases build a wait-for graph and abort one
  transaction as the victim.
- Cousins: livelock (both sides keep backing off in step) and starvation.
- Distributed locks add leases with timeouts, and fencing tokens so a paused old holder
  cannot write.

**Next follow-up: "Transfer money between accounts A and B concurrently — how do you
lock?"** Lock both accounts in a canonical order (lower id first), so two opposite
transfers can't each hold one lock and wait for the other. In SQL: one transaction,
`SELECT … FOR UPDATE` ordered by id; if the database still detects a deadlock, it
aborts one and the application retries.

**Go deeper.** `05` §3 and the deadlock flow there.

</details>

### Q3.4 · L4 — Mutex vs semaphore vs condition variable?

<details>
<summary>Open the answer</summary>

**Say this first.** A mutex lets one owner at a time into a critical section. A
semaphore is a counter that admits up to N holders — a limit. A condition variable lets
a thread sleep until some predicate becomes true, releasing the mutex while it waits.

**Then explain.**
- The condition-variable pattern is always
  `with lock: while not predicate: cond.wait()` — `while`, never `if`.
- `notify` wakes one waiter; `notify_all` wakes all of them (safer when waiters wait for
  different predicates).
- Semaphores bound concurrency: a connection pool, "at most 10 downloads at once".
- A bounded blocking queue is one mutex and two conditions: `not_full` and `not_empty`.
- In Go, prefer channels; a buffered channel works as a semaphore.

**Next follow-up: "Why `while` rather than `if` around `wait()`?"** Spurious wakeups are
allowed, and between being notified and re-acquiring the lock, another thread may have
consumed the item. Re-check the predicate every time you wake.

**Go deeper.** `05` §2 and §4, and the producer–consumer lab in `05`.

</details>

### Q3.5 · L5 — Design a thread-safe LRU cache. What do you lock, and where is the bottleneck?

<details>
<summary>Open the answer</summary>

**Say this first.** A hash map plus a doubly linked list, with one lock around both, is
correct. But every `get` *moves* a node to the front — a write — so even reads contend
on that lock. Shard the cache by key hash into independent LRUs, or use an approximate
policy so reads don't write.

**Then explain.**
- A read-write lock doesn't help: `get` mutates the list.
- Sharding: N segments, each with its own lock and its own LRU.
- Approximate LRU: CLOCK (a reference bit per entry), or sampling as Redis does.
  Caffeine (Java) records reads in lock-free buffers and applies them to the policy in
  batches.
- Watch the miss path: many threads missing the same key at once all call the slow
  backend.

**Next follow-up: "Two threads miss the same key at once and both hit the database.
Fix it."** Single-flight (request coalescing): the first miss stores an in-flight
future for that key; later callers wait on it instead of calling the backend. In Go:
`golang.org/x/sync/singleflight`.

**Go deeper.** `05` §7 and `10` §9.

</details>

### Q3.6 · L5 — What is a memory model, and why can one thread see a stale value from another?

<details>
<summary>Open the answer</summary>

**Say this first.** A memory model defines which writes a read is allowed to see across
threads. Without synchronisation — a lock, an atomic, a channel — compilers and CPUs
may keep values in registers or reorder memory operations, so another thread can see
stale values or see writes in a different order.

**Then explain.**
- The compiler can hoist a flag check out of a loop: `while not done: pass` may never
  exit.
- CPUs buffer stores: x86 allows a later load to pass an earlier store, and ARM allows
  much more.
- Synchronisation creates **happens-before** edges: unlock → later lock, channel send →
  receive, atomic release-store → acquire-load, thread start and join.
- Classic broken pattern: double-checked locking without a volatile or atomic field.

**Next follow-up: "Fix a busy-wait on a `done` flag."** Make the flag an atomic
(`atomic.Bool` in Go, `volatile` in Java) or, better, stop spinning: wait on a channel,
a condition variable, or `threading.Event`.

**Go deeper.** `05` §9.

</details>

### Q3.7 · L6+ — 200 request threads, 20 database connections: under load, latency climbs and throughput falls. Why, and how should it be sized?

<details>
<summary>Open the answer</summary>

**Say this first.** 200 threads queue for 20 connections. Requests hold threads while
they wait, timeouts fire, clients retry, and throughput collapses instead of
plateauing. Size concurrency with Little's law, bound every queue, and reject excess
work early.

**Then explain.**
- **Little's law:** in-flight requests = throughput × latency. At 10 ms per query and a
  database that runs well at 2,000 queries/s, about 20 connections is right. More
  connections than the database has cores add context switching and lock contention
  *inside* the database.
- The 180 extra threads add nothing but waiting. Put a bulkhead in front: limit
  in-flight requests to what the database can serve, queue briefly with a timeout
  shorter than the request deadline, and shed the rest with a 429 or 503.
- Adaptive concurrency limits (Netflix's `concurrency-limits`) find the right limit from
  observed latency.
- Monitor pool wait time, not just pool size.

**Next follow-up: "Why does throughput *drop* rather than level off?"** Work is spent on
requests that will time out anyway (goodput collapses), everyone waits in queues, and
client retries add load exactly when the system is weakest — a metastable failure that
can persist even after the trigger is gone.

**Go deeper.** `05` §5, SD building blocks 12 and 28, and the queueing lab in `04`.

</details>

## 4. Networking

### Q4.1 · L3 — TCP vs UDP?

<details>
<summary>Open the answer</summary>

**Say this first.** TCP is a connection-oriented, reliable, ordered byte stream with flow
and congestion control. UDP sends independent datagrams with no delivery or ordering
guarantees and minimal overhead. TCP for most APIs; UDP for DNS, real-time media,
games, and as the base for QUIC.

**Then explain.**
- TCP costs a handshake round trip before data, and one lost packet delays everything
  behind it (head-of-line blocking).
- With UDP the application decides what loss means — a video call just skips the lost
  frame.
- QUIC (HTTP/3) rebuilds reliability and TLS 1.3 on top of UDP, per stream, so one lost
  packet only stalls its own stream, and connections survive a change of IP address.

**Next follow-up: "Why does DNS mostly use UDP?"** A lookup is one small question and one
small answer; a TCP handshake would triple the cost. DNS falls back to TCP for large
responses and zone transfers, and DNS-over-HTTPS or DNS-over-TLS use encrypted
connections for privacy.

**Go deeper.** `02` Foundations and §1.

</details>

### Q4.2 · L3 — What happens when you type a URL and press Enter?

<details>
<summary>Open the answer</summary>

**Say this first.** DNS resolves the name to an IP address; the browser opens a TCP (or
QUIC) connection and does a TLS handshake; it sends the HTTP request, usually to a CDN
edge or load balancer; the response comes back; the browser parses it, fetches
sub-resources, and renders.

**Then explain.**
- Browser caches and HSTS are checked first.
- DNS: stub resolver → recursive resolver → root → TLD → authoritative server, each
  answer cached for its TTL.
- TCP three-way handshake (1 RTT), TLS 1.3 (1 RTT, certificate validated against the
  trust store, SNI names the site), then the HTTP/2 or HTTP/3 request.
- Server side: edge cache, load balancer, application, database.
- Rendering: HTML → DOM, CSS → CSSOM, run JavaScript, layout, paint.
- Strong answers say where each step fails and what the user would see.

**Next follow-up: "Where does the time go on a first visit from another continent?"** In
round trips: DNS, TCP, TLS and the request itself are at least four RTTs, about 600 ms
at 150 ms each, before the first byte. A CDN edge nearby terminates TCP and TLS close to
the user; TLS 1.3, HTTP/3, preconnect and keep-alive remove round trips.

**Go deeper.** `02` §0, the web-request flow, and the latency lab in `02`.

</details>

### Q4.3 · L4 — Walk through the TCP handshake. Why does TIME_WAIT exist?

<details>
<summary>Open the answer</summary>

**Say this first.** SYN, SYN-ACK, ACK: each side picks an initial sequence number and
confirms the other can send and receive. The side that closes first waits in TIME_WAIT
(twice the maximum segment lifetime) so stray packets from the old connection expire
and its final ACK can be resent if lost.

**Then explain.**
- Initial sequence numbers are randomised so attackers can't inject into connections.
- SYN floods fill the half-open queue; SYN cookies encode state in the sequence number
  instead.
- Close is four segments (a FIN and an ACK in each direction).
- On Linux TIME_WAIT lasts 60 s. `SO_REUSEADDR` lets a restarted server rebind its
  port.

**Next follow-up: "A service making many outbound HTTP calls fails with 'cannot assign
requested address'. Why?"** Ephemeral port exhaustion. Each new connection to the same
destination uses a local port that then sits in TIME_WAIT for 60 s. Linux's default
range has about 28,000 ports, so roughly 470 new connections per second to one
destination exhausts it. Reuse connections (keep-alive, pooling).

**Go deeper.** `02` §1 and the TCP flow there.

</details>

### Q4.4 · L5 — Why can one TCP connection be slow on a fast, long-distance link?

<details>
<summary>Open the answer</summary>

**Say this first.** Throughput is capped at window ÷ RTT. To fill a link, you need a
full **bandwidth-delay product** of data in flight; small windows, slow start and
loss-based congestion control keep a single flow far below that on high-RTT paths.

**Then explain.**
- 1 Gbps × 150 ms = 18.75 MB must be unacknowledged at once to keep that pipe full.
- The receive window needs the window-scaling option beyond 64 KB; OS buffer
  autotuning must allow it.
- Slow start doubles the congestion window once per RTT, so reaching the BDP takes
  about ten round trips — seconds on an intercontinental path.
- CUBIC treats any loss as congestion and backs off; BBR instead estimates bottleneck
  bandwidth and RTT and paces at that rate.

**Next follow-up: "Why does BBR help on lossy links?"** Random, non-congestive loss (Wi-Fi,
long-haul) makes loss-based algorithms shrink the window needlessly; BBR keeps sending
at the measured bottleneck rate. The trade-offs: fairness against CUBIC flows and more
retransmissions in shallow buffers.

**Go deeper.** `02` §2, and the sliding-window and BBR labs there.

</details>

### Q4.5 · L5 — L4 vs L7 load balancing: when do you need each?

<details>
<summary>Open the answer</summary>

**Say this first.** An L4 balancer routes TCP/UDP connections by address and port without
reading the payload: fast and protocol-agnostic. An L7 balancer terminates the connection
and routes each HTTP request by path, header or cookie — which enables retries,
per-request balancing, TLS termination and auth, at more CPU and latency.

**Then explain.**
- L4 can't see individual HTTP/2 or gRPC requests inside one long-lived connection.
- Common shape: anycast plus an L4 tier (Google's Maglev, AWS NLB) in front of a fleet of
  L7 proxies (Envoy, AWS ALB).
- Health checks, connection draining on deploy, consistent hashing for stickiness,
  direct server return for heavy responses at L4.

**Next follow-up: "Clients use gRPC and one backend is overloaded. Why?"** HTTP/2
multiplexes every request over one long-lived connection, and an L4 balancer pins that
connection to one backend. Balance per request at L7, balance on the client (gRPC's
`round_robin` or xDS), or cap connection age so clients reconnect and spread out.

**Go deeper.** `02` §4, the L4/L7 flow, and SD building block 13.

</details>

### Q4.6 · L5 — Walk through the TLS 1.3 handshake. What does the certificate prove?

<details>
<summary>Open the answer</summary>

**Say this first.** The client sends ClientHello with key shares; the server replies with
its key share, then — already encrypted — its certificate, a CertificateVerify signature
proving it holds the private key, and Finished. One round trip, with forward secrecy from
ephemeral Diffie–Hellman. The certificate binds a public key to a domain name, signed by
a certificate authority the client trusts.

**Then explain.**
- The client checks the chain (leaf → intermediate → a root in its trust store), that
  the name matches, that it is in its validity period, and revocation (OCSP stapling);
  Certificate Transparency logs make misissued certificates visible.
- TLS 1.2 needed two round trips and allowed static RSA key exchange (no forward
  secrecy); 1.3 removed it and weak ciphers.
- Mutual TLS (both sides present certificates) is how service meshes authenticate
  services to each other.

**Next follow-up: "Why is 0-RTT resumption risky?"** Early data can be replayed by an
attacker who captured it. Servers should accept only idempotent requests as 0-RTT data,
or apply anti-replay protection.

**Go deeper.** `02` §5, `11`, and the TLS 1.3 flow.

</details>

### Q4.7 · L6+ — Users in Asia see 2-second page loads; US users see 300 ms. Everything runs in us-east. What do you do, in what order?

<details>
<summary>Open the answer</summary>

**Say this first.** Measure where the time goes first (round trips vs server time).
Then cut distance and round trips in order of cost: a CDN for static and cacheable
responses, edge TLS termination with warm connections to the origin, HTTP/2 and 3, fewer
dependent requests; then regional read replicas or caches; multi-region writes only if
the product truly needs them.

**Then explain.**
- us-east to Singapore is roughly 200–250 ms RTT. A cold page needing DNS, TCP, TLS,
  the HTML and a few dependent requests is eight or so round trips — about 2 s.
- The edge terminates TCP and TLS near the user and reuses warm connections to the
  origin, removing several long round trips.
- Read replicas in the region help read-heavy APIs *if* slightly stale data is
  acceptable.
- Active-active writes bring conflict resolution and consistency costs — justify them
  with a product requirement, not latency alone.
- Measure after each step with real-user monitoring (time to first byte, not just
  server time).

**Next follow-up: "What breaks when you add a read replica in Singapore?"** Replication
lag breaks read-your-writes: a user posts and then doesn't see the post. Route that
user's reads to the primary for a short window after a write, or pass a
"read at least this log position" token with the request.

**Go deeper.** `02` §0, and SD building blocks 27 and 29.

</details>

## 5. Databases

### Q5.1 · L3 — What does ACID mean?

<details>
<summary>Open the answer</summary>

**Say this first.** Atomicity: all of a transaction happens or none of it. Consistency:
constraints hold before and after. Isolation: concurrent transactions don't interfere
beyond what the chosen isolation level allows. Durability: once committed, data survives
a crash.

**Then explain.**
- Atomicity and durability come from the write-ahead log: the commit record is forced to
  disk before the database says "committed".
- Isolation comes from locks and/or MVCC, at a configurable level.
- Consistency is partly the application's job: the database only enforces the
  constraints you declared.
- The "C" in ACID has nothing to do with the "C" in CAP.

**Next follow-up: "How is a commit durable if the machine crashes right after COMMIT
returns?"** The commit record was `fsync`ed to the log before the acknowledgement. On
restart, recovery replays the log (redo committed work, undo uncommitted work). Group
commit batches many transactions into one `fsync` for throughput.

**Go deeper.** `03` Foundations and §9.

</details>

### Q5.2 · L4 — Explain isolation levels and the anomalies each allows.

<details>
<summary>Open the answer</summary>

**Say this first.** Weaker levels permit anomalies in exchange for concurrency. Read
committed prevents dirty reads. Repeatable read / snapshot isolation adds stable reads
within a transaction. Only serializable prevents everything — including write skew.

**Then explain.**
- PostgreSQL defaults to read committed; MySQL InnoDB to repeatable read.
- PostgreSQL's repeatable read is snapshot isolation: it prevents lost updates by
  aborting the second writer, but still allows **write skew** (two transactions read the
  same data and write *different* rows, together breaking a rule).
- PostgreSQL's serializable (SSI) detects dangerous read/write patterns and aborts one
  transaction — so the application must retry.
- MySQL's repeatable read updates the latest committed row instead of erroring, so a
  read-modify-write in application code can still lose an update there.
- Defences below serializable: atomic updates (`SET stock = stock - 1`),
  `SELECT … FOR UPDATE`, constraints, optimistic version columns.

**Next follow-up: "Two doctors are on call and both go off call at the same time. Which
level stops it?"** Only serializable, or explicit locking of the rows read (or a
constraint). Snapshot isolation allows it, because each transaction writes a different
row and neither sees the other's change.

**Go deeper.** `03` §3 and the isolation lab there, which runs all five anomalies.

</details>

### Q5.3 · L4 — How do indexes speed up queries, and when do they hurt?

<details>
<summary>Open the answer</summary>

**Say this first.** A B-tree index lets the database jump to matching rows in a few page
reads instead of scanning the table. The costs: every write must update every index,
indexes take space, and for predicates that match many rows the planner will still
choose a scan.

**Then explain.**
- Composite indexes are used left to right: put equality columns first, then the range
  column.
- A **covering** index includes every column the query needs, so the table isn't touched
  (an index-only scan).
- Wrapping the column in a function (`WHERE lower(email) = …`) defeats a plain index;
  create an expression index instead. `LIKE 'abc%'` can use an index; `LIKE '%abc'`
  cannot.
- An index matching `ORDER BY … LIMIT` avoids a sort.
- Always check with `EXPLAIN (ANALYZE, BUFFERS)`.

**Next follow-up: "Index on `(a, b)`. Does `WHERE b = 5` use it?"** Not efficiently —
`b` isn't a leftmost prefix. Some engines can do a *skip scan* when `a` has few distinct
values (MySQL 8.0.13+, PostgreSQL 18+); otherwise add an index on `b`.

**Go deeper.** `03` §2 and §8, and the SQL module.

</details>

### Q5.4 · L5 — B-tree vs LSM-tree storage engines: which for what?

<details>
<summary>Open the answer</summary>

**Say this first.** B-trees update pages in place: excellent reads and predictable latency,
at the cost of random writes. LSM trees buffer writes in memory and flush them as sorted
immutable files: very high write throughput, but a read may check several files and
background compaction rewrites data.

**Then explain.**
- The trade-off triangle is read, write and space amplification (the RUM conjecture):
  you can optimise two.
- LSM path: write-ahead log + memtable → sorted SSTables → compaction (leveled favours
  reads, tiered favours writes). Bloom filters let reads skip files. Deletes are
  tombstones until compaction removes them.
- B-trees: PostgreSQL, InnoDB, SQL Server. LSM: RocksDB, Cassandra, ScyllaDB, Bigtable,
  HBase.
- Write-heavy, append-mostly data (events, time series, logs) favours LSM; read-heavy
  transactional workloads with range queries favour B-trees.

**Next follow-up: "Why are LSM lookups for a *missing* key still fast?"** Each SSTable has a
Bloom filter. With about 10 bits per key the false-positive rate is about 1%, so almost
every file that can't contain the key is skipped without a disk read.

**Go deeper.** `03` §1–2, and the LSM and B+ tree labs there.

</details>

### Q5.5 · L5 — How does replication work, and what does replication lag break?

<details>
<summary>Open the answer</summary>

**Say this first.** The leader streams its write log to followers, synchronously or
asynchronously. With asynchronous replication, followers serve stale reads, and a
failover can lose writes the old leader had already acknowledged.

**Then explain.**
- Synchronous: no acknowledged write is lost, but every write waits for a follower.
  Semi-synchronous: wait for at least one. Quorum replication (Raft, Paxos): wait for a
  majority.
- Lag breaks **read-your-writes** (you don't see your own post) and **monotonic reads**
  (a refresh goes back in time when it hits a different replica). Fixes: read from the
  leader after a write, sticky sessions, or a position token.
- Failover risks split brain — two leaders accepting writes. Prevent it with consensus
  for leader election and fencing of the old leader.
- Multi-leader and leaderless designs must resolve conflicts: last-writer-wins silently
  drops data; version vectors or CRDTs keep it.

**Next follow-up: "What are the RPO and RTO of asynchronous failover?"** RPO is greater
than zero: whatever was in the replication lag is lost. RTO is detection plus promotion
plus clients reconnecting — seconds to minutes. Synchronous or quorum replication
brings RPO to zero at a latency cost.

**Go deeper.** `03` §5, and SD building blocks 05 and 06.

</details>

### Q5.6 · L5 — State the CAP theorem precisely.

<details>
<summary>Open the answer</summary>

**Say this first.** When a network partition separates replicas, a system must choose
between consistency (linearizability: every read sees the latest write) and
availability (every non-failed node still answers). With no partition you can have
both; PACELC adds that, even then, you trade latency against consistency.

**Then explain.**
- Partitions aren't optional in a distributed system, so "pick two of three" is the wrong
  model: the real choice is what to do *during* a partition.
- CAP's availability is strict (every request to a live node succeeds); real systems are
  judged by SLOs instead. Spanner is technically CP but highly available in practice.
- Many systems are neither: an asynchronously replicated database is not linearizable,
  and it isn't available on the minority side either.

**Next follow-up: "Isn't a single-node PostgreSQL 'CA'?"** CAP is about replicated
systems. If clients are partitioned from the only node, it is simply unavailable to
them; the "CA" label doesn't describe any useful distributed behaviour.

**Go deeper.** `03` §7, with its runnable CP-vs-AP model and partition flow.

</details>

### Q5.7 · L6+ — A 5 TB PostgreSQL primary is at 80% CPU, growing 10% a month. What are your options, in order?

<details>
<summary>Open the answer</summary>

**Say this first.** Buy time cheaply first: fix the top queries and indexes, add
connection pooling, cache hot reads, move reads to replicas, and take a bigger machine.
Then remove load structurally — split off a domain, archive cold data. Shard only when a
single-writer ceiling is truly close: it's a multi-quarter migration with permanent
costs.

**Then explain.**
- The clock: 10% monthly growth from 80% reaches 100% in under 2.5 months — quick wins
  first.
- `pg_stat_statements` usually shows a handful of queries causing most of the load.
- PgBouncer for connection storms; caches with an explicit invalidation plan; read
  replicas for lag-tolerant reads.
- Table partitioning by time shrinks indexes and makes retention and vacuum cheap.
- Functional split: a separate database per bounded context that doesn't need joins.
- Sharding by tenant or customer ID (Citus, or application-level), or distributed SQL
  (Spanner, CockroachDB, YugabyteDB). Costs: cross-shard queries and transactions,
  resharding, operations.

**Next follow-up: "How would you choose the shard key?"** The key that most queries filter
on and that keeps transactions on one shard (usually tenant or user ID), with high
cardinality and even load. Avoid monotonically increasing keys (time) that send every
write to the newest shard, and plan for very large tenants (split them or give them
dedicated shards).

**Go deeper.** `03` §10, SD building block 25, and the consistent-hashing lab in `03`.

</details>

## 6. Architecture and Distributed Systems

### Q6.1 · L3 — Monolith or microservices?

<details>
<summary>Open the answer</summary>

**Say this first.** A monolith is one deployable unit; microservices split a system into
independently deployable services along business capabilities. Microservices buy team
autonomy and independent scaling, paid for with network calls, partial failures and
operational overhead. Start with a well-modularised monolith unless team size and clear
boundaries justify the split.

**Then explain.**
- Conway's law: system boundaries tend to mirror team boundaries.
- A modular monolith keeps clean internal boundaries without network hops.
- Each service owns its data; sharing a database couples services invisibly.
- Split when a part needs to scale, deploy or fail independently, or when one team
  owns it end to end.

**Next follow-up: "What is a distributed monolith, and how do you spot one?"** Services
that must be deployed together, share a database, or call each other synchronously in
long chains for every request. You get the costs of both styles and the benefits of
neither.

**Go deeper.** `04` Foundations.

</details>

### Q6.2 · L4 — How do you make an API call safe to retry?

<details>
<summary>Open the answer</summary>

**Say this first.** Make it idempotent. The client sends an idempotency key; the server
records the key and the result atomically with the side effect, and returns the stored
result for any repeat.

**Then explain.**
- GET, PUT and DELETE are idempotent by definition; POST is not.
- Store keys under a unique constraint, in the same transaction as the effect, with a
  TTL. A concurrent duplicate either waits for the first to finish or gets a 409.
- Retry only retryable errors (timeouts, 503), with exponential backoff and jitter, and a
  retry budget.
- "Exactly-once delivery" doesn't exist across a network; exactly-once *effect* is
  at-least-once delivery plus idempotent processing.

**Next follow-up: "The payment provider timed out. Did the charge happen?"** You don't know.
Retry with the *same* idempotency key (the provider deduplicates), or query the payment's
status — never charge again blindly — and reconcile against the provider's records later.

**Go deeper.** `04` §6, and SD building block 03 and problem 017.

</details>

### Q6.3 · L5 — How do you publish an event reliably when you also write to your database?

<details>
<summary>Open the answer</summary>

**Say this first.** The transactional outbox: write the business row and an outbox row in
the same database transaction, then have a relay (a poller or change data capture)
publish outbox rows to the broker. Delivery is at-least-once, so consumers must be
idempotent.

**Then explain.**
- The dual-write problem: commit then publish can lose the event if the process dies in
  between; publish then commit can announce something that never happened.
- Two-phase commit across a database and a broker is rarely available and rarely worth
  it.
- CDC tools (Debezium) read the database log, so the outbox needs no polling.
- Keep per-entity order by partitioning on the entity ID.

**Next follow-up: "The relay publishes and crashes before marking the row sent. Now
what?"** It publishes again on restart — a duplicate. Consumers deduplicate by event ID
(a processed-events table, or idempotent upserts).

**Go deeper.** `04` §2 and the outbox flow.

</details>

### Q6.4 · L5 — Saga vs two-phase commit?

<details>
<summary>Open the answer</summary>

**Say this first.** Two-phase commit makes several participants commit atomically, but
blocks if the coordinator fails and holds locks across network round trips. A saga
splits the business transaction into local transactions, each with a compensating
action: no global locks, eventually consistent, and you must design the compensations
and the visible in-between states.

**Then explain.**
- Orchestration (one coordinator drives the steps) is easier to follow than
  choreography (services react to each other's events).
- A compensation is a new business action, not an undo: a refund, not an un-charge.
- Every step must be idempotent and have a timeout; record saga state durably.
- 2PC isn't always bad: Spanner runs 2PC between Paxos groups, so the coordinator is
  replicated and doesn't block on one machine's failure.

**Next follow-up: "The payment succeeded but reserving inventory failed. What happens?"**
The saga runs the payment's compensation — void the authorisation or refund. Better:
order the steps so the cheapest to undo comes first (reserve inventory, then capture
payment), and use authorise-then-capture so a failed order never takes money.

**Go deeper.** `04` §3 and the saga lab.

</details>

### Q6.5 · L5 — How do timeouts, retries and circuit breakers work together?

<details>
<summary>Open the answer</summary>

**Say this first.** Timeouts bound how long you wait. Retries with jittered backoff ride out
brief failures. A circuit breaker stops calling a dependency that is clearly failing, so
threads and connections aren't tied up — all inside a request deadline and a retry
budget.

**Then explain.**
- Propagate the deadline: each hop's timeout is shorter than its caller's.
- Retry at one layer only, and cap retries at about 10% of traffic.
- Breaker states: closed → open (fail fast) → half-open (let a trial request through).
- Add bulkheads (separate pools per dependency), load shedding, and a fallback
  (cached or degraded response).

**Next follow-up: "Three layers each retry three times. The bottom service fails. What
happens?"** Up to 27× the load reaches it (3 × 3 × 3) at the moment it's weakest — a retry
storm. Retry in one place, with a budget.

**Go deeper.** `04` §6, SD building blocks 12 and 28, and the queueing and circuit-breaker
labs in `04`.

</details>

### Q6.6 · L6+ — How would you set SLOs for a new service, and what happens when the error budget runs out?

<details>
<summary>Open the answer</summary>

**Say this first.** Pick SLIs that reflect what users experience (success rate and latency
of the key requests), set the SLO a little below what users need and what you can
deliver, turn the gap into an error budget, alert on how fast it burns, and when it's
spent, shift effort from features to reliability.

**Then explain.**
- SLI = good events ÷ valid events. Example: 99.9% of checkout requests succeed within
  300 ms over 28 days — a budget of about 40 minutes.
- Alert on burn rate across two windows (for example 14.4× over an hour and five minutes
  pages someone) rather than on raw error counts.
- Never target 100%: every extra nine costs more, and users can't tell beyond their own
  network's reliability.
- Dependencies multiply: you can't promise more than your hard dependencies in series
  allow.
- Agree an error-budget policy with product before you need it.

**Next follow-up: "You depend on five services at 99.9% each. Can you promise 99.95%?"**
Not if they are hard dependencies in series: 0.999⁵ ≈ 99.5%. You need redundancy, caches
and fallbacks that turn them into soft dependencies, or a lower SLO.

**Go deeper.** `04` §7, SD building block 15, and the availability lab in `04`.

</details>

## 7. Security

### Q7.1 · L3 — Authentication vs authorization?

<details>
<summary>Open the answer</summary>

**Say this first.** Authentication establishes who you are; authorization decides what you
may do. HTTP reflects it: 401 means "I don't know who you are", 403 means "I know, and
the answer is no".

**Then explain.**
- Authentication: passwords plus MFA, passkeys (WebAuthn), single sign-on through OIDC.
- Authorization models: role-based (RBAC), attribute-based (ABAC), relationship-based
  (ReBAC, as in Google's Zanzibar).
- Check authorization on the server, on every request, for every object — broken access
  control is the top item in the OWASP Top 10.

**Next follow-up: "What is an IDOR?"** An insecure direct object reference:
`/invoices/124` returns someone else's invoice because the server checked that you're
logged in but not that the invoice is yours. Enforce ownership checks in the data-access
layer; unguessable IDs are not a control.

**Go deeper.** `11`.

</details>

### Q7.2 · L4 — How should passwords be stored?

<details>
<summary>Open the answer</summary>

**Say this first.** Never encrypted and never with a fast hash. Use a slow, salted,
memory-hard password hash — Argon2id (or scrypt or bcrypt) — with a unique salt per user,
and compare in constant time.

**Then explain.**
- Fast hashes like SHA-256 run billions of guesses per second on a GPU; password hashes
  are deliberately slow and memory-hungry.
- A per-user salt defeats precomputed tables and hides users who share a password.
- An optional pepper — a secret kept in a KMS or HSM, not in the database — protects a
  stolen database dump.
- Rehash with stronger parameters when a user next logs in; add rate limiting, MFA, and
  checks against known-breached passwords.

**Next follow-up: "bcrypt or Argon2id?"** Both are acceptable. Argon2id is memory-hard, so
it resists GPU and ASIC attacks better, and it is OWASP's first recommendation; bcrypt
also ignores input beyond 72 bytes.

**Go deeper.** `11`.

</details>

### Q7.3 · L4 — Server sessions vs JWTs?

<details>
<summary>Open the answer</summary>

**Say this first.** A server-side session keeps state on the server and gives the client an
opaque ID — trivially revocable. A JWT is a signed, self-contained token that any server
can verify without a lookup — easy to scale, hard to revoke before it expires. Keep JWT
access tokens short-lived and pair them with refresh tokens.

**Then explain.**
- Validate JWTs strictly: the expected algorithm only (reject `none` and algorithm
  confusion), plus `exp`, `nbf`, `iss` and `aud`.
- The payload is only base64-encoded — never put secrets in it.
- Store tokens in `HttpOnly`, `Secure`, `SameSite` cookies rather than `localStorage`,
  which any XSS can read.

**Next follow-up: "A user's laptop is stolen. How do you end their sessions?"** Revoke their
refresh tokens (kept server-side), rely on short access-token lifetimes, and for
sensitive actions check a per-user token version — or keep a deny-list of token IDs until
they expire.

**Go deeper.** `11` and the OIDC chapter in the API module.

</details>

### Q7.4 · L5 — Explain the OAuth 2.0 authorization code flow with PKCE.

<details>
<summary>Open the answer</summary>

**Say this first.** The app sends the user to the authorization server with a
`code_challenge`; the user signs in and consents; the app receives a short-lived code on
its registered redirect URI and exchanges it — together with the secret `code_verifier` —
for tokens. PKCE makes an intercepted code useless to anyone who didn't start the flow.

**Then explain.**
- Roles: resource owner (user), client (app), authorization server, resource server
  (API).
- The `state` parameter prevents CSRF on the redirect; redirect URIs must match exactly.
- OIDC adds an ID token (a JWT describing the user) for *login*; the access token is for
  calling APIs.
- The implicit and password grants are deprecated (OAuth 2.1 drops them); rotate refresh
  tokens.

**Next follow-up: "OAuth vs OIDC?"** OAuth is delegated authorization: it lets an app call
an API on your behalf. OIDC is an identity layer on top that says who you are. Don't
treat an access token as proof of login.

**Go deeper.** `11` and the OAuth PKCE flow.

</details>

### Q7.5 · L5 — How do SQL injection and XSS work, and what actually prevents them?

<details>
<summary>Open the answer</summary>

**Say this first.** Both mix untrusted data into code — into a SQL query, or into HTML and
JavaScript. Prevent them by keeping code and data separate: parameterised queries, and
context-aware output encoding (plus a Content Security Policy). Input blacklists don't
work.

**Then explain.**
- Prepared statements send the query and its values separately; ORMs are safe until
  someone builds raw SQL strings. Give the database user least privilege.
- XSS comes in stored, reflected and DOM-based forms. Templating frameworks escape by
  default; the danger is raw sinks (`innerHTML`, `dangerouslySetInnerHTML`).
- A CSP with nonces blocks injected scripts; `HttpOnly` cookies limit what a script can
  steal.
- Related: CSRF (use `SameSite` cookies and tokens) and SSRF (allowlist outbound
  destinations).

**Next follow-up: "Can you parameterise a table name or an ORDER BY column?"** No —
placeholders are for values only. Map the user's choice through an allowlist of known
identifiers.

**Go deeper.** `11`, OWASP Top 10 section.

</details>

### Q7.6 · L6+ — Design secrets management for 200 microservices.

<details>
<summary>Open the answer</summary>

**Say this first.** Centralise secrets in a secrets manager backed by a KMS, authenticate
workloads by *identity* rather than by static keys, issue short-lived dynamic credentials,
audit every access, rotate automatically, and keep secrets out of code, images and
environment files in git.

**Then explain.**
- Workload identity: SPIFFE IDs, cloud IAM roles, Kubernetes service accounts federated
  through OIDC.
- Envelope encryption: data keys encrypted by a key-encryption key that never leaves the
  KMS or HSM.
- Dynamic database credentials with leases (Vault) limit the blast radius of a leak.
- Inject secrets at runtime (sidecar, CSI driver), scan repositories and CI logs for
  leaks, and keep a documented break-glass path.
- mTLS between services removes many shared secrets altogether.

**Next follow-up: "Rotate a database password with zero downtime."** Support two valid
credentials at once: create the new one, roll it out to every client, verify nothing uses
the old one, then revoke it — or use per-instance dynamic credentials that renew
themselves.

**Go deeper.** `11`, the Tool-Kit secrets chapter, and the Vault lease flow.

</details>

## 8. Rapid Fire: One-Sentence Answers

Cover the right-hand column and answer each in one sentence. These come up as warm-ups
and as quick checks in the middle of longer questions.

| Question | One-sentence answer |
|---|---|
| Stack vs heap memory? | The stack holds each call's local variables and is freed automatically on return; the heap holds data whose lifetime outlives a call and is freed explicitly or by a garbage collector. |
| Why is binary search O(log n)? | Each comparison discards half of the remaining range, so n items need about log₂ n steps. |
| What is a cache line? | The unit the CPU moves between RAM and cache — usually 64 bytes — so neighbouring data comes along for free. |
| What does `fsync` do? | It forces a file's buffered writes out to stable storage and waits until the device confirms them. |
| What is a system call? | A controlled jump from user mode into the kernel to ask for a privileged service such as I/O or memory. |
| Little's law? | Items in a system = arrival rate × average time in the system (L = λW). |
| Latency vs throughput? | Latency is how long one operation takes; throughput is how many operations complete per unit of time. |
| What does idempotent mean? | Doing it twice has the same effect as doing it once. |
| What is a Bloom filter's false positive? | It can say "maybe present" for a key that was never added, but never "absent" for one that was. |
| What is consistent hashing for? | Adding or removing a node moves only about 1/N of the keys instead of nearly all of them. |
| What is backpressure? | A slow consumer signals upstream to slow down instead of letting work pile up in memory. |
| Optimistic vs pessimistic locking? | Pessimistic locks before touching data; optimistic proceeds and checks a version at commit, retrying on conflict. |
| What is a write-ahead log? | An append-only record of changes written durably before the data pages, so a crash can be recovered by replaying it. |
| What is head-of-line blocking? | One stalled item at the front of a queue or stream holds up everything behind it. |
| What is a zombie process? | A process that has exited but whose parent has not yet collected its exit status with `wait()`. |
| What is a thundering herd? | Many clients waking or retrying at the same instant, overloading the thing they all wait on. |
| What is eventual consistency? | If writes stop, all replicas converge to the same value — with no promise about how soon. |
| What is p99 latency? | The latency that 99% of requests beat; the slowest 1% take longer. |
| What are vector clocks for? | Telling "happened before" apart from "concurrent", so conflicting writes can be detected. |
| What is a fencing token? | A number that increases with each lock grant, so storage can reject writes from a holder whose lock has expired. |
| What is two's complement? | The signed-integer encoding where the top bit has negative weight, so one adder handles both signs and `-x == ~x + 1`. |
| What is machine epsilon? | The gap between 1.0 and the next larger float — about 2.2 × 10⁻¹⁶ for `float64` — the scale of relative rounding error. |
| Little-endian? | The least significant byte is stored at the lowest address; x86 and ARM are little-endian, network protocols are big-endian. |
| What is a branch misprediction? | The CPU guessed the wrong side of a branch and must discard the work it did speculatively, costing roughly 15–20 cycles. |
| What is escape analysis? | The compiler proving a value can't outlive its function, so it can live on the stack instead of the heap. |
| Why can't reference counting free cycles? | Objects in a cycle keep each other's counts above zero even when nothing else references them. |
| What is a write barrier? | Code added to pointer stores so a concurrent or generational collector learns about pointers the program moved. |
| What is a quorum? | A subset of replicas large enough that any two overlap — usually a majority — so decisions can't conflict. |
| What is a term in Raft? | A numbered leadership generation; a node that sees a higher term steps down. |
| What is a CRDT? | A replicated data type whose merge is commutative, associative and idempotent, so replicas converge without coordination. |
| What is exit code 137? | 128 + 9: the process was killed by SIGKILL, very often by the OOM killer. |

## 9. Computer Architecture and Data Representation

### Q9.1 · L3 — Why does `0.1 + 0.2 == 0.3` return false?

<details>
<summary>Open the answer</summary>

**Say this first.** Floats are stored in binary, and 0.1, 0.2 and 0.3 have no exact
binary representation — like 1/3 in decimal. Each is rounded to the nearest float, the
rounding errors don't cancel, and `==` compares every bit. Compare with a relative
tolerance instead (`math.isclose`).

**Then explain.**
- A `float64` is 1 sign bit, 11 exponent bits and 52 fraction bits: about 15–17
  significant decimal digits, whatever the magnitude.
- The error is relative: the gap between adjacent floats near 1.0 is ~2.2 × 10⁻¹⁶
  (machine epsilon), near 10¹⁶ it is 2, so `1e16 + 1 - 1e16` is 0.
- Every operation is exactly rounded, so errors are deterministic — but addition is not
  associative, so summing in a different order changes the result.

**Next follow-up: "How would you store money?"** As integers in the smallest unit (cents)
or a decimal type (`Decimal`, SQL `NUMERIC`), because currency rounding rules are defined
in decimal and binary floats can't represent most decimal fractions.

**Go deeper.** `13` §5.

</details>

### Q9.2 · L4 — Where can `mid = (lo + hi) / 2` go wrong, and what else overflows like it?

<details>
<summary>Open the answer</summary>

**Say this first.** With fixed-width integers, `lo + hi` can exceed the maximum (2³¹ − 1
for `int32`) and wrap to a negative number, giving a negative index. Write
`lo + (hi - lo) / 2`.

**Then explain.**
- Go, Java, C and Rust release builds wrap silently; C and C++ make signed overflow
  undefined behaviour, so the optimiser may assume it never happens.
- Two's complement has one more negative value than positive, so `abs(MIN_INT)` and
  `-MIN_INT` are still negative.
- Unsigned `0 - 1` becomes the maximum value, so `for i := uint(n-1); i >= 0; i--` never
  ends.
- Python's `int` never overflows, but Python code overflows at every boundary: NumPy
  arrays, `struct`, database columns, and JSON numbers read by JavaScript (exact only to
  2⁵³).

**Next follow-up: "Why is `hash % n` dangerous in Java or Go?"** Their `%` truncates toward
zero, so a negative hash gives a negative remainder and an out-of-range bucket. Python's
`%` takes the sign of the divisor and doesn't have this bug.

**Go deeper.** `13` §2–§3.

</details>

### Q9.3 · L4 — Explain `x & (x - 1)` and give two uses.

<details>
<summary>Open the answer</summary>

**Say this first.** It clears the lowest set bit of `x`. Subtracting 1 flips the lowest 1
to 0 and every 0 below it to 1; AND-ing with the original keeps everything above and
clears the rest.

**Then explain.**
- `x > 0 and x & (x - 1) == 0` tests for a power of two.
- Repeating it until zero counts set bits in O(number of ones) (Kernighan).
- Its sibling `x & -x` isolates the lowest set bit — the step a Fenwick tree uses to jump
  between ranges.
- `s = (s - 1) & mask` enumerates every subset of a bitmask, the inner loop of bitmask
  DP.

**Next follow-up: "Find the one number that appears once when every other appears
twice."** XOR everything: `a ^ a = 0` and XOR is commutative and associative, so pairs
cancel and the single number remains. O(n) time, O(1) space.

**Go deeper.** `13` §4; DSA topic 20.

</details>

### Q9.4 · L5 — The same loop runs 3× faster on sorted input than on shuffled input. Why?

<details>
<summary>Open the answer</summary>

**Say this first.** Branch prediction. On sorted data the `if` goes the same way for long
runs, so the CPU predicts it almost perfectly; on shuffled data it's a coin flip, and
each misprediction throws away the speculatively executed work — roughly 15–20 cycles.

**Then explain.**
- A pipelined CPU fetches instructions long before a branch condition is known, so it
  guesses and executes speculatively.
- Measured in `13` §10: a real branch ran 3.6× slower on shuffled data, about 7 ns per
  misprediction.
- If the compiler turns the branch into a conditional move (`CMOV`), there's nothing to
  predict and sorted and shuffled run at the same speed — which is why this demonstration
  doesn't reproduce everywhere.

**Next follow-up: "How would you make it fast on unsorted data?"** Make it branch-free:
arithmetic on the comparison result, `min`/`max`, a lookup table, or restructure so the
compiler can emit `CMOV` — or vectorise it with SIMD. Sorting first pays off only if the
data is filtered many times.

**Go deeper.** `13` §8–§10.

</details>

### Q9.5 · L5 — Why can summing an array with four accumulators be several times faster than with one?

<details>
<summary>Open the answer</summary>

**Say this first.** With one accumulator every add depends on the previous one, so the
loop runs at the add's *latency* (several cycles). Four independent accumulators let an
out-of-order core overlap them, so it runs at the add's *throughput* (one or two per
cycle). Measured: 3.6× faster.

**Then explain.**
- Latency is how long one operation takes; throughput is how many finish per cycle when
  they're independent. Dependency chains expose latency.
- The same idea explains why a linked-list walk is slow: each load needs the previous
  node's pointer, so memory latency can't be overlapped.
- Compilers do this rewrite for integers but not for floats, because float addition isn't
  associative; the result can change.

**Next follow-up: "When wouldn't this help?"** When the loop is memory-bound — data not in
cache — because then the limit is memory bandwidth or latency, not the adder.

**Go deeper.** `13` §9 and §11.

</details>

## 10. Memory Management

### Q10.1 · L3 — What lives on the stack and what lives on the heap?

<details>
<summary>Open the answer</summary>

**Say this first.** The stack holds one frame per active function call — parameters,
locals, the return address — and is freed automatically when the call returns. The heap
holds anything whose lifetime isn't tied to one call, and must be freed by the programmer,
the compiler, or a garbage collector.

**Then explain.**
- Stack allocation is one instruction and always cache-hot; heap allocation goes through an
  allocator and may create GC work later.
- Stacks are small and per-thread (8 MB for the main thread on Linux; Go goroutines start at
  2 KB and grow), so deep recursion overflows them.
- The rule "primitives on the stack, objects on the heap" is only a heuristic: every CPython
  value is a heap object, and Go's compiler keeps `&T{}` on the stack when it doesn't escape.

**Next follow-up: "What happens when recursion is too deep?"** Python raises
`RecursionError` at its limit (1,000 by default); C hits a guard page and dies with
`SIGSEGV`; Go grows the goroutine's stack by copying, up to 1 GB.

**Go deeper.** `14` Foundations and §1–§2.

</details>

### Q10.2 · L4 — How does Python free memory, and when does it need a garbage collector?

<details>
<summary>Open the answer</summary>

**Say this first.** CPython uses reference counting: every object counts the references to
it and is freed the instant the count reaches zero. A separate, generational cycle collector
finds groups of objects that reference each other but are unreachable, which reference
counting alone can never free.

**Then explain.**
- Refcounting frees promptly and keeps memory small, but every reference copy writes to the
  object — which costs cache traffic, defeats copy-on-write after `fork`, and is a big reason
  for the GIL.
- The cycle collector has three generations and triggers when allocations minus deallocations
  of container objects pass a threshold (700 for generation 0).
- `weakref` lets you reference an object without keeping it alive — the standard way to break
  parent/child cycles and build caches.

**Next follow-up: "Is disabling the GC a good optimisation?"** Only if you're sure there are
no cycles or the process is short-lived. Measured in `14` §8: disabling it saved CPU but let
2 million dead objects accumulate, 100 MB instead of 8 MB.

**Go deeper.** `14` §6 and §8.

</details>

### Q10.3 · L5 — How does a tracing garbage collector work, and why do concurrent collectors need write barriers?

<details>
<summary>Open the answer</summary>

**Say this first.** It marks everything reachable from the roots (globals, stacks,
registers) and frees the rest. A concurrent collector marks while the program runs, so the
program can hide a live object from it by moving a pointer; the write barrier is code on
every pointer store that tells the collector about such moves.

**Then explain.**
- Tri-colour marking: white (not reached), grey (reached, children not scanned), black
  (done). The invariant is that no black object points to a white one.
- Storing a pointer to a white object into a black one, then deleting the only other path
  to it, breaks the invariant: the object is freed while still referenced.
- A Dijkstra (insertion) barrier greys the new target; a Yuasa (deletion) barrier greys the
  old one; Go uses a hybrid of both.
- Generational collectors also need barriers, to record old-to-young pointers.

**Next follow-up: "What does a GC cost you?"** CPU for marking (proportional to live data ×
number of cycles), memory headroom (garbage accumulates between cycles), and pause time.
Collectors trade among throughput, latency and footprint.

**Go deeper.** `14` §7–§9; the toy collector in §9 shows the lost object and the fix.

</details>

### Q10.4 · L5 — Your Go service's memory grows steadily. How do you find out why?

<details>
<summary>Open the answer</summary>

**Say this first.** Confirm it's a leak and not normal behaviour, then compare heap profiles
over time to find which allocation site keeps growing, and ask what still references those
objects.

**Then explain.**
- Watch heap-in-use (`HeapAlloc`, `inuse_space`), not RSS alone: allocators and Go's
  scavenger return memory to the OS lazily, so RSS staying high after a spike isn't a leak.
- `go tool pprof -inuse_space` on two profiles taken hours apart, with `-base`, shows the
  growth by call site. Check `goroutine` profiles too: leaked goroutines hold their stacks
  and everything they reference.
- Usual causes: an unbounded map or cache, goroutines blocked forever on channels without a
  cancelled context, a small slice keeping a huge backing array alive, timers or tickers
  never stopped.

**Next follow-up: "And if it's not a leak, just too much memory?"** Tune rather than fix:
set `GOMEMLIMIT` just under the container limit, reduce allocations in hot paths (escape
analysis with `-gcflags=-m`, reusing buffers), or store large caches as pointer-free data
that the GC doesn't scan.

**Go deeper.** `14` §10–§13.

</details>

### Q10.5 · L6+ — Choose a memory-management strategy for a latency-sensitive service with a 20 GB in-memory cache.

<details>
<summary>Open the answer</summary>

**Say this first.** The risk is that a tracing GC has to mark 20 GB on every cycle, costing
CPU and threatening tail latency. Either keep the cache out of the collector's view or
choose a runtime whose collector handles large heaps with short pauses — and measure p99
under realistic allocation rates before deciding.

**Then explain.**
- In Go: store entries in large pointer-free arrays (`[]byte` slabs with an index of
  offsets — the BigCache/FreeCache approach) so the GC doesn't scan them, and use
  `GOMEMLIMIT` for headroom.
- On the JVM: ZGC or Shenandoah keep pauses sub-millisecond on very large heaps at some
  throughput cost; or move the cache off-heap.
- Rust or C++ remove the collector entirely at the cost of development speed and, for C++,
  memory safety.
- Often the right answer is architectural: an external cache (Redis, Memcached) or sharding
  the cache across more, smaller processes.

**Next follow-up: "How would you know it worked?"** GC CPU fraction and pause-time
histograms, p99/p999 latency under load tests that include cache churn, and memory headroom
against the container limit — compared before and after.

**Go deeper.** `14` §10–§11 and §14.

</details>

## 11. Distributed Systems Fundamentals

### Q11.1 · L3 — Why is it hard to tell whether another server has crashed?

<details>
<summary>Open the answer</summary>

**Say this first.** Because a crashed server, a slow one, and a network that dropped the
messages all look the same from outside: silence. All you can do is choose a timeout, and
every timeout is sometimes wrong.

**Then explain.**
- Short timeouts suspect healthy servers during GC pauses or network hiccups, triggering
  needless failovers.
- Long timeouts leave real failures undetected longer.
- In `15` §2's simulation, a 250 ms timeout falsely suspected a healthy node 83 times in an
  hour; a 1,000 ms timeout never did but took a second to notice a real crash.

**Next follow-up: "How do real systems do better?"** Phi accrual detectors output a suspicion
level based on the observed heartbeat distribution; SWIM asks other nodes to probe
indirectly before declaring a node dead.

**Go deeper.** `15` §1–§2.

</details>

### Q11.2 · L4 — Why can't you order events on different machines by their timestamps?

<details>
<summary>Open the answer</summary>

**Say this first.** Machine clocks drift and are only synchronised to within milliseconds by
NTP, which can also step them backwards. A skew smaller than the gap between two related
events is enough to put an effect before its cause.

**Then explain.**
- Lamport clocks give every event a counter such that if *a* could have caused *b*,
  L(*a*) < L(*b*).
- Vector clocks keep one counter per node and can tell "happened before" apart from
  "concurrent" — needed to detect conflicting writes.
- Hybrid logical clocks combine physical time with a logical counter: causal like Lamport,
  and close to wall time.
- Spanner's TrueTime bounds clock uncertainty with GPS and atomic clocks and waits it out on
  commit.

**Next follow-up: "What clock should you use to measure a timeout?"** A monotonic clock, which
never goes backwards. Wall-clock time can jump during an NTP correction.

**Go deeper.** `15` §3.

</details>

### Q11.3 · L5 — What exactly does "linearizable" mean, and how is it different from "serializable"?

<details>
<summary>Open the answer</summary>

**Say this first.** Linearizable: each operation on an object appears to take effect at one
instant between its start and its end, so the system behaves like a single copy and never
shows a value older than one already returned. Serializable: concurrent multi-object
transactions have the same result as some serial order, which need not respect real time.

**Then explain.**
- A read that starts after a write has completed must see it; a read overlapping the write
  may see either value; once any client has seen the new value, no later read may return the
  old one.
- Lagging replicas break linearizability even though every replica is "correct."
- The two properties are independent; strict serializability (Spanner's external
  consistency) is both.
- Linearizability requires coordination — a majority must be reachable — so it can't stay
  available in a partition.

**Next follow-up: "Is R + W > N linearizable?"** No. Quorum overlap guarantees a read sees the
latest *completed* write, but concurrent writes, partially failed writes and sloppy quorums
can still produce a "new, then old" history.

**Go deeper.** `15` §4–§5; the brute-force checker in §4.

</details>

### Q11.4 · L5 — Walk through how Raft elects a leader and commits a write. What stops a stale node from becoming leader?

<details>
<summary>Open the answer</summary>

**Say this first.** A follower that hears nothing from a leader for a randomised timeout
starts an election in a new term and asks for votes; a majority makes it leader. The leader
appends writes to its log and replicates them; an entry is committed once a majority has
stored it. A node only votes for a candidate whose log is at least as up to date as its own,
so a node missing committed entries can't win.

**Then explain.**
- Terms act as logical clocks for leadership: any higher term makes a node step down.
- Randomised timeouts make split votes rare.
- `AppendEntries` carries the previous entry's index and term; followers reject mismatches and
  the leader backs up until logs agree, then overwrites the follower's conflicting suffix.
- A leader only counts replicas for entries from its own term; earlier entries commit
  indirectly. Removing that rule in `15` §6's fuzzing broke safety in 1 of 2,000 schedules —
  rare, but real.

**Next follow-up: "The old leader is partitioned with a minority. What happens to writes sent
to it?"** They're appended but never committed, because it can't reach a majority. When the
partition heals, it sees a higher term, steps down, and those entries are overwritten. Clients
must treat unacknowledged writes as unknown and retry idempotently.

**Go deeper.** `15` §6 and the Raft lab.

</details>

### Q11.5 · L5 — A job must run exactly once across a cluster of workers. How do you guarantee it?

<details>
<summary>Open the answer</summary>

**Say this first.** You can't guarantee exactly-once *execution* over an unreliable network,
but you can guarantee exactly-once *effect*: make the job's effect idempotent (keyed by the
job ID, applied with a conditional write), and use a lease with a fencing token so a worker
that lost its lease can't commit.

**Then explain.**
- A lease alone is not enough: a worker can pause (GC, VM migration) past its expiry and
  wake up still believing it holds the lease.
- The fencing token increases with each grant, and the resource rejects writes carrying an
  older token than it has seen.
- If the resource can't check tokens, use compare-and-swap on a state field ("PENDING →
  DONE, only if still PENDING").
- Retries with the same job ID are then harmless.

**Next follow-up: "Kafka says it's exactly-once. Isn't that enough?"** Only within Kafka:
idempotent producers and transactions cover writes to Kafka and consumer offsets. A consumer
that calls an external API needs its own idempotency there.

**Go deeper.** `15` §7–§8.

</details>

### Q11.6 · L6+ — When would you choose CRDTs over consensus for replicated state?

<details>
<summary>Open the answer</summary>

**Say this first.** When every replica must accept writes even while disconnected —
offline-first apps, collaborative editing, multi-region active-active counters — and the
data has a well-defined merge. Use consensus when you must enforce a global invariant such as
uniqueness or "balance never below zero."

**Then explain.**
- CRDT merges are commutative, associative and idempotent, so replicas converge whatever the
  order and number of merges, with no coordination on the write path.
- Consensus needs a majority on every write: strong guarantees, but cross-region latency and
  unavailability for the minority side of a partition.
- CRDT metadata (tags, tombstones, per-replica counters) grows and needs garbage collection;
  and some intents don't merge meaningfully.
- Hybrid designs are common: CRDTs for collaborative content, consensus for permissions,
  billing and identity.

**Next follow-up: "Why not just last-writer-wins?"** LWW silently discards one of two
concurrent updates and depends on clock accuracy; it's acceptable only when losing a
concurrent update is fine.

**Go deeper.** `15` §10 and [Real-Time Communication and Collaboration](../SystemDesign/building_blocks/22_realtime_and_collaboration.md).

</details>

## Keep Going

- Missed a question? Its **Go deeper** line names the section and lab. Reread it, then
  retest the question cold in a day.
- For system design questions — scaling, caching, sharding, queues, multi-region — use
  the matching bank in the System Design module ([System Design Interview Question Bank](../SystemDesign/07_interview_question_bank.md)).
- For coding-round execution and follow-ups, pair this bank with `09` and `10`.

## What Each Engineering Level Should Know

| Level | What this chapter should give you |
|---|---|
| **L3 · Junior** | Solid, correct one-paragraph answers to every L3 question and most L4 ones, each with an example |
| **L4 · Mid** | The mechanism behind every L4 question, the common bug, and a clean answer to each follow-up |
| **L5 · Senior** | Numbers, failure modes and alternatives for every L5 question, volunteered before being asked |
| **L6+ · Staff** | A structured plan for every L6 question: measure first, cheapest fix first, costs and migration named |

## Interview checklist

- [ ] I can answer every question in my target level's tag, out loud, in under two minutes.
- [ ] I can answer the follow-up for each without looking.
- [ ] I end answers with a trade-off sentence: what I chose, what it costs, why that's acceptable.
- [ ] I can do every row of the rapid-fire table in one sentence.
- [ ] I have retested my missed questions after 1, 3 and 10 days.

Related: every other chapter in this module · [System Design Interview Question Bank](../SystemDesign/07_interview_question_bank.md) · [Google Interview Master Study Plan (L5 / Senior SWE)](../GOOGLE_INTERVIEW_PREP.md)
