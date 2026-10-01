# Back-of-the-Envelope Estimation

An estimate in a design interview has one job: to force a decision. "12,000 writes per second at peak" is only useful if the next sentence is "…which is more than one relational primary comfortably takes, so we partition the write path." This file gives you the arithmetic toolkit, the method, the numbers to carry in your head, and worked examples you can reproduce in under four minutes. It then checks those numbers against measurements: what one core does per second, Little's law and the utilisation curve, how percentiles combine, and how big records really are on disk, followed by a third worked example and practice drills.

> 💡 Precision is not the goal. Being within a factor of 2–3 is plenty, because design decisions change at factors of 10: one machine vs a cluster, a database vs object storage, a single region vs a CDN.

## Foundations — The Arithmetic Toolkit

### Work in powers of ten

Write every number as a mantissa times a power of ten, round the mantissa to one digit, then
multiply mantissas and add exponents:

```text
500 million users × 30 views/day ÷ 86,400 s/day
= (5 × 10⁸) × (3 × 10¹) ÷ (~1 × 10⁵)
= 15 × 10⁹⁻⁵ = 15 × 10⁴ ≈ 150,000 views/s
```

Rounding 86,400 to 10⁵ makes the answer about 15% low, which is fine: estimates only need to be
within a factor of 2–3. Round in whichever direction keeps the arithmetic easy, and when several
roundings go the same way, correct at the end.

### Conversions to carry

| Quantity | Value | Handy form |
|---|---|---|
| Seconds per day | 86,400 | ≈ 10⁵ (1M per day ≈ 12 per second) |
| Seconds per month | ≈ 2.6 million | ≈ 2.5 × 10⁶ (1M per month ≈ 0.4 per second) |
| Seconds per year | ≈ 31.5 million | ≈ π × 10⁷ |
| Bits per byte | 8 | 1 Gbps ≈ 125 MB/s; 10 Gbps ≈ 1.25 GB/s |
| KB → MB → GB → TB → PB | × 1,000 each (× 1,024 for KiB, MiB, ...) | The 2.4% (KiB) to 12.6% (PiB) difference never matters in an estimate |
| Requests/s × payload | Bandwidth | 10,000/s × 100 KB = 1 GB/s = 8 Gbps |
| Requests/s × latency | Requests in flight (Little's law, below) | 10,000/s × 0.2 s = 2,000 concurrent |

### Break a big unknown into small knowns

Estimation is Fermi decomposition: an unknown quantity ("how much storage?") becomes a product of
quantities you can guess ("users × uploads per user per day × bytes per upload × days kept ×
copies"). Each factor may be off by 2×, but the errors partly cancel, and more importantly each
factor is visible, so the interviewer can challenge one assumption without discarding the rest.

### Vocabulary

| Term | Meaning |
|---|---|
| DAU / MAU | Daily / monthly active users; DAU ÷ MAU (often 20–50%) is "stickiness" |
| QPS / RPS | Queries or requests per second |
| Peak factor | Peak rate ÷ average rate over a day |
| Read:write ratio | How many reads each write gets; drives caching and replicas |
| Fan-out / amplification | Internal operations caused by one external request |
| Working set / hot set | The data actually touched in a period, which is what must fit in memory |
| Utilisation | Busy time ÷ total time for a resource |
| Headroom | Spare capacity kept for failures, deploys and growth |
| Little's law | Items in a system = arrival rate × time each spends in it |

## Why estimate at all

| Question the numbers answer | Decision it drives |
|---|---|
| Does the write rate fit on one primary? | Single database vs sharding / write-optimised store. |
| Is the read:write ratio skewed? | Caching and read replicas vs a balanced design. |
| Does the dataset fit in memory? | Cache the whole hot set vs cache selectively. |
| How big does storage get over the retention period? | Database vs object storage; tiering; erasure coding. |
| How much bandwidth leaves the origin? | Whether a CDN is required rather than nice to have. |
| How many servers at peak, with a zone down? | Capacity plan and cost ballpark. |

## The method

1. **State the assumptions** out loud: daily active users, actions per user, object size, retention, replication. Round them.
2. **Convert per day to per second**: divide by 86,400 ≈ 10⁵. One million events a day is about 12 per second.
3. **Apply a peak factor**: 2–3× for most consumer products, 5–10× for event-driven spikes (ticket sales, sports, launches).
4. **Multiply out storage and bandwidth**, including replication and retention.
5. **Say the consequence** of each number, then move on. The whole thing should take 3–4 minutes.

Use the estimator to practise: set a preset, estimate in your head first, then check.

```arch
%% caption: The estimation workflow moves from business assumptions to system constraints, culminating in an architectural decision.
route straight
grid 200x100
node assum "1. Assumptions" at 0,0 icon=user shape=card color=blue sub="DAU, actions"
node req "2. Per-second rate" at 0,1 icon=metrics shape=card color=amber sub="RPS / QPS"
node peak "3. Peak factor" at 0,2 icon=timer shape=card color=red sub="x2 or x3 multiplier"
node store "4. Storage & IO" at 0,3 icon=db shape=card color=slate sub="size x time"
node dec "5. Arch Decision" at 0,4 icon=app shape=card color=green sub="implications"

assum -> req
req -> peak
peak -> store
store -> dec
```

## Latency numbers and tail latency

Memorise the orders of magnitude, not the digits. The ratios are what matter: memory is roughly 1,000× faster than an SSD random read, a datacenter round trip is 300× faster than crossing an ocean.

| Operation | Approximate time |
|---|---|
| L1 cache reference | 0.5 ns |
| Branch mispredict | 5 ns |
| Mutex lock/unlock | 25 ns |
| Main memory reference | 100 ns |
| Transmit 1 KB on a 10 Gbps link (serialization time only) | ~0.8 µs (~8 µs at 1 Gbps) |
| Compress 1 KB with a fast codec | 2–10 µs |
| Read 4 KB randomly from an SSD | 20–150 µs |
| Read 1 MB sequentially from memory | 250 µs |
| Round trip within one datacenter | 500 µs |
| Read 1 MB sequentially from an SSD | ~1 ms |
| HDD seek | 10 ms |
| Read 1 MB sequentially from an HDD | 20 ms |
| Round trip across a continent | 50–80 ms |
| Round trip California ↔ Europe | 150 ms |

The wire row is pure transmission time: `1 KB × 8 bits ÷ 10 Gbps ≈ 0.8 µs`. A real small send also pays for the kernel network stack, the NIC, switch hops and any queueing, which is why the round trip *within* one datacenter is closer to 500 µs than to 1 µs. Confusing wire time with a completed request under-estimates network cost by two to three orders of magnitude.

Averages hide the tail. When one user request fans out to many servers and waits for all of them, the slowest server decides the latency. If each server has a 1% chance of being slow, a request touching 100 servers hits at least one slow server 63% of the time: `1 − 0.99¹⁰⁰ ≈ 0.63`. That is why search and feed backends care about per-server p99, and use hedged requests and partial results.

## Powers of two and data sizes

| Power | Value | Rule of thumb |
|---|---|---|
| 2¹⁰ | ~1 thousand | KB |
| 2²⁰ | ~1 million | MB |
| 2³⁰ | ~1 billion | GB |
| 2⁴⁰ | ~1 trillion | TB |
| 2⁵⁰ | ~1 quadrillion | PB |

| Thing | Typical size |
|---|---|
| A UUID / 128-bit ID | 16 bytes (36 as text) |
| A 64-bit integer or timestamp | 8 bytes |
| A tweet-sized text post with metadata | 0.5–2 KB |
| A row in a typical OLTP table | 0.2–1 KB |
| A compressed phone photo | 1–3 MB |
| One minute of 1080p video (streaming bitrate, ~5–8 Mbps) | ~40–60 MB |
| An embedding vector (768 float32) | ~3 KB |

## Availability and the nines

| Target | Downtime per year | Per 30 days | What it usually implies |
|---|---|---|---|
| 99% | 3.65 days | 7.2 h | One region, manual recovery is tolerable. |
| 99.9% | 8.8 h | 43 min | Redundant instances, automated failover within a region. |
| 99.99% | 53 min | 4.3 min | Multi-zone everything, no single-writer bottleneck without fast failover, careful deploys. |
| 99.999% | 5.3 min | 26 s | Multi-region active-active, extensive automation — very expensive. |

Components in series multiply availability; components in parallel (with independent failures) combine as `1 − (1 − a)ⁿ`. Two independent replicas at 99% give 99.99% — but only if they don't share a failure domain.

## Worked example: a photo-sharing app

Assumptions: 500M DAU, each uploads 0.2 photos and views 30 photos a day, 2 MB per photo, keep forever (plan 10 years), 3 copies.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Upload QPS | 500M × 0.2 ÷ 10⁵ | ~1,000/s, peak ~3,000/s | Uploads go directly to object storage with presigned URLs; the API only writes metadata. |
| View QPS | 500M × 30 ÷ 10⁵ | ~150,000/s, peak ~450,000/s | Read-heavy at 150:1 — a CDN serves image bytes; the metadata path needs caching. |
| New storage/day | 100M photos × 2 MB | 200 TB/day | Object storage with lifecycle tiers; not a database. |
| 10-year storage | 200 TB × 3,650 × 3 | ~2 EB | At this size, erasure coding instead of 3× replication saves roughly half. |
| Egress | 150,000/s × 2 MB × 8 bits | ~2.4 Tbps average, ~7 Tbps at the 3× peak | CDN is mandatory; origin serves only cache misses. |
| Metadata store | 100M rows/day × 1 KB × 3,650 | ~365 TB before replication | Sharded metadata store, partitioned by photo ID or owner. |

## Worked example: a chat service

Assumptions: 1B DAU, 40 messages sent per user per day, 1 KB per message with metadata, 3-year retention, 3 copies.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Message QPS | 1B × 40 ÷ 10⁵ | ~400,000/s, peak ~1.2M/s at 3× | Partition by conversation; single ordered log per conversation, not a global order. |
| Storage | 40B msgs/day × 1 KB = 40 TB/day; × 365 = 14.6 PB/yr raw; × 3 years × 3 copies | ~15 PB/yr raw, ~44 PB raw over retention, ~130 PB replicated | Ingest is modest (40 TB/day ÷ 86,400 ≈ 0.5 GB/s), but the retained volume is not: shard a wide-column or log-structured store by conversation ID, tier old messages to cold storage, and use erasure coding (~1.5× instead of 3×, so ~66 PB) for the cold tier. Also question whether every user needs 3 years online. |
| Concurrent connections | say 30% of DAU online: 1B × 0.3 | ~300M WebSockets | Assuming ~100K connections per gateway host: 300M ÷ 100K = ~3,000 gateway servers, plus headroom. |

## Capacity: servers, cache, and headroom

- **Servers** = peak QPS ÷ per-server QPS. Measure or assume: a stateless API server doing a few database calls handles hundreds to low thousands of requests per second; a cache node handles 100K+ simple gets per second.
- **Headroom**: with three zones, losing one leaves two carrying the load, so utilisation `u` becomes `u × 3/2` on the survivors. At 60% that is 90%, at 70% it is 105% (overload), so plan for roughly 50–60% average utilisation before you also allow for a deploy in flight.
- **Cache size**: if 20% of items receive 80% of reads, caching the daily read set's hot 20% (item size × count) captures most of the benefit. If that is more memory than is sensible, cache small things (IDs, metadata, rendered fragments) instead of whole objects.
- **Queues**: a queue does not create capacity, it only buys time. If producers run faster than consumers for an hour, the backlog must fit, and the drain time must be acceptable.

## Common estimation mistakes

1. Forgetting the peak factor, then sizing for the average.
2. Forgetting replication (×3) and retention (×years) in storage.
3. Mixing bits and bytes in bandwidth (×8).
4. Computing numbers and never saying what they imply.
5. Estimating everything. Pick the 3–4 numbers that drive decisions for *this* problem.
6. False precision: "11,574 requests per second" — say "about 12K".

## What one core does, measured

"How many servers?" needs a per-server throughput, and that comes from the cost of the work each
request does. Some common operations, timed on the machine that built this page:

```python
"""What does one core do per second? Timing common server-side operations on
this machine, then turning the slowest into a server count. Python adds
overhead to the cheap operations; the expensive ones are C underneath."""
import hashlib, json, os, socket, sqlite3, threading, time, zlib

def per_op(fn, seconds=0.3):
    n, t0 = 0, time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        fn(); n += 1
    return (time.perf_counter() - t0) / n

doc = {"id": 123456789, "user": "user_42", "text": "x" * 800, "tags": ["a", "b"], "likes": 17}
blob = json.dumps(doc).encode()
mb = os.urandom(1 << 20)
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
db.executemany("INSERT INTO t VALUES (?, ?)", ((i, "v") for i in range(1_000_000)))

srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen()
def echo():
    c, _ = srv.accept()
    while (d := c.recv(64)):
        c.sendall(d)
threading.Thread(target=echo, daemon=True).start()
cli = socket.create_connection(srv.getsockname())
cli.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
def rtt():
    cli.sendall(b"x"); cli.recv(64)

ops = [
    ("parse a 1 KB JSON document",             lambda: json.loads(blob)),
    ("gzip-compress 1 KB (level 6)",           lambda: zlib.compress(blob, 6)),
    ("SHA-256 of 1 KB",                        lambda: hashlib.sha256(blob).digest()),
    ("SHA-256 of 1 MB",                        lambda: hashlib.sha256(mb).digest()),
    ("copy 1 MB in memory",                    lambda: bytearray(mb)),
    ("indexed lookup in a 1M-row SQLite table", lambda: db.execute("SELECT v FROM t WHERE id = 777777").fetchone()),
    ("TCP round trip over loopback",           rtt),
    ("scrypt password hash (n=2^14, r=8)",     lambda: hashlib.scrypt(b"hunter2", salt=b"s" * 16, n=2**14, r=8, p=1)),
]
print(f"  {'operation':42} {'time':>10} {'per core per s':>15}")
costs = {}
for name, fn in ops:
    t = per_op(fn)
    costs[name] = t
    unit = f"{t * 1e6:8.1f} µs" if t < 1e-3 else f"{t * 1e3:8.1f} ms"
    print(f"  {name:42} {unit:>10} {1 / t:15,.0f}")

t = costs["scrypt password hash (n=2^14, r=8)"]
print(f"\nPeak of 5,000 logins/s x {t * 1e3:.0f} ms of scrypt each = {5000 * t:,.0f} cores busy hashing alone")
print(f"At 50% target utilisation on 16-core servers: {5000 * t / 0.5 / 16:,.0f} servers")
```

```text
  operation                                        time  per core per s
  parse a 1 KB JSON document                      4.6 µs         215,162
  gzip-compress 1 KB (level 6)                   56.4 µs          17,732
  SHA-256 of 1 KB                                 3.1 µs         326,751
  SHA-256 of 1 MB                                 2.9 ms             341
  copy 1 MB in memory                            63.7 µs          15,702
  indexed lookup in a 1M-row SQLite table         1.9 µs         518,955
  TCP round trip over loopback                   65.2 µs          15,343
  scrypt password hash (n=2^14, r=8)             47.7 ms              21

Peak of 5,000 logins/s x 48 ms of scrypt each = 238 cores busy hashing alone
At 50% target utilisation on 16-core servers: 30 servers
```

Your machine will give different numbers. Treat the output as orders of magnitude, which is how
estimates use them:

- **Cheap work is microseconds.** Parsing a small JSON document, hashing a kilobyte, or looking a
  row up in memory costs a few microseconds: hundreds of thousands per core per second. A typical
  API request does dozens of these, so its CPU cost is 0.1–1 ms, and a core serves roughly
  1,000–10,000 such requests a second.
- **Fixed costs dominate small inputs.** Compressing 1 KB costs far more per byte than hashing it,
  because the compressor sets up its state on every call. Batch small items before compressing,
  encrypting or sending them.
- **A network round trip is much more than a local function call**, even over loopback. Between
  machines in a datacenter it is typically 0.1–0.5 ms, which is why the number of calls per
  request matters more than their size (the N+1 section of [API Design — High Level](03_api_design_high_level.md)).
- **Some operations are slow on purpose.** A password hash is designed to take tens of
  milliseconds so that stolen hashes can't be brute-forced quickly. At 5,000 logins a second that
  one operation needs hundreds of cores. This is the kind of number that changes a design: a
  dedicated, separately scaled authentication tier, and session tokens so that a password is
  checked once per login, not once per request.

The general method: find the most expensive operation per request, measure or estimate its cost,
and divide. `servers = peak requests/s × CPU-seconds per request ÷ (cores per server × target
utilisation)`.

## Little's law and utilisation, measured

**Little's law**: the average number of items in a system equals the arrival rate times the
average time each item spends inside, `L = λ × W`. It holds for any stable system (queues,
thread pools, connection pools, warehouses), whatever happens inside. The simulation measures the
two sides independently: W from each request's timing, L by counting requests inside at random
moments:

```python
"""A service with 8 workers; each request needs 50 ms of work on average
(exponentially distributed), so capacity is 160 requests/s. Requests arrive at
random. For each arrival rate, measure the average time a request spends inside
(W) and, separately, the number of requests inside at 20,000 random instants (L).
Little's law says L = arrival rate x W, whatever the service does inside."""
import bisect, heapq, random

WORKERS, MEAN_S, N = 8, 0.050, 200_000


def run(rate, seed=5):
    rng = random.Random(seed)
    free = [0.0] * WORKERS                       # when each worker is next free
    t, arrivals, departures = 0.0, [], []
    for _ in range(N):
        t += rng.expovariate(rate)
        start = max(t, heapq.heappop(free))      # first-come first-served
        done = start + rng.expovariate(1 / MEAN_S)
        heapq.heappush(free, done)
        arrivals.append(t)
        departures.append(done)
    times = sorted(d - a for a, d in zip(arrivals, departures))
    W = sum(times) / N
    departures.sort()
    probes = [rng.uniform(arrivals[1000], arrivals[-1000]) for _ in range(20_000)]
    L = sum(bisect.bisect(arrivals, p) - bisect.bisect(departures, p) for p in probes) / len(probes)
    return L, W, times[int(0.99 * N)]


print(f"  {'load':>5} {'arrivals/s':>10} {'W avg':>9} {'rate x W':>9} {'L sampled':>10} {'p99':>8}")
for util in (0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
    rate = util * WORKERS / MEAN_S
    L, W, p99 = run(rate)
    print(f"  {util:5.0%} {rate:10.0f} {W * 1000:7.1f}ms {rate * W:9.2f} {L:10.2f} {p99 * 1000:6.0f}ms")
```

```text
   load arrivals/s     W avg  rate x W  L sampled      p99
    30%         48    49.9ms      2.39       2.39    231ms
    50%         80    50.5ms      4.04       4.04    232ms
    60%         96    51.9ms      4.98       4.97    234ms
    70%        112    55.1ms      6.17       6.15    239ms
    80%        128    63.2ms      8.09       8.05    256ms
    90%        144    90.5ms     13.03      12.99    335ms
    95%        152   143.7ms     21.85      21.89    552ms
```

The two columns agree at every load, so Little's law can be used in both directions:

- **Concurrency from rate and latency.** 10,000 requests/s at 200 ms each means about 2,000
  requests in flight, so 2,000 threads, or 2,000 connections, or an async server.
- **Pool sizes.** A service making 3,000 database queries/s at 5 ms each has 15 queries in flight on
  average, so a pool of 30–50 connections is plenty; a pool of 500 only adds load to the database.
- **Queues.** A queue with 60,000 messages and consumers completing 1,000/s means a new message
  waits about 60 s.

The p99 column shows why capacity plans target 50–70% utilisation. Up to about 70% the average
latency is close to the 50 ms of work. At 90% it nearly doubles, and at 95% it nearly triples,
because a random arrival increasingly finds every worker busy. With fewer workers (or one) the
curve bends even earlier. The next 10% of load costs far more latency than the previous 10%, and
that is also the headroom that absorbs a zone failure or a deploy
([Scaling and Load Balancing](13_scaling_and_load_balancing.md)).

## Percentiles don't average and don't add, measured

Latency budgets are built from percentiles, and percentiles combine in ways that surprise people:

```python
"""Percentiles don't average and don't add. Latencies are log-normal (a common
shape: most requests near the median, a long slow tail)."""
import random, statistics

rng = random.Random(11)

def p(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]

def call(median_ms):
    return rng.lognormvariate(0, 0.6) * median_ms

# 1. Ten servers behind a load balancer, one of them slow.
servers = [[call(60 if s == 0 else 20) for _ in range(20_000)] for s in range(10)]
avg_of_p99 = statistics.mean(p(x, 0.99) for x in servers)
true_p99 = p([v for x in servers for v in x], 0.99)
print("1. Ten servers, one three times slower")
print(f"   average of the ten per-server p99s {avg_of_p99:6.1f} ms")
print(f"   real p99 of all requests           {true_p99:6.1f} ms")

# 2. Two calls in sequence: A then B.
a = [call(20) for _ in range(200_000)]
b = [call(20) for _ in range(200_000)]
both = [x + y for x, y in zip(a, b)]
print("\n2. Two independent calls in sequence")
print(f"   p99(A) + p99(B)  {p(a, 0.99) + p(b, 0.99):6.1f} ms   (a safe upper bound)")
print(f"   p99(A + B)       {p(both, 0.99):6.1f} ms")
print(f"   p50(A) + p50(B)  {p(a, 0.5) + p(b, 0.5):6.1f} ms   p50(A + B) {p(both, 0.5):6.1f} ms")

# 3. One call fanned out to N backends in parallel, waiting for all of them.
print("\n3. Fan-out: wait for the slowest of N parallel calls")
single = [call(20) for _ in range(200_000)]
print(f"   one call: p50 {p(single, 0.5):5.1f} ms  p99 {p(single, 0.99):5.1f} ms  p99.9 {p(single, 0.999):5.1f} ms")
for n in (10, 100):
    fan = [max(call(20) for _ in range(n)) for _ in range(20_000)]
    print(f"   N = {n:3}:  p50 {p(fan, 0.5):5.1f} ms  p99 {p(fan, 0.99):5.1f} ms")
```

```text
1. Ten servers, one three times slower
   average of the ten per-server p99s   97.3 ms
   real p99 of all requests            133.0 ms

2. Two independent calls in sequence
   p99(A) + p99(B)   160.9 ms   (a safe upper bound)
   p99(A + B)        121.4 ms
   p50(A) + p50(B)    40.0 ms   p50(A + B)   43.4 ms

3. Fan-out: wait for the slowest of N parallel calls
   one call: p50  20.0 ms  p99  81.1 ms  p99.9 125.9 ms
   N =  10:  p50  49.3 ms  p99 131.4 ms
   N = 100:  p50  87.6 ms  p99 185.7 ms
```

1. **Don't average percentiles.** A dashboard showing the average of per-server p99s reported
   97 ms while the real p99 of the traffic was 133 ms, because the slow server contributes most of
   the slowest requests. Compute percentiles from merged data or mergeable histograms.
2. **Sequential calls: the p99s over-add.** Two slow tails rarely coincide, so p99(A + B) is well
   below p99(A) + p99(B). Adding p99s gives a safe, pessimistic budget; the medians add almost
   exactly.
3. **Parallel calls: the slowest one decides.** Waiting for 10 calls turns a 20 ms median into
   about 50 ms; waiting for 100 turns it into about 90 ms, close to a single call's p99. In a fan-out,
   the backend's tail becomes the user's median.

For a latency budget, start from the user-facing target (say p99 300 ms), subtract network and
rendering, and give each dependency a budget at the percentile that matters for its position: a
fan-out leaf needs a much tighter tail than a single sequential call.

## How big data really is, measured

The size table above gives typical sizes. What a record costs on disk depends on encoding,
indexes and compression:

```python
"""How big is a record really? One social-media post, stored four ways, and a
day of access logs compressed. Payload: 8-byte id, 8-byte author, 8-byte
timestamp, and 140 characters of text = 164 bytes of actual information."""
import json, os, random, sqlite3, struct, tempfile, zlib

rng = random.Random(2)
words = "the a system design cache queue shard replica user post photo like share".split()

def text():
    return " ".join(rng.choice(words) for _ in range(40))[:140].ljust(140)

post = {"id": 1790758747123456789, "author_id": 4411223344, "created_at": "2026-09-30T10:15:02Z",
        "text": text(), "like_count": 0, "reply_count": 0, "visibility": "public"}
as_json = json.dumps(post).encode()
packed = struct.pack("<qqq", post["id"], post["author_id"], 1790758502) + post["text"].encode()
print(f"one post as JSON           {len(as_json):5} bytes")
print(f"one post, packed binary    {len(packed):5} bytes")

path = os.path.join(tempfile.mkdtemp(), "posts.db")
db = sqlite3.connect(path)
db.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, author INTEGER, created INTEGER, text TEXT)")
ROWS = 200_000
db.executemany("INSERT INTO posts VALUES (?, ?, ?, ?)",
               ((i, rng.randrange(10**9), 1790000000 + i, text()) for i in range(ROWS)))
db.commit()
base = os.path.getsize(path)
db.execute("CREATE INDEX by_author ON posts (author, created)")
db.commit()
print(f"in SQLite, per row         {base / ROWS:5.0f} bytes")
print(f"  + index (author, created){(os.path.getsize(path) - base) / ROWS:4.0f} bytes more per row")


lines = []
for i in range(50_000):
    lines.append(json.dumps({"ts": f"2026-09-30T10:{i // 1000 % 60:02}:{i % 60:02}.{i % 1000:03}Z",
                             "method": rng.choice(["GET", "GET", "GET", "POST"]),
                             "path": f"/v1/posts/{rng.randrange(10**6)}",
                             "status": rng.choice([200] * 20 + [404, 500]),
                             "ms": round(rng.lognormvariate(3, 0.6), 1),
                             "ua": rng.choice(["ios/7.2", "android/7.1", "web/chrome"])}))
raw = "\n".join(lines).encode()
print(f"\naccess log: {len(raw) / len(lines):.0f} bytes per line; "
      f"gzip -6 compresses it {len(raw) / len(zlib.compress(raw, 6)):.1f}x")
```

```text
one post as JSON             301 bytes
one post, packed binary      164 bytes
in SQLite, per row           164 bytes
  + index (author, created)  18 bytes more per row

access log: 126 bytes per line; gzip -6 compresses it 9.4x
```

- **JSON nearly doubles the information** (301 bytes for 164 bytes of data) because every record
  repeats its field names and writes numbers as text. APIs and logs pay this; storage engines
  and binary formats (Protobuf, Avro, Parquet) mostly don't.
- **A database row is roughly its data plus overhead**, and every index adds more. SQLite is
  compact; PostgreSQL adds about 28 bytes of header per row, and most OLTP tables carry several
  indexes. A safe estimate is 1.5–2× the raw fields, then × replicas.
- **Logs compress very well** (about 9× here) because lines repeat structure. Log and metrics
  storage estimates should use compressed sizes, but ingest bandwidth and CPU use the raw ones.

## Worked example: a logging pipeline

Assumptions: 10,000 servers, each writing 100 log lines a second, about 126 bytes per line (as
measured above), searchable for 30 days, 3 replicas, 9× compression.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Lines per second | 10⁴ × 10² | 1M/s | A partitioned log (Kafka) in front, not direct writes to the search index |
| Raw ingest | 1M/s × 126 B | ~126 MB/s ≈ 1 Gbps; ~11 TB/day | Collectors batch and compress before sending |
| Log partitions | 126 MB/s ÷ ~10 MB/s per partition | ~13, so provision 32–64 | Headroom for spikes and per-consumer parallelism |
| Stored, compressed | 11 TB/day ÷ 9 × 30 days × 3 | ~110 TB | Fits a mid-sized search cluster; hot/warm tiers for older days |
| Index cost | Full-text indexing can double stored size | ~220 TB if everything is indexed | Index only structured fields plus message text; drop or sample debug logs |
| Archive | 11 TB/day ÷ 9 × 365 | ~450 TB/year in object storage | Cheap, queried rarely with a batch engine |

The design follows from the table: agents batch and compress, a partitioned log absorbs bursts,
indexers consume at their own pace, 30 days stay searchable, and everything goes to object storage
for a year. The biggest cost lever is not hardware but **volume**: sampling debug logs by 10× saves
more than any storage optimisation.

## Practice drills

Estimate each one in your head (2–3 minutes), then open the answer.

<details>
<summary>1. A URL shortener creates 100 million links a month and each link is read 100 times. Read rate, and storage for 10 years?</summary>

Writes: 10⁸ ÷ 2.5 × 10⁶ s ≈ 40/s. Reads: 100× that ≈ 4,000/s, maybe 12,000/s at peak. Storage:
10⁸ × 12 months × 10 years = 1.2 × 10¹⁰ links × ~500 bytes ≈ 6 TB, ×3 replicas ≈ 18 TB.
**So:** reads fit easily behind a cache; storage fits a modestly sharded key-value store; the
7-character base-62 key space (3.5 × 10¹²) is 300× larger than needed.

</details>

<details>
<summary>2. A video site has 5 million concurrent viewers at 5 Mbps. Egress bandwidth?</summary>

5 × 10⁶ × 5 × 10⁶ bits/s = 2.5 × 10¹³ = 25 Tbps. **So:** only a CDN (many providers, or your own
edge caches inside ISPs) can serve that; origin bandwidth must be a small fraction via a high cache
hit rate.

</details>

<details>
<summary>3. A service takes 20,000 requests/s at 150 ms average latency. How many requests are in flight, and how many threads with one thread per request?</summary>

Little's law: 20,000 × 0.15 = 3,000 in flight. With 200 threads per instance at 70% utilisation,
about 3,000 ÷ 140 ≈ 22 instances. **So:** latency, not CPU, may decide the instance count;
reducing latency by a third cuts the instances too (or use async I/O).

</details>

<details>
<summary>4. Does the hot set of 300 million user profiles at 2 KB each fit in a cache?</summary>

3 × 10⁸ × 2 × 10³ = 6 × 10¹¹ B = 600 GB. If 20% are active daily, 120 GB. **So:** the hot set fits
on a handful of cache nodes (with replication); caching all profiles needs a cluster of ~10 large
nodes, which may still be reasonable.

</details>

<details>
<summary>5. Three services in series each have 99.95% availability. What does the caller see, and what must change for 99.99%?</summary>

0.9995³ ≈ 99.85%, about 13 hours of downtime a year. For 99.99% you can't get there by chaining:
remove dependencies from the critical path (cache, degrade gracefully, go asynchronous) or make each
one redundant across independent failure domains.

</details>

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Rates and sizes** | Converts per day to per second; includes peak factor | Estimates QPS, storage, bandwidth and memory in under 4 minutes, and states the design consequence of each | Uses estimates to rule designs in or out early, and checks them against production data |
| **Capacity** | Divides QPS by per-server throughput | Uses per-request cost, Little's law and target utilisation; plans headroom for a zone loss | Owns fleet capacity and cost models; knows which resource saturates first |
| **Latency** | Knows the latency table | Builds latency budgets; knows percentiles don't average and fan-out amplifies tails | Sets SLOs across services and designs to meet them (hedging, partial results) |
| **Judgment** | Estimates everything | Picks the 3–4 numbers that decide the design | Spots an assumption that is off by 10× and says what it changes |

## Interview checklist

- [ ] I can do powers-of-ten arithmetic quickly and know the conversions (seconds per day, bits vs bytes).
- [ ] I can estimate QPS, peak, storage with replication and retention, bandwidth, and memory for a hot set.
- [ ] I can turn per-request CPU cost into a server count at a target utilisation.
- [ ] I can apply Little's law to concurrency, pool sizes and queue delays.
- [ ] I can explain why utilisation above about 70% raises latency sharply.
- [ ] I can explain why percentiles can't be averaged, and how sequential and parallel calls combine.
- [ ] I can estimate real record sizes including encoding, indexes, replicas and compression.
- [ ] I state the design consequence of every number, and skip numbers that don't change the design.

## Related building blocks

- [Scaling and Load Balancing](13_scaling_and_load_balancing.md)
- [Observability and Reliability](15_observability_and_reliability.md)
- [Decision Framework](17_decision_framework.md)
- [API Design — High Level](03_api_design_high_level.md)
- [Object Storage](08_object_storage.md)
- [Google L5 System Design Playbook](../00_google_l5_playbook.md)
