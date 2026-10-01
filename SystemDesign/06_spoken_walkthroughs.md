# Spoken Walkthroughs: Five 45-Minute Answers, Out Loud

A solution file shows *what* a strong design contains. It does not show what a strong candidate *sounds like*: when they stop asking questions, how they turn a number into a decision in one breath, what they say when the interviewer cuts in, and how they fit a failure story into the last seven minutes. This page fills that gap. Each walkthrough is a first-person script of a 45-minute round, with the clock, the interviewer's interjections, and what was on the board at each point.

Why this matters: in most large-company loops the interviewer writes notes during the round, and people who never met you (a hiring committee, a debrief panel) make the decision from those notes. They can only record what you *said*. A design you had in your head but never narrated does not exist for them. Pacing is the other half: most failed rounds are not wrong, they are unfinished, with no deep dive or no failure story because the first 20 minutes went to requirements and boxes.

> ⚠️ These are illustrative scripts, not transcripts of real interviews. Every number is an assumption taken from the matching solution file, rounded the way you would round it aloud. Interview formats are commonly reported, not official; confirm the round length with your recruiter.

---

## How to use this page

1. **Read one walkthrough aloud, with a timer.** Not silently. You are calibrating how much you can say in five minutes; most people discover they talk half as fast as they think.
2. **Then do a different problem cold**, out loud, against a 45-minute clock (the practice-problem coach in the reader has one). Record yourself.
3. **Score the recording** with the checklist at the end of this page. Compare *decisions and timing* against the walkthrough, not wording.
4. **Redo the same problem a week later** under one changed constraint, as in step 5 of the [module README](README.md).

The five problems are chosen to cover the five shapes most design prompts take:

| # | Walkthrough | Shape of the problem | The skill the script demonstrates |
|---|---|---|---|
| 1 | [URL Shortener (001)](#walkthrough-1-url-shortener-001) | Small, read-heavy, "easy" prompt | Finding L5 depth in a problem that looks trivial; not over-building |
| 2 | [News Feed (007)](#walkthrough-2-news-feed-007) | Product system with a skewed fan-out | Letting one number (the celebrity burst) drive the architecture |
| 3 | [Seat Reservation (010)](#walkthrough-3-seat-reservation-010) | Correctness under contention | Naming the single arbiter, then protecting it |
| 4 | [Ad Click Aggregation (027)](#walkthrough-4-ad-click-aggregation-027) | Streaming data pipeline | Two outputs with two contracts; exactly-once without hand-waving |
| 5 | [Distributed Key-Value Store (023)](#walkthrough-5-distributed-key-value-store-023) | Infrastructure primitive | Defending a consistency model under interviewer pushback |

**Reading the scripts.** Lines marked **You** are what the candidate says. Lines marked **Interviewer** are interjections. *Board* blocks list what is written on the whiteboard or shared doc at that point (plain text, the way you would type it in an interview doc). Short **Coach** notes explain why a line is there. Minute marks are where the candidate *is*, not hard rules; the phase budget comes from the [45-minute timeline](00_google_l5_playbook.md#the-45-minute-timeline).

---

## Moves that recur in every walkthrough

The walkthroughs reuse a small set of sentences. Learn the shape, not the words.

| Moment | The sentence shape | What it signals to the note-taker |
|---|---|---|
| First 30 seconds | "I'll spend about five minutes on requirements and scale, sketch the API and data, draw a baseline and walk one write and one read, then go deep on the two hardest parts and finish with failure. I'll check in at each step." | Drives the round; has a plan the interviewer can interrupt against. |
| Proposing, not asking | "I'll assume X. Is that right, or should I plan for Y?" | Explores the problem without handing the work back to the interviewer. |
| Closing requirements | "So: three functional requirements, these non-goals, and the one non-functional that decides the design is Z. Is that the right scope?" | Explicit scope, and knows which requirement matters most. |
| A number with a consequence | "That's about 20K per second at peak, **so** a single database can serve the misses but not the full read load, **so** we need a cache." | Estimation used for decisions, not decoration. |
| Choosing a store | "I'll use A because it gives P. I'm rejecting B because of Q." | Chooses by property, not by brand. |
| The trade-off sentence | "I'll choose X. It gives us A, it costs us B, and B is acceptable here because C." | Commits. This is the single most important sentence shape in the round. |
| Announcing a deep dive | "The two parts where this is actually hard are M and N. I'll start with M unless you'd rather I go to N." | Picks depth unprompted, still lets the interviewer steer. |
| Receiving a hint | "Good point. If that's a constraint, it changes P; let me rework that piece." | Treats a hint as new information, not as an attack. |
| Not knowing | "I don't know the exact figure. I'd assume about X, and here's how the design changes if it's 10× off." | Honest, and still makes progress. |
| Time check | "I've got about eight minutes. I'll leave the second deep dive at the decision and move to failure modes." | Manages the clock instead of being managed by it. |
| Close | "To summarize: the source of truth is S, the hard decision was D, it costs C, and the first thing I'd revisit at 10× is R." | Leaves a clean summary in the interviewer's notes. |

## Handling interjections

Interviewers interrupt for one of five reasons. Each has a right response and a common wrong one.

| Interjection | What it usually means | Right response | Wrong response |
|---|---|---|---|
| "What about X?" (early) | You skipped something they care about, or they want to see if you can prioritize. | Answer in one or two sentences, say where it fits in your plan, return to the plan. | Abandon the plan and spend ten minutes on X. |
| "Why not Y instead?" | A genuine alternative; they want your comparison. | Compare on one or two properties, commit, and say what would make you switch. | Immediately switch to Y to please them, or defend your choice without comparing. |
| "Let's say the constraint is now Z." | They are testing whether the design bends or breaks. | Say which component changes and which does not, rework only that piece. | Start over from scratch. |
| "Let's move on" / "That's fine" | You've shown enough there, or you're over time. | Stop mid-sentence if needed, state the decision in one line, move. | Finish the paragraph anyway. |
| Silence | Usually nothing; they're writing. | Keep going. Check in at the next transition, not every sentence. | Filling silence by re-explaining the last point. |

> 💡 A hint is data. If an interviewer asks the same kind of question twice ("what about the big accounts?"), it is the deep dive they want. Take it.

---

## Walkthrough 1: URL Shortener (001)

**Prompt:** "Design a URL shortener." Reference: [question](problems/001_url_shortener_question.md) · [solution](solutions/001_url_shortener_solution.md).

**What the interviewer is testing.** Whether you can make an easy problem interesting without inventing complexity. The trap is drawing a 12-box microservice diagram for 190 writes a second. The L5 signal is finding the real hard parts: code-space math, the analytics path staying off the redirect, disable propagation, and abuse.

### 0:00–0:30 Plan

**You:** "I'll spend about four minutes on requirements and scale, because this one is small enough that the numbers will tell us what *not* to build. Then API and data model, a baseline with one create and one redirect walked through, then two deep dives. I expect those to be code generation and the analytics path. I'll finish with failure and abuse, which matters more than usual here because a shortener is a phishing tool if you're careless."

### 0:30–4:00 Requirements

**You:** "Functionally: create a short link, optionally with a custom alias; redirect; owners can disable a link; and click counts. I'll treat billing, team ownership, and the analytics dashboard itself as out of scope, and just produce the click events. Does that match what you had in mind?"

**Interviewer:** "Yes. Assume 100 million new links a month and 10 billion redirects a month."

**You:** "Good, that's a 100 to 1 read ratio. Non-functionally I'll propose: redirect p99 under 100 milliseconds; redirects are the thing that must stay up, creation can degrade; links are durable, so plan for ten years; analytics can lag, say five minutes, but must never slow a redirect. One question that changes the design: when an owner disables a link, how fast must that take effect?"

**Interviewer:** "What would you suggest?"

**You:** "Seconds globally for disable, because disable is how we respond to abuse. For a new link being visible everywhere, a few seconds of replication lag is fine as long as the creator's own first click works."

**Coach:** The disable question is the "requirement nobody said out loud". It produces a deep-dive topic later and costs 20 seconds now.

```text
Board
FR: create (+alias), redirect, disable, click events
Out: billing, dashboards, teams
NFR: redirect p99 < 100 ms | redirects > creates for availability | 10-year durability
     analytics lag <= 5 min, never on redirect path | disable: seconds, global
```

### 4:00–8:00 Estimates

**You:** "A month is about 2.6 million seconds. 100 million creates is about 40 a second, 10 billion redirects is about 4,000 a second. I'll assume a 5× peak, so roughly 200 creates and 20,000 redirects a second at peak.

"Two conclusions. First, 200 writes a second never forces sharding on its own. Second, storage: say 1 KB a link including indexes, that's 100 GB a month, 1.2 TB a year, 12 TB over ten years. **So** storage, not write rate, is what eventually splits the database, around year three for a node that comfortably holds a few terabytes. I'll start unsharded but pick a key that hashes cleanly.

"For the cache: link popularity is heavily skewed. If I assume a Zipf-like curve, the top 100 million links, about 25 GB, take roughly 80% of redirects. **So** 20% of 20,000 is 4,000 misses a second, which one SSD-backed primary-key lookup tier handles. I won't size the cache for 99%, because that costs ten times the RAM for the last ten points."

**Interviewer:** "What about bandwidth?"

**You:** "About 500 bytes each way per redirect, so 20,000 a second is about 10 MB/s, under 100 megabits. Not the constraint. Connection setup is: TLS handshakes cost CPU, so I'd terminate TLS at the edge with keep-alive to the redirect tier."

### 8:00–12:00 API and data model

**You:** "Three endpoints.

```text
POST /v1/links  {destination_url, custom_alias?}  Idempotency-Key header
  -> 201 {code, short_url}      409 if the alias belongs to someone else
GET /{code}     -> 302 Location: destination
DELETE /v1/links/{code}   (disable) -> 204
```

"I'm choosing **302, not 301**. A 301 can be cached by browsers indefinitely, so disabling a link would stop working for anyone who's visited it, and we'd stop seeing repeat clicks. 302 costs us a request to our edge on repeat visits, which is acceptable because the edge serves it from cache.

"The create needs an idempotency key: if we commit and the response is lost, the retry must return the same link, not mint a second one.

"Data model: one table, `Link(code PK, destination, owner_id, status, created_at, expires_at)`. The hot query is lookup by code, a primary-key read. I'll use a relational database: 1.2 TB a year and a primary-key lookup is well within it, and I get a unique constraint, which I'm about to need. Click events do **not** go in this table: that would turn a read-only hot path into 20,000 writes a second."

### 12:00–20:00 Baseline and one flow each

**You:** "Visitor to DNS and CDN with a WAF, to a stateless redirect service, which does cache-aside against a Redis-style cache, falling back to the link database. The redirect service emits a click event into a local buffer that ships to a log asynchronously. Creation is a separate API service writing to the same database.

"**One redirect:** `GET /abc1234` hits the edge, the redirect service checks a small disabled-codes denylist, then the cache; on a miss it reads the database, fills the cache with a TTL of a few minutes, returns 302, and appends a click event to its buffer. If the buffer is full it drops and counts the drop. It never blocks.

"**One create:** validate the URL against a reputation check, generate a code, insert with the unique constraint, store the idempotency key in the same transaction, return 201."

```text
Board
visitor -> edge (CDN, WAF, TLS) -> redirect svc -> [denylist] -> cache -> link DB
                                         \-> local buffer -> log -> analytics
creator -> API svc -> link DB (unique code, idempotency key)
```

**Interviewer:** "Why a separate redirect service? Isn't that the microservices over-engineering you mentioned?"

**You:** "Fair challenge. I'd deploy it as its own fleet because it has a different scaling and availability profile: it must survive the database being down, serving from cache, and it scales with redirects, not creates. But it can be the same codebase. If the team is small I'd ship one binary with two deployment roles."

### 20:00–33:00 Deep dives

**You:** "Two hard parts: code generation, and making disable fast without giving up the cache. Code generation first.

"Seven base-62 characters is 62 to the 7th, about 3.5 trillion codes. Over ten years we need 12 billion, so we'd be 0.3% full, and a random code collides with an existing one about 0.3% of the time at year ten. People say 'the space is huge, collisions don't happen', but the birthday bound says there's a 50% chance of the *first* collision after only about 2 million codes, and over ten years roughly 20 million inserts will collide. **So** the database unique constraint is the correctness mechanism, and the application just retries on a violation.

"The alternative is a counter handed out in ranges, say a million per instance, run through a keyed permutation so codes aren't sequential. No collisions and no retries, but I now run an allocator whose state must be durable before a range is handed out, and a permutation key I have to protect. I'll choose random codes plus the unique constraint. It gives simplicity; it costs a retry on 0.3% of creates; that's acceptable at 200 creates a second. I'd switch to ranges if creation went multi-region active-active, because then cross-region uniqueness checks hurt."

**Interviewer:** "And custom aliases?"

**You:** "Same mechanism: insert directly and map a unique-key violation to 409. The bug to avoid is 'check if available, then insert' as two steps; two requests both see it free."

**You:** "Second deep dive, disable. Cached mappings have a TTL of minutes, and edges may cache too. If disable waited for TTLs, a phishing link would keep working for minutes. So disable writes the database *and* publishes the code to a denylist that is streamed to every redirect node, which checks it before the cache. Ten million blocked codes at 8 bytes is 80 MB a node, fine. That bounds propagation to seconds while mapping TTLs stay long. It costs a second distribution path to operate; it's acceptable because disable is the abuse response and it's rare."

**Coach:** Each deep dive ends in the four-part trade-off sentence. Notice the interviewer's alias question was answered in two sentences, then the candidate returned to the plan.

### 33:00–41:00 Failure, abuse, operations

**You:** "Box by box. **Cache cluster down:** misses fall to the database, 20,000 a second instead of 4,000. That's over its budget, so the redirect tier coalesces requests for the same code and sheds invalid-code traffic first; valid redirects degrade in latency but work. **Database down:** creates fail cleanly with a retryable error, redirects keep serving cached mappings. **Analytics log down:** buffers fill, we drop and count, redirects are unaffected. That's why the click path is asynchronous.

"**Abuse:** a shortener hides phishing. Reputation check at create and a periodic rescan, rate limits per account and IP, reject destinations that are themselves short links, and the denylist as the kill switch. **Enumeration:** at 0.3% density, a scanner guessing 10,000 codes a second finds about 34 live links a second, so random codes are not security. Rate-limit per IP and alert on a high 404 ratio.

"SLIs: redirect success rate and p99 by region, cache hit rate, disable propagation delay, click-event lag. The paging alert is redirect success rate burning its SLO."

### 41:00–45:00 Evolution and close

**You:** "At 10×: 200,000 redirects a second; more cache and edge, and shard the mapping by hash of code. At 100×: 7 characters would be about a third full, so move to 8, which I've kept as a config value. Multi-region: give each region a disjoint slice of the code space and send custom aliases to one authority.

"To summarize: the link table is the source of truth, analytics is derived and asynchronous; the hard decisions were random codes with the unique constraint as the safety net, and a denylist so disable is fast without killing the cache. The first thing I'd measure is the real popularity curve, because it sizes the cache."

**What made this L5.** Two numbers that each killed an over-build (200 writes/s; 25 GB covers 80%). The birthday-bound correction. Disable raised as a requirement, then used as a deep dive. Abuse and failure before being asked.

---

## Walkthrough 2: News Feed (007)

**Prompt:** "Design the home news feed for a social network." Reference: [question](problems/007_news_feed_question.md) · [solution](solutions/007_news_feed_solution.md).

**What the interviewer is testing.** Whether you model the follower *distribution* and not the average, and whether the push/pull decision falls out of arithmetic. At L5 you volunteer the celebrity problem; at L4 the interviewer has to ask.

### 0:00–0:30 Plan

**You:** "Plan: requirements and scale, then estimates. I expect the fan-out numbers to decide the architecture, so I'll spend a little extra there. Then API and data model, baseline with one post and one feed read, deep dives on fan-out and on ranking with stable pagination, then failure."

### 0:30–5:00 Requirements

**You:** "Functionally: users post, follow others, and read a home feed of posts from people they follow. Is the feed ranked or chronological?"

**Interviewer:** "Ranked."

**You:** "Then I'll include candidate generation and ranking, but treat the ranking model itself as a black box with a latency budget. Out of scope: ads, stories, comments, and notifications. Non-functionally I'll assume: about 300 million daily users, around 300 follows each; feed read p99 under 200 ms; a new post is eligible in followers' feeds within 30 seconds; a delete must disappear within about a minute. Availability over consistency for the feed, since a slightly stale feed is fine and an empty one isn't. Some accounts have tens of millions of followers. I'll say 50 million as the largest. Right scope?"

**Interviewer:** "Good. Go."

**Coach:** "Within 30 seconds" is a promise about *eligibility*, not position. Saying so early prevents a later argument about what the ranker does to freshness.

### 5:00–10:00 Estimates

**You:** "Reads first. 300 million users times 20 page loads a day is 6 billion, about 70,000 a second, call it 200,000 at peak. Each page hydrates about 25 posts and looks up dozens of authors, so the post cache sees millions of lookups a second. **So** a sharded post cache with a 95%+ hit rate, not reads to the post store.

"Writes. Say 300 million posts a day, 3,500 a second. Naive push to 300 followers each is a million feed inserts a second on average, three million at peak. That's big but it's a fleet, not impossible.

"The number that actually decides the design: one post from a 50-million-follower account is 50 million inserts. To meet 30 seconds, that's 1.7 million writes a second **for one post**, more than the fleet's whole peak. **So** we cannot push for the head accounts, whatever the average says. That's my first deep dive."

**Interviewer:** "How many accounts are we talking about?"

**You:** "I don't know the real distribution. I'd assume a heavy tail, Pareto-like, and I'd measure it before trusting any threshold. Under that assumption, with a threshold around 100,000 active followers, it's tens of thousands of accounts, about 17% of all follow edges."

### 10:00–14:00 API and data model

**You:**

```text
GET  /v1/feed?cursor=...&limit=25  -> {items, next_cursor}
POST /v1/posts {client_post_id, body, media_ids}   (client_post_id = idempotency key)
PUT/DELETE /v1/follows/{user_id}   (idempotent)
```

"The cursor is opaque and signed, so I can change what's in it without a client release.

"Data: `posts` keyed by a time-ordered `post_id`, the source of truth; `following` by user, `followers` by author **chunked**, because a 50-million-row follower list is one hot partition otherwise. The feed itself is derived: per user, a capped list of `(post_id, author_id)` references, **IDs only, not post bodies**. I'm choosing references because a delete or privacy change is then one row flip on the post that every read respects; if I copied bodies into feeds, a delete means rewriting millions of rows. It costs a hydration read per item, which the post cache absorbs."

### 14:00–22:00 Baseline and one flow each

**You:** "**One post:** the post API writes the post row and an outbox row in one transaction. A relay publishes to a queue partitioned by author. A fan-out worker reads the author's followers in chunks of about 5,000 and inserts the reference into each follower's feed list, trimming to the newest few hundred. Inserts are keyed by `post_id`, so a retried chunk is a no-op.

"**One read:** the feed service reads the user's reference list, merges, ranks, and hydrates the top 25 from the post cache, checking the delete and visibility flags at hydration time. Returns items and a cursor."

```text
Board
author -> post API -> post store (+outbox) -> queue by author -> fan-out workers -> feed refs (per user)
reader -> feed svc -> feed refs + [pull-tier recent posts] -> ranker -> hydrate from post cache
```

### 22:00–35:00 Deep dives

**You:** "Deep dive one: push versus pull. Pure push breaks on the head accounts, as we saw. Pure pull means every read merges ~300 authors: at 200,000 reads a second that's tens of millions of author lookups a second, and the p99 is the slowest of 300. So **hybrid**: push for authors below a threshold of active followers, pull for authors above it.

"Where to put the threshold: at 100,000 active followers, pulling those accounts removes only about 17% of the push volume, so volume isn't really why. What it buys is a cap on the burst: **no single post fans out to more than roughly the threshold**, tens of thousands of refs, about a second of fan-out work instead of the 1.7 million writes a second we started with. The pull side is cheap: the tens of thousands of pull-tier authors' last 20 post IDs total about 10 MB, so I replicate that map into every read-path process and the merge costs no network hop.

"Two more levers: push only to followers active in the last day, which cuts volume by about 40%, and rebuild a returning user's feed on read. And cap each feed at about 800 references. That's several days of posts for an active user and makes feed storage a few terabytes of RAM instead of growing 700 GB a day."

**Interviewer:** "What happens when an account crosses the threshold? Say it goes viral mid-day."

**You:** "Two rules keep that safe. Hysteresis: promote above 120,000 for ten minutes, demote below 80,000 for a day, so an account near the line doesn't flap. And the fan-out mode is **stamped on each post** at creation. An in-flight push job finishes as push even if the author flips to pull, and the read path dedupes by `post_id`, so a post in both the pushed refs and the pull map shows once. Going pull-to-push, readers keep merging that author's recent list for a day so nothing posted during the pull period is lost."

**Coach:** The interviewer asked the "what about the big accounts" question in a second form. The candidate had already raised it, so the interjection became a depth probe instead of a rescue.

**You:** "Deep dive two, briefly, since time: ranking and pagination. Candidates are up to 800 pushed refs plus the pull authors' recent posts, about a thousand after dedupe. A light model cuts to 200, a heavy model to 50, then blending rules for diversity and integrity. The pagination problem: if I re-rank on page two, scores drift and items repeat or vanish. So page one saves the ordered top 200 IDs as a **snapshot** with a 30-minute TTL; later pages read the snapshot. It costs a small per-session store; it's acceptable because it's the only way to get stable pages from a ranker."

### 35:00–42:00 Failure and operations

**You:** "**Fan-out backlog:** the 30-second bound is at risk. Alert on queue age, not length; shed by skipping inactive followers first. **Ranker down or slow:** fall back to the light ranker, then to reverse-chronological. A worse feed, never an empty one. **Post cache down:** hydration falls to the post store, which can't take millions of reads a second; coalesce and serve fewer items per page. **Feed store shard lost:** feeds are derived, so rebuild on read from followees' recent posts, about 50 ms each, and repopulate.

"SLIs: feed p99, post-to-eligible lag p99, empty-feed rate, ranker fallback rate. The page goes on post-to-eligible lag breaching 30 seconds."

### 42:00–45:00 Close

**You:** "Posts and the follow graph are the truth; feeds are a rebuildable projection of IDs. The deciding number was the 1.7 million writes a second for one celebrity post, which forced hybrid fan-out with a threshold, hysteresis, and post-stamped modes. At 100× I'd move to cells, independent copies of the stack per user cohort. The first thing I'd measure is the real follower distribution and whether big accounts post more often than average, because that moves every number in the volume table."

**What made this L5.** The average-versus-tail distinction volunteered at minute 8. IDs not bodies, with the delete argument. Tier migration safety (stamping, dedupe, hysteresis) answered without hesitation. A degraded mode for every stage of the read path.

---

## Walkthrough 3: Seat Reservation (010)

**Prompt:** "Design ticket sales for a big concert: 2 million people arrive at on-sale time for 60,000 seats." Reference: [question](problems/010_seat_reservation_question.md) · [solution](solutions/010_seat_reservation_solution.md).

**What the interviewer is testing.** Whether you can name the **one** thing allowed to decide a sale and then design everything else to protect it. The L4 answer puts a Redis lock in front of the database and calls it done.

### 0:00–0:30 Plan

**You:** "This is a correctness-under-contention problem, so I'll state the invariant early and keep coming back to it. Plan: requirements, estimates focused on how big the crowd is compared to the seats, API and data model, baseline, then deep dives on the atomic hold and on the waiting room, then failure."

### 0:30–5:00 Requirements

**You:** "Functionally: see a seat map, hold one to four seats for a few minutes, pay, and the sale confirms. The invariant: **no seat is ever sold to two buyers**. I'll also propose that a multi-seat hold is all or nothing. Out of scope: the payment processor internals and resale. Non-functionally: seat selection p99 under 300 ms for people who are in; the seat map is near real time but advisory; the hold is 5 minutes. Is the hold time fixed?"

**Interviewer:** "5 minutes. What if payment finishes after it expires?"

**You:** "Then the seat row decides, not the payment. If the seat's still ours, confirm; if someone else has it, we void the payment and apologize. I'll come back to that. It's a real edge."

### 5:00–8:00 Estimates

**You:** "2 million people for 60,000 seats. At 2.5 seats a party that's 24,000 winning parties, about 1% of arrivals. **So** the main job of the front of this system is to say no to 99% of people, cheaply and fairly.

"Arrivals: half in the first 30 seconds is about 33,000 joins a second. If each join touched the seat database we'd be done. So joining a queue is a signed ticket, no database write.

"The database side: I'll assume a partition sustains about 5,000 conditional updates a second, which I'd benchmark. An admitted user does about four writes (a couple of hold attempts, checkout, confirm), so about 1,250 admissions a second. **So** the crowd arrives about 25 times faster than we can let people in, and we need a waiting room with a controlled admission rate.

"Seat data is tiny: 60,000 rows at ~150 bytes is 9 MB. Partitioning here is for write contention and blast radius, not size."

### 8:00–10:00 Estimates, continued: the queue-position trap

**You:** "One more number: if 2 million waiting users poll 'what's my position' every 10 seconds, that's 200,000 requests a second at a stateful service. Instead, publish one small `serving.json` through the CDN with the current admission pointer; each client compares its own ticket number. That's cache hits, not a service."

**Coach:** Three numbers, three components justified: the waiting room, the stateless ticket, and the CDN-published pointer. None of them were drawn before the number that required them.

### 10:00–14:00 API and data model

**You:**

```text
POST /queue/join            -> {ticket}            (signed, no DB row)
GET  /queue/serving.json    (CDN, 1 s cache)
POST /queue/admit {ticket}  -> {admission_token}   (single use per ticket)
POST /holds {seat_ids}      Idempotency-Key, admission token required
     -> 201 {hold_id, expires_at} | 409 SEAT_TAKEN {suggestions}
POST /holds/{id}/checkout   -> extends hold once, hands to payment saga
```

"Data: `seats(event_id, seat_id)` with status AVAILABLE, HELD, or SOLD, plus `hold_id` and `hold_expires_at`. This row is the **source of truth for the sale**. Nothing else (not a cache, not the map, not the queue) decides a sale. Partition by event and section, so contention on the front section never blocks the balcony. A relational database, because I need conditional updates and multi-row transactions."

### 14:00–21:00 Baseline

**You:** "Buyer to CDN for the queue pointer and seat-map snapshot; the waiting room issues tickets and admission tokens; the gateway verifies the token by signature before anything touches the seat service; the seat service runs conditional updates on the seats database; an outbox from the same transactions feeds a seat-map relay that pushes coalesced per-section deltas over SSE.

"**One hold:** gateway verifies token, seat service runs one transaction that flips the requested seats to HELD only if they're currently available, commits with outbox rows, returns hold ID. **One map read:** snapshot from the CDN on entry, then deltas for the sections you're looking at."

### 21:00–34:00 Deep dives

**You:** "Deep dive one: the atomic hold. The bug everyone knows is check-then-update: two buyers both read AVAILABLE, both write HELD. So the hold is a single conditional update:

```sql
UPDATE seats SET status='HELD', hold_id=:h, hold_expires_at=now()+'5 min'
 WHERE event_id=:e AND seat_id = ANY(:ids)
   AND (status='AVAILABLE' OR (status='HELD' AND hold_expires_at < now()))
```

"and I require the row count to equal the number of seats, or roll back. Two details. First, **lock order**: two buyers asking for seats 12 and 13 in opposite orders can deadlock, and Postgres only breaks that after a second by default, which blows the budget. So I lock with `SELECT ... ORDER BY seat_id FOR UPDATE NOWAIT` first; the loser fails in milliseconds with a 409. Second, the expiry is **inside the predicate**: an expired hold counts as available at that instant, so correctness never depends on a sweeper having run. The sweeper still exists, but only so the map looks right."

**Interviewer:** "Why not a Redis lock per seat? It's faster."

**You:** "Speed isn't the problem. At about 4,000 holds a second the database is fine. The problem is two systems agreeing: if the lock TTL is shorter than a pause or a failover, two clients both think they own the seat, and the database write that follows has no guard. If I used Redis at all it would be to *choose* seats, never to *decide* them. So: the database row arbitrates. It costs a transaction per hold; that's acceptable because we already capped the rate with the waiting room."

**You:** "Deep dive two: the waiting room's admission rate. A fixed drip is wrong because there are two limits. The database limit is 1,250 a second. The supply limit: letting in 48,000 people, about twice the seats divided by party size, is enough to sell out, and letting in more just creates disappointed people inside. So it's a control loop: admit up to the database rate until the inside count hits the supply target, then admit as people leave, and cut the rate automatically if hold p99 rises. Tickets are signed and single-use at admission, so a replayed ticket can't jump the queue."

### 34:00–42:00 Failure and abuse

**You:** "**Payment succeeds after the hold lapsed:** checkout already extended the hold once. If it still lapses and someone else took the seat, the confirm's conditional update matches zero rows, and the saga voids the authorization. The seat row, not the payment callback, says who owns it. **Seat database primary fails:** synchronous replica in another zone promotes in seconds, in-flight transactions abort, clients retry with the same idempotency key, and the room cuts admission during failover. **Map pusher fails:** clients poll the snapshot; sales unaffected, because the map is advisory. **Bots:** challenge at join, per-account limits, and the hold API rejects anything without a valid token, so bots can't skip the room.

"The one paging alert: **any nonzero count of a seat sold twice**. It should be zero forever, so any value is an incident."

### 42:00–45:00 Close

**You:** "The seat row is the only arbiter; every transition is one conditional update with expiry in the predicate and a fixed lock order. Everything in front of it, the CDN pointer, stateless tickets, the admission control loop, exists to keep contention at a rate that row can sustain. First thing I'd measure: hold-to-purchase conversion, because it sets the hold time and how many people to let in."

**What made this L5.** The invariant stated in minute one and used to reject the Redis lock. Numbers that sized the waiting room from both the database and the seat supply. Deadlock and lazy expiry raised without prompting. A paging alert on the invariant itself.

---

## Walkthrough 4: Ad Click Aggregation (027)

**Prompt:** "Design a system that counts ad clicks for advertiser dashboards and billing." Reference: [question](problems/027_ad_click_aggregation_question.md) · [solution](solutions/027_ad_click_aggregation_solution.md).

**What the interviewer is testing.** Whether you notice there are two outputs with two different contracts, and whether "exactly once" comes out as concrete mechanisms (dedup keys, checkpoints, idempotent sinks, batch recompute) instead of a product name.

### 0:00–5:00 Plan and requirements

**You:** "Plan as usual; I suspect the key decision is in the requirements, so let me get there fast.

"Functionally: ingest clicks, show clicks per ad per minute on dashboards, stop serving an ad within seconds of its budget running out, and produce exact hourly counts for billing, with invalid traffic filtered. Queries over 90 days by ad, campaign, country, device.

"Here's the thing I want to confirm: dashboards need freshness, about a minute, and can be slightly wrong. Billing needs to be exact, deduplicated, and reproducible for audits, but can take hours. Those are **two contracts**. If I build one pipeline for both, either dashboards are slow or bills are wrong. So I'm going to propose a streaming path for freshness and a batch path, over an immutable raw log, that is the truth for money. Is that acceptable, that the dashboard number is labelled preliminary?"

**Interviewer:** "Advertisers will complain if the dashboard and the invoice differ."

**You:** "They'll differ by the late and invalid clicks, and we'll show a reconciliation. I'll come back to what it would cost to make them match exactly. It's possible, but expensive."

**Coach:** The interviewer pushed on the central decision in minute 3. The candidate held the decision, named the cost of the alternative, and deferred the detail to the trade-off section instead of arguing now.

### 5:00–10:00 Estimates

**You:** "A billion clicks a day is about 12,000 a second, and with a 5× peak, 60,000 a second. At about 1 KB per raw event that's 1 TB a day, 90 TB for 90 days. **So** raw events go to object storage in a columnar format, not to the query store.

"Aggregates: 10 million ads times 1,440 minutes is 14 billion possible rows a day, but only non-zero rows exist and a billion clicks caps them. Assume about 5 clicks per non-zero row, so 200 million rows a day, a couple of thousand upserts a second. **So** the OLAP store sees thousands of writes a second, not 60,000. Aggregating in the stream first is what makes that true.

"Dedup state: one hour of click IDs at peak is about 200 million IDs, a few GB, spread across partitions. Fine for keyed state in a stream processor.

"Budget pacing: a big campaign might take 3,000 clicks a second. If pacing updates every 5 seconds, we can overshoot by 15,000 clicks before stopping, several thousand dollars at an assumed 50 cents a click. **So** the pacing interval is a business decision, and I'd say that to the product owner."

### 10:00–14:00 Event schema and API

**You:**

```text
ClickEvent { click_id, ad_id, campaign_id, event_time, ingest_time, ip, device, country, signature }
GET /v1/stats?advertiser_id=&group_by=ad,hour&from=&to=&filters=country:US
```

"`click_id` is minted when the ad is rendered plus a click nonce; it's the dedup key everywhere downstream. `event_time` and `ingest_time` are both kept because windows use event time, and I'll clamp event time against ingest time so a device with a broken clock can't move the watermark. The click URL is signed by the ad server so clicks can't be forged."

### 14:00–21:00 Baseline

**You:** "User clicks, hits our click server, which appends the event to a local buffer and 302s the user to the advertiser. **The log write never blocks the redirect.** The buffer ships to a durable partitioned log keyed by ad. From the log, two consumers: a stream aggregator writing per-minute counts to a real-time OLAP store and spend deltas to the pacing service; and an archiver writing raw events to object storage, where hourly batch jobs dedupe globally, apply fraud decisions, and write billing tables. Dashboards read OLAP for recent data and billing tables for closed periods."

```text
Board
click -> click server (buffer, 302) -> log (by ad_id)
   log -> stream agg -> OLAP (per ad/minute)  -> dashboards
                     -> pacing -> ad servers
   log -> raw archive (Parquet) -> hourly batch (dedup, fraud) -> billing tables
                                                   \-> reconciliation vs stream
```

### 21:00–34:00 Deep dives

**You:** "Deep dive one: windows and late data. Tumbling one-minute windows on **event time**, not processing time: a phone that syncs three hours later must count in the minute the click happened. A watermark at max event time minus one minute finalizes each window about two minutes after it opens, which is too slow for 'about a minute', so I add early firings every 10 seconds as provisional upserts. Allowed lateness one hour: a late click updates the already-emitted minute. Anything later goes to a side output that only the batch path counts."

**Interviewer:** "A phone comes online after 6 hours. Walk me through it."

**You:** "It's past the one-hour lateness, so the stream sends it to the side output and the dashboard doesn't move. The hourly batch over the raw archive puts it in the right event-time hour. Billing closes after 48 hours, so it's on this invoice; if it arrived after the close, it's an adjustment on the next one."

**You:** "Deep dive two: exactly-once, in four layers, because there is no single switch. One, client duplicates like double taps: dedupe by `click_id` in keyed state with a one-hour TTL. Two, pipeline restarts: the stream processor checkpoints state together with log offsets, so a restart replays without double-counting internally. Three, the sink: I write the **absolute count** for `(ad_id, window_start)` as an upsert, never `count += n`, so a replayed window overwrites instead of adding. That increment is the classic bug. Four, billing recomputes from the immutable raw archive with global dedup, so it's reproducible for an auditor.

"Then reconciliation: compare stream and batch per hour and alert above about half a percent, because a gap that big is a bug, not late data."

### 34:00–41:00 Failure and hot keys

**You:** "**Click server can't reach the log:** buffer to local disk, bounded, keep redirecting, alert as it fills. **Stream job crashes:** restart from checkpoint, dashboards lag briefly, idempotent sinks mean no double counts. **Viral ad:** one partition gets hot because we key by ad, so salt known hot ads into sub-keys and sum. **Bug in aggregation logic:** fix it and recompute the affected hours from the raw archive. That's the point of keeping it immutable.

"SLIs: event-time-to-dashboard lag, watermark delay, late and dropped event rates, stream-versus-batch discrepancy, pacing overspend. Page on the log consumer falling behind past the pacing budget, because that's when we overspend real money."

### 41:00–45:00 Trade-off and close

**You:** "Back to your earlier point. If advertisers need the dashboard to match the invoice exactly in real time, that needs transactional sinks committed with each checkpoint, no data accepted after the watermark, and deterministic processing, which means latency of at least a checkpoint interval, a failed commit stalling the job, and a harder recovery story. I'd push back and keep the preliminary label, but that's how I'd build it if the business insists.

"Summary: the immutable raw log is the truth; streaming gives fast approximate numbers, batch gives exact ones; exactly-once is dedup keys plus checkpoints plus absolute upserts plus batch recompute. First thing I'd measure: the lateness distribution, since it sets both the allowed lateness and the billing close period."

**What made this L5.** Two contracts separated in minute 2 and defended when challenged. Event time, watermark, early firings, and allowed lateness each tied to a stated requirement. The `+=` bug named. The interviewer's objection answered with a costed alternative at the end instead of a concession at the start.

---

## Walkthrough 5: Distributed Key-Value Store (023)

**Prompt:** "Design a distributed key-value store like Dynamo or Cassandra." Reference: [question](problems/023_distributed_key_value_store_question.md) · [solution](solutions/023_distributed_key_value_store_solution.md).

**What the interviewer is testing.** Precision about consistency. Every candidate says "consistent hashing, quorums, R + W > N". The L5 signal is knowing exactly what that does *not* guarantee, and doing the durability arithmetic instead of asserting it.

### 0:00–5:00 Plan and requirements

**You:** "Plan: requirements, especially the consistency and failure requirements, because they pick the replication model. Then sizing, API, partitioning and replication, then deep dives on consistency and conflicts and on membership and repair, then failure.

"Functionally: get, put, delete; values up to 1 MB; per-request consistency. Adding and removing nodes online. Non-functionally, I'll take the stated constraints: 10 TB growing to 100 TB, 10 KB average values, 200,000 reads and 50,000 writes a second at peak, p99 under 10 ms in region. Two requirements decide the architecture: no acknowledged write lost if **any two** servers fail, and the store stays **writable during a network partition**.

"That second one matters: a leader-per-partition design, Raft per shard, can't accept writes on the minority side of a partition. So I'm going leaderless, Dynamo-style, and clients will sometimes have to handle concurrent versions. If writability during partitions weren't required, I'd choose Raft and simpler clients. Does that framing work?"

**Interviewer:** "Yes, go leaderless."

### 5:00–10:00 Estimates

**You:** "Storage: 100 TB times 3 replicas is 300 TB. At 2 TB usable per node, leaving room for compaction, that's 150 nodes at the end state. At today's 10 TB it's only 15 nodes by storage.

"Throughput: 250,000 operations a second, each touching 3 replicas, is 750,000 replica operations a second. If a node does about 10,000 a second at our p99, an assumption I'd load-test, that's 75 nodes. **So** throughput sizes the fleet today, 75 not 15, and storage takes over as data grows. The mistake would be sizing from storage alone.

"Latency: an in-region round trip is about half a millisecond, so waiting for the second-fastest of three replicas fits in 10 ms if nodes aren't overloaded."

### 10:00–14:00 API

**You:**

```text
put(key, value, context?, W)  -> ok
get(key, R)                   -> [(value, context)]   # >1 means concurrent versions
delete(key, context?)         -> ok                   # writes a tombstone
```

"`context` is an opaque version vector. A client that passes it back gets its update ordered after what it read; a client that ignores it effectively gets last-writer-wins. Returning a list from `get` is honest: in a leaderless store there can be siblings, and the API shouldn't pretend otherwise."

### 14:00–21:00 Baseline: partitioning and replication

**You:** "Keys hash onto a ring. Each physical node owns about 128 virtual nodes, so arcs are even and a new node takes a little from everyone instead of half of one neighbour's data. A key lives on the first N=3 **distinct physical** nodes clockwise, placed in different zones. Any node can coordinate: clients use a partition-aware library or go through a load balancer. The coordinator sends a write to all three and acknowledges after W; a read goes to all three and returns after R, then reconciles versions. Default W=2, R=2, so R + W > N.

"Each node stores data in an LSM tree: commit log, memtable, immutable sorted files with Bloom filters, and compaction. Writes are sequential appends, which fits 50,000 writes a second."

**Interviewer:** "So with R + W > N, reads are linearizable?"

**You:** "No, and that's worth being precise about. R + W > N gives overlap between a write quorum and a read quorum **when both use the key's home replicas**. It breaks in three ways: sloppy quorums, where a write lands on a stand-in node that the next read doesn't contact; concurrent writers, where overlap doesn't order them; and read-repair races. So I'd say 'read-your-writes in the common case', not linearizable. If you need compare-and-set, say for inventory, I'd run a consensus round per key for just those operations, the way Cassandra's lightweight transactions run Paxos per partition: several round trips, a couple of milliseconds in region."

**Coach:** This is the precision question the problem exists to ask. The candidate said "no" in the first word, gave the three failure cases, and offered the fix for the subset that needs it.

### 21:00–33:00 Deep dives

**You:** "Deep dive one: the durability requirement, because I think W=2 doesn't meet it. An acknowledgement with W=2 means two durable copies. If exactly those two nodes die before the third replica applies the write, the write is gone, and the requirement said any two. So writes under that contract need **three durable copies at ack time**. Two options: N=3, W=3, with sloppy-quorum stand-ins counting as copies so a write still succeeds with one replica down; or N=5, W=3, R=3, which costs 500 TB raw, 250 nodes instead of 150. I'd offer that as a per-keyspace option for data that truly needs it, and keep W=2 for the rest, with an alert on replica lag to bound the window. It costs complexity in configuration; it's acceptable because paying 100 extra nodes for all data to protect some of it is worse."

**You:** "Deep dive two: conflicts and repair. Concurrent writes produce versions where neither version vector descends from the other. The read returns both siblings. Resolution is per data type: last-writer-wins by timestamp for caches and idempotent overwrites, accepting that clock skew silently drops a write; application merge, like a cart union; or CRDT values that merge themselves.

"Repair has three layers: read repair when a read sees a stale replica; hinted handoff, where a stand-in forwards writes when the real replica returns; and Merkle-tree comparison per token range, which catches data that was never read. Deletes are tombstones kept longer than the maximum repair interval, say 10 days, or a replica that missed the delete resurrects the key during repair.

"Membership is gossip with a phi-accrual failure detector. Important: **suspicion only changes routing**, meaning hints go to a stand-in. Removing a node and moving its data is an explicit decision, so a flapping node doesn't trigger terabytes of rebalancing."

### 33:00–41:00 Failure

**You:** "**One node down:** quorums of 2 of 3 still succeed, hints cover writes. **Partition:** both sides accept writes with sloppy quorums; version vectors detect the conflict after healing and reads return siblings. That's the requirement we paid for. **Slow node, not dead:** the failure detector doesn't flag it, so it inflates p99. The coordinator hedges: send a speculative read to the next replica after about the p95 latency, take the first answer. Alert on per-node p99, not liveness. **Hot key:** one preference list overloaded; client-side caching and coalescing. **Disk corruption:** block checksums detect it, Merkle repair rebuilds the range.

"SLIs: p99 by operation and consistency level, quorum failures, hint queue depth, sibling rate, whether a full repair finishes inside the tombstone window."

### 41:00–45:00 Close

**You:** "Leaderless replication with sloppy quorums, because the requirement was writability during partitions; the price is that clients handle siblings, and R + W > N is not linearizability. Durability for 'any two failures' means three copies at ack. I'd offer it per keyspace. At 100× data I'd stop growing one ring and split into cells behind a routing layer, and erasure-code cold data. First measurement: key and access skew, because hot keys break the even-ring assumption before anything else."

**What made this L5.** The requirement tied to the replication model in minute 4. The "linearizable?" trap answered precisely. The durability arithmetic caught a flaw in the textbook W=2 answer. Suspicion versus removal distinguished.

---

## Compressing to a 35-minute round

Meta and Amazon rounds commonly leave about 35 to 40 minutes of design time (see the [company interview guide](01_company_interview_guide.md#adapting-the-timeline-minutes-per-phase)). The scripts above compress without losing the signals if you cut in this order:

1. **Merge API into data model.** Say three endpoints in one breath while writing the tables.
2. **Keep two numbers, not five.** In the news feed, keep peak reads and the celebrity burst; drop storage totals and say "storage is terabytes, not the constraint".
3. **Walk one flow, not two**, choosing the one on the hard path (the post in the news feed, the hold in seat reservation).
4. **Do the second deep dive at decision level only:** one trade-off sentence, no mechanism.
5. **Never cut failure to zero.** Three boxes and the paging alert take 90 seconds.

A 35-minute news-feed plan, said in the first 30 seconds: *"Three minutes of scope, two minutes on the two numbers that matter, a quick API and data model, one post walked end to end, then most of the time on fan-out for big accounts, and I'll close with failure."*

---

## Scoring your own recording

Listen back once, with this checklist and the clock. Each "no" is a specific thing to fix on the next attempt.

| # | Check | Where it should happen |
|---|---|---|
| 1 | Plan stated aloud in the first 30 seconds | 0:00 |
| 2 | Scope written down and confirmed; at least one non-goal named | by 5:00 |
| 3 | Each estimate followed by "so…" and a decision | 5:00–10:00 |
| 4 | Every store chosen by a property, with a rejected alternative | 10:00–15:00 |
| 5 | One write and one read walked end to end | by 25:00 |
| 6 | Two deep dives chosen by you, not the interviewer | 20:00–38:00 |
| 7 | At least two four-part trade-off sentences (choice, gives, costs, why acceptable) | deep dives |
| 8 | Failure raised before being asked, with a degraded mode and one paging alert | by 40:00 |
| 9 | Each interjection answered in under a minute, then back to the plan | throughout |
| 10 | A closing summary: truth, hard decision, cost, what to measure first | 43:00–45:00 |

> 💡 If you consistently miss check 8, move failure earlier: say one failure line at the end of each deep dive ("and if this component dies, …"). Then the final phase is a summary, not a first mention.

## Related

- [00 — Google L5 playbook](00_google_l5_playbook.md): the timeline, estimation numbers and red flags these scripts follow.
- [01 — Company interview guide](01_company_interview_guide.md): how the timeline compresses per company.
- [02 — Problem catalog](02_problem_catalog.md): all 41 problems, to practice the same narration on the rest.
- [03 — Practice prompts](03_practice_prompts.md), [04 — Practice answers](04_practice_answers.md), [05 — Architecture blueprints](05_architecture_blueprints.md): the condensed review layer.
- [Back-of-the-Envelope Estimation](building_blocks/18_back_of_envelope_estimation.md): the arithmetic behind the "so…" sentences.
