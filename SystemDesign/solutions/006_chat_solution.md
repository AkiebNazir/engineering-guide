# 006 — Real-Time Chat: Full System Design Solution

## Requirements

Support direct/group messages, durable history, live delivery, offline sync, read/delivery status, and per-conversation order. Groups can have 100k members. Presence is useful but allowed to be approximate.

**Functional:** 1:1 and group messaging, attachments by reference, multi-device sync, delivery and read receipts, typing indicators, push notifications when offline, message history with pagination. **Out of scope unless asked:** voice/video calls, full-text search, bots.

**Non-functional:** send-to-deliver p99 < 200 ms when both users are online in the same region (the question's contract; offline catch-up within a few seconds of reconnect); no message loss once the sender sees "sent"; per-conversation total order; availability favored over global consistency for presence and typing; end-to-end encryption compatible design.

## Scale estimates

| Quantity | Assumption | Result |
|---|---|---|
| DAU | 500M | — |
| Messages | 40 per DAU per day | 20B/day ≈ **230k msg/s avg**, peak ~3x ≈ 700k/s |
| Message size | ~100 B text + ~200 B metadata | ≈ 6 TB/day, ~2 PB/year before replication |
| Concurrent connections | ~30% of DAU at peak | ≈ **150M WebSockets** |
| Connections per gateway | ~200k-500k with a tuned event loop (memory per connection is the limit) | ≈ 300-750 gateway hosts, plus headroom |
| Receipts/typing | ~3-5 events per message | control-plane traffic larger than message traffic |

What shapes the design: **150M long-lived connections** (a stateful gateway tier with a session registry), **700k writes/s** partitioned by conversation, and **receipts/presence volume** (must be cheap and lossy-tolerant).

More derived numbers the rest of the design leans on:

- **Scale is an assumption, the contract is "millions of concurrent clients".** 150M sockets is a WhatsApp-scale worst case chosen so nothing breaks later. At 5M sockets the same design needs 5M ÷ 300k ≈ 17 gateway hosts (round up for zone spread and headroom); only the counts change, not the shape.
- **Receipt and typing events:** 230k msg/s × ~4 events ≈ 920k control events/s. So receipts must be cursors and typing must be droppable, otherwise the control plane out-runs the data plane.
- **Heartbeats:** 150M sockets ÷ 30 s = **5M heartbeats/s**. So the gateway absorbs them locally and refreshes the registry as a per-gateway lease plus connect/disconnect events, not as 5M writes/s to the registry.
- **Storage:** ~2.2 PB/year raw × replication factor 3 ≈ 6.6 PB/year. So history older than the hot window (say 90 days, an assumption) moves to a cheaper tier, and clients page from it on demand.
- **Latency budget (assumed, same region):** gateway hop and auth ~10 ms, log append with in-region quorum ~10-20 ms, registry lookup ~2 ms, publish to the recipient's gateway ~5 ms, gateway to device over mobile radio ~50-100 ms. That totals roughly 80-140 ms at p99, so there is real headroom under 200 ms, but only if nothing on the path does a cross-region call.

## API

Real-time over WebSocket (or MQTT/gRPC streams on mobile); history over HTTPS.

```text
client → server
  SEND   {client_msg_id, conversation_id, body | attachment_ref, sent_at_client}
  ACK    {conversation_id, delivered_seq}          # delivery receipt
  READ   {conversation_id, read_seq}
  TYPING {conversation_id}                         # fire-and-forget
  SYNC   {cursors: {conversation_id: last_seq}}    # on reconnect
  PING   {active: {conversation_id: last_seq}}     # 15 s foreground, 60 s background

server → client
  SENT     {client_msg_id, conversation_id, seq, server_ts}
  MESSAGE  {conversation_id, seq, message_id, sender, body, server_ts}
  RECEIPT  {conversation_id, user_id, delivered_seq | read_seq}
  PONG     {heads: {conversation_id: latest_seq}}  # client SYNCs any conversation it is behind on

HTTPS
  GET /v1/conversations/{id}/messages?before_seq=…&limit=50
  GET /v1/conversations?updated_after=…           # inbox list
  POST /v1/attachments → signed upload URL (see 005 photo pipeline)
```

## Architecture and data

```arch
%% caption: Gateways hold the live sockets, the message service assigns the per-conversation sequence and persists first, and every fan-out path (online hint, offline push, search) runs after the durable append.
node client "Client devices" at 1,0 icon=mobile
node lb "L4 load balancer" at 1,1 icon=lb
node gw "WebSocket gateways" at 1,2 icon=websocket sub="own sockets, not truth"
node registry "Session registry" at 0,3 icon=kv sub="device to gateway, TTL"
node svc "Message service" at 1,3 icon=service sub="assigns seq"
node notif "Notification workers" at 2,3 icon=notify sub="push if offline"
node apns "APNs / FCM" at 3,3 icon=mobile
group data "Durable stores" color=blue icon=db
node members "Membership store" at 0,4 in data icon=sql sub="strongly consistent"
node log "Message store / log" at 1,4 in data icon=nosql sub="conversation_id#seq"
node search "Search / moderation" at 2,4 icon=search sub="index projection"
client -> lb -> gw
gw:L -> registry:T : "lease"
gw <-> svc : "send, hint"
svc:L -> registry:R : "lookup"
svc:B -> log:T
svc:B -> members:T
svc -> notif
notif -> apns
log ..> search
```

```arch
node Client "Client" at 1,2
node GW "WebSocket gateway" at 2,2
node Svc "Message service" at 3,2
node Log "Durable store/log" at 4,2
node Fanout "Online fanout gateways" at 3,1
node Notif "Notification workers" at 4,3
node Search "Search/moderation projection" at 3,3

Client -> GW
GW -> Svc
Svc -> Log
Log -> Svc
Svc -> GW
GW -> Client
Svc -> Fanout
Svc -> Notif
Svc -> Search
```

`Message(conversation_id, sequence, message_id UNIQUE, sender, body_ref, created_at)` is ordered by `(conversation_id, sequence)`. The client creates `message_id`; retrying the same send returns the original persisted sequence. `ConversationMember` handles permissions; `MemberCursor(conversation_id, member_id, delivered_seq, read_seq)` stores monotonic acknowledgement.

Persist before acknowledging send. Sequence is assigned by the single ordered partition/transaction boundary for that conversation; there is no need for expensive global order. A reconnect asks for messages after its durable cursor. WebSocket gateway owns a live connection, not the message truth; its loss must not lose history/delivery.

**Storage:** messages in a wide-column store with row key `conversation_id#seq` (Bigtable/Cassandra/HBase: sorted by key, so history pagination is a range scan, and writes are sequential per conversation). Conversation membership and user inbox metadata in a strongly consistent store. The **session registry** (`user_id → [(device_id, gateway_id)]`) in a low-latency KV with TTL heartbeats.

## Deep dive 1: Connection routing

- Clients connect through an L4 load balancer to any gateway. The gateway authenticates, then writes `(user, device) → gateway_id` into the session registry with a TTL refreshed by heartbeats (~30 s). Heartbeats are absorbed at the gateway (5M/s cluster-wide) and only lease renewals reach the registry.
- To deliver, the message service looks up the recipient's gateways and publishes to each gateway's inbound channel (a per-gateway queue or direct RPC).
- **Gateway death:** clients reconnect elsewhere with exponential backoff + jitter (avoid a reconnect storm after a zone failure); registry entries expire via TTL; nothing is lost because truth is in the store and clients `SYNC` from cursors.
- **Deploys:** drain gateways gradually; tell clients to reconnect over minutes, not all at once.

## Deep dive 2: Ordering and exactly-once *effect*

- **Per-conversation sequence** from a single writer: the conversation is owned by one partition leader (a Raft/Paxos-replicated shard, or the partition leader of a log). It assigns `seq = last_seq + 1` and persists the message with a unique `message_id`.
- **Sender retries:** the client generates `client_msg_id` (a UUID) and retries until it gets `SENT`. A duplicate send hits the unique key and returns the original `seq`. The user sees exactly one message even though delivery to the server was at-least-once.
- **Receivers:** delivery is at-least-once; clients dedupe by `message_id` and render by `seq`. A gap in `seq` triggers a `SYNC` fetch, but **only when a later message arrives**. That is a fast path, not a guarantee (next bullet).
- **The last-message hole, and the fix.** If the live push of the *last* message in a burst is lost (the publish to the gateway is dropped, the gateway restarts, the client's socket is half-open, or the registry entry expired during a GC pause so the recipient was treated as offline), no later message ever exposes the gap. A healthy socket could stay behind for hours until the next reconnect. Fire-and-forget push cannot be the delivery mechanism. Three layers close it:
  1. **Drive online delivery from the durable log, with a per-connection high-watermark.** The publish from the message service to the gateway is only a wake-up hint `(conversation_id, latest_seq)`. The gateway keeps `pushed_seq[conversation]` per connection and, on any hint, reads the durable range `(pushed_seq, latest_seq]` from the log (or its cache) and sends it in order. A lost hint is repaired by the next hint or by a per-connection sweep every ~5 s; a message is never "sent" without being readable from the log first. The upstream consumer that produces hints commits its log offset only after the gateway acknowledges, so a crash replays instead of dropping.
  2. **Ack-driven redelivery.** The client's `ACK {delivered_seq}` advances the watermark. Frames not acked within ~2 s are resent (backoff to ~10 s); after 3 tries, or when the bounded outbound buffer overflows, the gateway closes the socket so the client reconnects and runs `SYNC`. If the message is still unacked after ~10 s, the notification worker treats the user as effectively offline and sends the push, so the existing offline path also covers a healthy-looking but stuck socket.
  3. **Heartbeats carry the head.** The client's `PING` lists its active conversations with its local last seq; the `PONG` returns each conversation's latest seq from a small head cache (the "head" is just the last assigned `seq`). If `latest_seq > local_seq` the client issues `SYNC` immediately. Cost, with the assumption that ~10% of sockets are foreground: 15M × one on-screen conversation ÷ 15 s = 1M head lookups/s, cheap for a sharded in-memory cache. Background sockets ping every 60 s and rely on layers 1 and 2 plus OS push.
  So the worst-case staleness for the on-screen conversation is one ping interval (15 s), not "until reconnect", and it is bounded by the ack timeout (10 s) for everything else.
- **Why not a global order:** a global sequencer is a throughput bottleneck and a single point of failure, and no user can observe ordering across different conversations.
- **Hot conversations:** a 100k-member group with high traffic is one partition; if one partition can't keep up, it's the rare case that needs a dedicated shard.

## Group fanout and failure

For a 100k-member group, persist one message then fan out to currently connected members/subscribers; offline users fetch from history and notification policy decides who receives push. Do not write 100k complete copies synchronously on send. Presence uses TTL heartbeats and can be stale; never conclude a message was delivered merely because presence said online.

Gateway backpressure matters: a slow client gets bounded outbound buffer, then drops/reconnects and catches up by cursor. Workers and gateways retry within budgets; duplicate fanout is safe because client renders by message ID/sequence. Encrypt/authorize room membership, validate content/attachments, and rate limit spam.

Measure connected sockets, gateway CPU/memory, append p99, per-room partition hotness, fanout lag, notification rate, reconnect catch-up volume, and delivery/read cursor lag. Build one-room chat with durable sequence/cursor, then test duplicate send, gateway restart, slow receiver, and offline replay.

## Deep dive 3: Fanout strategy by group size

| Group size | Strategy | Why |
|---|---|---|
| 1:1 and small groups (≤ ~100) | **Fanout on write** to each member's inbox row (conversation list ordering, unread counts) + push to online devices | Cheap, keeps inbox queries simple |
| Large groups / channels (thousands to 100k+) | **Fanout on read**: store once; members fetch by cursor; only currently-connected members get live pushes; unread counts computed as `last_seq - read_seq` | Writing 100k inbox rows per message is too expensive |

This is the same hybrid as news feed fanout (`007_news_feed_solution.md`).

## Deep dive 4: Receipts, typing, and presence

- **Receipts** are cursors, not per-message rows: `read_seq` for a member means "read everything up to here." Monotonic updates (`max(old, new)`) make duplicates and reordering harmless. In large groups, don't fan out every read receipt to everyone; aggregate or show only on request.
- **Typing indicators** are ephemeral: never persisted, dropped under load, expire after a few seconds.
- **Presence** costs O(contacts) fanout per status change. Cheaper: heartbeat into the registry; clients subscribe to presence only for the conversation on screen; batch and debounce updates; show "last seen" coarsely.

## Deep dive 5: Offline delivery and multi-device

- Offline recipient: the notification worker sends a push (APNs/FCM) with minimal content (or only "new message" for E2E), subject to preferences and collapsing (one push for a burst of messages).
- Each device keeps its own cursor per conversation; a new device syncs history (with limits) from the store.
- **End-to-end encryption awareness:** with a Signal-protocol-style design, the server stores and routes ciphertext and never sees content. Consequences to mention: per-device keys (a message is encrypted for each recipient device), server-side search and moderation of content aren't possible, backups need client-side keys, and key changes must be surfaced to users.

## Deep dive 6: Multi-region

- Pin each conversation to a **home region** (e.g., where most members are); its sequence authority lives there. Users connect to their nearest gateway region; cross-region delivery rides the backbone.
- A region failure: conversations homed there fail over to a replica region (consensus-replicated shards across regions trade write latency for no data loss; async replication accepts a small loss window). State the choice.

## Interview close

"Gateways own connections, never truth: a message is durable with a per-conversation sequence before the sender sees 'sent,' and every client catches up by cursor. Sender retries are made idempotent by a client-generated message id, receivers dedupe by id and order by sequence, and there's no global order because nobody can observe one. Small groups fan out on write, large groups on read, and receipts, typing, and presence are cheap, monotonic, or ephemeral so control traffic can't overwhelm message traffic."

## Follow-ups the interviewer will ask

1. **"How does this work across regions? What about a chat between a user in Europe and one in the US?"** Each conversation has one home region that owns its sequence; a SEND from the other region crosses the backbone once (roughly 80-100 ms, assumed) to reach the sequencer, so cross-region 1:1 chats miss the 200 ms same-region budget and I would state a looser target for them (say 400 ms) rather than pretend otherwise. Delivery to the recipient's regional gateways rides the replicated log. For a conversation whose members move (a new home country), migrate the home region by draining writes, replicating the tail, and flipping a routing record, never by running two sequencers at once.
2. **"What changes at 10× and 100×?"** The gateway tier, log partitions and registry all scale linearly because conversations are independent. Registry size is 150M × ~100 B ≈ 15 GB today, so even 100× (1.5 TB) shards fine. What breaks first is the big-group hot path: a 100k-member room with 30% online is 30k sockets spread over up to ~750 gateways, so fan out in two levels (message service to gateways, then gateway to local sockets) and cap a single conversation's send rate. At 100× I would move to cells (independent stacks per user cohort) so a bad deploy or a viral group is contained.
3. **"What if we need stricter guarantees, such as a user seeing their own edits and deletes in order across devices, or one total order across all of a user's conversations?"** Edits, deletes and reactions are just more events in the conversation's log with their own seq, so per-conversation order already covers them. A single per-user timeline needs a per-user sequence written to every member's inbox, which is the fan-out-on-write cost I avoid for large groups; I would offer it for small groups only and use hybrid logical timestamps for cross-conversation display order, stating that it is approximate.
4. **"What dominates cost?"** Storage (~6.6 PB/year after 3x replication), then the gateway fleet (memory per idle socket, 300-750 hosts), then push notifications. Levers: tier history older than ~90 days to cold storage and compress it, collapse push bursts, shed typing/presence under load, and pack more sockets per host with smaller per-connection buffers.
5. **"How do you deal with abuse and spam?"** Token-bucket limits per sender, per conversation and per recipient (a 100k group turns one send into 100k deliveries, so the amplification is the thing to cap), stricter limits for new accounts, and link and attachment scanning on the upload path. Under end-to-end encryption the server cannot read content, so moderation relies on client-side reports that forward the reported messages with the reporter's consent, plus metadata heuristics such as bursts of identical-size messages to many strangers.
6. **"A user comes back after a month with 10,000 unread messages across 500 conversations. What does SYNC do?"** It must not stream 10,000 messages up front. Return the inbox list first (per conversation: head seq, unread = `head - read_seq`, last message preview), then page each conversation's history only when the user opens it, newest first. Deliver the on-screen conversation with priority and let everything else backfill at low priority under a per-client byte budget.
7. **"A zone hosting 30M sockets dies. What happens?"** All 30M clients reconnect. Spread over 60 s that is 500k handshakes/s, which is a self-inflicted outage, so clients use exponential backoff with full jitter (spreading over ~5 min gives 100k/s) and gateways shed load with a `retry_after` when CPU is high. Truth is in the log, so nothing is lost; the risk is the herd, not data.
8. **"What if the interviewer says a per-conversation sequencer is overkill and timestamps are enough?"** Client clocks skew and two members can send in the same millisecond, so different members would see different orders, and receipts by `seq` would lose meaning. A single writer per conversation is cheap because 700k writes/s spread over hundreds of millions of conversations is tiny per conversation, and a leader failover only pauses the affected conversations for seconds. If pressed, I would concede that hybrid logical clocks with a deterministic tiebreak give a stable order for a 1:1 chat, but history can then gain messages in the middle, so cursors are no longer monotonic and sync gets harder.

## Common mistakes

1. **Treating the WebSocket push as the delivery.** A fire-and-forget push loses messages silently, and a `seq` gap check cannot see a lost final message. Deliver from the durable log with a per-connection watermark, acks and heartbeats that carry the head.
2. **Ordering by timestamp or a global counter.** Client clocks disagree, and a global sequencer is a bottleneck nobody needs because no user can observe cross-conversation order. Use a per-conversation sequence from one owner.
3. **Per-message, per-recipient receipt rows.** A 100k-member group would write 100k rows per message. Store a monotonic cursor per member per conversation and aggregate in large groups.
4. **Fan-out on write to 100k inboxes.** One message becomes 100k writes and the tail of the group sees it seconds later. Store once, push to connected members, compute unread from `head - read_seq`.
5. **Letting presence decide delivery.** Presence is stale by design (TTL heartbeats); skipping the log or the push because the registry says "online" loses messages. Always persist first and use presence only to choose the delivery path.
6. **Keeping message state only in the gateway.** If the gateway holds the only copy of an unsent frame or a session, a restart loses it. Gateways hold connections and buffers, never truth.
7. **Reconnecting without jitter.** After a zone failure every client retries at once and the recovery traffic finishes off the surviving gateways. Use backoff with full jitter and server-side admission control.
8. **Ignoring encryption and multi-device consequences.** With end-to-end encryption the server cannot search or moderate content, each message is encrypted per recipient device, and backups need client-held keys. State these consequences instead of promising server-side search.

## Going from L5 to L6

- **Migration and rollout path.** Start single-region with a partitioned database that assigns per-conversation sequences and simple polling plus push, add the gateway tier when socket count demands it, and add cells when blast radius does. Clients live for years, so version the wire protocol and keep old versions working; you cannot force-update every phone.
- **Cost model.** Express cost per DAU as three lines (sockets, storage, push) and show which knob moves each: idle memory per connection, hot-window length, and push collapsing. A staff answer says which line dominates and why.
- **Ownership and blast radius.** Shard users into cells, each with its own gateways, registry and log. A bad gateway deploy, a poison message or a viral 100k group is contained to one cell, and a very hot group gets a dedicated shard.
- **Build versus buy.** APNs/FCM are unavoidable, a Kafka-like log and a managed wide-column store are commodity, the gateway is where custom work pays (event-loop tuning, memory per socket), and cryptography is a vetted library (Signal-protocol style), never home-grown.
- **What to measure first.** The distribution of group sizes, the fraction of sockets in the foreground, messages per DAU, and the fraction of messages whose delivery ack takes more than 10 s. That last number is the delivery-hole rate, and it is the SLI that exposes the failure mode this design exists to prevent.
- **Phased evolution.** Ship 1:1 and small groups first, add large-group fan-out on read, then presence and multi-device, and treat E2E as a foundation decided on day one because retrofitting it later is a rewrite.

## Build exercise

Implement one gateway (WebSocket or a fake transport), a message service that assigns per-conversation sequences with a unique `client_msg_id`, and cursor-based sync. Tests: duplicate SEND returns the same seq; kill the gateway mid-conversation and verify reconnect + SYNC delivers everything exactly once on screen; a slow receiver's buffer overflows and it recovers through SYNC without affecting other receivers. Named assertions:

- `test_lost_last_push_is_delivered`: drop the gateway push of the last message in a burst (no later message follows); assert the client has it within one ack timeout via redelivery or the PONG head check, without reconnecting.
- `test_pong_head_triggers_sync`: silence pushes for one conversation while a message is appended; assert the next PONG carries a head greater than the client's seq and the client SYNCs exactly the missing range.
- `test_duplicate_send_same_seq`: send the same `client_msg_id` twice through two gateways; assert one row and one seq.
- `test_consumer_offset_replays_after_crash`: kill the hint consumer before it commits; assert the restart resends and the client shows each message once.
