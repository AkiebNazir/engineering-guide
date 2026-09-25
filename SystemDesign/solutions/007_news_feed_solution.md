# 007 — News Feed: Full System Design Solution

## Goal and contract

A news feed answers "what should this user see now" from the posts of the accounts they follow. Posts and the follow graph are the source of truth; every feed is a derived, rebuildable projection over them.

Assume (scale numbers are assumptions; the latency and freshness targets come from the question):

- 500M registered users, ~300M daily active (DAU), average 300 follows each.
- 300M posts/day system-wide (the question says "hundreds of millions").
- Home feed read is the hottest endpoint: about 200k page loads/s at peak (derived in Estimates), p99 under 200 ms.
- Some accounts (celebrities) have up to 50M followers.
- A new post is visible in followers' feeds within 30 seconds; a delete or privacy change is reflected within 60 seconds.

The contract is bounded freshness, not strict consistency: a feed may lag the true post/follow state by up to 30 seconds under normal load, and it degrades gracefully — never silently — under backlog. The read path always hydrates current post state (text, media, visibility, delete flag) rather than trusting stale copies baked into the feed, so a delete or privacy change propagates correctly even if the feed entry itself is momentarily stale. Pagination must be stable: paging forward must not skip or duplicate items even as new posts arrive.

The feed is *ranked*, so the 30-second bound is a promise about **eligibility** (a new post is in the candidate set of every follower within 30 s), not about **position** (where the ranker places it is the ranker's business). The one hard decision is the split between pushing a post into followers' precomputed feeds and pulling it at read time, because that choice sets write volume, freshness, and read latency all at once.

## Estimates

- **Posts**: 300M/day ÷ 86,400 ≈ **3.5k posts/s** average, ~10k/s at a 3× peak. The post write path itself is small; the trouble is what each post multiplies into.
- **Feed reads**: 300M DAU × 20 page loads/day (5 sessions × 4 pages, assumption) = 6B/day ≈ **69k/s average, ~210k/s peak**. Each page needs one feed-ref read, ~50 pull-author lookups, and ~25 post hydrations, so the post/profile cache tier sees about 210k × 50 ≈ **10M lookups/s** at peak. So we need a sharded, replicated post cache with a 95%+ hit rate, not reads straight from the post store.
- **Follow graph**: 500M × 300 = **150B edges**. Two indexes (following-of and followers-of) at ~24 B each ≈ 7 TB before replication. So the graph is sharded, and the followers index is chunked, because one 50M-follower account is a 50M-row list.
- **Post storage**: 300M × ~1 KB (text plus metadata; media lives in object storage) = 300 GB/day ≈ **110 TB/year**, ~330 TB with three replicas. So the post store is sharded by `post_id` and old posts move to a cheaper tier.
- **Naive push volume**: 3.5k posts/s × 300 average followers ≈ **1.0M feed-ref writes/s average, 3.1M/s at peak, 90B refs/day**. (The earlier draft of this document claimed 10–50k/s; even its own smaller input, 100M posts/day × 300 = 350k/s, was 7–35× above that claim.)
- **The celebrity burst**: one post from a 50M-follower account is 50M refs. Inside the 30 s freshness bound that is 1.7M writes/s *for a single post* — more than the whole fleet's peak. So the head cannot be pushed, whatever the average says.

## <abbr title="Application Programming Interface">API</abbr>

```text
GET /v1/feed?limit=25&cursor=…
→ 200 { items: [{post_id, author: {id, name, avatar}, body, media: [...], created_at,
                 counts: {likes, comments}, viewer_state: {liked}}],
        next_cursor, has_more, feed_generated_at }
→ 410 if the cursor's snapshot expired (client restarts with no cursor)

POST /v1/posts        { client_post_id, body, media_ids: [...], visibility }
→ 201 { post_id, created_at }        # client_post_id is the idempotency key, retried safely
DELETE /v1/posts/{post_id}           → 204 (idempotent; second call is also 204)

PUT    /v1/follows/{user_id}         → 204 (idempotent follow)
DELETE /v1/follows/{user_id}         → 204 (idempotent unfollow)
```

- **Cursor** is opaque and HMAC-signed: `{snapshot_id, offset, expires_at}`. The client never builds one; the server can change what is inside without a client release.
- **Errors**: 429 on post-rate or follow-rate limits (abuse control), 409 if `client_post_id` was used with a different body, 404 on a deleted post fetched directly.
- **Read your own writes**: `POST /v1/posts` returns the post, and the client inserts it locally. The server also merges the viewer's own recent posts into their next feed read (see Follow-ups).

## Data model

| Entity | Key and shape | Role | Partitioning |
|---|---|---|---|
| `posts` | `post_id` (64-bit, time-ordered) → `author_id, body, media_refs, visibility, created_at, deleted_at, version, fanout_mode` | **Source of truth** | Hash of `post_id`; time-ordered IDs make "newer than X" a key comparison |
| `following` | `(user_id, followee_id)` → `created_at, state` | Source of truth (who I follow) | By `user_id` |
| `followers` | `(author_id, chunk_no, follower_id)` | Source of truth (who follows me), chunked to bound row size | By `(author_id, chunk_no)`, so a 50M-follower list spreads over many shards |
| `author_tier` | `author_id` → `tier (PUSH/PULL), active_followers, tier_changed_at` | Derived, small (~59k pull authors at a 100k threshold) | Replicated everywhere |
| `author_recent` | `author_id` → last ~20 `post_id`s | Derived, tiny (~10 MB for all pull-tier authors) | Replicated into every read-path process |
| `feed_refs` | `user_id` → sorted list of `(post_id, author_id, affinity_hint)`, capped at N=800 | **Derived**, rebuildable, in a fast store | By `user_id` — one user's feed is one shard's write |
| `feed_snapshot` | `snapshot_id` → ordered top ~200 `post_id`s, TTL 30 min | Derived, per session, powers stable pagination | By `snapshot_id` |
| `outbox` | `(post_id, event_type, ts)` written in the post's own transaction | Reliable hand-off to fan-out workers | With the post |

`fanout_mode` is stamped on the post at creation (PUSH or PULL). That single field is what makes retries and tier migrations safe (see the migration rules below).

## Fanout strategies

| Strategy | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Push (fanout-on-write) | On post creation, write a feed-reference row into every follower's feed. | Normal accounts with bounded follower counts; optimizes for read latency. | A celebrity post triggers tens of millions of writes — fanout storm. |
| Pull (fanout-on-read) | Feed is assembled at read time by merging recent posts from all followed accounts. | Celebrity/high-fanout accounts, or low-traffic followers who rarely read. | Read-time merge across hundreds of authors is expensive per request; higher read latency. |
| Hybrid | Push for accounts under a follower threshold (e.g. 100k); pull-and-merge celebrity posts into the read path. | Realistic production system with a skewed follower distribution. | Two code paths to build, test, and reason about; merge logic must correctly order/rank across both sources. |

The threshold is the actual design lever: too low and readers must merge too many authors per request; too high and a single post from a large account threatens the fanout workers and the 30-second freshness bound. Track *active* follower count as a first-class signal and move an account between push/pull tiers automatically, not by manual flag. The sizing of that threshold, with numbers, is in Capacity and storage below.

## Architecture and data flow

```arch
%% caption: Posts are written once with an outbox row; fan-out pushes id-only refs for normal authors and only records recent ids for pull-tier authors, and the read path merges both tiers, ranks them, snapshots the order and hydrates from the post store.
group wp "Write path" color=blue icon=edit
group rp "Read path" color=green icon=feed
node author "Author" at 0,0 icon=user
node reader "Reader" at 3,0 icon=users
node postapi "Post API" at 0,1 in wp icon=api sub="idempotent create"
node poststore "Post store" at 0,2 in wp icon=db sub="posts + outbox"
node queue "Fan-out queue" at 0,3 in wp icon=queue sub="by author_id"
node fanout "Fan-out workers" at 0,4 in wp icon=worker sub="5k-follower chunks"
node feedsvc "Feed read service" at 3,1 in rp icon=service sub="merge, dedupe"
node ranker "Ranker" at 3,2 in rp icon=model sub="light + heavy"
node snapshot "Snapshot store" at 3,3 in rp icon=kv sub="top 200 ids, 30 min"
node cache "Post cache" at 1.5,2 icon=cache sub="hydrate"
node refs "Feed refs" at 1,4 icon=kv sub="per user, newest 800"
node recent "author_recent" at 1,5 icon=memory sub="pull tier, replicated"
author -> postapi -> poststore
poststore ..> queue : "outbox relay"
queue -> fanout
fanout -> refs : "PUSH"
fanout:B -> recent:L : "PULL"
reader -> feedsvc -> ranker -> snapshot
feedsvc:L -> cache:T : "hydrate"
cache:L -> poststore:R : "miss"
feedsvc:L -> refs:T
feedsvc:L -> recent:R
```

```arch
%% caption: Push and pull tiers write differently but the read path always merges both and ranks the union, so a threshold change never breaks reads.
node author "Author" at 0,1
node reader "Reader" at 0,3
node outbox "Outbox" at 1,0
node fanout "Fanout worker" at 2,0
node shard "Follower feed store" at 2,1
node read_path "Read path" at 1,3
node ranker "Ranker" at 2,3
node post_store "Post store" at 2,2

author -> outbox : "post write (post_id, author_id, ts)"
outbox -> fanout : "consume"
fanout -> shard : "insert feed ref per active follower"
fanout -> fanout : "skip fan-out, author is in the pull tier"
reader -> read_path : "GET /feed"
read_path -> shard : "fetch push-tier refs"
read_path -> post_store : "fetch recent posts of pull-tier authors"
read_path -> ranker : "candidates from both tiers, deduped"
ranker -> read_path : "ordered ids, snapshot saved"
read_path -> post_store : "hydrate body, visibility, delete flag"
read_path -> reader : "page plus cursor"
```

**One write, end to end.** `POST /v1/posts` writes the post row and an outbox row in one transaction (idempotent on `client_post_id`). A relay publishes the outbox row to a queue partitioned by `author_id`. The fan-out worker reads the post's stamped `fanout_mode`. For PUSH it reads the author's follower list in chunks of ~5k, drops followers who are not recently active, and inserts `(post_id, author_id, affinity_hint)` into each remaining follower's feed list, trimming the list to the newest 800. An insert keyed by `post_id` is a set-add, so a retried chunk changes nothing. For PULL it does nothing except append the `post_id` to `author_recent`.

**One read, end to end.** `GET /v1/feed` with no cursor starts a new session: read the user's feed refs (push tier), look up `author_recent` for every pull-tier author the user follows (an in-process map, see Capacity and storage), dedupe by `post_id`, rank the union, save the ordered top ~200 ids as a snapshot, then hydrate the first 25 from the post cache and return them with a cursor. Page 2 reads ids 25–49 from the snapshot and hydrates them; it does not rank again.

Feed-reference rows are small: `(user_id, post_id, author_id, affinity_hint)`. `post_id` is time-ordered, so it doubles as the chronological cursor; `affinity_hint` is a cheap write-time signal for the ranker, never a final score. They are not the post itself — the post body lives in one place, the post store, and is hydrated at read time. This is the key hard decision: storing full post content redundantly in every follower's feed would make deletes and privacy edits require rewriting millions of rows; storing only a reference means a delete is one row flip that every subsequent read naturally respects. This trades a hydration join (extra read-path cost, mitigated by post-cache) for write-path simplicity and correctness under edits/deletes.

## Capacity and storage

**Model the follower distribution, not the average.** Assume follower counts follow a heavy-tailed (truncated Pareto) distribution, exponent α ≈ 1.2, capped at 50M and scaled to a mean of 300 (assumption; real graphs vary, so measure yours). Assume for now that posting rate does not depend on follower count (0.6 posts/account/day). Then the share of follow edges pointing at accounts above a threshold T equals the share of naive push volume avoided by pulling those accounts, and equals the share of a reader's 300 follows that must be merged at read time:

| Threshold T (active followers) | Accounts at or above T | Share of follow edges | Push volume left (of 1.04M/s avg) | Pull authors per reader | Largest single-post fan-out (60% active) |
|---|---|---|---|---|---|
| 1M | ~3.7k | 8% | 92% ≈ 0.96M/s | ~24 | 600k refs |
| **100k** | ~59k | 17% | **83% ≈ 0.87M/s** | ~50 | **60k refs** |
| 10k | ~0.94M | 31% | 69% ≈ 0.72M/s | ~92 | 6k refs |

What this says: the head is a **burst** problem, not a **volume** problem. Moving from T=1M to T=100k saves only 9 points of sustained volume; what it buys is that no single post ever exceeds ~60k refs (about 0.6 s of one 100k-writes/s slice of the fleet) instead of 600k. If head accounts post far more often than average, their volume share rises and pulling them is even more clearly right.

**Why pull is cheap for the head.** At T=100k there are ~59k pull-tier authors. Their recent-post lists (20 ids × 8 B = 160 B) total ~10 MB. That map can be replicated into every read-path process and refreshed every few seconds, so a reader's ~50 pull-author lookups are in-process memory reads with no network hop. Even at T=10k the map is only ~150 MB. So we choose **T ≈ 100k active followers**: the largest single burst stays small and the read-time merge stays trivial. Lower it if the fleet bill dominates; each 10× drop saves ~14 points of push volume and adds ~40 authors to every read's merge.

**Two levers on the remaining volume.**

1. **Fan out only to recently active followers.** Only users seen in the last 24 h (~300M of 500M, so ×0.6) get refs pushed. A returning user whose feed went cold is rebuilt on read by merging the recent posts of their ~300 followees (~300 cache lookups, about 50 ms, a few hundred rebuilds/s system-wide). Push volume: 0.87M/s × 0.6 ≈ **0.52M/s average, ~1.6M/s at peak**, ~45B refs/day. So the fan-out fleet needs on the order of 16 store nodes at ~100k inserts/s each at full tilt, more like 40 with headroom (per-node and per-worker rates are assumptions; benchmark them). The earlier draft's "10–50k/s" was 30–100× too low.
2. **Cap each precomputed feed at the newest N=800 refs.** An active user receives ~45B ÷ 300M ≈ 150 refs/day, so 800 covers about five days, far more than any scroll session reaches. Refs are 16 B (`post_id` 8 B, `author_id` 4 B, hint 4 B): 300M × 800 × 16 B = **3.8 TB raw** (about 8 TB with two replicas, ~11 TB with structure overhead, roughly 115 nodes of 100 GB usable). Without the cap the same store would grow by 45B × 16 B ≈ **720 GB/day** (~260 TB/year) of refs almost nobody reads. So **the <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> for the capped feeds, not the write rate, sizes this tier**; halving N or the active window halves the bill.

Partition feed-ref storage by `user_id` (each user's feed is one shard's write problem) so fanout writers parallelize across shards without contention. Partition the post store by `post_id` so hydration reads are independent of feed shard layout. Chunk each fan-out job by follower range (~5k followers per chunk) and spread chunks across many workers, so a 60k-ref job finishes in about a second and never sits in front of small authors in a single queue (see [Partitioning and hot keys](../building_blocks/25_partitioning_and_hot_keys.md)).

Do not fan out celebrity posts to followers — at 50M followers, one post would be 50M writes, an instant fanout-worker DDoS and a huge storage bill for rows that are 99% never read (most followers don't scroll back far enough to see it, or read <30 min after posting anyway). Pull those posts at read time instead: fetch the last N posts from each pull-tier followed author and merge. Do not use the feed's own table as a cache for post content — that duplicates the source of truth and reintroduces the delete-propagation bug this design exists to avoid.

## Celebrity threshold and tier migration

The tier is a function of *active* follower count, evaluated by a periodic job, with rules that keep readers correct while accounts move:

1. **Hysteresis.** Promote to PULL when active followers stay above 120k for 10 minutes; demote to PUSH when they stay below 80k for 24 hours. Without the band, an account hovering at 100k flaps and thrashes both paths. Threshold flips are also rate-limited per account.
2. **Stamp the mode on the post, not on the reader.** Each post records its `fanout_mode` at creation. An in-flight PUSH job always finishes as PUSH, even if the author flips to PULL a second later. The read path dedupes by `post_id`, so a post that is both in a follower's feed refs and in the author's recent list appears once. That is what prevents double delivery.
3. **PUSH → PULL needs no backfill.** New posts stop fanning out; refs already in feeds remain valid and age out at the cap. Readers start consulting `author_recent` for this author as soon as the tier flip reaches the replicated `author_tier` map (seconds).
4. **PULL → PUSH needs a transition window.** Posts made while the author was PULL are not in anyone's refs. For 24 hours after the flip readers keep merging that author's `author_recent` alongside the pushed refs (dedup by `post_id` again), then stop. New posts go out as PUSH from the flip.
5. **Fan-out is idempotent.** Job key is `(post_id, chunk_no)`; the insert is a set-add by `post_id`. At-least-once queue delivery therefore cannot duplicate a ref.
6. **Bots do not promote accounts.** Count only followers that are recently active and pass basic quality filters; otherwise an account buys its way into the pull tier, or a fake-follower ring inflates fan-out cost.

## Ranking and pagination

"Ranked, not strictly chronological" means the read path is a candidate-generation-then-ranking pipeline. Depth belongs in [032 — Ranked Home Feed](032_ranked_home_feed_solution.md) and [Ranking, recommendation, and experimentation](../building_blocks/31_ranking_recommendation_and_experimentation.md); this section shows where it plugs into the feed.

```arch
%% caption: Both tiers feed one candidate pool that is narrowed by a cheap ranker, then an expensive one, then blending rules, and the result is frozen as a snapshot.
node push "Push-tier refs" at 0,0 shape=cyl sub="up to 800"
node pull "Pull-tier recent lists" at 0,1 shape=cyl sub="~50 authors"
node merge "Merge and dedupe" at 1,0.5 sub="~1,000 candidates"
node light "Light ranker" at 2,0.5 sub="1,000 to 200"
node heavy "Heavy ranker" at 3,0.5 sub="200 to 50"
node blend "Blend" at 3,1.5 sub="diversity, integrity, seen-suppression"
node snap "Snapshot" at 2,1.5 shape=cyl sub="top 200 ids, TTL 30 min"
node page "Hydrate page of 25" at 1,1.5 color=green
push -> merge
pull -> merge
merge -> light -> heavy -> blend -> snap -> page
```

**Candidates.** Up to 800 push refs plus about 50 pull authors × ≤10 recent posts each is ≤1,300 raw candidates, ~1,000 after dedupe and removing already-seen ids (a per-user seen set of recent `post_id`s).

**Two-stage ranking.** A *light ranker* (a linear or small gradient-boosted model over cheap features already in cache: post age, author affinity, early engagement counts) scores all ~1,000 and keeps ~200. A *heavy ranker* (a larger model with richer features, run as a batched inference call) scores those 200 and keeps ~50. Doing the expensive model on 200 instead of 1,000 candidates is the whole point: inference cost is linear in candidates, so a 5× narrower funnel is a 5× cheaper heavy stage. Cost: the light ranker can drop a post the heavy model would have loved; we accept that because the light model is tuned for recall at the cut-off.

**Blending, diversity, integrity.** After scoring: no more than two consecutive posts from one author, a mix of formats, muted and blocked authors removed, policy-violating or borderline content removed or demoted by an integrity classifier, and a slot for ads inserted by a separate system. These are rules on the ordered list, not model features, so policy can change without retraining.

**Freshness versus relevance.** The relevance score is multiplied by a time decay so old posts fade, and a post younger than about five minutes from a high-affinity author gets an explicit boost so the 30 s promise is felt, not just met on paper.

**Latency budget** (budgets to design toward, not measurements):

| Stage | Budget |
|---|---|
| Feed-ref read (cache) | 10 ms |
| Pull merge from in-process lists | 5 ms |
| Candidate features (multiget, ~1,000 items) | 25 ms |
| Light ranker | 10 ms |
| Heavy ranker (batched inference) | 50 ms |
| Blending and filters | 5 ms |
| Hydrate 25 items | 15 ms |
| Network, serialization, slack | 40 ms |
| **Total** | **160 ms** (of the 200 ms p99 target) |

**Stable pagination: session snapshot versus keyset cursor.**

| Approach | How it works | Gives | Costs |
|---|---|---|---|
| **Session snapshot** (chosen) | First request ranks and stores the ordered top ~200 ids; cursor = `(snapshot_id, offset)`. Later pages read ids from the snapshot and only hydrate. | No re-ranking on pages 2+; no skips or duplicates by construction; cheap pages. | ~1.6 KB per session; with ~17k new sessions/s and a 30 min TTL that is ~31M live snapshots ≈ 50 GB. New posts show only on refresh. |
| `(score, post_id)` keyset cursor over a frozen candidate set | Score once, cursor is the last `(score, id)`; next page = next candidates below it. | No server-side session state beyond the frozen scores. | Scores must be frozen anyway or time-decay makes pages overlap, so you end up storing the candidate set. |
| Re-rank on every page | Recompute per request. | Always freshest. | Scores drift between calls, so items repeat or vanish. Ranking cost paid per page. |

We choose the snapshot: paging stability is a stated requirement, and 50 GB is cheap next to the ranker cost we avoid. Past the ranked 200, the tail continues chronologically from the feed refs using a `post_id` keyset cursor, skipping ids already served. A separate cheap query ("refs newer than the snapshot's timestamp") drives a "new posts" pill; pull-to-refresh starts a new session.

## Deletes, blocks, and privacy

Deleting a post sets `deleted_at` and bumps `version` in the post store, then publishes an invalidation to the post-cache tier. Snapshots and feed refs contain only ids, and every page hydrates current state, so a deleted post is dropped the next time any page containing it is built. Timing: the invalidation reaches caches in seconds; a cache entry has a ≤30 s TTL as a backstop if an invalidation is lost; so the worst case is about 30 s plus queue lag, inside the 60 s target. Hydration that finds a dead ref also removes it from the feed list (read repair).

A block or a visibility change is enforced the same way: hydration checks `(viewer, author)` block state and the post's current visibility per viewer. **Unfollow** is the one case that is not free at read time, since hydration would have to check the follow edge on every item. Instead, an unfollow enqueues a purge that removes that author's refs from the user's feed list (the refs carry `author_id`, so it is a scan of at most 800 entries), and the read path keeps a small per-user "recently unfollowed" set for 24 hours as a filter until the purge is confirmed.

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Fanout worker backlog | Feed-ref writes lag; freshness bound is missed for affected users — surface as degraded, not silent staleness; drain backlog before accepting more work loss. Large jobs are chunked and prioritized so a backlog of big authors never starves small ones. |
| Post deleted after fanout | Delete flag flips at the post store; read-time hydration filters it out of every feed instantly, no need to touch feed-ref rows. |
| Privacy change (post made private, user blocked) | Hydration re-checks visibility per viewer at read time; a stale feed-ref row simply gets filtered, never served. |
| Celebrity account crosses fanout threshold mid-spike | Tier reassignment must be atomic/idempotent — a post must not be double-delivered by being fanned out and also pulled. The stamped `fanout_mode` plus dedup by `post_id` guarantees this. |
| Hot pull-tier author (viral pull post) | Read-time merge fan-in across many readers hitting the same author's recent posts is served from the replicated in-process `author_recent` map, so one viral author cannot overload a single cache key. |
| Follow/unfollow race with fanout | Fanout worker reads follower list at post-time; a user who unfollows mid-fanout may still receive one stray feed-ref — hydration's visibility check and the "recently unfollowed" filter are the backstop, not the fanout write path. |
| Ranker slow or down | The read path has a deadline (about 120 ms). It skips the heavy ranker and returns light-ranker order; if that fails, chronological order by `post_id`. The response carries a degraded flag and a counter increments. |
| Feed-store shard lost | Refs are derived. Reads for its users rebuild the feed from followees' recent posts (~50 ms extra) while re-materialization runs in the background; rebuilds are rate-limited so they cannot overload the post store. |
| Zone or region failure | Follow graph and posts replicate across regions; feed stores do not, because they are rebuildable. Users fail over to the surviving region and rebuild on read, throttled. Freshness and p99 degrade for the failover window; correctness does not. |
| Bad ranker or fan-out deploy | Ranking models roll out behind a canary with guardrails on latency, errors, and engagement; automatic rollback to the previous model. Fan-out workers roll by percentage of partitions, and a stalled partition shows up as lag on the paging alert. |
| Spam, follow-bombing, fake followers | Per-account rate limits on posts and follows (429); tier and ranking use *active, quality-filtered* follower counts; integrity classifier demotes spam before the blend stage. |

## Observability and interview close

Measure post-to-feed lag (post write timestamp to feed-ref visible timestamp, p50/p99), fanout worker backlog depth and age, feed read p99 latency and per-stage timings (ranker included), ranker degraded-response rate, delete/privacy propagation latency, push/pull tier distribution and threshold crossings, feed-store memory per node against the cap, and hot-author read amplification. The one paging alert is **post-to-feed lag p99 above 30 s**, because it is the freshness SLO burning; secondary alerts are the ranker degraded rate and a hydration cache miss spike, which signals post-store overload risk from the read path.

Interview close: "I treat posts and follows as truth and feeds as disposable projections. I push-fanout small accounts for fast reads and pull-merge celebrity accounts to avoid write amplification, hydrating current post state at read time so deletes and privacy changes propagate for free instead of requiring a rewrite of every follower's feed."

Trade-off to state: "I push to recently active followers below ~100k and pull above it, so writes stay bounded and no single post can break the 30-second freshness bound, at the cost of two code paths and a ranker that must merge both; the cost is acceptable because the pull set is only ~10 MB and can live in every read process."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Posts and the follow graph are the replicated source of truth (async cross-region, with the author's home region as the writer). Feed refs are derived and stay regional: each region fans out from the replicated outbox to its own users. Cross-region lag adds to the 30 s budget, so budget ~5–10 s for replication and alert on it separately.
2. **"What changes at 10× and 100× scale?"** At 10×, storage and fleet grow linearly; the design does not change, but the cap N and active window become the main cost knobs. At 100×, the follow-graph and post-cache tiers are the first to need cell-based sharding (independent copies of the whole stack per user cohort), and the pull-tier map may outgrow per-process replication and move to a shared cache tier.
3. **"What if I need read-your-writes on my own post, or strict ordering?"** For self, merge the viewer's own last posts into the feed at read time (a pull of one author) so they never wait for fan-out. For a stricter chronological mode, skip the ranker and page by `post_id`; the tiers and dedup are unchanged. Strict global order is not worth its cost for a feed.
4. **"What dominates cost?"** The RAM for capped feed lists (~11 TB at N=800) and the heavy-ranker inference fleet. Knobs: lower N, shorten the active window, lower T, and cache ranker scores for near-identical sessions.
5. **"How do you defend against abuse?"** Rate limits on posts and follows, follower quality filters feeding the tier decision, integrity classifiers in the blend stage, and hard caps on how many accounts one user can follow so a scraper cannot force huge pull merges.
6. **"What if a user returns after 30 days?"** Their feed list was dropped or is stale. Rebuild on read from ~300 followees' recent posts (about 50 ms), write the result back as their new feed, and resume pushing. Cold-start ranking uses coarser features.
7. **"Why not pure pull? It is simpler."** Pure pull makes every read a fan-in over ~300 authors: at 210k reads/s that is ~63M author lookups/s, each needing per-author post lists that are not all in memory, and p99 is the slowest of 300. Push moves that cost to write time, where it is batchable and off the user's latency path. I would happily start with pure pull for a small product and add push when read latency demands it.
8. **"What if the interviewer says the threshold is unnecessary and we should push everything?"** Show the burst arithmetic: a 50M-follower post is 1.7M writes/s for 30 s from one event, more than the fleet's peak, and 99% of those refs go unread. I would concede that a hard threshold is a tunable, not a law, and that "push to the first ~2M active followers, pull the rest" is a valid refinement.

## Common mistakes

1. **Sizing fan-out from the average follower count.** The mean hides a heavy tail; head accounts drive bursts and storage. Model the distribution and check the largest single post against the freshness bound.
2. **Pushing to every follower, active or not.** Two-fifths of the writes go to users who will not open the app today. Fan out to recently active users and rebuild the rest on return.
3. **Unbounded per-user feed storage.** Without a cap the feed store grows ~720 GB/day. Cap it and say what the cap number covers.
4. **Storing post bodies in feed rows.** Deletes and privacy edits then need millions of row rewrites. Store ids and hydrate.
5. **Treating "ranked" as a footnote.** If the answer is only merge-by-time, you skipped a stated requirement. Show candidate generation, the two-stage funnel, blending, and a degraded mode.
6. **Re-ranking on every page.** Scores drift, so items repeat or disappear between pages. Freeze a snapshot or a candidate set.
7. **Letting tier flips race with in-flight posts.** Without stamping `fanout_mode` on the post and deduping by `post_id`, a flip can double-deliver or drop a post.
8. **Promoting by raw follower count.** Bought or bot followers inflate it; use active, quality-filtered followers.

## Going from L5 to L6

- **Migration path.** Start pure pull with a cache (correct, simple), add push for the mid-tier when p99 read latency demands it, add the celebrity pull carve-out when a burst first threatens freshness. Each step is reversible because feeds are derived.
- **Cost model.** Express the design as three knobs (T, N, active window) and show the dollar curve for each, then pick the point where marginal RAM equals marginal read latency benefit.
- **Ownership and blast radius.** Split the stack into four independently deployable units (post service, graph service, fan-out fleet, ranking service) with separate on-call, quotas, and deadlines; the read path degrades stage by stage instead of failing whole.
- **Build versus buy.** Feed stores and queues are commodity (managed Redis-like store, Kafka-like log); the graph store and the ranker are where a company's differentiation and cost actually live.
- **What to measure first.** The real follower distribution and per-tier posting rates from production logs. If the head posts 10× more than the mean, or if the active fraction is 85% instead of 60%, the whole volume table moves.
- **Experimentation.** Every ranker or blend change ships behind an A/B test with a guardrail metric; see the building block on ranking and experimentation.

## Build exercise

Build a chronological (non-ranked) feed first: implement push fanout for accounts under a follower threshold, pull-and-merge for accounts over it, and a hydration step that filters deleted/private posts at read time. Then add a ranker stub and snapshot pagination. Named assertions:

- `test_delete_removes_from_every_feed_without_touching_refs`: delete a post mid-test and assert it disappears from every follower's feed on the next read while the feed-ref rows are unchanged.
- `test_no_duplicate_after_tier_flip`: flip an author from PUSH to PULL between the outbox write and the fan-out job; assert every follower sees the post exactly once.
- `test_fanout_retry_is_idempotent`: deliver each fan-out chunk twice; assert feed lengths are unchanged.
- `test_feed_cap_enforced`: push 2,000 posts to one user; assert the list is exactly the newest 800 in `post_id` order.
- `test_snapshot_pagination_stable`: page through a ranked feed while 500 new posts arrive; assert no duplicate and no skipped id across all pages.
- `test_ranker_failure_degrades`: make the ranker raise; assert a chronological page is returned with the degraded flag set.
