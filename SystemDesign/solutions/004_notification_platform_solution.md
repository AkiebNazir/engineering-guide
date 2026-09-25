# 004 — Notification Platform: Full System Design Solution

## Requirements and invariants

The platform delivers product events over email, push, and SMS. Users control consent, channels, quiet hours, locale, and time zone. A password reset is urgent; a 20-million-recipient campaign is low priority. Provider APIs can time out, callbacks can arrive twice, and a product event must not create duplicate user notifications.

The invariant is not "exactly once sent"—a provider can accept a message while its response is lost. The useful promise is: each notification intent is recorded, delivery attempts are auditable, and duplicate sending is prevented as far as the channel/provider contract allows.

**Functional scope:** accept notification requests from internal services (single recipient or campaign), apply preferences/consent/quiet hours, render templates per locale, deliver over push (APNs/FCM), email, SMS, and in-app inbox, track delivery/open/bounce, and expose status. **Out of scope:** authoring UI for marketing campaigns, the email provider itself.

**Non-functional:** the question's contract is a password reset *delivered* within 10 s at p99. We own the first half, so the budget is transactional p99 intent-to-provider-handoff under 5 s, leaving about 5 s for the provider and network (push is usually a second or two; email and SMS delivery time depends on the carrier or mailbox provider, which is why the promise is handoff plus a per-channel delivery <abbr title="Service Level Indicator - A carefully defined quantitative measure of some aspect of the level of service that is provided, such as latency.">SLI</abbr>, not a guarantee of inbox time); campaigns may take hours but must not delay transactional traffic; no lost intents (durable before acknowledging the caller); duplicates rare and bounded; regional data residency for PII.

## Scale estimates

| Quantity | Assumption | Result |
|---|---|---|
| Users | 500M, 40% with push enabled | — |
| Notifications/day | ~4 per user average | 2B/day ≈ **23k/s average**, peak 3-5× ≈ 70-115k/s (design for 100k/s) |
| Largest campaign | 20M recipients within 1 hour | ≈ 5.5k/s sustained for that campaign alone |
| Intent record | ~500 bytes (ids, template ref, params, status, timestamps) | 2B × 500 B ≈ **1 TB/day**; 30 days hot ≈ 30 TB, then archive |
| Attempt/callback events | ~2 per notification | ~4B events/day ≈ 46k/s average on the event log |
| Providers | SMS ≈ $0.005-0.05 per message (assumption; varies by country and volume) | SMS volume is a cost decision, not just an engineering one: a 20M-recipient SMS campaign would cost about $100k-$1M |

The numbers that shape the design: the **100k/s peak** (partitioned queues, horizontally scaled workers), **provider rate limits** (usually lower than our peak, so we need per-provider throttling and backlog), and **SMS cost** (preference and dedupe correctness saves real money).

## <abbr title="Application Programming Interface">API</abbr>

```http
POST /v1/notifications
Idempotency-Key: order-812-shipped-user-42
{
  "recipient": {"user_id": "42"},
  "category": "order_update",          // maps to preference + priority class
  "template": "order_shipped", "template_version": 7,
  "params": {"order_id": "812", "eta": "2026-09-20"},
  "channels": ["push", "email"],        // allowed channels; policy may narrow
  "not_before": null, "expires_at": "2026-09-19T00:00:00Z"
}
→ 202 {"notification_id": "ntf_9f..", "status": "ACCEPTED"}

POST /v1/campaigns        {"segment_id": "...", "template": "...", "schedule": "...", "rate_limit_per_s": 5000}
GET  /v1/notifications/{id}          → status per channel and attempt history
PUT  /v1/users/{id}/preferences      → categories × channels, quiet hours, time zone
POST /v1/providers/{name}/webhook    → signed delivery/bounce/complaint callbacks
```

`202 Accepted` — the caller gets durability, not delivery. Replaying the same `Idempotency-Key` returns the same `notification_id`.

## Data and architecture

```arch
%% caption: A product event becomes a durable, deduplicated intent before any provider is called; queues and token buckets pace the sends, and provider callbacks only update attempt state.
node product "Product service" at 1,0 icon=service sub="DB + outbox"
group core "Notification platform" color=blue icon=notify
node intake "Notification intake" at 1,1 in core icon=api sub="dedupe, route"
node intent "Intent store" at 2,1 in core icon=nosql sub="intents + attempts"
node pref "Preferences" at 2,2 in core icon=kv sub="consent, quiet hours"
node queue "Priority + channel queues" at 1,3 in core icon=queue sub="partitioned by user_id"
node sched "Schedule store" at 2,3 in core icon=time sub="not_before buckets"
node workers "Email / push / SMS workers" at 1,4 in core icon=worker
node buckets "Provider token buckets" at 2,4 in core icon=counter sub="shared store"
node provider "Provider" at 0,5 icon=email sub="email, push, SMS"
product -> intake
intake -> intent : "record"
intent -> pref : "evaluate"
pref:L -> queue:T : "enqueue"
pref -> sched : "quiet hours"
sched:L ..> queue:R : "due"
queue -> workers
workers -> buckets : "take token"
workers:B -> provider:R : "send"
provider:T ..> intake:L : "signed webhook"
```

```arch
%% caption: The intent is durable before any provider is called; the provider callback only ever updates delivery-attempt state, never creates a new intent.
node Product "Product DB + outbox" at 0,1
node Intake "Notification intake" at 1,1
node Intent "Intent store" at 2,1
node Pref "Preference store" at 3,1
node Queue "Priority queues" at 3,2
node Worker "Workers" at 2,2
node Provider "Provider" at 1,2

Product -> Intake : "event"
Intake -> Intent : "record intent"
Intent -> Pref : "evaluate prefs"
Pref -> Queue : "enqueue"
Queue -> Worker : "dequeue"
Worker -> Provider : "send"
Provider -> Worker : "accepted/rejected"
Provider -> Intake : "signed webhook"
Intake -> Intent : "update state"
```

`NotificationIntent(event_id, user_id, template_version, channel, status)` has a unique key across the logical event/recipient/channel. Store preference snapshot or decision evidence, template version, provider message ID, attempts, and timestamps. Keep transactional and marketing queues/pools separate; otherwise campaign fanout starves recovery/security messages.

**Storage choices.** Intents and attempts: a horizontally scalable store keyed by `notification_id` with a secondary lookup by `(user_id, created_at)` for the inbox and support tooling (Bigtable/Cassandra/DynamoDB-style wide-column works; Spanner if you need cross-row transactions). Preferences: a relational or strongly consistent KV store, cached with short TTL and change events for invalidation. Queues: a partitioned log (Kafka/Pub/Sub) partitioned by `user_id` so per-user ordering and dedupe are local to a partition. Device tokens: KV `user_id → [token, platform, last_seen]`.

## Flow and trade-offs

Product service writes its change and outbox row atomically. Intake creates idempotent intents, evaluates consent/quiet hours, schedules delayed work where needed, and routes by priority. A worker claims an attempt, calls a provider with provider idempotency reference if supported, then records result. Callback signature/timestamp/replay checks update the same delivery record idempotently.

Do not send inline from product requests: a slow provider turns signup/checkout into an outage. Do not expand a 20M campaign in one giant transaction: batch/partition recipient expansion and enforce provider/tenant quotas. "At least once queue delivery plus idempotent intent" is safer than pretending the entire external send is exactly once.

## Deep dive 1: Deduplication without pretending to be exactly-once

Three layers, each cheap:

1. **Intake dedupe.** Unique constraint on `idempotency_key` (or `(event_id, user_id, category)`). A retried <abbr title="Application Programming Interface">API</abbr> call or a replayed outbox event hits the constraint and returns the existing intent.
2. **Worker claim.** An attempt row moves `PENDING → SENDING` with a conditional update (`WHERE status = 'PENDING'`), plus a lease timeout. Two workers that both received the same queue message can't both claim it.
3. **Provider idempotency.** Pass our attempt id as the provider's idempotency/reference key when supported (many email/SMS APIs support it). If the provider times out *after* accepting, the retry is deduplicated on their side; if not supported, we accept a small duplicate risk and prefer it over silently dropping a password reset.

The one unavoidable window: the worker calls the provider, the provider accepts, and the worker crashes before recording it. Retrying may duplicate; not retrying may lose. Choose per category: **retry for security/transactional, don't retry past the lease for marketing.**

## Deep dive 2: Priority isolation and provider rate limits

```arch
%% caption: Each priority class gets its own queue and worker pool, and every pool draws from the same per-provider token buckets.
node intake "Intake" at 0,1 icon=api
node tq "Transactional queue" at 1,0 icon=queue sub="per channel"
node sq "Standard queue" at 1,1 icon=queue
node bq "Bulk / campaign queue" at 1,2 icon=queue
node tp "Dedicated worker pool" at 2,0 icon=worker
node sp "Shared pool" at 2,1 icon=worker
node cp "Capped pool" at 2,2 icon=worker
node tb "Per-provider token buckets" at 3,1 icon=counter sub="global, shared store"
intake:R -> tq:L
intake -> sq
intake:R -> bq:L
tq -> tp
sq -> sp
bq -> cp
tp:R -> tb:T
sp -> tb
cp:R -> tb:B
```

- **Separate queues and worker pools per priority class.** Weighted fair queuing is not enough on its own: if a campaign consumes all provider rate-limit tokens, transactional traffic still waits. Reserve a share of each provider's quota for transactional traffic.
- **Per-provider and per-tenant token buckets** stored centrally (see `002_rate_limiter_solution.md`). Workers take a token before calling the provider; no token → message stays queued (backpressure), it is not dropped.
- **Provider failover:** if the primary SMS provider's error rate crosses a threshold, a circuit breaker opens and traffic shifts to a secondary provider for the same channel.
- **Campaign pacing:** a campaign is expanded in batches of, say, 10k recipients by a scheduler that watches bulk-queue age; if age grows, expansion slows. A 20M campaign becomes a steady stream, not a spike.

## Deep dive 3: Quiet hours, time zones, and scheduled sends

- Store the user's IANA time zone. A notification that falls inside quiet hours gets a `not_before` computed in the user's local time (careful with DST transitions).
- Delayed delivery uses a **time-bucketed schedule store**: rows keyed by `(bucket = floor(send_at to minute), shard)`; a scheduler scans the current minute's buckets and enqueues due items. It's the same design as `012_workflow_scheduler_solution.md`, simplified. A timing wheel in memory works for short delays but must be rebuilt from durable storage after restart.
- "Send at 9 AM local time" campaigns naturally spread load across 24 hours of time zones.
- Always check `expires_at` at send time: a "your ride is arriving" push delivered 40 minutes late is worse than none.

## Failure, security, and operations

Retry transient errors with exponential backoff/jitter and a max age/attempt policy. DLQ permanent failures with a replay tool; bounce/complaint events update channel eligibility. If preference service is unavailable, prefer a conservative policy for marketing and a documented exception for security messages.

Protect PII, phone/email addresses, templates, and webhook secrets. Audit preference changes and privileged campaigns. Measure intent-to-delivery latency by priority, queue age, provider acceptance/error/bounce, duplicate rate, opt-out violations, DLQ count, and notification cost. Build email first, then add a fake provider that returns timeout-after-accept to prove idempotency.

| Failure | Behavior |
|---|---|
| Provider down | Circuit breaker, failover to secondary provider or hold in queue until `expires_at` |
| Push token invalid (APNs/FCM says unregistered) | Delete the token; don't retry |
| Hard email bounce / spam complaint | Suppress that address for that channel; required for sender reputation |
| Intake region outage | Callers' outbox relays retry; intents are idempotent so replays are safe |
| Template render error | Fail that intent to DLQ with the template version; don't block the queue |
| Duplicate webhook | Idempotent update keyed by provider message id + event type |

**Compliance:** marketing requires opt-in in many jurisdictions (e.g., GDPR/ePrivacy in the EU, TCPA for US SMS); every marketing email needs a working unsubscribe link, and unsubscribes must take effect promptly. Store consent with timestamp and source.

## Interview close

"I treat a notification as a durable, idempotent intent with an auditable attempt history, because external providers make exactly-once delivery impossible. Priority classes get separate queues, worker pools, and reserved provider quota, so a 20M campaign can never delay a password reset. Preferences and quiet hours are evaluated at send time, campaigns are paced by queue age, and dedupe happens at intake, at worker claim, and at the provider when it supports idempotency keys."

## Follow-ups the interviewer will ask

1. **"How does this work across regions, with data residency?"** Keep each user's intents, preferences and device tokens in their home region and run intake, queues and workers there, so PII never crosses a border. A global campaign controller splits a campaign into per-region shards, each with its own rate budget, and the idempotency key is enforced in the home region only. If a region fails, a paired region may take over only where residency rules allow it; otherwise its transactional messages queue until it recovers, and you state that trade-off.
2. **"What changes at 10× and 100×?"** At 10× peak is about 1M intents/s and 460k callbacks/s; the log ingest is 500 MB/s at 500 B per intent, so partitions and workers scale out, but provider rate limits bind first. At 100× you need several providers per channel, dedicated sending <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> pools for email, direct carrier or aggregator connections for SMS, and a cell-per-region design so one bad partition does not affect everyone.
3. **"What if unsubscribes and quiet hours must be honoured strictly, and duplicates are never acceptable?"** Check consent at send time from a version-stamped cache invalidated on write (about 100k lookups/s at peak, mostly cache hits), and give each user an opt-out epoch so queued items from before the change are dropped by the worker. Exactly-once across a provider boundary is impossible; get effectively-once with provider idempotency keys, and where a channel (often SMS) lacks them, state the small duplicate window per category.
4. **"What dominates cost?"** SMS: at the assumed $0.005-0.05, one 20M-recipient SMS campaign is $100k-$1M, while push and in-app are nearly free. Levers: push first and SMS only if unread after N minutes, suppress dead numbers and bounced addresses, digest low-value messages, and require approval and a budget for any SMS campaign above a cost threshold. Track cost per intent so the number is visible.
5. **"How is it abused, by callers or by attackers?"** A retrying caller can create the "100 copies" problem, so cap per user per category per hour at intake (say 5 pushes an hour) on top of the intent dedupe key. Attackers trigger OTP or verification SMS to premium or foreign numbers ("SMS pumping"), so limit per phone number, per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> and per account, by destination country, and alert on per-country spend. Verify webhook signatures and timestamps, and use signed, unguessable unsubscribe tokens.
6. **"Marketing sent the wrong copy to 20M users. How fast can you stop it?"** Cancelling sets campaign state, and each worker checks a locally cached campaign state refreshed about every 2 s before calling the provider. At 5.6k/s that is at most ~11k more messages plus what is already in flight, versus 168k if it took 30 s. Also make the campaign unique on `(campaign_id, user_id, channel)` so a double-submitted send cannot double-deliver.
7. **"You fail over from SMS provider A to B after a timeout. Can the user get two texts?"** Yes, if A accepted the message and the response was lost. So fail over only on definitive failures or an open circuit breaker, retry ambiguous timeouts on the same provider with the same idempotency reference first, and for transactional messages accept the small duplicate risk after a bounded wait because a lost password reset is worse. Marketing does not fail over past its lease.
8. **"A single priority queue is simpler than separate queues and pools."** A single queue with priority lanes works at small scale, and on brokers without native priorities you end up with separate topics anyway. Separate pools give bulkheads: a hung connection or slow provider on bulk traffic cannot consume the workers or the provider quota that transactional traffic needs, and each class can have its own retry and expiry policy. The cost is more infrastructure to run, which is justified only because a 20M-recipient campaign must never delay a password reset.

## Common mistakes

1. **Promising exactly-once sending.** A provider can accept a message and lose the response. Promise a durable intent, auditable attempts and bounded duplicates.
2. **One queue and worker pool for everything.** A 20M campaign then starves password resets. Separate queues, pools and reserved provider quota per priority class.
3. **Sending inline from the product request.** A slow provider becomes a checkout or signup outage. Return `202` after the intent is durable and send asynchronously.
4. **Evaluating preferences only at intake.** A user who unsubscribes during the one-hour drain still gets the message. Re-check consent at send time.
5. **Expanding a 20M campaign in one transaction or one burst.** It overloads the database and the providers. Expand in batches (2,000 batches of 10k) paced by queue age and provider budget.
6. **Retrying and failing over blindly.** Unbounded retries and provider switches on ambiguous timeouts create duplicates and retry storms. Use idempotency keys, backoff with jitter, a max age, and per-category policy.
7. **Computing quiet hours in server time or ignoring `expires_at`.** Users get messages at 3 a.m. local time, or a ride-arrival push 40 minutes late. Store the IANA time zone (mind DST) and check expiry at send time.
8. **Trusting webhooks and ignoring suppression.** Unsigned callbacks let anyone rewrite delivery state, and ignoring bounces and complaints damages sender reputation. Verify signatures, timestamps and replay, and suppress bad addresses per channel.

## Going from L5 to L6

- **Migration and rollout path.** Move callers off direct provider calls one product at a time through the outbox, running the platform in shadow mode first (compute the decision, do not send, compare with the legacy path). Ramp a new provider from 1% to 10% to 100% of a channel with a one-flag rollback, and version templates so a bad template rolls back without a deploy.
- **Cost model.** Show cost per channel and per intent, identify SMS as the dominant line, and set per-tenant budgets and approval thresholds. Then show the savings from push-first with SMS fallback and from suppression.
- **Ownership and blast radius.** Give the transactional path its own <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> and on-call, isolated from campaigns, and run cells per region so an incident stays local. Product teams own categories and templates; the platform owns delivery, consent and audit; legal owns retention and erasure requests (deleting a user's intents on request).
- **Build versus buy.** Providers (APNs, FCM, an email service, an SMS aggregator) are bought. Build the intent model, the consent and preference store, and priority isolation, since these are where correctness and differentiation live. A thin multi-provider abstraction is cheap insurance against an outage or a price change.
- **What to measure first.** Volume by category, the SMS share, provider timeout and error rates, the duplicate rate, and the fraction of notifications ever opened. That last number decides how much low-value traffic to digest or suppress.
- **Phased evolution.** Ship transactional email and push with idempotent intents, add priority isolation and pacing before the first campaign, add SMS with cost controls, then multi-provider failover and multi-region residency.

## Build exercise

Implement intake with an idempotency-key table, two priority queues, and a worker that claims attempts with a conditional update. Add a fake SMS provider that (a) accepts then times out and (b) rate-limits at 10 msg/s. Assert: no duplicate sends on intake replay, transactional latency unaffected while a 10,000-message campaign drains, and messages past `expires_at` are dropped. Named assertions:

- `test_intake_replay_returns_same_intent`: post the same `Idempotency-Key` twice; assert one intent and one send.
- `test_two_workers_one_claim`: deliver the same queue message to two workers; assert exactly one provider call.
- `test_timeout_after_accept_no_duplicate_with_provider_key`: make the fake provider accept then time out; assert the retry carries the same reference and the provider records one message.
- `test_campaign_cannot_delay_transactional`: drain a 10,000-message campaign at 10 msg/s while sending password resets; assert reset p99 stays within the budget.
- `test_optout_during_drain_is_honoured`: unsubscribe a user mid-campaign; assert no later send to that user.
- `test_cancel_stops_within_two_seconds`: cancel a campaign; assert at most 2 s of further sends.
