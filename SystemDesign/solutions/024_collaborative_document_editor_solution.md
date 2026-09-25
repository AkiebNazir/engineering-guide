# 024 — Collaborative Document Editor: Full System Design Solution

## Goal and contract

Every accepted edit is durable, every client converges to the same document, and a user's own typing never waits on the network (local edits apply instantly; the server reconciles). Cursors and presence are best effort. Permissions are enforced on every operation, not only when the document is opened.

## Estimates

- **Concurrent editing sessions**: 10M DAU, say 10% editing at peak → 1M open WebSocket connections; ~100K gateway connections per host → ~10–20 connection hosts plus headroom.
- **Operation rate**: an active typist produces ~5 ops/second, but clients batch keystrokes every ~50–100 ms; assume 1M connections × ~2 batched ops/s ≈ **2M ops/s** at peak, heavily skewed to the documents currently open.
- **Storage**: 100M new docs/year × 50 KB ≈ **5 TB/year** of latest content. The operation log is the bigger stream. Assume each of 10M DAU edits ~20 minutes a day at ~1 batched op/s: 10M × 1,200 s = 1.2×10¹⁰ ops/day ≈ 140K ops/s on average (about 7% of the 2M ops/s peak ceiling), and at ~50 bytes per op that is 600 GB/day ≈ **220 TB/year raw**. So keep raw ops for ~30 days (18 TB) for fine-grained history and undo, and compact older ranges into periodic snapshots.
- **Session servers**: at ~2.5 editors per open document (assumption), 1M editors ≈ 400K open documents; at ~150 KB in memory each (content plus recent ops) that is 60 GB in total, so ~10K documents per server means ~40 servers, each transforming 2M ÷ 40 = 50K ops/s. So ordinary documents are not the constraint; a single hot document's fan-out is (see the follow-ups).

These numbers say the hard part is not total storage; it is **stateful, low-latency sessions** for millions of hot documents and keeping every replica of a document convergent.

## Client-server protocol

```text
Client → Server   {doc_id, client_id, op_id, base_revision, ops: [...]}    # ops against the revision the client last saw
Server → Client   {ack: op_id, revision}                                  # your ops were applied as revision r
Server → Clients  {revision, ops, author}                                 # transformed ops from others
Client ↔ Server   {cursor: {user, position, selection}}                   # ephemeral, may be dropped
Client → Server   {resync: last_revision}                                 # after reconnect
```

`op_id` is unique per client so resends after a reconnect are idempotent. The <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr> handles everything that is not real time: create, list, share, fetch history, export.

## Session servers and connections

```arch
%% caption: All editors of one document connect to the same session server, which owns ordering for that document.
node c1 "Editor A" at 0.5,0 icon=browser
node c2 "Editor B" at 1.5,0 icon=browser
node gw "Connection gateways" at 1,1 icon=gateway sub="hold WebSockets, auth"
node api "REST API" at 3,1 icon=api sub="create, share, history"
node sess "Session server" at 1,2 icon=server sub="in-memory doc + OT"
node acl "Permissions service" at 1,3 icon=auth
node oplog "Operation log" at 0,3 icon=db sub="append per doc"
node snap "Snapshots" at 2,3 icon=blob
node meta "Document metadata" at 3,3 icon=db
c1 <-> gw : "WebSocket"
c2 <-> gw : "WebSocket"
gw -> sess : "route by doc_id"
sess:R ..> gw:R : "cursor + presence"
sess -> oplog
sess -> snap
sess -> acl
api -> meta
api -> snap
```

- **Connection gateways** hold WebSockets and authenticate users; they are stateless beyond sockets.
- Each **open document is owned by exactly one session server**, chosen by consistent hashing on `doc_id` plus a lease in a coordination service so two servers can never both own it. Routing all editors of a document to one owner gives a single place to order operations, which is what makes OT tractable.
- The session server keeps the current document and recent revisions in memory, applies and transforms operations, appends them to the durable **operation log**, then acknowledges the author and broadcasts to other editors.
- Idle documents are unloaded; the next open loads the latest snapshot plus subsequent ops.

## Concurrency control: OT vs CRDT

| | Operational transformation | CRDT |
|---|---|---|
| Ordering | Central server orders ops per document | No central order needed |
| Wire format | Position-based ops (`insert "x" at 42`) | Ops referencing element IDs |
| Metadata cost | Low | Per-character IDs and tombstones (compressible) |
| Offline edits | Transformed against everything that happened meanwhile | Merge naturally |
| Fit here | Strong: we already have one owner per document | Strong for local-first and peer-to-peer products |

**Decision: OT with a central session server per document**, as Google Docs does. We already need a server for permissions, durability, and history; a single ordering point keeps transformation correct and metadata small. The trade-off is that convergence depends on reaching that server, which the offline design below addresses.

How it works:

1. The client applies an edit locally at once and sends it with `base_revision` (the last server revision it has seen). While waiting for the ack it buffers further edits.
2. The server transforms the incoming op against all ops committed after `base_revision` (e.g. an insert before the position shifts it right; ties broken by client ID), applies it as revision `r+1`, appends to the log, acks, and broadcasts.
3. A client receiving others' ops transforms them against its own unacknowledged local ops before applying, so its local view stays consistent.

Rich text is modelled as a sequence with formatting attributes (spans) rather than HTML, so operations stay small and transformable: `retain(n)`, `insert(text, attributes)`, `delete(n)`.

**Worked example of the transform.** Document `abc` at revision 5. Client A inserts `X` at position 1 while client B concurrently deletes the character at position 1 (`b`), both based on revision 5. The server receives A first and commits revision 6 = `aXbc`. B's delete is transformed against A's insert: the insert position (1) is at or before the delete position (1), so the delete shifts to position 2, and applying it gives revision 7 = `aXc`. On B's client, A's insert is transformed against B's already-applied local delete (a delete at 1 does not move an insert at 1), so B also shows `aXc`. Without the transform the delete would remove `X` and leave `b`. The rules: an insert shifts right past an earlier insert at a smaller position (ties broken by client ID, so exactly one side shifts); a delete shifts right past an earlier insert at or before it; an insert shifts left past an earlier delete strictly before it; two deletes of one character collapse to a no-op.

## Storage: operation log and snapshots

- **Operation log**: append-only per document, keyed `(doc_id, revision)` in a store that supports ordered range scans (Bigtable/Spanner-style). The revision number is assigned by the session server, so appends are conditional on `revision = last + 1`, which also fences a stale owner.
- **Snapshots** every N ops (e.g. 1,000) or on idle, stored in blob storage with a pointer in metadata. Opening a document = latest snapshot + ops after it.
- **Revision history**: named versions are snapshot pointers; "see changes since yesterday" replays ops between two snapshots. Old op ranges are compacted into coarser snapshots to bound storage.

## Offline editing

The client persists unacknowledged ops and its `base_revision` in IndexedDB. On reconnect it sends `resync(last_revision)`; the server returns ops since then, and the client sends its buffered ops, which the server transforms against everything that happened meanwhile. Long offline sessions are bounded (e.g. 24 hours or N thousand ops), beyond which the client offers a merge view instead of silently transforming huge divergent histories.

## Permissions

The session server checks access when a user joins **and** caches a permission version per document; each op is checked against the cached ACL, and the permissions service pushes invalidations. When access is revoked, the session server disconnects that user's socket immediately. Sharing uses a relationship model (users, groups, domain, link sharing) — the Zanzibar approach described in [24_google_papers.md](../building_blocks/24_google_papers.md).

## Presence and cursors

Cursor and selection updates go through the same WebSocket but bypass the op log: they are coalesced (latest position per user every ~100 ms), never persisted, and dropped first under load. Presence uses heartbeats with a TTL. Cursor positions are transformed along with ops so they stay attached to the right text.

## Failure handling

| Failure | Behaviour |
|---|---|
| Gateway dies | Clients reconnect to another gateway with jittered backoff and resync from their last revision. |
| Session server dies | Its lease expires; another server loads snapshot + log and takes over. Clients resend unacknowledged ops (idempotent by `op_id`). Acknowledged ops are in the log, so nothing is lost. |
| Split ownership (two servers think they own a doc) | Conditional appends on revision number reject the stale owner's writes; it steps down. |
| Operation log store slow | Session server stops acknowledging (backpressure); clients keep editing locally and show "saving…". |
| Malformed or malicious op | Validated and rejected server-side; the client resyncs from the server's authoritative state. |

## Observability and interview close

Measure: op round-trip latency (send → ack), transform and apply time, broadcast lag per document, reconnect/resync rate, op-log append latency, snapshot age, documents per session server, convergence checks (periodic checksums compared between clients and server — any mismatch is a bug alert).

Trade-off to state: "One session server per document keeps OT simple and correct, but it caps a single document's throughput at what one server can transform. For thousands of simultaneous editors — say a live event document — I'd move to a CRDT so edits can merge across several servers, shard the document into sections, or make most participants read-only viewers fed from a broadcast stream."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Give each document a home region (where most of its editors are) and route every editor to that region's session server. Remote editors pay the WAN round trip (assume 100–150 ms) on top of the 200 ms p95 target, which the question scopes to "within a region"; their typing still applies locally at once. The log replicates synchronously across zones and asynchronously across regions, so a region loss can lose the last few seconds of acknowledged edits unless those documents pay for a second synchronous region. Multi-master editing needs a CRDT or server-to-server transformation, which I would not take on without a product reason.
2. **"What changes at 10× and 100×?"** At 10× I need about 100 connection hosts and 20M ops/s (about 1 GB/s of log appends at 50 B per op), so I batch appends per document every 50 ms. Session servers scale linearly by `doc_id`; what breaks first is one document's fan-out. With N editors at 2 ops/s each, every client receives 2N ops/s, so the owner sends N × 2N × 50 B: 100 MB/s (0.8 Gbps) at N = 1,000 and 80 Gbps at N = 10,000. Past a few thousand editors, cap the active editors and serve the rest as viewers from a broadcast tier that coalesces once a second.
3. **"What if every acknowledged edit must survive a region loss?"** The ack must wait for a durable write in a second region: an in-region quorum costs a few milliseconds, a cross-region commit 60–150 ms (assumed). We broadcast only after the durable append (earlier could show others text that later vanishes), so remote display latency rises by that amount too. Pay it only for documents flagged critical, or ack after the local quorum and state the recovery point as the replication lag.
4. **"What does it cost?"** Compute is small: 10–20 gateway hosts and about 40 session servers holding 60 GB of hot documents. Storage dominates: 5 TB of content plus 18 TB of 30-day raw log, about $2.7k a month per replica (about $8k with three zone replicas) at an assumed $0.15 per GB-month for the ordered log store; compacted history sits at object-storage prices. Track dollars per daily active editor.
5. **"How do you handle abuse?"** Rate-limit ops per client (assume 50 ops/s), cap op and document size, and validate every op against the current document length. Check permission per op, drop the socket on revoke, use unguessable 128-bit document IDs for link sharing, and throttle anonymous joins. A vandal with edit rights is handled by attributed history and restore, not prevention.
6. **"CRDTs are the modern answer. Why OT?"** CRDTs win for offline-first and peer-to-peer, and libraries such as Yjs and Automerge make them practical. Here one owner per document already exists for permissions, durability and history, so OT's central order keeps metadata small. If the interviewer prefers a CRDT, the same architecture works with the session server relaying and persisting CRDT updates: I gain multi-region writes and lose compactness (per-character metadata, tombstone cleanup).
7. **"How does undo work under concurrent edits?"** Undo is an operation, not a state restore: invert the user's own op (the inverse of an insert is a delete of those characters) and transform it against every op committed since, so it undoes only that user's change. If someone else already deleted the text, it becomes a no-op. Restoring a version writes a new revision holding the snapshot's content, so history is never rewritten.

## Common mistakes

1. **Last-write-wins on a whole document or paragraph.** Two people typing in one paragraph lose an edit. Transform position-based ops, or merge with a CRDT.
2. **Letting any server accept edits for a document.** Two owners fork the history. Use one owner (consistent hashing plus a lease) and conditional appends on `revision = last + 1` to fence a stale one.
3. **Broadcasting before the durable append.** Editors see text that disappears when the server crashes, and their views diverge. Append, ack, then broadcast.
4. **Sending the whole document, or one message per keystroke.** At 1M connections that is millions of messages a second. Send batched ops every 50–100 ms against a base revision.
5. **Checking permissions only when the document opens.** A revoked user keeps typing. Check per op against a cached ACL version and drop the socket on invalidation.
6. **Persisting cursors in the op log.** It multiplies write volume and history noise. Coalesce them, drop them first under load, and never store them.
7. **Implementing undo as "go back to the previous state".** It erases others' concurrent edits. Undo is the inverse op transformed over later ops.

## Going from L5 to L6

- **Migration and rollout.** Ops in the log are permanent, so version the op format and the transform. Before shipping a transform change, replay recorded op logs through old and new code and compare final documents, then roll out by document cohort.
- **Cost model.** Compute is small next to storage and retention. Tier the log (30 days raw, then snapshots) and report cost per daily active editor.
- **Ownership and blast radius.** Sharding by document limits a bad session-server deploy to the documents it owns; run cells per region. The lease and permissions services are the shared dependencies, so cache ACLs and let leases outlive short outages: existing sessions keep editing while new opens degrade.
- **Build versus buy.** Build the session and transform core, since it is the product; buy the ordered log store, blob storage and coordination service, and consider a maintained CRDT library if the product goes offline-first.
- **Phased evolution and what to measure first.** Ship plain-text OT with one owner per document, then add rich text, offline and comments. Measure first: editors per document (how many exceed 100), ops per editor, p95 keystroke-to-display, reconnect rate.

## Build exercise

Implement OT for plain text with `insert`/`delete`, a server that orders ops with revision numbers, and two simulated clients with random network delays. Fuzz 10,000 random concurrent edits and assert every run converges. Then reimplement with a sequence CRDT and compare metadata size.
