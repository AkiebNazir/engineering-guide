# 008 — Checkout: Full System Design Solution

## Goal and contract

Checkout converts a cart into a paid, fulfillable order exactly once from the customer's point of view, even though the underlying systems (payment provider, inventory, fulfillment) cannot be updated in a single atomic transaction. The order record, the inventory reservation, and the financial journal are the sources of truth; everything else (UI state, cached cart) is disposable.

Assume (the first five come from the question, the rest are labelled assumptions):

- Tens of thousands of checkouts per minute at peak, a flash sale: I use **50k/min ≈ 830/s**, with hot SKUs receiving thousands of concurrent buy attempts on one item.
- Payment provider round-trip is 200 ms to 5 s, callbacks (webhooks) arrive milliseconds to tens of seconds later and are occasionally duplicated, and the provider can time out with the charge actually having succeeded.
- Happy-path checkout p99 under 3 s. Zero tolerance for double charges, near-zero for oversell. Stuck or partial orders are reconciled within minutes.
- Clients retry on any timeout or network error.
- Assumption: a hold lasts 5 minutes, the average cart has 3 lines, a hot-SKU drop is ~10k units, and the provider supports idempotency keys and an authorize-then-capture split.

The invariant is: a given idempotency key yields exactly one order outcome — never two orders, never a charge with no order, never an order with no corresponding payment guarantee or explicit compensation. This is not "exactly-once payment" (impossible — the provider's ack can be lost); it is "exactly-once *recorded outcome*" achieved via idempotency keys, a durable order state machine, and reconciliation against the provider's own record.

The contract has two halves. **Safety** (never violated): no double charge, no unit sold twice, no confirmed order against a lapsed hold, no financial row edited in place. **Liveness** (bounded, alarmed): every order reaches a terminal state, and the customer gets either a decision within 3 s or an honest `PAYMENT_PENDING` that resolves within minutes. The one hard decision is where the irreversible step sits. I order the saga so every step before it can be undone for free (a hold is released, an authorization is voided) and the only money movement that is costly to undo, capture, comes last.

## Estimates

- **Checkouts**: 50,000/min ÷ 60 ≈ **830/s** sustained at peak. Assume the first seconds of a drop run at 3× that, **~2.5k/s for 10–20 s** (assumption). If the average day is 5M orders (assumption, ≈ 58/s), the peak is ~14× the average. So we size for the burst, not the mean, and the design must shed or queue rather than fall over.
- **Row writes**: about 15 per checkout (1 order, 3 lines, 3 holds, 3 stock updates, 1 idempotency key, 1 payment, 2 outbox rows, 1 audit event) ≈ 12.5k/s sustained and **~37k/s at the 3× burst**. About 9 of the 15 land on the order side (2.5k × 9 ≈ 22k/s at burst, ~1.4k/s per shard across 16 shards) and 6 on the inventory side (~15k/s, spread by SKU except for the hot one). So order storage shards by user, inventory by SKU, and the hot SKU is the only place one row can be hammered (below).
- **Provider calls**: one authorization per checkout hot-path, so 830/s sustained and 2.5k/s at burst, plus ~30% for retries and status lookups (assumption). By Little's law, in-flight calls = rate × latency: at a 1 s mean (the question says 200 ms to 5 s) that is **~830 concurrent calls sustained and 2.5k at burst**. So the payment workers are async I/O with thousands of open calls, not a thread per call, and the provider's rate limit must be negotiated up front (default per-account limits are often on the order of 100 requests/s, so check your provider's documented limits).
- **Hot SKU**: at ~3k reserve attempts/s against 10k units, stock is gone in **10,000 ÷ 3,000 ≈ 3.3 s**. A single-row conditional update holds its row lock for a commit, about 1.5 ms (assumption), so one row sustains ~**670 updates/s**. That is ~4.5× short, and after sell-out the refreshing crowd (say 30k/s) is 45× a single row's capacity. So the hot SKU needs a purpose-built allocator, not a plain counter.
- **Held-then-released stock**: with ~12% of attempts failing or being abandoned at payment (assumption), ~1,200 of 10,000 units go through a hold-and-release cycle inside 5 minutes. So released stock returns in waves and must not trigger a retry stampede.
- **Storage**: 5M orders/day × ~2.5 KB (order, lines, payment, events) = 12.5 GB/day ≈ **4.6 TB/year**, ~14 TB with three replicas. Idempotency keys: 5M × 200 B = 1 GB/day, retained 48 h. So storage does not drive the design; retention is a finance/compliance decision (keep years, move rows older than ~90 days to a cheaper tier).
- **Bandwidth and polling**: 830/s × ~4 KB request plus response ≈ 3.3 MB/s. While orders are in flight (830/s × 2 s ≈ 1.7k pending) clients poll once a second, so ~1.7k reads/s, ~5k/s at burst, served from replicas or a short cache. So reads are not the constraint.
- **Latency budget for the synchronous part** (targets, not measurements): order transaction 30 ms, reserve holds 60 ms, second transaction 30 ms, saga pickup 50 ms, authorization 1.5 s (p99, happy path), commit holds 50 ms, confirm transaction 30 ms. Summing the p99s gives ~1.75 s, inside 3 s with slack. So the handler waits up to 2.5 s for a terminal state, then returns `202 PAYMENT_PENDING` instead of blocking on a slow provider tail.

## Mechanisms compared

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Synchronous inventory decrement in checkout transaction | Decrement stock immediately, in the same DB transaction as order creation. | Never as the final step, but fine as a *reservation* (hold) step. | If used post-payment without a prior hold, payment can succeed while stock sells out — oversell. |
| Conditional reservation (hold) | Atomically move N units from available to held, tied to an order and an expiry. | Standard approach: reserve before authorizing, release on failure/expiry. | Requires an expiry sweep and idempotent release; a leaked hold silently starves inventory. |
| Saga / workflow-driven payment | Local transaction creates the pending order plus an outbox event; a separate process drives the provider call and confirms or cancels via guarded state transitions. | Any flow calling an external, slow, fallible provider. | More moving parts than a single transaction; requires a careful state machine and compensation logic. |
| Direct in-transaction payment call | Call the payment provider while holding DB locks for the order/inventory row. | Never at scale. | Provider latency or outage holds locks open, blocking unrelated checkouts — a remote failure becomes a local outage. |
| Two-phase commit across order, inventory, and provider | One coordinator, all participants prepare then commit. | Only between databases you own. | The provider is not an XA participant, and a coordinator crash leaves locks held across a remote call. |

## <abbr title="Application Programming Interface">API</abbr>

```text
POST /v1/checkouts
  Headers: Idempotency-Key: <client uuid, stable across retries>   (required)
  Body:    { cart_id, quote_id, payment_method_token, shipping_address_id }
  201 { order_id, state: "CONFIRMED", totals: {...}, lines: [...] }
  202 { order_id, state: "PAYMENT_PENDING", poll_url, retry_after_ms: 1000 }
  402 { code: "PAYMENT_DECLINED", decline_category, can_retry_with_new_method }
  409 { code: "OUT_OF_STOCK", lines: [{sku_id, requested, available_hint}] }
  409 { code: "PRICE_CHANGED", new_quote: {...} }
  410 { code: "QUOTE_EXPIRED" }
  422 { code: "IDEMPOTENCY_KEY_REUSED" }     # same key, different request body
  429 with Retry-After                        # per-user limit or per-SKU admission bucket

GET  /v1/orders/{order_id}            → 200 { state, lines, totals, payment: {status, last4}, timeline: [...] }
GET  /v1/orders?limit=20&cursor=…     → 200 { items: [...], next_cursor }   # keyset on (placed_at, order_id)

POST /v1/orders/{order_id}/cancel     Idempotency-Key required
  200 { state: "CANCELLED" | "REFUND_PENDING" }   409 if already shipped
POST /v1/orders/{order_id}/refunds    { amount, reason, line_nos? }   Idempotency-Key required
  202 { refund_id, status: "PENDING" }

POST /internal/webhooks/provider      # provider → us, signed
  Body: { id: "evt_…", type: "payment.authorized|payment.failed|payment.captured|refund.succeeded|dispute.created", data: {...} }
  200 after the event is durably stored, 4xx only for a bad signature (the provider retries any non-2xx)
```

- **Idempotency.** The client generates the key once per user intent and reuses it on every retry. The server scopes it to `(user_id, key)`, stores a hash of the request body, and returns the stored outcome for a repeat. Same key with a different body is a 422, not a silent second order. Keys live 48 h (assumption: longer than any client retry horizon and than the provider's own key retention, which some providers document as at least 24 hours). See [API design: idempotency](../building_blocks/03_api_design_high_level.md).
- **The client never sends an amount.** The charge is computed server-side from the price snapshot referenced by `quote_id`; see the section on cart versus checkout prices.
- **Order status is the truth for the UI.** A `202` is not a failure. The client polls `poll_url` (or listens on a push channel) until a terminal state, and the confirmation page renders from `GET /v1/orders/{id}`, never from the checkout response alone.
- **Webhooks** are verified (HMAC signature plus a timestamp tolerance), deduplicated on `event_id`, stored, then processed asynchronously. Acknowledge fast; do the work after.

## Data model

| Entity | Key and shape | Role | Partitioning |
|---|---|---|---|
| `orders` | `order_id` (time-ordered, shard id embedded) → `user_id, state, version, currency, subtotal, tax, shipping, discount, total, quote_id, hold_expires_at, placed_at, updated_at, failure_reason` | **Source of truth** for the order lifecycle | Hash of `user_id`, so a user's orders and idempotency keys share a shard. Partial index on `state IN (CREATED, PAYMENT_PENDING, REFUND_PENDING)` for the reconciler |
| `order_items` | `(order_id, line_no)` → `sku_id, qty, unit_price, tax, discount, line_total` | Immutable copy of the price snapshot, used for refunds | With the order |
| `idempotency_keys` | `(user_id, idem_key)` → `request_hash, order_id, created_at` | Dedup of client intent, written in the same transaction as the order | With the order |
| `order_events` | `(order_id, seq)` → `from_state, to_state, actor, reason, at` | Append-only audit trail; written in the same transaction as every transition | With the order |
| `payments` | `payment_id` → `order_id, attempt_no, provider_ref, status, amount, auth_key, capture_key` with `UNIQUE(order_id, attempt_no)` | Our record of provider state; statuses `NEW, AUTH_UNKNOWN, AUTHORIZED, DECLINED, VOIDED, CAPTURED, PARTIALLY_REFUNDED, REFUNDED` | With the order |
| `refunds` | `refund_id` → `order_id, payment_id, amount, reason, idem_key, status`, plus the conditional rule `refunded + amount ≤ captured` | Refund ledger | With the order |
| `provider_events` | `event_id` (unique) → `type, payload_hash, received_at, processed_at` | Webhook dedup and replay | By `event_id` |
| `outbox` | `(order_id, seq)` → `type, payload, published_at` | Reliable hand-off to the saga workers and to fulfillment | With the order; relay publishes to a queue partitioned by `order_id`, so events for one order stay in order |
| `stock_shards` | `(sku_id, shard_no)` → `available, version` | **Source of truth** for sellable units; a normal SKU has one shard, a hot SKU has k | By `sku_id` (a hot SKU's shards may sit on different nodes) |
| `holds` | `(order_id, sku_id)` → `shard_no, qty, status (HELD/COMMITTED/RELEASED), expires_at` | Attribution of held units to an order; primary key is the reserve idempotency key | With the SKU's stock shard; index on `(status, expires_at)` for the sweeper |
| `price_quotes` | `quote_id` → `cart_hash, lines, totals, currency, expires_at, signature` | Immutable price snapshot the customer saw | By `quote_id`; TTL 10 min plus retention with the order |

The double-entry financial journal is owned by the ledger service ([017 — Payment Ledger](017_payment_ledger_solution.md)); confirmed captures, refunds, and adjustments post there as new entries, never as edits. **Inventory invariant**: for every SKU, `Σ available + Σ qty of HELD and COMMITTED holds = initial + restocks − write-offs`. The reconciler checks it continuously.

## Architecture and flow

```arch
%% caption: The order shard commits intent through an outbox, inventory holds stock with conditional updates, and the saga worker is the only thing that calls the payment provider, outside every transaction and lock.
node client "Client" at 1,0 icon=client
node gw "API gateway" at 1,1 icon=gateway sub="auth, per-user limits"
node order "Order service" at 1,2 icon=service sub="idempotent checkout"
node inv "Inventory service" at 2,2 icon=service sub="holds, hot-SKU shards"
node stock "Stock + holds" at 3,2 icon=db sub="stock_shards, holds"
node orderdb "Order shard" at 1,3 icon=db sub="orders, keys, outbox"
node saga "Payment saga worker" at 2,3 icon=worker
node provider "Payment provider" at 3,3 icon=payment
node queue "Outbox queue" at 1,4 icon=queue sub="by order_id"
node rec "Reconciler" at 0,4 icon=sync sub="stuck + settled"
client -> gw -> order
order -> inv : "reserve"
inv -> stock : "decrement"
order -> orderdb : "txn 1, txn 2"
orderdb ..> queue : "relay"
queue:R -> saga:B
saga:T -> inv:B : "commit / release"
saga:L -> orderdb:R : "state"
saga -> provider : "authorize"
provider:R ..> order:T : "webhook"
rec:B -> provider:B : "compare"
rec:T -> orderdb:L : "heal"
```

```arch
node client "Client" at 1,4
node ord "Order service" at 3,4
node saga "Payment saga worker" at 5,4
node inv "Inventory service" at 3,2
node prov "Payment provider" at 5,2
node rec "Reconciler" at 5,0

client -> ord
ord -> inv
ord -> saga
saga -> prov
saga -> inv
saga -> ord
prov -> ord
rec -> prov
rec -> ord
```

**One write, end to end.** The gateway authenticates the caller, applies per-user limits, and routes by `user_id` to the order shard.

1. **Transaction 1** on that shard: insert `idempotency_keys(user_id, key, request_hash, order_id)`. A conflict means a retry: load the existing order, compare `request_hash` (mismatch is 422), and return its current state, or, if it is still `CREATED`, resume at step 2. The primary key makes two concurrent requests with the same key serialize; the second waits for the first to commit and then reads its result. Then insert the order in `CREATED` with the price snapshot copied into `order_items`, plus an `order_events` row.
2. **Reserve** every line through the inventory service, keyed by `(order_id, sku_id)`, in ascending `sku_id` order (a fixed order prevents two carts holding each other's SKUs). A repeat call is a no-op that returns the existing hold. If any line is rejected, the lines already taken are released and the order ends `OUT_OF_STOCK`. The allocator itself is in the hot-SKU section below.
3. **Transaction 2**: `UPDATE orders SET state='PAYMENT_PENDING' … WHERE order_id=? AND state='CREATED'`, insert the `payments` row (attempt 1), and insert the outbox row `PaymentRequested`. The order and its intent to pay commit together or not at all.
4. The outbox relay publishes to a queue partitioned by `order_id`. A saga worker calls the provider (next sections), commits the holds, and moves the order to `CONFIRMED` with an outbox row for fulfillment.
5. The handler waits up to 2.5 s for a terminal state and answers `201`, `402`, or `202`.

**One read, end to end.** `GET /v1/orders/{id}` routes by the `user_id` in the auth token (or the shard bits in the id) to one shard. Orders that are non-terminal or under 5 s old are read from the primary, so the customer never sees a checkout they just made "missing"; everything else is served from a replica. The response includes the timeline from `order_events`, so support and the customer see the same story.

## Flow and trade-offs

At 50k checkouts/minute (~830/sec) with hot SKUs, the inventory hold step is the contention point, not the payment call (which is already decoupled). Partition inventory rows by SKU and use short, single-row conditional updates (`UPDATE stock SET available = available - qty WHERE sku=? AND available >= qty`) rather than long-held locks; for extreme hot SKUs (a single item drawing thousands of concurrent buyers), the hot-SKU allocator below turns contention into either parallel shards or ordered waiting instead of transactional retry storms.

The order's idempotency key (client-supplied, stable across retries) makes the initial local transaction naturally safe to retry: a retried request finds the existing order and returns its current state instead of creating a duplicate. This trades a small unique-index check on every checkout for eliminating an entire class of duplicate-order bugs. The hard decision is keeping the payment call *outside* the local transactions and outside any inventory lock — this trades immediate consistency (the order briefly sits in `PAYMENT_PENDING` while the provider works) for availability: a slow or down provider degrades the async saga's throughput, not the database's lock table for every other in-flight checkout.

Do not call the payment provider from inside the database transaction that holds the inventory row lock — that is the single most common checkout-system bug, and it turns a provider slowdown into a full checkout outage. Do not decrement inventory as a side effect of a successful payment webhook without a pre-existing hold — a window opens between "payment succeeded" and "inventory decremented" where the same units can be sold to someone else, producing oversell. The hold must exist before payment is attempted, not after. See [Transactions and concurrency](../building_blocks/11_transactions_and_concurrency.md) for the saga pattern this follows.

## Hot-SKU allocator

**The problem.** A conditional update is correct on one row, but every writer on that row queues on its lock. At ~1.5 ms per committed update a row tops out near 670/s (assumption; measure your database), and the hot SKU sees ~3k attempts/s at the start, then a much larger refreshing crowd after sell-out. The allocator must (a) never oversell, (b) absorb the burst, and (c) answer "sold out" without touching the database.

| Option | How it works | Throughput (10k units, 3k/s burst) | Gives | Costs |
|---|---|---|---|---|
| Single-row conditional update | `UPDATE … SET available = available - q WHERE sku=? AND available >= q` | ~670/s per row: 4.5× short at burst, backlog grows ~2.3k/s | Exact, trivial, no new component | Lock-wait queue grows to tens of seconds, blowing the 3 s target |
| **Sharded stock counters** (chosen default) | Split the units over k rows (k = 8: 1,250 each); a request tries the shard chosen by `hash(order_id) mod k`, and probes a bounded number of others if it is short | 8 × 670 ≈ **5.3k/s**, so 3k/s is ~56% utilization | Same primitive and same database, near-linear write scaling, shards may sit on different nodes | Tail fragmentation (see below) and a slightly approximate "remaining" figure |
| Per-SKU serialized allocator | All reserves for a SKU route to one single-writer owner (an actor or a log partition keyed by `sku_id`) holding the counter in memory and appending decisions to a replicated log in batches | Tens of thousands per second (a batched log append, not a row lock, is the limit) | Exact, <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>-fair, no retry storms, natural fit for atomic multi-SKU bundles | A new stateful component, a leader-failover gap of seconds per SKU, and the counter must be rebuilt from the log and reconciled with holds |
| Token-bucket admission in front of either | A per-SKU bucket (say 4k tokens/s, burst 2k) plus a cached `SOLD_OUT` flag at the edge | Shed load before it reaches storage: 30k/s of refreshes cost cache reads, not row locks | Protects the database from a crowd it cannot serve anyway | Rejected users get 429 or 409 even if a unit is about to be released |

**Decision.** Default every SKU to a single row. Promote a SKU to sharded counters when it is flagged hot, either from the marketing calendar or automatically when its lock-wait p99 exceeds 50 ms or its attempts exceed ~300/s. Choose k from the burst: `k = ceil(peak ÷ (per-row rate × 0.5))`, so 3,000 ÷ (670 × 0.5) ≈ 9; I use k = 8 (56% utilization, close enough to the 50% target and a clean power-of-two layout) and verify it with a load test. Always put the admission bucket and the `SOLD_OUT` edge flag in front. Use the serialized allocator instead when <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> fairness is a stated requirement ("the first 10k clickers win") or bundles must be atomic across SKUs. This trades a slightly fuzzy remaining-count and a tail-handling routine for horizontal scaling on the database we already run; the cost is acceptable because the alternative that avoids it, a per-SKU single-writer service, is a new stateful tier to operate for a handful of SKUs a year.

```arch
%% caption: The edge flag and admission bucket keep post-sell-out traffic off the database, and the sharded conditional update plus a tail collapse keep it exact.
grid 190x105
node A "Reserve request for hot SKU" at 1,0 shape=pill
node B "SOLD_OUT flag set at edge?" at 1,1 shape=diamond color=amber
node C "409 OUT_OF_STOCK" at 2,1 color=red sub="from cache"
node D "Admission bucket has a token?" at 1,2 shape=diamond color=amber
node E "429" at 2,2 color=red sub="jittered Retry-After"
node F "Insert hold row" at 1,3 sub="keyed by order_id and sku_id"
node G "Row already existed?" at 1,4 shape=diamond color=amber
node H "Return the existing hold" at 2,4
node I "Conditional decrement" at 1,5 sub="on shard hash mod k"
node J "rowcount is 1?" at 1,6 shape=diamond color=amber
node K "Hold HELD" at 2,6 color=green sub="expiry in 5 min"
node L "Probed fewer than 3 shards?" at 1,7 shape=diamond color=amber
node M "Sum of shards is 0?" at 1,8 shape=diamond color=amber
node N "Set SOLD_OUT flag" at 2,8 color=red sub="answer 409"
node O "Tail collapse" at 0,8 sub="then retry once"
A -> B
B -> C : "yes"
B -> D : "no"
D -> E : "no"
D -> F : "yes"
F -> G
G -> H : "yes"
G -> I : "no"
I -> J
J -> K : "yes"
J -> L : "no"
L:L -> I:L : "yes"
L -> M : "no"
M -> N : "yes"
M -> O : "no"
```

**What each part does, with numbers.**

- **The reserve is one transaction.** Insert the hold row `(order_id, sku_id, shard_no, qty, HELD, expires_at)` with `ON CONFLICT DO NOTHING`, and if a row was inserted run the conditional decrement on the shard; `rowcount = 0` rolls the transaction back and the next probe starts. The hold's primary key is the idempotency key, so a retried reserve cannot take units twice. Never read `available`, decide in application code, and write it back: that read-then-write is the oversell.
- **Purchase limits bound the tail.** At most 2 units per buyer and one live hold per `(user, SKU)` (assumption). This also blunts scalpers, and it is what keeps `qty` small enough for the tail rule.
- **Tail fragmentation.** Shards deplete unevenly, so late in the sale a request for 2 units can find every probed shard holding 1. When `Σ available < k × max_qty` (here 8 × 2 = 16) a rebalancer collapses the remainder into shard 0 in one transaction and switches the SKU back to single-row mode. The last 16 units then sell at 670/s, which is fine; nobody is racing for them at 3k/s any more. "Sold out" is declared only when the shard sum is zero, never on the first empty probe.
- **Released stock is offered to a waitlist first.** With ~1,200 units cycling through failed payments, opening each release to the public re-triggers a stampede on a nearly empty SKU. The unit goes to the head of a per-SKU <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> waitlist (a notification with a 2-minute claim window, itself a hold) and joins the open pool only after that. The cost is complexity and slightly slower recycling; the benefit is a fair, quiet tail. Simpler variant: flip `SOLD_OUT` off and tell clients to re-check no more often than every 5 s, jittered.
- **Expiry is a sweeper for liveness, a guard for safety.** A background job releases holds where `status='HELD' AND expires_at < now()` using the same guarded release the checkout path uses. Correctness never depends on it: the commit step is `UPDATE holds SET status='COMMITTED' WHERE order_id=? AND sku_id=? AND status='HELD' AND expires_at > now()` using the *database's* clock, so an expired hold cannot commit whether or not the sweeper has run.

More on sharding a single hot key and why probes must be bounded is in [Partitioning and hot keys](../building_blocks/25_partitioning_and_hot_keys.md). The same conditional-update discipline, under a waiting room, is developed in [010 — Seat Reservation](010_seat_reservation_solution.md).

## State machine and legal transitions

```arch
%% caption: Money-affecting steps happen only after every free-to-undo step succeeded, and every arrow is a guarded conditional update on the current state.
grid 250x120
node created "CREATED" at 1,0 shape=pill color=blue
node oos "OUT_OF_STOCK" at 2,0 shape=pill color=red
node expired "EXPIRED" at 0,0 shape=pill color=red sub="auth voided"
node pp "PAYMENT_PENDING" at 1,1 shape=pill color=amber
node cancelled "CANCELLED" at 2,1.5 shape=pill color=slate
node failed "PAYMENT_FAILED" at 0,2 shape=pill color=red
node confirmed "CONFIRMED" at 1,2 shape=pill color=green
node rp "REFUND_PENDING" at 1,3 shape=pill color=amber
node refunded "REFUNDED" at 1,4 shape=pill color=slate
created -> oos : "a line rejected"
created -> pp : "all lines held"
pp:L -> expired:B : "hold lapsed at commit"
pp:L -> failed:T : "declined or not authorized"
pp -> confirmed : "authorized, holds committed"
pp:R -> cancelled:T : "customer cancels"
confirmed:R -> cancelled:B : "cancel before capture"
confirmed -> rp : "cancel or return after capture"
rp -> refunded : "provider confirms refund"
```

| From | To | Trigger | Guard and side effects |
|---|---|---|---|
| `CREATED` | `PAYMENT_PENDING` | All lines held | `WHERE state='CREATED'`; writes `hold_expires_at`; outbox `PaymentRequested` |
| `CREATED` | `OUT_OF_STOCK` | Any line rejected | Release the lines already taken |
| `PAYMENT_PENDING` | `CONFIRMED` | Authorization succeeded **and** every hold committed | Commit is conditional on `HELD` and unexpired; outbox `OrderConfirmed` to fulfillment |
| `PAYMENT_PENDING` | `PAYMENT_FAILED` | Definitive decline, or the unknown-outcome protocol finds no authorization | Release holds |
| `PAYMENT_PENDING` | `EXPIRED` | Hold commit rejected because the hold lapsed | Void the authorization; nothing was captured, so no refund |
| `PAYMENT_PENDING` | `CANCELLED` | Customer cancels before confirmation | Void any authorization; release holds |
| `CONFIRMED` | `CANCELLED` | Cancel before capture | Void authorization; return committed units to stock |
| `CONFIRMED` | `REFUND_PENDING` | Cancel or return after capture | Create a `refunds` row with its own idempotency key |
| `REFUND_PENDING` | `REFUNDED` | Provider confirms the refund | Post reversing journal entries; restock if the goods returned |

Rules that make the table safe:

1. **Every transition is a conditional update**: `UPDATE orders SET state=:to, version=version+1 WHERE order_id=:id AND state IN (:allowed_from)`, in the same transaction as its `order_events` row and any outbox row. Rowcount 0 means re-read: if the order is already in `:to`, treat it as success (a retry); if it is elsewhere, the transition is illegal, so log it, alert, and do not retry.
2. **Terminal states are terminal.** `OUT_OF_STOCK`, `PAYMENT_FAILED`, `EXPIRED`, `CANCELLED`, and `REFUNDED` are never revived by a late success. A late "authorized" or "captured" event on a terminal order triggers compensation (void or refund) and, if the customer still wants it, a fresh checkout. This trades a small chance of asking a customer to re-buy for never having to prove that a resurrected order is still safe to fulfill.
3. **Side effects follow the state, not the request.** Releasing holds, voiding, and refunding are driven from outbox rows or the reconciler, each with its own idempotency key, so a crash between "state changed" and "side effect done" is healed by re-running, not by hoping.
4. **Provider events may arrive out of order** (captured before authorized). Payment statuses advance only forward along `NEW → AUTHORIZED → CAPTURED → REFUNDED`; a stale event that would move backward is stored and ignored.

## Provider calls: authorize versus capture

**The problem.** The provider can charge successfully and lose the response. If the saga treats a timeout as a failure it releases the stock and tells the customer "failed", the customer retries with another card, and the first charge is still live: a double charge. Two decisions prevent it: split the money movement into authorize and capture, and make every provider call idempotent.

| Approach | What it gives | What it costs |
|---|---|---|
| Single-step charge (authorize and capture together) | One call, one round-trip, simplest | A charge that must be undone by a *refund*: fees on both legs, and settlement takes days to reach the customer's statement |
| **Authorize at checkout, capture later** (chosen) | Authorization reserves funds and can be *voided* without a settled charge; capture happens at fulfillment (or immediately for digital goods) | Two calls, an authorization that lapses after some days (card networks and issuers define the window; check your provider), and a capture that can still fail |
| Payment object created first, then confirmed (for example Stripe's PaymentIntents model) | The provider holds a durable object with an id before money moves, which shrinks the unknown-outcome window | Provider-specific lifecycle to model |

**Decision.** Confirm the order when the authorization succeeds and the holds are committed; capture separately. This trades a second provider call and a rare capture failure for a fast happy path (one provider call inside the 3 s budget) and cheap, fee-free rollbacks; the cost is acceptable because capturing an authorized amount fails rarely and the failure has a defined compensation (below).

**Idempotency keys, per call.** Each provider call carries a key derived from our own ids, so a retry is by construction the same request: `auth:{order_id}:{attempt}`, `capture:{payment_id}`, `void:{payment_id}`, `refund:{order_id}:{n}`. As documented for providers such as Stripe, a repeated key with the same parameters returns the first call's stored result (including a failure), and a repeated key with different parameters is rejected. So retrying a timed-out authorization is safe, and a *declined* authorization must not be retried on the same key (it returns the same decline); a customer trying a new card is a new `attempt` with a new key.

**The unknown-outcome protocol** (timeout, 5xx, dropped connection) for an authorization:

1. Do not change the order. It stays `PAYMENT_PENDING` with `payments.status = AUTH_UNKNOWN`.
2. Retry the same key with backoff (250 ms, 500 ms, 1 s, …) inside a 30 s window. If the first call reached the provider, the retry returns its result; if not, it executes fresh.
3. If still unknown, look the payment up by our reference (we send `order_id:attempt` as the merchant reference or metadata on every call). Found authorized: continue as a success. Found declined: fail. Found nothing: wait the provider's documented settling delay, look again, and only then mark the attempt failed.
4. If an authorization appears *after* we gave up, a webhook (or the reconciler) sees `authorized` on an attempt whose order is terminal and **voids** it. The void is idempotent on `void:{payment_id}`.

The result: a timeout can cost a few seconds of `PAYMENT_PENDING`, but it cannot produce two live authorizations, and it cannot leave one behind. See [Application resilience patterns](../building_blocks/12_application_resilience_patterns.md) for the retry and circuit-breaker rules the worker applies (bounded retries, jitter, a breaker that stops calling a provider that is timing out for everyone).

**Webhooks as a second source.** Verify the signature and timestamp, then `INSERT INTO provider_events(event_id, …)`; a unique-key conflict is a duplicate and a no-op. The payload applies through the same guarded transitions as the saga, so the two paths cannot disagree: whichever arrives first wins and the other is a no-op. With callbacks arriving up to tens of seconds late, the design never *waits* for a webhook on the happy path; it uses the provider's synchronous response and treats the webhook as the safety net for the lost response.

**If the provider offers no idempotency key.** Then never auto-retry a non-idempotent call. Send the merchant reference, and on a timeout look up by reference before doing anything else (step 3 above becomes the only path). Say this out loud in the interview; it is the honest fallback.

## Partial failure, cancel, and refund flows

Each row says what has happened to money and stock at the moment of the failure, and the compensation that restores the invariant.

| Failure point | Money | Stock | Compensation |
|---|---|---|---|
| Line 2 out of stock after line 1 was held | None | Line 1 held | Release line 1 (idempotent on `(order_id, sku_id)`), order `OUT_OF_STOCK` |
| Authorization declined | None | Held | Keep the hold while the customer may try another method (up to 3 attempts inside the hold TTL), else release and `PAYMENT_FAILED` |
| Authorization succeeded, hold commit rejected (lapsed) | Authorized | Already released, possibly resold | Void the authorization, order `EXPIRED`; no refund needed, no fees |
| Authorization succeeded, saga crashes before `CONFIRMED` | Authorized | Held or committed | The outbox event is redelivered; every step is idempotent, so the saga resumes; the reconciler picks up anything older than 2 min |
| Authorization outcome unknown | Unknown | Held | Unknown-outcome protocol above; hold TTL (extended once while resolving, up to 10 min) bounds it |
| Late `authorized` webhook on a terminal order | Authorized | Released | Void |
| Async payment method (bank redirect, wallet) succeeds after the hold lapsed | Captured or authorized by the method | Released | Void or refund; customer told to re-buy if stock remains |
| Capture fails after `CONFIRMED` | Authorized (maybe lapsed) | Committed | Retry `capture:{payment_id}`; on a definitive failure move to `CANCELLED`, return the units to stock, and notify the customer; alert if the rate exceeds baseline |
| Customer cancels before capture | Authorized | Committed | Void, restock, `CANCELLED` |
| Customer cancels or returns after capture | Captured | Committed | Refund with key `refund:{order_id}:{n}`, `REFUND_PENDING`, then `REFUNDED` and reversing journal entries |
| Partial refund (one line) | Captured | Partial | Refund amount computed from `order_items.line_total` (and its tax share), never from today's catalog price, and guarded by `refunded + amount ≤ captured` |
| Refund fails at the provider | Captured | Committed | Retry with the same key; after N attempts route to a manual queue; `REFUND_PENDING` age is alarmed |

Two principles keep these tables short. **Order the saga so the irreversible step is last**: hold, authorize, commit, confirm are all undone for free; capture is the only step that costs money to undo. **Every compensation is idempotent and keyed**, so "run it again" is always a legal recovery.

## Reconciliation

Webhooks and retries give convergence in the common case; reconciliation catches everything they miss. It has three loops.

1. **Stuck-order sweep (every 30 s).** Query the partial index for orders in `CREATED` older than 60 s, `PAYMENT_PENDING` older than 2 min, or `REFUND_PENDING` older than 5 min. For each, ask the provider for the truth (by reference), then drive the same guarded transition the saga would have. At 830/s with ~2 s in flight there are only ~1.7k rows in these states, so this is a small indexed scan, and it is what turns "reconciliation within minutes" from a hope into a bound: the worst case is the sweep interval plus one provider lookup, well under 5 minutes.
2. **Provider settlement match (hourly for recent, daily for the settled file).** Join the provider's charge and refund records to `payments` on `provider_ref`. Four mismatch classes: (a) provider charge with no local payment (an orphan charge: void or refund it and investigate), (b) local `CONFIRMED` with no provider record (revenue leakage: hold fulfillment), (c) amount or currency differences, (d) refund differences. Each mismatch writes an `adjustment` event and a journal correction; **nothing is edited in place**, so the audit trail stays intact.
3. **Inventory invariant check (continuous).** For every SKU verify `Σ available + Σ HELD/COMMITTED qty = initial + restocks − write-offs`. Then the specific breaks: `HELD` past `expires_at` plus a grace period (a leaked hold: release it), `COMMITTED` with a terminal-failed order (release it), and `CONFIRMED` with an uncommitted hold (an oversell risk: page).

Reconciliation is the reason the failure table can say "flag, never guess". Its throughput is tiny; its value is that every silent failure of the fast path becomes a countable, alarmed, fixable row within minutes.

## Cart versus checkout prices

The **cart** is a mutable, cache-backed convenience with no promises: prices in it may be minutes old, and promotions may have ended. **Checkout** is a commitment, so it works from an immutable snapshot.

1. When the customer starts checkout, the server re-prices the cart authoritatively (catalog price, promotion rules, tax, shipping) and stores a `price_quotes` row: lines, totals, currency, `cart_hash`, `expires_at` (10 minutes, assumption), and a signature. The customer sees exactly those numbers.
2. `POST /v1/checkouts` carries `quote_id`, never an amount. The server verifies the signature, that `cart_hash` still matches the cart, and that the quote has not expired (410 `QUOTE_EXPIRED` if it has). The charge is `order.total`, copied from the quote into the order and its lines.
3. If the cart changed, or the business rule is to re-validate the live catalog and the price moved, the server answers `409 PRICE_CHANGED` with a new quote for the customer to accept. **Never charge an amount the customer has not seen.**
4. The lines are immutable copies. Later catalog changes cannot alter a placed order, and refunds, tax reports, and disputes are computed from the order's own lines.

The policy choice is what to do about a price that rises inside the quote window. Honoring the quote gives the customer a promise they can see, at the cost of absorbing a rare price rise; re-validating avoids the loss but adds a 409 at the worst moment (mid-flash-sale). I honor the quote until it expires and keep the window short, because a 10-minute exposure is a small, bounded cost while a mid-sale price prompt is a conversion killer.

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Hold expires before payment completes | The saga commits holds *before* confirming; a lapsed hold fails the conditional commit, the authorization is voided, and the order ends `EXPIRED`. Never confirm an order against a lapsed hold. |
| Duplicate checkout request (client retry) | Idempotency key finds the existing order; return its current status. A retry that finds `CREATED` resumes the workflow, and neither a second order nor a second authorization is created. |
| Payment provider callback arrives twice | Dedupe on provider event ID; the second delivery is a no-op against an already-processed event and an already-advanced payment status. |
| Late callback after the saga gave up | The order is terminal; a late `authorized` is voided, a late `captured` is refunded. The order is never resurrected. |
| Reconciliation mismatch (provider settled, internal record missing or differs) | Write an auditable adjustment event and route it to the automated or manual queue; never silently edit the financial journal. |
| Hot SKU oversold under concurrent holds | The conditional decrement is the enforcement point; the design forbids read-then-write. Sharded counters preserve this, because each shard's decrement is still conditional on its own `available`. |
| Payment provider slow or down | Per-call deadlines and a circuit breaker; orders stay `PAYMENT_PENDING` (holds extended once, up to 10 min) and the customer sees "processing". Do not fail over the *same* attempt to a second provider without first voiding the first one's authorization. Queue depth and pending age alarm. |
| Inventory shard unavailable | Fail closed: checkouts touching those SKUs get a 503 or `OUT_OF_STOCK`; never sell without a hold. Other SKUs are unaffected because inventory partitions by SKU. |
| Order-DB primary failover | Idempotency keys and orders live in the same shard, so dedupe survives failover. With synchronous replication across zones there is no loss; with async cross-region promotion the tail may be lost, and the reconciler's provider-versus-orders join finds any authorization with no order and voids it. |
| Zone or region failure | Order shards run a primary plus synchronous replicas across three zones; a region loss promotes the async replica and heals through reconciliation: an order lost in the replication tail means the client's retry mints a new order, and the provider-versus-orders join voids the orphaned authorization, so the customer sees at most a temporary hold on funds, never a capture. Provider and webhook endpoints are multi-region. |
| Saga worker or outbox relay crashes | Events are redelivered at least once; every step is idempotent. Lag on the outbox and the age of the oldest `PAYMENT_PENDING` are alarmed. |
| Bad deploy of the saga or state machine | Roll out by percent of order shards behind the invariant metrics (double authorization, oversell, illegal-transition count); an illegal transition or a nonzero invariant halts the rollout. Because every transition is guarded and logged, a bad version cannot silently corrupt state. |
| Forged or replayed webhook | Signature and timestamp tolerance verified before storage; `event_id` uniqueness kills replays. |
| Bots, scalpers, card testing | Per-user and per-SKU limits (2 units, one live hold per buyer), a waiting room or queue for known drops (see [010 — Seat Reservation](010_seat_reservation_solution.md)), velocity checks on cards and addresses **before** the authorization call (a decline costs fees and card-network reputation), and challenges on anomalies. |

## Observability and interview close

Measure: checkout success rate excluding customer declines, synchronous latency p50/p99 with a per-stage split, oldest-`PAYMENT_PENDING` age, hold expiry rate and hold-to-confirm latency, idempotency hit rate, provider latency p50/p99 and timeout rate, unknown-outcome resolution time, webhook lag and duplicate rate, outbox lag, reconciliation mismatches per day by class, hot-SKU lock-wait p99 and shard skew, and the two invariants directly: **oversell** (orders `CONFIRMED` against an expired or consumed hold, or `Σ` inventory not balancing) and **duplicate money** (orders with more than one live authorization or capture).

The one paging alert is **any nonzero oversell or duplicate-money invariant**, because it is the zero-tolerance requirement burning. Ticket-level signals: age of the oldest `PAYMENT_PENDING` crossing 2 min (the "reconciliation within minutes" <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>), reconciliation mismatch rate crossing a small absolute threshold, and payment saga backlog age.

Interview close: "I never call an external payment provider while holding a database lock — checkout uses a local transaction to durably record intent (order, outbox event), holds stock with a conditional update keyed by the order, and a separate saga drives the slow, fallible provider call, with idempotency keys on both the client request and every provider call, and reconciliation as the backstop for the outcomes I can't observe in real time."

Trade-off to state: "I authorize and hold stock before confirming and capture later, so a rollback is a free void instead of a fee-bearing refund, at the cost of an extra `PAYMENT_PENDING` state, an authorization that can lapse, and a reconciler to run; the cost is acceptable because the alternatives are overselling or holding locks across a remote call."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Make one region the writer for a user's orders (by home region) and keep the idempotency key with the order, so a retry after failover lands on the same record. Inventory needs a home per SKU; a cross-region hold costs a round trip, so for a global drop give each region a stock quota (sized from expected demand) and rebalance slowly, accepting "sold out here, in stock there" as the price of local latency. Provider keys derive from order ids, so a re-driven saga in another region cannot double charge.
2. **"What changes at 10× and 100×?"** At 10× (8.3k/s sustained, 25k/s burst) the order shards grow from 16 to ~160 or the rows per shard are cut by batching; the sharded counters raise k; the provider's rate limit contract becomes the first hard wall. At 100× (83k/s) run the whole stack as independent cells per user cohort, add multiple provider accounts or acquirers, and move hot SKUs to the serialized allocator because per-row parallelism stops being enough.
3. **"What if I need strict no-oversell and strict fairness?"** Use the per-SKU serialized allocator (single writer, <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> log) so the order of arrival is the order of decision, and never shard the counter, which removes tail fragmentation. The cost is a stateful tier and a failover gap; hold stock only when the user reaches payment, since holds at add-to-cart starve inventory with abandoned carts.
4. **"What dominates cost?"** Provider fees are a percentage of the money moved and dwarf compute, so the levers are authorization approval rate, avoiding refunds by preferring voids, not paying for declines (fraud checks first), and retry policy. Infrastructure is small: 4.6 TB/year of orders and a few thousand provider calls per second at burst.
5. **"How do you defend against abuse?"** Purchase limits per user and payment method, a waiting room in front of announced drops, bot and velocity scoring before the authorization call, single-use checkout tokens, and per-SKU admission buckets so a crowd cannot turn the hot row into a denial of service for every other product.
6. **"Why not charge first and reserve after?"** Payment succeeds, stock has sold out, and you are refunding paying customers: fees, chargebacks, and trust. Reserve-then-authorize means the expensive, slow, fallible step only happens for orders we can actually fulfill.
7. **"Why not a distributed transaction across order, inventory, and payment?"** The provider is not a transaction participant, and holding locks across a remote call with tens-of-seconds tails is the outage we are avoiding. A saga with compensations gives the same safety with bounded, visible intermediate states.
8. **"What if the interviewer says sharded counters are over-engineered and a single row with retries is fine?"** Show the arithmetic: 3k attempts/s against a ~670/s row means a backlog growing ~2.3k/s and waits in the tens of seconds; retries make it worse (a retry storm). Concede that for the 99.9% of SKUs that never see a drop a single row is correct, which is exactly why the design promotes only the hot SKUs.

## Common mistakes

1. **Treating a timeout as a failure.** The charge may have succeeded, so releasing stock and telling the customer to retry produces a double charge. Keep the order pending and resolve with the same idempotency key, then a lookup by reference.
2. **Calling the provider inside a database transaction.** Provider latency becomes lock hold time and a provider incident becomes a full outage. Commit intent first, call outside.
3. **A server-generated idempotency key per request.** A key minted per <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> request dedupes nothing. The client generates one key per intent and reuses it; provider keys derive from stable ids plus an attempt number.
4. **Decrementing inventory after payment.** A window opens between charge and decrement where the same unit is sold twice. Hold first, authorize second.
5. **Read-then-write on stock.** Two buyers read `available = 1`, both write. Use one conditional update whose `rowcount` decides.
6. **One row for a hot SKU, or sharded counters with no tail rule.** The first queues every buyer behind a lock; the second reports "sold out" while units sit in other shards. Shard by measured burst, collapse the tail, and declare sold out only on a zero shard sum.
7. **Trusting a client-supplied price, or repricing at confirm from the live catalog.** The customer is charged something they never saw. Charge the snapshot in the order.
8. **Reconciliation that edits rows.** A silently "fixed" mismatch destroys the audit trail. Post an adjustment or reversing entry, and page on invariant violations instead of smoothing them.

## Going from L5 to L6

- **Migration path.** Start with inventory and orders in one database and a single conditional update (correct and simple). Extract inventory into its own service when contention or ownership demands it, running the new allocator in shadow mode (compare its counts against the old) and cutting over SKU by SKU behind a flag. Add sharded counters only for SKUs that trip the hot threshold.
- **Cost model.** Provider fees dominate; compute is small. Express the design as levers (authorization rate, void versus refund mix, retry policy, fraud checks before authorization) and measure each in currency per thousand orders before optimizing infrastructure.
- **Ownership and blast radius.** Separate order, inventory, payment-saga, and ledger owners with their own quotas and on-call. An inventory outage should reject only the affected SKUs; a provider outage should leave orders `PAYMENT_PENDING` but never affect browsing or the cart.
- **Build versus buy.** Buy the payment mechanics (a provider's payment-object model already tracks the lifecycle) and consider a workflow engine for the saga instead of hand-rolled outbox workers; build the order state machine, the allocator, and the reconciler, because they encode your correctness invariants.
- **What to measure first.** The provider's real latency distribution and timeout rate, the authorization decline rate during drops, the concurrency a hot SKU actually draws, and the per-row lock-hold time of your database. Every number in the hot-SKU table moves with them.
- **Phased rollout of the invariants.** Ship the oversell and duplicate-money counters and the reconciler *before* the first flash sale, and run a game day that kills the saga mid-flight and drops provider acks.

## Build exercise

Implement an order state machine (`CREATED → PAYMENT_PENDING → CONFIRMED` or `PAYMENT_FAILED` or `EXPIRED`, with guarded transitions and an `order_events` log) plus a fake payment provider that randomly times out *after* actually succeeding, duplicates webhooks, and delivers them out of order; simulate concurrent buyers against a single hot SKU with k sharded counters and duplicate client retries. Named assertions:

- `test_no_oversell_hot_sku`: 200 units, 5,000 concurrent buyers, k = 8; assert confirmed units ≤ 200 and that `Σ available + held + committed = 200` at every step.
- `test_duplicate_requests_one_order`: send 50 concurrent requests with one idempotency key; assert exactly one order, one authorization call at the provider, and identical responses.
- `test_timeout_after_success_is_not_a_failure`: the fake provider authorizes then drops the ack; assert the order ends `CONFIRMED` with one live authorization and stock committed once.
- `test_expired_hold_voids_never_captures`: delay the provider past the hold TTL; assert the order is `EXPIRED`, the authorization is voided, and no capture was issued.
- `test_duplicate_and_reordered_webhooks_converge`: deliver every event twice and shuffled; assert the same final state and each `event_id` processed once.
- `test_late_authorization_on_terminal_order_is_voided`: fail the order, then deliver a late `authorized`; assert a single void and no state change on the order.
- `test_tail_collapse_no_phantom_sold_out`: sell down to 15 units across 8 shards; assert requests for 2 units still succeed until the shard sum is zero.
- `test_illegal_transition_rejected`: attempt `CONFIRMED → PAYMENT_FAILED`; assert rowcount 0, no event row, and an illegal-transition counter increment.
- `test_reconciler_heals_stuck_order`: kill the saga after authorization, before `CONFIRMED`; assert the sweep completes the order within its interval and never double-authorizes.
