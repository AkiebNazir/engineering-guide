# Distributed Systems Fundamentals — Failure, Time, and Agreement

A distributed system is one in which "the failure of a computer you didn't even know
existed can render your own computer unusable" (Leslie Lamport). The moment a program
runs on more than one machine, three things you took for granted disappear: a shared
memory, a shared clock, and the ability to tell a crashed machine from a slow one. This
chapter starts from first principles — why systems are distributed at all, what the
standard assumptions are, and what is provably impossible — then goes as deep as a
Senior or Staff interview goes: failure detectors and their trade-off, logical and
hybrid clocks, what linearizability precisely means (with a checker you can run),
quorums, a complete Raft implementation you can run, break and fuzz, leases and fencing
tokens, exactly-once delivery, gossip, and CRDTs. Every simulation here is a runnable
Python program, and its output is shown exactly as it printed. Corrections of common
myths are marked **Precision note**. Other chapters cover the pieces that sit on top:
[Database Storage Engines & Advanced Structures](03_databases_deep_dive.md) §5–§7 (replication in databases, Spanner, CAP and PACELC),
[Software Engineering & Architecture](04_software_engineering_deep_dive.md) §2–§3 and §6 (outbox, sagas, retries and circuit
breakers), and the System Design building blocks apply all of it to real designs. A
breakdown of what Junior through Staff+ engineers are expected to know closes the
chapter, just before the interview checklist.

## Foundations — What Is a Distributed System, and Why Is It Hard?

### Why Distribute at All

Nobody distributes a system for fun; every reason is a limit of one machine:

- **Scale.** One machine has a ceiling on CPU, memory, disk and network. Data or
  traffic beyond it has to be *partitioned* across machines (`03` §10).
- **Availability.** One machine fails — disks die, kernels panic, racks lose power. To
  keep serving, the data must be *replicated* on machines that fail independently.
- **Latency.** Light takes ~70 ms to cross the Atlantic and back. Serving users on
  several continents quickly means putting copies near them.
- **Organisation.** Large teams ship independently only if their services can deploy
  independently (`04` Foundations).

Partitioning and replication are the two tools, and replication is where every hard
problem in this chapter comes from: as soon as there are two copies of something, they
can disagree.

### What a Distributed System Actually Is

A set of **nodes** (processes, usually on separate machines) that cooperate by sending
**messages** over a **network**. Nothing else is shared: no memory, no clock, no
global view. Each node knows only its own state and the messages it has received, and
every message can be delayed, lost, duplicated or reordered.

The consequence that drives everything below: **a node cannot distinguish a peer that
crashed from one that is slow, or from a network that dropped its messages.** All three
look identical — silence.

### The Eight Fallacies

Engineers at Sun Microsystems listed the assumptions people make about networks that
are false. Each one is the root cause of a class of outage:

| Fallacy | Reality | Where this chapter deals with it |
|---|---|---|
| The network is reliable | Packets are lost; links and switches fail; partitions happen | §1, §2, §8 |
| Latency is zero | A cross-region round trip is 50–200 ms, and the tail is far worse | §5, §6 |
| Bandwidth is infinite | Replication and rebalancing traffic compete with users | §5, §9 |
| The network is secure | Every hop can be observed or forged | [Security Fundamentals](11_security_fundamentals_deep_dive.md) |
| Topology doesn't change | Nodes join, leave, move and get new addresses | §9 |
| There is one administrator | Different teams and providers configure different parts | — |
| Transport cost is zero | Serialisation, cross-zone traffic and egress cost CPU and money | — |
| The network is homogeneous | Mixed hardware, versions and protocols | `04` §4 |

### System Models: the Assumptions Every Algorithm States

A distributed algorithm is only correct under a **system model** — explicit assumptions
about timing and failures. Always ask which one a protocol assumes.

**Timing:**

- **Synchronous**: message delays and processing speeds have known upper bounds. Timeouts
  are then exact failure detectors. Real networks are not like this.
- **Asynchronous**: no bounds at all. A message may take arbitrarily long. This is the
  most honest model and the one in which the impossibility results of §1 hold.
- **Partially synchronous**: the system behaves asynchronously for unknown periods but is
  *eventually* synchronous for long enough. Raft, Paxos and nearly every practical
  protocol assume this: they are **always safe**, and **make progress when the network
  behaves**.

**Node failures:**

- **Crash-stop**: a node works correctly until it halts, forever.
- **Crash-recovery**: a node can crash and restart, losing memory but keeping what it
  wrote to disk. Real servers, and the reason protocols persist state before replying.
- **Byzantine**: a node can behave arbitrarily — buggy or malicious — including lying.
  Tolerating *f* Byzantine nodes needs 3*f* + 1 nodes; blockchains and some aerospace
  systems pay that cost. Datacenter systems assume crash-recovery and defend against
  corruption with checksums instead.

### The Core Components

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Failure detector** | Deciding which nodes to treat as dead | §2 |
| **Clocks** | Ordering events and bounding time (leases, TTLs) | §3 |
| **Replication protocol** | Keeping copies of data in step | §5 |
| **Consensus** | Making a group agree on one value or one sequence of values | §6 |
| **Coordination primitives** | Leader election, leases, locks, fencing | §7 |
| **Delivery and idempotency layer** | Turning retries into exactly-once effects | §8 |
| **Membership and dissemination** | Who is in the cluster; spreading state | §9 |
| **Conflict resolution** | Merging concurrent updates without coordination | §10 |

### How the Pieces Fit Together

```arch
%% caption: A typical replicated service: clients reach a leader chosen by consensus; the leader replicates a log to followers; a coordination service holds leases and membership; gossip spreads health information among data nodes.
grid 170x100
node cl "Clients" at 1,0 icon=users sub="retry with idempotency keys"
group rg "Replica group (Raft)" color=blue icon=db
node ld "Leader" at 1,1 in rg icon=db sub="orders all writes"
node f1 "Follower" at 0,2 in rg icon=replica sub="copy of the log"
node f2 "Follower" at 2,2 in rg icon=replica sub="copy of the log"
group cp "Control plane" color=purple icon=shield
node co "Coordination service" at 3.5,1 in cp icon=lock sub="leases, fencing tokens"
node mem "Membership" at 3.5,2 in cp icon=group sub="gossip + failure detection"
cl -> ld : "writes"
ld -> f1 : "AppendEntries"
ld -> f2
ld ..> co : "renew lease"
f2 ..> mem : "heartbeats"
```

### Vocabulary You'll Meet Below, in One Table

| Term | Meaning |
|---|---|
| Partition (network) | Nodes that are up but can't reach each other |
| Partition (data), shard | A subset of the data owned by some nodes (`03` §10) |
| Replica | A node holding a copy of some data |
| Quorum | A subset of replicas big enough that any two overlap, usually a majority (§5) |
| Linearizable | Behaves like a single copy, respecting real-time order (§4) |
| Happens-before (→) | *a* could have influenced *b*: same node earlier, or linked by messages (§3) |
| Term / epoch | A monotonically increasing generation number for leadership (§6) |
| Commit (consensus) | An entry stored on a majority; it will never be lost (§6) |
| Lease | A lock that expires unless renewed (§7) |
| Fencing token | A number, increasing with every lease grant, that storage uses to reject stale holders (§7) |
| Idempotent | Applying it twice has the same effect as once (§8) |
| Gossip | Spreading information by random peer-to-peer exchange (§9) |
| CRDT | A data type whose replicas merge deterministically without coordination (§10) |

## 1. Two Impossibility Results That Shape Everything

**The Two Generals problem.** Two generals must attack at the same time and can only
communicate by messengers who may be captured. General A sends "attack at dawn." Did it
arrive? B sends an acknowledgement — but did *that* arrive? A must acknowledge the
acknowledgement, and so on forever. **No finite protocol over an unreliable link gives
both sides certainty that they agree.** This is why a TCP connection close needs a
`TIME_WAIT` state (`02` §1), why a payment API can never know for sure whether a timed-out
request was processed, and why §8's idempotency keys exist: you can't eliminate the
uncertainty, so you make repetition harmless.

**FLP (Fischer, Lynch and Paterson, 1985).** In a fully *asynchronous* system, **no
deterministic algorithm can guarantee that nodes reach consensus if even one node may
crash.** The intuition: a node waiting for a vote can't tell whether the voter crashed
(so it should proceed without it) or is slow (so proceeding may contradict the vote when
it arrives), and an adversarial scheduler can keep the protocol forever on that knife's
edge.

What FLP does **not** say is that consensus is impossible in practice. Real protocols
escape it three ways:

1. **Partial synchrony** — assume timing bounds hold *eventually*. Raft and Paxos never
   violate safety; they might stall during a bad network period and resume after.
2. **Randomisation** — Raft's random election timeouts make endless split votes happen
   with probability zero.
3. **Failure detectors** — an oracle that may be wrong but eventually suspects crashed
   nodes (§2) is enough to solve consensus.

**Precision note:** the CAP theorem (`03` §7) is a close cousin: in a partition, a
replicated system must refuse some requests or return possibly stale answers. Both
results say the same thing from different angles — **agreement costs availability when
communication fails**.

## 2. Failure Detection: Deciding Someone Is Dead

Every failure detector is a timeout in disguise: if I haven't heard from you in *T*, I
suspect you. The whole difficulty is choosing *T*, and simulation makes the trade-off
concrete. One hour of heartbeats from a **healthy** node, sent every 100 ms, with normal
network jitter and occasional GC or VM pauses:

```python
"""Failure detection is a trade-off: simulate one hour of heartbeats from a
healthy node (100 ms interval, network jitter, occasional GC pauses), then
crash it, and see what each timeout gets wrong."""
import math, random, statistics

rng = random.Random(1)
arrivals, t = [], 0.0
while t < 3600_000:                              # one hour, in milliseconds
    gap = 100 + rng.gauss(0, 8)                  # heartbeat interval with jitter
    if rng.random() < 0.002:                     # ~70 GC or VM pauses per hour
        gap += rng.uniform(150, 900)
    t += max(gap, 1)
    arrivals.append(t)
gaps = [b - a for a, b in zip(arrivals, arrivals[1:])]

print("timeout   false suspicions/hour   time to detect a real crash")
for timeout in (150, 250, 500, 1000, 2000):
    false = sum(1 for g in gaps if g > timeout)
    print(f"{timeout:6} ms  {false:21}   {timeout:6} ms after the last heartbeat")

# Phi accrual: instead of yes/no, how surprising is the current silence,
# given the gaps seen so far? phi = -log10(P(gap >= silence)).
window = gaps[-1000:]
mu, sigma = statistics.mean(window), statistics.stdev(window)
def phi(silence):
    p = 0.5 * math.erfc((silence - mu) / (sigma * math.sqrt(2)))
    return -math.log10(max(p, 1e-300))
print(f"\nobserved gaps: mean {mu:.1f} ms, stdev {sigma:.1f} ms")
for silence in (110, 150, 200, 300, 500):
    print(f"silent for {silence:3} ms -> phi = {phi(silence):6.1f}")
```

```text
timeout   false suspicions/hour   time to detect a real crash
   150 ms                     84      150 ms after the last heartbeat
   250 ms                     83      250 ms after the last heartbeat
   500 ms                     57      500 ms after the last heartbeat
  1000 ms                      0     1000 ms after the last heartbeat
  2000 ms                      0     2000 ms after the last heartbeat

observed gaps: mean 100.3 ms, stdev 9.1 ms
silent for 110 ms -> phi =    0.8
silent for 150 ms -> phi =    7.6
silent for 200 ms -> phi =   27.5
silent for 300 ms -> phi =  106.4
silent for 500 ms -> phi =  300.0
```

- **Short timeouts suspect healthy nodes.** At 150–500 ms the detector fires 57–84 times an
  hour on a node that never failed — every GC pause looks like a death. Each false
  suspicion can trigger a failover, a leader election, a rebalance of data: expensive,
  and it can cascade when the "failed" node's load moves onto others.
- **Long timeouts leave real failures undetected.** At 1,000 ms no false alarms, but a real
  crash goes unnoticed for a full second, during which requests to it fail or wait.
- **There is no timeout that is both fast and never wrong** — a direct consequence of
  asynchrony (§1).

**Phi accrual detectors** (Cassandra, Akka) don't output "dead or alive." They keep the
distribution of recent heartbeat gaps and output φ = −log₁₀ P(a gap this long), a
*suspicion level*: φ = 1 means a 10% chance that a healthy node would be this late,
φ = 8 means one in 10⁸. Each consumer then picks its own threshold — a load balancer may
act at φ = 3, a data-rebalancing system at φ = 12 — and the threshold adapts
automatically to a noisy or a quiet network. Note what the numbers above also show: a
pure normal model rises steeply (φ = 27 at 200 ms), so real implementations add a
minimum standard deviation and an acceptable-pause allowance to avoid treating every GC
pause as certain death.

**Reducing false positives in large clusters (SWIM).** When node A's ping to B times out,
A asks *k* other nodes to ping B on its behalf ("indirect probes"). B is suspected only
if none of them can reach it, which filters out problems with A's own link. Suspicion is
then gossiped (§9), and B can refute it by gossiping a higher incarnation number. Consul,
Serf and many membership systems use this protocol.

## 3. Time and Order

### Physical clocks

Each machine's clock is a quartz oscillator that drifts — commonly quoted at up to tens
of parts per million, which is a few seconds a day. **NTP** corrects it against reference
servers, typically to within milliseconds on a LAN and tens of milliseconds across the
internet; during a correction the wall clock can **jump backwards**. Two rules follow:

1. **Measure durations with a monotonic clock** (`time.monotonic()` in Python,
   `time.Since` in Go, which uses the monotonic reading). The wall clock
   (`time.time()`) can go backwards between two readings; a timeout computed from it
   can be negative or huge.
2. **Never order events on different machines by wall-clock time alone.** Skew of a few
   milliseconds is enough to put an effect before its cause, which the first part of
   the program below shows.

### Logical clocks

Lamport defined **happens-before** (→): *a* → *b* if they happen on the same node and *a*
comes first, or *a* is sending a message and *b* is receiving it, or by transitivity.
If neither *a* → *b* nor *b* → *a*, the events are **concurrent**: neither could have
influenced the other. Clocks that respect → give an order that no user can contradict,
without needing synchronised time.

```python
"""Ordering events across machines whose clocks disagree."""

# Three machines. B's wall clock runs 50 ms behind A's; C is 20 ms ahead.
SKEW = {"A": 0, "B": -50, "C": +20}

# ---- 1. Wall-clock timestamps put an effect before its cause ----------------
true_time = 1000
post  = ("A", "post 'lunch?'",  true_time + SKEW["A"])          # A posts at t=1000
reply = ("B", "reply 'yes!'",   true_time + 10 + SKEW["B"])     # B replies 10 ms later
print("1) sorted by wall-clock timestamp:",
      [e[1] for e in sorted([post, reply], key=lambda e: e[2])])


# ---- 2. Lamport clocks: if a -> b then L(a) < L(b) ---------------------------
class Lamport:
    def __init__(self):
        self.t = 0
    def local(self):
        self.t += 1
        return self.t
    def send(self):
        return self.local()
    def recv(self, ts):
        self.t = max(self.t, ts) + 1
        return self.t

a, b = Lamport(), Lamport()
t_post = a.send()                     # A posts; the message carries t_post
t_reply = b.recv(t_post)              # B reads it, then replies
print(f"2) Lamport: post={t_post}, reply={t_reply}  -> the reply sorts after the post")


# ---- 3. Vector clocks tell "happened before" apart from "concurrent" ---------
def vc_compare(x, y):
    le = all(x[k] <= y[k] for k in x)
    ge = all(x[k] >= y[k] for k in x)
    return "equal" if le and ge else "before" if le else "after" if ge else "concurrent"

def vc_merge(x, y, me):
    z = {k: max(x[k], y[k]) for k in x}
    z[me] += 1
    return z

v0 = {"A": 0, "B": 0, "C": 0}
p  = {**v0, "A": 1}                                   # A posts
r  = vc_merge(v0, p, "B")                             # B saw the post, then replied
c  = {**v0, "C": 1}                                   # C posts, having seen nothing
print("3) vector clocks: post vs reply ->", vc_compare(p, r),
      "| post vs C's post ->", vc_compare(p, c))
print("   Lamport can't tell: both posts have L=1, yet neither caused the other")


# ---- 4. Hybrid logical clocks: causal like Lamport, close to wall time -------
class HLC:
    def __init__(self, node):
        self.node, self.l, self.c = node, 0, 0
    def now(self, true_t):
        return true_t + SKEW[self.node]
    def send(self, true_t):
        pt = self.now(true_t)
        if pt > self.l:
            self.l, self.c = pt, 0
        else:
            self.c += 1
        return (self.l, self.c)
    def recv(self, msg, true_t):
        pt, (ml, mc) = self.now(true_t), msg
        new_l = max(self.l, ml, pt)
        if new_l == self.l == ml:
            self.c = max(self.c, mc) + 1
        elif new_l == self.l:
            self.c += 1
        elif new_l == ml:
            self.c = mc + 1
        else:
            self.c = 0
        self.l = new_l
        return (self.l, self.c)

ha, hb = HLC("A"), HLC("B")
m = ha.send(1000)
h_reply = hb.recv(m, 1010)
print(f"4) HLC: post={m}, reply={h_reply}  -> ordered correctly, and within one clock-skew of real time")
```

```text
1) sorted by wall-clock timestamp: ["reply 'yes!'", "post 'lunch?'"]
2) Lamport: post=1, reply=2  -> the reply sorts after the post
3) vector clocks: post vs reply -> before | post vs C's post -> concurrent
   Lamport can't tell: both posts have L=1, yet neither caused the other
4) HLC: post=(1000, 0), reply=(1000, 1)  -> ordered correctly, and within one clock-skew of real time
```

- **Wall clocks lie by exactly the skew.** B's clock is 50 ms behind, so a reply sent 10 ms
  after the post gets an earlier timestamp and is sorted first.
- **Lamport clocks** (a counter; on receive, jump past the sender's value) guarantee
  *a* → *b* ⇒ L(*a*) < L(*b*). The converse fails: L(*a*) < L(*b*) doesn't mean *a*
  caused *b*. Two independent posts both have L = 1. Lamport timestamps plus a node ID
  as a tie-breaker give a total order consistent with causality, which is enough for a
  mutual-exclusion algorithm or a replicated log's ordering.
- **Vector clocks** keep one counter per node and compare element-wise, so they detect
  concurrency exactly: *before*, *after* or *concurrent*. Dynamo-style stores use them
  (or the related *version vectors*) to detect conflicting writes and hand both versions
  to the application. The cost is one entry per writer.
- **Hybrid logical clocks** (HLC, used by CockroachDB and MongoDB) combine a physical
  component with a logical counter: timestamps respect causality like Lamport clocks,
  yet stay within the clock-skew bound of real time, so they can be used for snapshot
  reads "as of" a time. The reply above gets `(1000, 1)` — after the post, and close to
  wall time.
- **TrueTime** (Spanner) goes the other way: GPS and atomic clocks bound the uncertainty to
  a few milliseconds, and each commit *waits out* that uncertainty so timestamp order
  matches real-time order globally (`03` §6).

**Try it: happens-before, visually.** Send messages between three processes and watch
Lamport and vector timestamps update. Find two events that Lamport orders but vector
clocks call concurrent.

<div class="lab" data-viz="sd-clocks"></div>

## 4. Consistency Models, Precisely

A consistency model is a contract: which results may a read return, given the writes
that happened? The strongest single-object model, and the one most interview questions
about "strong consistency" really mean, is **linearizability**: every operation appears
to take effect atomically at some instant between its start and its end, and all
clients see the same order. The system behaves like one copy of the data.

That definition is testable. A history of operations (who did what, when it started, when
it ended) is linearizable if you can find an order of the operations that respects real
time and in which every read returns the latest write. Here is a complete brute-force
checker for a single register:

```python
"""A brute-force linearizability checker for a single register.

An operation is (client, kind, value, start, end). The history is linearizable
if some order of the operations (1) never puts an operation before one that
finished before it started, and (2) makes every read return the latest write."""
from itertools import permutations


def linearizable(history, initial=0):
    for order in permutations(history):
        # real-time rule: if a ended before b started, a must come first
        pos = {id(op): i for i, op in enumerate(order)}
        if any(a[4] < b[3] and pos[id(a)] > pos[id(b)] for a in history for b in history):
            continue
        value, ok = initial, True
        for _, kind, v, _, _ in order:          # replay as a single-copy register
            if kind == "w":
                value = v
            elif v != value:
                ok = False
                break
        if ok:
            return True, [f"{c}:{k}({v})" for c, k, v, _, _ in order]
    return False, None


cases = {
    "read overlaps the write, sees old value":
        [("A", "w", 1, 0, 10), ("B", "r", 0, 2, 5)],
    "read overlaps the write, sees new value":
        [("A", "w", 1, 0, 10), ("B", "r", 1, 2, 5)],
    "read starts after the write finished, sees old value":
        [("A", "w", 1, 0, 10), ("B", "r", 0, 12, 15)],
    "B sees new, then C (later) sees old":
        [("A", "w", 1, 0, 20), ("B", "r", 1, 2, 5), ("C", "r", 0, 8, 12)],
}
for name, h in cases.items():
    ok, order = linearizable(h)
    print(f"{'YES' if ok else 'NO ':3}  {name:52} {order or ''}")
```

```text
YES  read overlaps the write, sees old value              ['B:r(0)', 'A:w(1)']
YES  read overlaps the write, sees new value              ['A:w(1)', 'B:r(1)']
NO   read starts after the write finished, sees old value 
NO   B sees new, then C (later) sees old                  
```

- **Overlapping operations may be ordered either way.** A read concurrent with a write
  may return the old or the new value — both are linearizable.
- **Once a write has finished, every later read must see it** (case 3). This is exactly what
  an asynchronous replica violates: the write was acknowledged, and a read from a lagging
  follower still returns the old value.
- **No going back in time** (case 4). Even though both reads overlap the write, once B has
  seen the new value, C — which started after B finished — can't see the old one. A
  quorum system without read repair can produce exactly this "new then old" history.

This tiny checker is the idea behind real tools. Jepsen's Knossos and Porcupine check
histories recorded from real databases under network faults, using smarter search (the
problem is NP-complete in general) — and have found violations in many databases that
claimed linearizability (§12).

The weaker models trade guarantees for availability and latency:

| Model | Guarantee | Can stay available in a partition? |
|---|---|---|
| **Linearizable** | Single-copy behaviour, real-time order | No — needs a majority (§6) |
| **Sequential** | One global order all clients agree on, consistent with each client's own order, not necessarily real time | No |
| **Causal** | Causally related operations are seen in causal order by everyone; concurrent ones may differ | Yes — the strongest model that can |
| **Session guarantees** | Read-your-writes, monotonic reads, monotonic writes, writes-follow-reads, per client | Yes, with sticky sessions or client-tracked versions |
| **Eventual** | If writes stop, replicas converge | Yes |

**Precision note:** *linearizable* (a single object, real time) and *serializable*
(multi-object transactions, some serial order) are different axes, and neither implies
the other. A database can offer serializable transactions whose order ignores real time,
or linearizable single-key operations with no multi-key transactions. **Strict
serializability** is both — what Spanner calls external consistency.
[Distributed Systems Theory](../SystemDesign/building_blocks/10_distributed_systems_theory.md) draws the full map.

## 5. Replication

Three architectures, distinguished by **who accepts writes**:

| Architecture | Writes go to | Strength | Weakness | Examples |
|---|---|---|---|---|
| **Single-leader** | One leader; followers copy its log | Simple, no write conflicts, easy to make linearizable | Leader is a bottleneck; failover is delicate | PostgreSQL, MySQL, MongoDB, Kafka partitions, Raft groups |
| **Multi-leader** | Any of several leaders (e.g. one per region) | Local write latency everywhere; survives region loss | Concurrent writes conflict and must be merged (§10) | Multi-region active-active databases, offline-first apps |
| **Leaderless** | Any replica; client or coordinator writes to several | No failover at all; tunable consistency | Conflicts; read repair needed; quorums are subtle | Dynamo, Cassandra, Riak |

**Synchronous vs asynchronous.** A synchronous follower acknowledges before the leader
replies to the client: no acknowledged write is lost if the leader dies, but a slow
follower slows every write. Asynchronous replication is fast but loses the latest writes
on failover and serves stale reads meanwhile. Most systems use a mix — "semi-synchronous"
with one synchronous follower, or a majority quorum (§6).

**Replication lag produces three anomalies worth naming** (and `03` §5 shows the database
view):

1. **Reading your own write fails**: you update your profile, refresh, and see the old one
   (served by a lagging follower). Fix: read-your-writes — route the user's reads to the
   leader for a while after a write, or read from a replica only once it has reached the
   version the user last wrote.
2. **Time moves backwards**: two refreshes hit two followers with different lag. Fix:
   monotonic reads — pin a session to one replica.
3. **Effects before causes**: a reply arrives before the question on a partitioned store.
   Fix: causal consistency — track dependencies (§3).

**Try it: lag and failover.** Write to the leader, then read from a follower before it
catches up. Kill the leader and see which acknowledged writes survive the failover.

<div class="lab" data-viz="sd-replication"></div>

### Quorums

In leaderless replication with *N* replicas, a write waits for *W* acknowledgements and a
read asks *R* replicas and keeps the newest version. The worst moment for a read is just
after a write was acknowledged, before it has reached the other replicas:

```python
"""N replicas. A write is acknowledged after W replicas store it; the others
haven't received it yet (replication lag). A read asks R random replicas and
keeps the highest version. How often does a read right after the ack miss it?"""
import random

N, TRIALS = 3, 100_000
rng = random.Random(3)

print(" W  R  R+W>N  stale reads  writes work with  reads work with")
for W, R in [(1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]:
    stale = 0
    for _ in range(TRIALS):
        have_new = set(rng.sample(range(N), W))          # the replicas that acked
        asked = set(rng.sample(range(N), R))             # the replicas the read hits
        if not have_new & asked:
            stale += 1
    print(f" {W}  {R}  {'yes' if R + W > N else 'no':5}  {100 * stale / TRIALS:10.1f}%  "
          f"{N - W} replica(s) down  {N - R} replica(s) down")
```

```text
 W  R  R+W>N  stale reads  writes work with  reads work with
 1  1  no           66.5%  2 replica(s) down  2 replica(s) down
 1  2  no           33.3%  2 replica(s) down  1 replica(s) down
 2  1  no           33.2%  1 replica(s) down  2 replica(s) down
 2  2  yes           0.0%  1 replica(s) down  1 replica(s) down
 1  3  yes           0.0%  2 replica(s) down  0 replica(s) down
 3  1  yes           0.0%  0 replica(s) down  2 replica(s) down
```

- **R + W > N makes stale reads impossible** in this model: the *R* replicas read and the *W*
  replicas written must share at least one, and that one has the new version. With
  *R* + *W* ≤ *N*, a third to two-thirds of reads right after a write miss it.
- **You choose where to pay.** *W* = 3, *R* = 1 makes reads cheap and writes impossible with
  any replica down; *W* = 1, *R* = 3 the reverse. *W* = *R* = 2 tolerates one failure on
  both paths — the usual choice for *N* = 3.

**Precision note:** R + W > N is not linearizability. Concurrent writes, a write that
succeeded on fewer than *W* replicas before failing (it may still be read later), clock-based
version comparison, and **sloppy quorums** — which accept writes on stand-in nodes during a
partition and hand them back later (*hinted handoff*) — all produce histories like case 4 of
§4. Dynamo-style stores accept this deliberately for availability; a linearizable store
needs consensus.

**Try it: overlap.** Take replicas down one at a time and watch which combinations of
*W* and *R* still succeed, and which reads can return a stale value.

<div class="lab" data-viz="sd-quorum"></div>

## 6. Consensus and Raft, Built and Broken

**Consensus** is getting a group of nodes to agree on a value such that: every node that
decides, decides the same value (**agreement**); the value was proposed by someone
(**validity**); and every non-crashed node eventually decides (**termination**). Applied
repeatedly, it gives **state machine replication**: agree on a *log* of commands, and
every replica that applies the same log in the same order ends in the same state. That is
how etcd, ZooKeeper, Consul, Spanner's Paxos groups, CockroachDB, TiKV and Kafka's KRaft
keep replicas identical.

**Why a majority?** Any two majorities of the same group overlap in at least one node. So
if every decision needs a majority, two decisions can never be made independently — the
overlapping node sees both. A 5-node group tolerates 2 failures, a 3-node group 1; an
even-sized group tolerates no more failures than the odd size below it, which is why
groups are 3, 5 or 7.

**Raft** breaks consensus into pieces that can each be explained:

- **Terms.** Time is divided into numbered terms, each with at most one leader. Any message
  carrying a higher term makes the receiver update its term and become a follower — this
  is how a deposed leader finds out.
- **Leader election.** A follower that hears nothing from a leader for a *randomised*
  election timeout becomes a candidate, increments the term, votes for itself and asks
  for votes. Each node votes at most once per term, and only for a candidate whose log is
  **at least as up to date** as its own (higher last term, or same last term and at least
  as long). A majority of votes makes a leader.
- **Log replication.** The leader appends client commands to its log and sends them to
  followers with `AppendEntries`, including the index and term of the entry just before
  the new ones. A follower accepts only if its log matches at that point (the **log
  matching property**); otherwise the leader backs up and retries, and the follower's
  conflicting suffix is overwritten.
- **Commit.** An entry is committed once it is stored on a majority **and it belongs to the
  leader's current term**. Committed entries are applied to the state machine and never
  lost.

Here is all of it — about 190 lines of Python, with a simulated network that can
partition, and a safety check on every tick that fails if two nodes ever commit
different histories:

```python
"""A small, complete Raft: leader election and log replication on a simulated
network that can partition. Time moves in ticks; a message sent in one tick
arrives in the next, unless the network drops it."""
import random

N = 5
MAJORITY = N // 2 + 1
HEARTBEAT = 2                                   # leader sends AppendEntries every 2 ticks


class Node:
    def __init__(self, nid, rng):
        self.id, self.rng = nid, rng
        self.term, self.voted_for, self.role = 0, None, "follower"
        self.log = []                           # list of (term, command)
        self.commit = 0                         # number of committed entries
        self.votes = set()
        self.reset_timer(0)

    def reset_timer(self, now):
        self.deadline = now + self.rng.randint(10, 20)   # randomised election timeout

    def last(self):
        return len(self.log), (self.log[-1][0] if self.log else 0)

    def become_follower(self, term, now):
        self.term, self.role, self.voted_for = term, "follower", None
        self.reset_timer(now)


class Cluster:
    def __init__(self, seed):
        rng = random.Random(seed)
        self.nodes = [Node(i, rng) for i in range(N)]
        self.inbox, self.now = [], 0
        self.cut = set()                        # frozenset({a, b}) pairs that can't talk
        self.leaders_by_term = {}
        self.committed = []                     # the committed prefix, as ever seen

    def send(self, src, dst, msg):
        if frozenset((src, dst)) not in self.cut:
            self.inbox.append((dst, src, msg))

    def partition(self, *groups):
        self.cut = {frozenset((a, b)) for g in groups for h in groups if g is not h
                    for a in g for b in h}

    # ---- the protocol -----------------------------------------------------
    def handle(self, n, src, m):
        kind = m["type"]
        if m["term"] > n.term:                  # rule for all servers: newer term wins
            n.become_follower(m["term"], self.now)
        if kind == "RequestVote":
            my_idx, my_term = n.last()
            up_to_date = (m["last_term"], m["last_idx"]) >= (my_term, my_idx)
            grant = (m["term"] == n.term and n.voted_for in (None, src) and up_to_date)
            if grant:
                n.voted_for = src
                n.reset_timer(self.now)
            self.send(n.id, src, {"type": "Vote", "term": n.term, "granted": grant})
        elif kind == "Vote" and n.role == "candidate" and m["term"] == n.term and m["granted"]:
            n.votes.add(src)
            if len(n.votes) >= MAJORITY:
                n.role = "leader"
                n.next = {p: len(n.log) for p in range(N)}
                n.match = {p: 0 for p in range(N)}
                n.match[n.id] = len(n.log)
                self.event(f"node {n.id} wins term {n.term} with votes from {sorted(n.votes)}")
                if self.leaders_by_term.setdefault(n.term, n.id) != n.id:
                    raise AssertionError("two leaders in one term")
                self.broadcast(n)
        elif kind == "AppendEntries":
            if m["term"] < n.term:
                self.send(n.id, src, {"type": "AppendResp", "term": n.term, "ok": False, "match": 0})
                return
            n.role = "follower"
            n.reset_timer(self.now)
            prev = m["prev_idx"]
            if prev > len(n.log) or (prev > 0 and n.log[prev - 1][0] != m["prev_term"]):
                self.send(n.id, src, {"type": "AppendResp", "term": n.term, "ok": False, "match": 0})
                return                          # log doesn't match: leader will back up
            for i, entry in enumerate(m["entries"]):
                j = prev + i
                if j < len(n.log) and n.log[j][0] != entry[0]:
                    del n.log[j:]               # conflicting suffix: discard it
                if j >= len(n.log):
                    n.log.append(entry)
            n.commit = max(n.commit, min(m["commit"], prev + len(m["entries"])))
            self.send(n.id, src, {"type": "AppendResp", "term": n.term, "ok": True,
                                  "match": prev + len(m["entries"])})
        elif kind == "AppendResp" and n.role == "leader" and m["term"] == n.term:
            if m["ok"]:
                n.match[src] = max(n.match[src], m["match"])
                n.next[src] = n.match[src]
                n.match[n.id] = len(n.log)      # the leader's own log counts toward a majority
                for idx in range(len(n.log), n.commit, -1):   # highest index on a majority
                    stored = sum(1 for p in range(N) if n.match[p] >= idx)
                    if stored >= MAJORITY and n.log[idx - 1][0] == n.term:
                        n.commit = idx          # only entries from the current term count
                        break
            else:
                n.next[src] = max(0, n.next[src] - 1)          # back up and retry

    def broadcast(self, leader):
        for p in range(N):
            if p != leader.id:
                prev = leader.next[p]
                self.send(leader.id, p, {
                    "type": "AppendEntries", "term": leader.term, "prev_idx": prev,
                    "prev_term": leader.log[prev - 1][0] if prev else 0,
                    "entries": leader.log[prev:], "commit": leader.commit})

    def tick(self):
        self.now += 1
        batch, self.inbox = self.inbox, []
        for dst, src, msg in batch:
            self.handle(self.nodes[dst], src, msg)
        for n in self.nodes:
            if n.role == "leader":
                if self.now % HEARTBEAT == 0:
                    self.broadcast(n)
            elif self.now >= n.deadline:        # heard nothing: stand for election
                n.term += 1
                n.role, n.voted_for, n.votes = "candidate", n.id, {n.id}
                n.reset_timer(self.now)
                idx, term = n.last()
                for p in range(N):
                    if p != n.id:
                        self.send(n.id, p, {"type": "RequestVote", "term": n.term,
                                            "last_idx": idx, "last_term": term})
        self.check_safety()

    def check_safety(self):
        """State-machine safety: a committed entry is never changed or lost."""
        for n in self.nodes:
            prefix = n.log[:n.commit]
            common = min(len(prefix), len(self.committed))
            if prefix[:common] != self.committed[:common]:
                raise AssertionError(f"node {n.id} committed a different history")
            if len(prefix) > len(self.committed):
                self.committed = prefix

    # ---- helpers for the story ---------------------------------------------
    def leader(self, among=range(N)):
        live = [self.nodes[i] for i in among if self.nodes[i].role == "leader"]
        return max(live, key=lambda n: n.term) if live else None

    def run_until(self, cond, limit=200):
        for _ in range(limit):
            self.tick()
            if cond():
                return
        raise RuntimeError("condition never became true")

    def event(self, text):
        print(f"t={self.now:3}  {text}")

    def show(self, label):
        print(f"       {label}")
        for n in self.nodes:
            log = " ".join(f"{c}@{t}" for t, c in n.log)
            print(f"         node {n.id} {n.role:9} term {n.term}  committed {n.commit}  log [{log}]")


c = Cluster(seed=4)
c.run_until(lambda: c.leader() is not None)
old = c.leader()

for cmd in ("x=1", "x=2"):
    old.log.append((old.term, cmd))
c.run_until(lambda: old.commit == 2)
c.event(f"leader {old.id} committed x=1, x=2 (stored on a majority)")

minority = {old.id, (old.id + 1) % N}
majority = set(range(N)) - minority
c.partition(minority, majority)
c.event(f"network splits: {sorted(minority)} | {sorted(majority)}")
old.log.append((old.term, "x=3"))               # a client write to the cut-off leader
c.run_until(lambda: c.leader(majority) is not None)
new = c.leader(majority)
new.log.append((new.term, "x=4"))
c.run_until(lambda: new.commit == 3)
c.event(f"new leader {new.id} committed x=4; old leader {old.id} still thinks it leads, x=3 uncommitted")
c.show("during the partition:")

c.partition()                                   # heal
c.event("network heals")
c.run_until(lambda: all(n.log == new.log and n.commit == 3 for n in c.nodes))
c.event(f"old leader {old.id} saw term {new.term}, stepped down, and replaced x=3 with x=4")
c.show("after healing:")
print("safety checks passed on every tick; leaders by term:", c.leaders_by_term)
```

```text
t= 13  node 2 wins term 1 with votes from [0, 1, 2]
t= 16  leader 2 committed x=1, x=2 (stored on a majority)
t= 16  network splits: [2, 3] | [0, 1, 4]
t= 29  node 0 wins term 2 with votes from [0, 1, 4]
t= 32  new leader 0 committed x=4; old leader 2 still thinks it leads, x=3 uncommitted
       during the partition:
         node 0 leader    term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
         node 1 follower  term 2  committed 2  log [x=1@1 x=2@1 x=4@2]
         node 2 leader    term 1  committed 2  log [x=1@1 x=2@1 x=3@1]
         node 3 follower  term 1  committed 2  log [x=1@1 x=2@1 x=3@1]
         node 4 follower  term 2  committed 2  log [x=1@1 x=2@1 x=4@2]
t= 32  network heals
t= 35  old leader 2 saw term 2, stepped down, and replaced x=3 with x=4
       after healing:
         node 0 leader    term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
         node 1 follower  term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
         node 2 follower  term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
         node 3 follower  term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
         node 4 follower  term 2  committed 3  log [x=1@1 x=2@1 x=4@2]
safety checks passed on every tick; leaders by term: {1: 2, 2: 0}
```

The story, step by step:

1. **Election.** At t=13, node 2's randomised timeout fires first; it wins term 1 with three
   of five votes.
2. **Replication.** `x=1` and `x=2` reach a majority and commit.
3. **Partition.** Nodes 2 and 3 are cut off from 0, 1 and 4. Node 2 still believes it leads
   term 1 and accepts `x=3` — but can reach only 2 of 5 nodes, so `x=3` can **never
   commit**. Meanwhile the majority side times out, elects node 0 in term 2, and commits
   `x=4`. For a while there are two nodes that think they are leader — in different terms,
   and only one of them can commit anything. Clients of the minority side see writes that
   never complete: that is the availability price CAP names.
4. **Heal.** Node 2 receives a term-2 message, steps down, and its log is repaired: the
   uncommitted `x=3` is overwritten by `x=4`. Every node converges on the same committed
   log, and the check ran on every tick.

**Break it to see why each rule exists.** Running the same simulation over randomised
partition schedules (a partition every 15 ticks, random client writes, 400 ticks per run)
and then deleting one rule at a time:

| Variant | Schedules with a safety violation |
|---|---|
| Raft as written | 0 of 500 |
| Votes granted without the "log at least as up to date" check | 2,000 of 2,000 |
| Leader counts replicas for entries from **earlier** terms | 1 of 2,000 |

- Without the **up-to-date check**, a node that missed committed entries can win an
  election and overwrite them. It happens on every schedule.
- Without the **current-term commit rule**, a leader can count a majority for an old entry
  that a later leader (which never had it) is still allowed to overwrite — the scenario of
  Figure 8 in the Raft paper. It reproduced in **one schedule in two thousand**. That
  single number is the best argument for why consensus is proven and model-checked, not
  tested: the rare interleavings are the dangerous ones, and ordinary tests don't find
  them.

**Reads need care too.** A leader can be deposed without knowing it (node 2 above), so
serving reads from its local state can return stale data. Correct options: send the read
through the log; confirm leadership with a round of heartbeats before answering
(*ReadIndex*); or hold a time-based **lease** during which no other leader can be elected,
which relies on bounded clock drift (§7).

**Paxos**, for comparison, reaches agreement on one value in two phases (*prepare/promise*,
*accept/accepted*); **Multi-Paxos** keeps a stable leader so each new log entry needs only the
second phase, which in practice looks very much like Raft. Raft's contribution was
understandability: the same guarantees, specified so that implementations are more likely to
be right.

**Try it: break a Raft cluster.** Crash the leader and watch an election; split the
network and add writes on both sides; heal it and watch the minority's entries get replaced.

<div class="lab" data-viz="sd-raft"></div>

## 7. Leases, Leader Election, and Fencing Tokens

A **lease** is a lock with an expiry: the holder must renew it before it runs out, so a
crashed holder releases it automatically without anyone detecting the crash. Leases are how
systems elect a single active master (Chubby, etcd, ZooKeeper's ephemeral nodes) and how Raft
leaders serve fast reads.

Leases have a flaw that no timeout can fix: **the holder can't know that its lease expired
while it was paused.** A GC pause, a VM migration or a swapped-out page can stop a process
for seconds between checking "do I still hold the lease?" and acting on it. The fix is to make
the *resource* check, not the client:

```python
"""A lease without fencing lets a paused ex-holder corrupt data."""


class LockService:
    def __init__(self):
        self.token = 32
    def acquire(self, who):
        self.token += 1                          # every grant gets a larger token
        return self.token


class Storage:
    def __init__(self, check_tokens):
        self.value, self.highest, self.check = None, 0, check_tokens
    def write(self, value, token):
        if self.check and token < self.highest:
            return f"REJECTED {value!r} (token {token} < {self.highest})"
        self.highest = max(self.highest, token)
        self.value = value
        return f"ok {value!r} (token {token})"


for check in (False, True):
    lock, disk = LockService(), Storage(check)
    t_a = lock.acquire("A")                      # A holds the lease...
    # ...then A stalls in a 30-second GC pause; the lease expires meanwhile
    t_b = lock.acquire("B")                      # B is granted the lease
    log = [disk.write("B's data", t_b)]
    log.append(disk.write("A's stale data", t_a))  # A wakes up, still believing it holds it
    print(f"fencing={check!s:5}", " | ".join(log), f"| final: {disk.value!r}")
```

```text
fencing=False ok "B's data" (token 34) | ok "A's stale data" (token 33) | final: "A's stale data"
fencing=True  ok "B's data" (token 34) | REJECTED "A's stale data" (token 33 < 34) | final: "B's data"
```

Every grant carries a larger **fencing token**; the storage remembers the largest token it
has accepted and rejects anything older. Without it, A's stale write lands after B's and
silently wins. The rules that follow:

- **A distributed lock without fencing is an efficiency hint, not a correctness
  guarantee.** It reduces duplicate work; it can't prevent it.
- **The token must be checked by the thing being protected** — the database row, the
  storage service. If the resource can't check tokens, use a conditional write
  (compare-and-swap on a version) instead.
- **Leases assume bounded clock drift** between holder and grantor. Holders should consider
  a lease expired a safety margin *before* its nominal end.

## 8. Delivery Semantics and Idempotency

A message sent over an unreliable network can be delivered:

- **At most once** — send once, never retry. Nothing is duplicated; some messages are lost.
- **At least once** — retry until acknowledged. Nothing is lost (while the sender keeps
  trying); some messages are processed twice, because the *acknowledgement* can be lost
  after the work was done (the Two Generals problem, §1).
- **Exactly once** — impossible as a *delivery* guarantee over a lossy network, but
  achievable as an *effect*: at-least-once delivery plus an **idempotent** receiver.

A simulation with 30% loss in each direction and 10,000 orders:

```python
"""At-least-once delivery + retries = duplicates, unless the receiver dedupes."""
import random
from collections import Counter


class PaymentService:
    def __init__(self, dedupe):
        self.charges, self.seen, self.dedupe = Counter(), {}, dedupe

    def charge(self, key, amount):
        if self.dedupe and key in self.seen:
            return self.seen[key]                     # replay the stored result
        self.charges[key] += 1
        result = f"charged {amount}"
        self.seen[key] = result
        return result


def run(dedupe, retries, loss=0.3, orders=10_000, seed=5):
    rng = random.Random(seed)
    svc = PaymentService(dedupe)
    for order in range(orders):
        key = f"order-{order}"                        # one key per logical intent
        for attempt in range(1 + retries):
            if rng.random() < loss:                   # request lost before arriving
                continue
            svc.charge(key, 10)
            if rng.random() < loss:                   # response lost: client times out
                continue
            break                                     # client saw the success
    per_order = Counter(svc.charges[f"order-{o}"] for o in range(orders))
    return per_order[0], per_order[1], sum(v for k, v in per_order.items() if k > 1)


print("                                   never   once   2+ times")
for label, dedupe, retries in [("at-most-once (no retries)", False, 0),
                               ("at-least-once (retries, no key)", False, 5),
                               ("effectively-once (retries + key)", True, 5)]:
    never, once, dup = run(dedupe, retries)
    print(f"{label:34} {never:5} {once:6} {dup:8}")
```

```text
                                   never   once   2+ times
at-most-once (no retries)           2997   7003        0
at-least-once (retries, no key)       10   7034     2956
effectively-once (retries + key)      10   9990        0
```

- **At most once** charges 30% of customers **never**. No duplicates, but lost orders.
- **At least once without a key** charges almost everyone, and **2,956 customers twice or
  more**, because a lost response makes the client retry work that already happened.
- **Retries plus an idempotency key** charge 9,990 customers exactly once. The 10 never
  charged are orders whose six attempts were all lost before reaching the server, and whose
  clients know they failed.

What a real idempotency layer needs beyond this toy: the key must identify the **intent**,
chosen by the client (one key per checkout, not per HTTP attempt); the service stores the
key **atomically with the effect** (same database transaction), or a crash between them
reintroduces duplicates; stored results expire after a window longer than the client's retry
horizon; and a second request with the same key but a different body is an error. Stripe's API,
Kafka's idempotent producer (sequence numbers per producer and partition, deduplicated by the
broker) and the transactional outbox (`04` §2) are all this pattern.

**Precision note:** "Kafka provides exactly-once" means exactly-once *within Kafka*:
idempotent producers plus transactions that atomically write outputs and consumer offsets. The
moment a consumer calls an external system — a payment API, an email service — that
system needs its own idempotency, or the guarantee ends at Kafka's edge.

**Try it: lose the response.** Charge a card, drop the response, retry, and compare the
outcome with and without an idempotency key.

<div class="lab" data-viz="sd-idempotency"></div>

## 9. Gossip, Membership, and Anti-Entropy

Some information — which nodes are alive, a new configuration, a schema version — must
reach every node, but not atomically. **Gossip** (epidemic) protocols spread it with no
coordinator: every round, each node that knows the news tells a random peer.

```python
"""Push gossip: every round, each node that knows the news tells one random peer."""
import math, random, statistics

def rounds_to_all(n, rng):
    informed, rounds = {0}, 0
    while len(informed) < n:
        rounds += 1
        for node in list(informed):
            informed.add(rng.randrange(n))      # tell one random peer (maybe one who knows)
    return rounds

rng = random.Random(2)
print("      N   rounds (median)   log2 N + ln N")
for n in (10, 100, 1_000, 10_000, 100_000):
    runs = [rounds_to_all(n, rng) for _ in range(50 if n <= 10_000 else 10)]
    print(f"{n:7}   {statistics.median(runs):14}   {math.log2(n) + math.log(n):13.1f}")
```

```text
      N   rounds (median)   log2 N + ln N
     10              6.0             5.6
    100             12.0            11.2
   1000             17.0            16.9
  10000             23.5            22.5
 100000             30.0            28.1
```

The number of rounds grows with the **logarithm** of the cluster size — about log₂ *N* rounds
for the news to reach half the nodes (the informed set roughly doubles each round) plus
about ln *N* more to find the last stragglers. Going from 10 to 100,000 nodes, a factor of
10,000, adds only 24 rounds. Each node's load per round is constant, no node is special, and
dead nodes just stop contributing. The trade-off is that membership is **eventually**
consistent: different nodes briefly disagree about who is alive.

The same idea repairs replicas. **Anti-entropy** compares replicas in the background; to
avoid shipping every key, each replica keeps a **Merkle tree** — leaves hash key ranges,
parents hash their children. Two replicas compare roots and descend only into subtrees
whose hashes differ, finding a handful of differences among billions of keys in a few dozen
hash comparisons. Dynamo, Cassandra and Riak all do this; together with **read repair**
(fix stale replicas seen during a read) and **hinted handoff** (§5) it is how leaderless
stores converge.

**Try it: epidemic spread.** Change the fanout, kill nodes, and switch between push and
pull, and watch how many rounds the whole cluster needs.

<div class="lab" data-viz="sd-gossip"></div>

## 10. CRDTs: Agreement Without Coordination

Consensus makes replicas agree by coordinating *before* accepting a write. **Conflict-free
replicated data types** make them agree *after*, with no coordination at all: each replica
accepts writes locally, and replicas exchange states and **merge**. If the merge function is
**commutative, associative and idempotent** (formally, the states form a join-semilattice and
merge is the join), then replicas that have seen the same updates reach the same state, in
whatever order and however many times the merges happen.

```python
"""State-based CRDTs: replicas update independently and merge in any order."""
import copy, itertools, random


class GCounter:                                     # grow-only counter
    def __init__(self, me, n):
        self.me, self.p = me, [0] * n
    def inc(self, k=1):
        self.p[self.me] += k
    def value(self):
        return sum(self.p)
    def merge(self, other):                         # element-wise max
        self.p = [max(a, b) for a, b in zip(self.p, other.p)]


class PNCounter:                                    # increments and decrements
    def __init__(self, me, n):
        self.pos, self.neg = GCounter(me, n), GCounter(me, n)
    def add(self, k):
        (self.pos if k > 0 else self.neg).inc(abs(k))
    def value(self):
        return self.pos.value() - self.neg.value()
    def merge(self, other):
        self.pos.merge(other.pos)
        self.neg.merge(other.neg)


class ORSet:                                        # observed-remove set
    def __init__(self, me):
        self.me, self.adds, self.removes, self.n = me, set(), set(), 0
    def add(self, x):
        self.n += 1
        self.adds.add((x, (self.me, self.n)))       # every add gets a unique tag
    def remove(self, x):
        self.removes |= {t for t in self.adds if t[0] == x}   # remove only tags seen here
    def value(self):
        return {x for x, tag in self.adds - self.removes}
    def merge(self, other):
        self.adds |= other.adds
        self.removes |= other.removes


# 1) Convergence: 3 replicas, random operations, then merge in every possible order.
rng = random.Random(11)
reps = [PNCounter(i, 3) for i in range(3)]
truth = 0
for _ in range(300):
    k = rng.choice([-2, -1, 1, 3])
    rng.choice(reps).add(k)
    truth += k
results = set()
for order in itertools.permutations(range(3)):
    rs = copy.deepcopy(reps)
    for i in order:                                 # gossip every state into replica order[0]
        rs[order[0]].merge(rs[i])
    results.add(rs[order[0]].value())
print("1) PN-counter: true total", truth, "| value after merging in all 6 orders:", results)

# 2) Merging twice changes nothing (idempotent), so duplicated gossip is harmless.
a = PNCounter(0, 2); b = PNCounter(1, 2)
a.add(5); b.add(-2)
a.merge(b); v1 = a.value(); a.merge(b); a.merge(b)
print("2) merge once:", v1, "| merge three times:", a.value())

# 3) OR-set: concurrent add and remove of the same item -> the add wins.
s1, s2 = ORSet("s1"), ORSet("s2")
s1.add("milk"); s2.merge(s1)                        # both replicas see milk
s2.remove("milk")                                   # replica 2 removes it...
s1.add("milk")                                      # ...while replica 1 adds it again
s1.merge(s2); s2.merge(s1)
print("3) OR-set after concurrent add + remove:", s1.value(), s2.value())

# 4) Last-writer-wins by timestamp loses one of two concurrent updates.
cart = {"ts": 0, "items": set()}
w1 = {"ts": 100, "items": {"milk"}}                 # phone adds milk
w2 = {"ts": 101, "items": {"eggs"}}                 # laptop adds eggs, 1 ms later
lww = max([cart, w1, w2], key=lambda w: w["ts"])
print("4) LWW register keeps:", lww["items"], "- the milk is silently gone")
```

```text
1) PN-counter: true total 32 | value after merging in all 6 orders: {32}
2) merge once: 3 | merge three times: 3
3) OR-set after concurrent add + remove: {'milk'} {'milk'}
4) LWW register keeps: {'eggs'} - the milk is silently gone
```

- **Counters.** A G-counter gives each replica its own slot and merges by element-wise
  maximum; a PN-counter is two G-counters (increments minus decrements). All six merge orders
  give the true total, and merging the same state three times changes nothing — duplicated or
  reordered gossip (§9) is harmless.
- **Sets need a rule for add-versus-remove.** The OR-set tags every add uniquely; a remove
  deletes only the tags that replica has *seen*. A concurrent re-add has a new tag, so the
  add wins, and both replicas agree on `{'milk'}`.
- **Last-writer-wins is the anti-pattern it replaces.** Picking the version with the later
  timestamp discards the other concurrent update entirely (and "later" is only as good as
  the clocks, §3). LWW is acceptable for data where losing a concurrent update is fine; it is
  wrong for carts, counters, permissions or money.

CRDTs power collaborative editors (sequence CRDTs such as RGA and the ones in Yjs and
Automerge), offline-first apps, Riak's data types, and Redis Enterprise's active-active
replication. Their limits: they can't enforce a global invariant ("stock never below zero",
"usernames are unique") — that needs coordination — and metadata (tags, tombstones) grows
unless garbage-collected.

## 11. Transactions Across Partitions

Consensus keeps *copies of the same data* in agreement. A transaction that touches data on
*different* partitions needs every partition to commit or none — a different problem.

- **Two-phase commit (2PC).** A coordinator asks every participant to *prepare* (make the
  change durable, promise to commit) and, if all say yes, tells them to *commit*. Its flaw is
  **blocking**: a participant that voted yes can't decide on its own if the coordinator crashes,
  and holds its locks until the coordinator returns (`04` §3).
- **2PC over consensus groups.** Spanner makes the coordinator and every participant a Paxos
  group, so "the coordinator crashed" means "a majority of the coordinator group failed" —
  rare enough to live with. That is how it offers strict-serializable transactions across
  shards and regions (`03` §6).
- **Deterministic ordering (Calvin, FaunaDB).** Agree on the order of transactions first,
  through a replicated log, then every partition executes them in that order with no commit
  protocol at all.
- **Sagas.** Across services or organisations, give up atomicity: run local transactions in
  sequence, and on failure run compensating actions (`04` §3). Consistency becomes eventual,
  and every step must be idempotent (§8).

## 12. How Distributed Systems Are Tested

Distributed bugs live in rare interleavings of messages, crashes and clock behaviour — the
one-in-two-thousand schedule of §6. The techniques that find them:

- **Model checking designs.** TLA+ specifications of a protocol are checked exhaustively
  over small configurations; Amazon has published its use for S3, DynamoDB and other
  services, and both Raft and Paxos have TLA+ specifications.
- **Deterministic simulation.** Run the real code with the network, disk and clock replaced
  by a simulator driven by a seed, and search millions of schedules; any failure replays
  exactly from its seed. FoundationDB was built this way from the start; the fuzzing of §6 is
  a miniature of it.
- **Fault injection against real systems.** Jepsen runs a database on real machines, injects
  partitions, clock skew and crashes, records every client operation, and checks the history
  against the claimed consistency model — the checker of §4 at industrial strength. It has
  found consistency violations in a long list of well-known databases.
- **Chaos engineering in production.** Deliberately kill instances, add latency, or fail a
  zone (Netflix's Chaos Monkey and its successors) to verify that failover actually works
  before a real outage tests it.

## What Each Engineering Level Should Know

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Models and impossibility** (Foundations, §1) | Knows networks fail and machines crash | Names the fallacies; knows timeouts can't distinguish slow from dead | States Two Generals and FLP, and how partial synchrony and randomisation escape FLP | States the system model of every protocol they adopt |
| **Failure detection** (§2) | Knows heartbeats exist | Explains the timeout trade-off | Explains phi accrual and SWIM indirect probes; tunes detectors to pauses | Designs failover policy so false positives can't cascade |
| **Time and order** (§3) | Knows machine clocks differ | Uses monotonic clocks for durations; knows NTP jumps | Explains Lamport, vector and hybrid clocks and when each is needed | Chooses ordering mechanisms (HLC, TrueTime, sequencers) for a platform |
| **Consistency models** (§4) | Knows "eventual consistency" | Explains read-your-writes and monotonic reads | Defines linearizability precisely; separates it from serializability | Picks a model per operation and states its cost |
| **Replication and quorums** (§5) | Knows data is copied for safety | Explains leader-follower, sync vs async, lag anomalies | Explains quorums, why R+W>N isn't linearizable, hinted handoff | Chooses replication topology per workload and region |
| **Consensus** (§6) | Knows a leader is elected | Explains majority quorums and terms | Walks through Raft election, replication, commit rules and safe reads | Evaluates consensus-based designs; knows when to avoid coordination |
| **Leases, fencing, idempotency** (§7–§8) | Knows retries can duplicate work | Uses idempotency keys | Explains fencing tokens and why exactly-once is an effect, not a delivery | Designs end-to-end exactly-once pipelines across system boundaries |
| **Gossip, CRDTs, cross-partition transactions** (§9–§11) | — | Knows gossip spreads state | Explains O(log N) gossip, Merkle anti-entropy, CRDT merge properties, 2PC blocking | Chooses between consensus, CRDTs and sagas for a product |
| **Testing** (§12) | Writes unit tests | Adds fault-injection tests | Knows Jepsen, deterministic simulation and TLA+ | Invests in simulation or model checking for critical systems |

**Reading this table as a study plan:** Foundations, §1–§2 and §5 cover what every
distributed-systems conversation assumes. §4, §6 and §7–§8 are the core of a Senior system
design interview's deep dives. §9–§12 are where Staff candidates show judgement.

## Interview checklist

- [ ] I can state the eight fallacies and the synchronous, asynchronous and partially synchronous models.
- [ ] I can explain the Two Generals problem and FLP, and how real protocols make progress anyway.
- [ ] I can explain the failure-detection trade-off with numbers, and what phi accrual and SWIM add.
- [ ] I can explain why wall clocks can't order events, and what Lamport, vector and hybrid clocks each guarantee.
- [ ] I can define linearizability precisely, check a small history by hand, and separate it from serializability.
- [ ] I can compare single-leader, multi-leader and leaderless replication and name the three replication-lag anomalies.
- [ ] I can explain R + W > N, what it guarantees, and why it isn't linearizability.
- [ ] I can walk through Raft: terms, elections, the up-to-date vote rule, log matching, the current-term commit rule, and safe reads.
- [ ] I can explain why a lock needs a fencing token and who must check it.
- [ ] I can explain at-most-once, at-least-once and effectively-once, and design an idempotency layer.
- [ ] I can explain why gossip takes O(log N) rounds and how Merkle trees make anti-entropy cheap.
- [ ] I can explain what makes a CRDT converge, give two examples, and name what CRDTs can't do.
- [ ] I can compare 2PC, 2PC over Paxos, deterministic ordering and sagas.

Related: [Database Storage Engines & Advanced Structures](03_databases_deep_dive.md) §5–§7 (replication, consensus, clocks, CAP and PACELC), [Software Engineering & Architecture](04_software_engineering_deep_dive.md) §2–§3 and §6 (outbox, sagas, resilience), [Networking & Distributed Communication](02_networking_deep_dive.md) §1 (TCP reliability); [Distributed Systems Theory](../SystemDesign/building_blocks/10_distributed_systems_theory.md), [Consensus and Coordination](../SystemDesign/building_blocks/19_consensus_and_coordination.md), [Partitioning, Shard Keys, and Hot Keys](../SystemDesign/building_blocks/25_partitioning_and_hot_keys.md), [Distributed Log Internals](../SystemDesign/building_blocks/26_distributed_log_internals.md).
