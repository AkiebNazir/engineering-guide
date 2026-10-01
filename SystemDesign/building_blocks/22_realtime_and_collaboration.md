# Real-Time Communication and Collaboration

Chat, live notifications, multiplayer cursors, and collaborative documents all break the request/response model: the server needs to reach the client the moment something happens, and several people may change the same state at once. This file covers the transports, the server architecture for millions of open connections, presence, and the two families of algorithms that make concurrent editing converge.

## Foundations — Pushing Data to Clients

### Why request/response isn't enough

HTTP was designed for the client to ask and the server to answer. Real-time features invert that:
the *server* learns something (a message arrived, a price moved, a collaborator typed) and must
tell the client **now**. The client can't know when to ask, so either it asks constantly (polling:
wasteful and slow) or it keeps a channel open that the server can write to (streaming: efficient,
but now the server holds state for every connected client).

That second choice changes the architecture in three ways this file keeps returning to:

- **Connections are state.** A server holding 500,000 open sockets can't be restarted or
  rebalanced casually; every deploy disconnects its clients, and they all come back at once.
- **Delivery needs a durable backstop.** A socket can drop at any moment, silently. The source of
  truth is a log the client can catch up from, never the socket.
- **Concurrent writers need a merge rule.** When several people edit the same thing live, their
  edits cross in flight, and the system needs a rule that makes every copy converge on the same,
  sensible result.

### Vocabulary

| Term | Meaning |
|---|---|
| Push vs pull | The server sends when something happens vs the client asks |
| Fan-out | Delivering one event to every interested connection |
| Session registry | Which gateway holds which user's connection |
| Catch-up / resync | A reconnecting client fetching everything after its last acknowledged sequence number |
| Presence | Soft state about who is online or viewing; cheap to lose |
| Operation | A single edit ("insert 'h' after character 17"), the unit collaborative systems exchange |
| Convergence | All replicas ending in the same state after seeing the same operations |
| Intent preservation | Each edit keeping the meaning its author intended, despite concurrent edits |

## Choosing a transport

| Transport | How it works | Latency | Cost per idle client | Direction | Good for |
|---|---|---|---|---|---|
| Short polling | Client asks every N seconds. | Up to N seconds | A full HTTP request every interval | Client → server | Rare updates, simplest possible client |
| Long polling | Server holds the request open until there is data (or a timeout), then the client re-opens. | Near-instant | One hanging request; a new request per message | Server → client | Legacy environments, firewalls that block WebSockets |
| Server-sent events (SSE) | One long-lived HTTP response streaming `text/event-stream`. Automatic reconnect with `Last-Event-ID`. | Instant | One connection | Server → client only | Live feeds, notifications, token streaming from LLMs |
| WebSocket | HTTP upgrade to a persistent full-duplex TCP connection; small frames. | Instant | One connection | Both | Chat, collaborative editing, games, presence |
| WebTransport / QUIC | Multiplexed streams and datagrams over HTTP/3. | Instant | One connection | Both | Emerging: media, games with unreliable datagrams |
| Mobile push (APNs/FCM) | Platform-owned connection wakes the app. | Seconds, best effort | Free for you | Server → device | Offline users, background delivery |

> 🎯 Default answer: WebSockets for bidirectional interactive features, SSE when updates only flow from server to client, and mobile push for users who are not connected. Always add a way to catch up from durable storage — no transport guarantees you did not miss something while disconnected.

## Architecture for millions of connections

A WebSocket is state pinned to one server. The design keeps that server thin and stateless apart from the socket itself:

```arch
%% caption: Gateways only hold sockets. Message truth lives in the durable store; routing uses a presence/session registry.
node c1 "Client A" at 0,0 icon=client
node c2 "Client B" at 0,2 icon=client
node g1 "Connection gateway 1" at 1,0 icon=gateway
node g2 "Connection gateway 2" at 1,2 icon=gateway
node bus "Pub/sub bus" at 1,1 icon=topic sub="routes to recipient's gateway"
node svc "Message / collab service" at 2,1 icon=service
node log "Durable log / store" at 3,0 icon=db
node reg "Session registry" at 3,1 icon=kv sub="user → gateway"
node push "Mobile push" at 3,2 icon=notify sub="for offline users"
c1 <-> g1
c2 <-> g2
g1:R -> svc:T
g2:R -> svc:B
svc -> log
svc -> reg
svc ..> bus
bus ..> g1
bus ..> g2
svc -> push
```

- **Connection gateways** terminate WebSockets, authenticate, apply per-connection rate limits and backpressure (bounded outbound buffers; drop and let the client resync if it is too slow). A single well-tuned host can hold on the order of 100K–1M idle connections; the limit is usually memory per connection and file descriptors.
- **Session registry**: which gateway holds which user's connection, with a TTL heartbeat. The service publishes a message to the recipient's gateway (directly or via a pub/sub channel per gateway).
- **Durability first**: persist, then fan out. A client that reconnects asks for everything after its last acknowledged sequence number.
- **Load balancing**: L4 or L7 with long-lived connections means new connections distribute well but existing ones do not rebalance. Drain gateways gracefully on deploy (tell clients to reconnect with jittered backoff to avoid a reconnect storm).

## Presence

"Online / typing / viewing this doc" is soft state: frequently updated, cheap to lose, and never a source of truth.

- Clients heartbeat every 10–30 s; the registry stores `user → last_seen` with a TTL. Missing heartbeats → offline after the TTL.
- Fan presence out only to people who can see it (friends, doc collaborators), batched and rate limited — a user with 5,000 contacts flapping online/offline must not generate 5,000 writes per flap.
- Never infer delivery from presence. "Online" can be minutes stale.

## Collaborative editing: why naive merges fail

Two users edit the same document at the same moment. Each sends an operation expressed against the version *they* saw, e.g. "insert 'H' at position 1" and "delete position 2". When the second operation arrives at the first user, positions have already shifted, so applying it blindly deletes the wrong character — and the two copies diverge permanently. Last-writer-wins on the whole document is worse: it throws away someone's work.

## Operational transformation (OT)

OT transforms each incoming operation against the concurrent operations that have already been applied locally, adjusting positions so the *intent* is preserved:

- An insert before your position shifts your position right; a delete before it shifts it left.
- Two inserts at the same position are ordered by a deterministic tie-break (e.g. site ID).
- A delete of an already deleted character becomes a no-op.

In practice (Google Docs, Google Wave's lineage), a **central server** assigns a total order to operations. Each client sends ops tagged with the last server revision it has seen; the server transforms them against everything that happened since and broadcasts the result. That central ordering keeps the transformation rules tractable. The costs: a server is required for convergence, transformation functions are notoriously hard to get right for rich text, and offline editing produces long histories to transform.

## CRDTs

A **conflict-free replicated data type** is designed so that replicas can apply the same set of operations in any order and still converge, with no central coordinator.

- For text, each character gets a permanent unique ID (e.g. `(site, counter)`), and operations refer to IDs: "insert 'H' after character o1", "delete character o3". Positions are derived, never sent.
- Concurrent inserts after the same character are ordered by ID, so every replica sorts them the same way.
- Deleted characters remain as **tombstones** so later operations can still reference them; periodic garbage collection removes them once all replicas have seen the delete.

Families to name: counters (G-Counter, PN-Counter), registers (last-writer-wins with hybrid logical clocks), sets (OR-Set), and sequence CRDTs for text (RGA, Logoot, and modern implementations such as Yjs and Automerge).

| | OT | CRDT |
|---|---|---|
| Needs a central server | Usually yes | No |
| Offline and peer-to-peer | Painful | Natural |
| Metadata overhead | Small | IDs per element and tombstones; mitigated by run-length encoding |
| Implementation difficulty | Transformation correctness | Data-structure design and memory |
| Typical users | Google Docs, classic collaborative editors | Figma-style multiplayer (with a server authority), Automerge/Yjs apps, local-first software |

## A collaborative document service, end to end

1. Clients open a WebSocket to a **session server** that owns the live document (route by document ID with consistent hashing, so all editors of one document hit the same server).
2. The session server keeps the current document in memory, sequences operations (OT) or merges them (CRDT), and appends every operation to a durable **operation log**.
3. Periodically write a **snapshot** so loading a document means "latest snapshot + ops since", not replaying years of history.
4. Broadcast accepted operations and cursor/selection updates to connected collaborators; cursor updates are ephemeral and can be dropped under load.
5. Offline clients buffer operations locally and submit them on reconnect; the server transforms or merges them against what happened meanwhile.
6. Permissions are checked when the session opens *and* on each operation, so a revoked share takes effect immediately.
7. If the session server dies, clients reconnect; the document is reloaded from snapshot + log on another server. Unacknowledged client ops are re-sent (idempotent by op ID).

## Concurrent edits, built and checked

The sections above describe why naive merges fail and how OT and CRDTs fix them. Here are all
three, small enough to read, on the classic example: Alice inserts `h` into `cat` to make `chat`,
while Bob deletes the `t`:

```python
"""Two people edit "cat" at the same moment. Alice inserts "h" at position 1
("chat"); Bob deletes position 2 (the "t"). Each applies their own edit
first, then the other's."""
import itertools
import random


# ---- 1. naive: apply the other's operation with its original position ----------
def apply(doc, op):
    kind, pos, ch = op
    return doc[:pos] + ch + doc[pos:] if kind == "ins" else doc[:pos] + doc[pos + 1:]


alice, bob = ("ins", 1, "h"), ("del", 2, "")
a_side = apply(apply("cat", alice), bob)          # Alice: "chat", then delete position 2
b_side = apply(apply("cat", bob), alice)          # Bob:   "ca",   then insert at 1
print(f"1) naive       Alice sees {a_side!r}, Bob sees {b_side!r}  -> diverged, and Alice lost the 'a'")


# ---- 2. operational transformation: shift the incoming op past the local one -----
def transform(op, applied):
    """Rewrite `op` so it means the same thing after `applied` has run."""
    kind, pos, ch = op
    akind, apos, _ = applied
    if akind == "ins" and apos <= pos:
        pos += 1                                   # an insert before me shifts me right
    elif akind == "del" and apos < pos:
        pos -= 1                                   # a delete before me shifts me left
    return (kind, pos, ch)


a_side = apply(apply("cat", alice), transform(bob, alice))
b_side = apply(apply("cat", bob), transform(alice, bob))
print(f"2) OT          Alice sees {a_side!r}, Bob sees {b_side!r}  -> converged, both intents kept")


# ---- 3. a sequence CRDT: characters get permanent IDs; positions are derived ------
class Seq:
    """RGA-style list. Each element: (id, char, deleted). id = (counter, site)."""
    def __init__(self, site, text=""):
        self.site, self.counter = site, 0
        self.items = [((0, f"init{i:03}"), c, False) for i, c in enumerate(text)]   # counter 0: older than any edit

    def visible(self):
        return "".join(c for _, c, dead in self.items if not dead)

    def local_insert(self, index, ch):             # insert before the index-th visible char
        vis = [k for k, it in enumerate(self.items) if not it[2]]
        after = self.items[vis[index - 1]][0] if index > 0 else None
        self.counter += 1
        op = ("ins", (self.counter, self.site), ch, after)
        self.apply(op)
        return op

    def local_delete(self, index):
        vis = [k for k, it in enumerate(self.items) if not it[2]]
        op = ("del", self.items[vis[index]][0])
        self.apply(op)
        return op

    def apply(self, op):
        if op[0] == "del":
            self.items = [(i, c, dead or i == op[1]) for i, c, dead in self.items]
            return
        _, new_id, ch, after = op
        self.counter = max(self.counter, new_id[0])
        k = 0 if after is None else next(n for n, it in enumerate(self.items) if it[0] == after) + 1
        while k < len(self.items) and self.items[k][0] > new_id:   # skip newer siblings
            k += 1
        self.items.insert(k, (new_id, ch, False))


a, b = Seq("alice", "cat"), Seq("bob", "cat")
op_a = a.local_insert(1, "h")
op_b = b.local_delete(2)
a.apply(op_b)
b.apply(op_a)
print(f"3) CRDT        Alice sees {a.visible()!r}, Bob sees {b.visible()!r}  -> converged, no server needed")

# Many replicas, random concurrent edits, every delivery order.
rng = random.Random(3)
bad = trials = 0
for _ in range(200):
    sites = [Seq(s, "abc") for s in ("x", "y", "z")]
    ops = []
    for s in sites:                                 # each replica makes 2 edits concurrently
        for _ in range(2):
            n = len(s.visible())
            if n and rng.random() < 0.4:
                ops.append((s.site, s.local_delete(rng.randrange(n))))
            else:
                ops.append((s.site, s.local_insert(rng.randint(0, n), rng.choice("PQRS"))))
    results = set()
    for order in itertools.islice(itertools.permutations(ops), 0, None, 37):
        r = Seq("reader", "abc")
        pending = list(order)
        while pending:                              # deliver inserts after their anchor exists
            for i, (_, op) in enumerate(pending):
                known = {it[0] for it in r.items}
                if (op[0] == "del" and op[1] in known) or (op[0] == "ins" and (op[3] is None or op[3] in known)):
                    r.apply(op)
                    pending.pop(i)
                    break
        results.add(r.visible())
        trials += 1
    bad += len(results) > 1
print(f"   {trials:,} delivery orders of random concurrent edits on 3 replicas: "
      f"{'all converged' if bad == 0 else f'{bad} scenarios diverged'}")
```

```text
1) naive       Alice sees 'cht', Bob sees 'cha'  -> diverged, and Alice lost the 'a'
2) OT          Alice sees 'cha', Bob sees 'cha'  -> converged, both intents kept
3) CRDT        Alice sees 'cha', Bob sees 'cha'  -> converged, no server needed
   4,000 delivery orders of random concurrent edits on 3 replicas: all converged
```

- **Naive:** each side applies the other's edit at its original position. Alice deletes position 2
  of `chat` — the `a` — so the two copies diverge, and one of them has lost a character nobody
  deleted.
- **OT:** before applying a remote edit, transform it past the local one — Bob's "delete position 2"
  becomes "delete position 3" on Alice's side because her insert came before it. Both reach `cha`.
  The transformation rules for plain text fit in a few lines; for rich text, lists and tables they
  multiply, which is why OT systems keep a central server to fix one order.
- **CRDT:** characters carry permanent IDs, and edits refer to IDs, never positions: "insert `h`
  after character `c`", "delete character `t`". Both reach `cha` with no transformation and no
  server, and on three replicas with random concurrent edits every one of 4,000 delivery orders
  converged.

**Convergence is not correctness.** The first version of this CRDT gave the initial characters IDs
that compared as *newer* than Alice's insert, so her `h` skipped past the `a`: both replicas showed
`cah`, and all 4,000 delivery orders agreed on that wrong answer. A convergence test alone would have
passed it. Real CRDT libraries are tested for intent as well — the property that an insert lands
where its author put it — which is the hard part.

## Reconnect storms, modelled

Every gateway deploy, crash or network blip disconnects all of its clients, and they all try to
reconnect at the same moment. Connection setup is expensive (a TCP and TLS handshake, then
authentication), so a reconnect wave is one of the most common self-inflicted outages in real-time
systems. A model of 200,000 clients coming back to a fleet that can complete 20,000 handshakes a
second, where a refused attempt still costs a quarter of a handshake:

```python
"""A gateway holding 200,000 WebSockets restarts. The rest of the fleet can
complete 20,000 new connections a second (TLS handshake + auth). An attempt that
arrives when the fleet is saturated still costs a quarter of a handshake's work
(accept, TLS start, then a timeout), and the client waits and tries again.
How long until everyone is back?"""
import random

CLIENTS, ACCEPT_PER_S, REFUSED_COST = 200_000, 20_000, 0.25


def reconnect(spread_s, retry_wait, seed=1, horizon=600):
    rng = random.Random(seed)
    attempts = [0] * horizon
    for _ in range(CLIENTS):                           # first attempt: spread over the window
        attempts[int(rng.uniform(0, spread_s))] += 1
    connected, peak, refused = 0, 0, 0
    for t in range(horizon):
        peak = max(peak, attempts[t])
        # capacity left after paying for the attempts that will be refused
        ok = int(min(attempts[t], max(0, (ACCEPT_PER_S - REFUSED_COST * attempts[t]) / (1 - REFUSED_COST))))
        connected += ok
        failed = attempts[t] - ok
        refused += failed
        for _ in range(failed):                        # refused clients retry later
            wait = retry_wait(rng)
            if t + wait < horizon:
                attempts[t + wait] += 1
        if connected == CLIENTS:
            return f"{t + 1:4} s", peak, refused
    return "never", peak, refused


policies = {
    "all at once, retry after 1 s":            (0.001, lambda r: 1),
    "all at once, jittered backoff":           (0.001, lambda r: 1 + int(r.uniform(0, 10))),
    "server spreads reconnects over 15 s":     (15, lambda r: 1 + int(r.uniform(0, 10))),
}
print(f"{CLIENTS:,} clients, fleet accepts {ACCEPT_PER_S:,}/s (ideal: {CLIENTS // ACCEPT_PER_S} s)")
for name, (spread, wait) in policies.items():
    done, peak, refused = reconnect(spread, wait)
    print(f"  {name:38} everyone back: {done:>6}, peak {peak:7,} attempts/s, {refused:9,} refused attempts")
```

```text
200,000 clients, fleet accepts 20,000/s (ideal: 10 s)
  all at once, retry after 1 s           everyone back:  never, peak 200,000 attempts/s, 120,000,000 refused attempts
  all at once, jittered backoff          everyone back:   21 s, peak 200,000 attempts/s,   200,772 refused attempts
  server spreads reconnects over 15 s    everyone back:   15 s, peak  13,579 attempts/s,         0 refused attempts
```

- **Synchronised retries never recover.** 200,000 attempts a second cost more than the fleet's whole
  capacity before a single handshake completes, so nobody gets in, everyone retries, and the next
  second is identical — the metastable pattern of
  [Application Resilience Patterns](12_application_resilience_patterns.md), with connections
  instead of requests.
- **Jittered backoff recovers** (21 s), because the second and later waves are spread out, though the
  first wave still wastes a second of capacity.
- **Pacing from the server side is best**: drain a gateway gradually, or have the server tell each
  client when to reconnect (a randomised delay in the close frame or a `Retry-After`), so attempts
  never exceed capacity. Everyone is back in 15 s with nothing refused.

Operational rules that follow: drain gateways one at a time and slowly on deploys, give clients
jittered exponential backoff with a cap, keep TLS session resumption on (it makes a reconnect much
cheaper than a first connection), and load-test the reconnect path, not just steady state.

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Transports** | Picks WebSockets for chat | Chooses among polling, SSE, WebSockets and push by direction, cost and firewalls | Sets the platform's real-time transport and fallback strategy |
| **Architecture at scale** | Knows sockets live on servers | Designs gateways, a session registry, pub/sub routing, and durable catch-up | Plans capacity for connection counts, deploys and regional failover |
| **Reconnects and backpressure** | Adds retry on disconnect | Explains reconnect storms; uses jitter, pacing, draining and bounded outbound buffers | Owns fleet-wide rollout policy for stateful connection tiers |
| **Collaborative editing** | Knows last-writer-wins loses edits | Explains OT vs CRDTs with an example; designs op logs and snapshots | Chooses OT or CRDT for a product (offline, peer-to-peer, rich text) and its costs |

## Interview checklist

- [ ] I can explain why real-time features need push, and what holding connections does to deploys and scaling.
- [ ] I can choose a transport (polling, SSE, WebSockets, mobile push) and justify it.
- [ ] I can design the gateway / registry / pub-sub / durable-log architecture and the catch-up path.
- [ ] I can explain a reconnect storm and how jitter, draining and server pacing prevent it.
- [ ] I can show with an example why naive merges diverge, and how OT and CRDTs converge.
- [ ] I can explain why convergence alone isn't correctness (intent preservation).
- [ ] I can outline a collaborative document service end to end: sessions, op log, snapshots, offline, permissions.

## Related building blocks

- [API Design — High Level](03_api_design_high_level.md)
- [Messaging and Streaming](09_messaging_and_streaming.md)
- [Distributed Systems Theory](10_distributed_systems_theory.md)
- [Consensus and Coordination](19_consensus_and_coordination.md)
