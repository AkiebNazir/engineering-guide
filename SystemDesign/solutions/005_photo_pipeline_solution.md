# 005 — Photo Upload and Processing: Full System Design Solution

## Requirements

Users upload originals up to 50 MB, resume interrupted uploads, see processing status, and view thumbnails/variants globally. The system validates/scans content, generates multiple sizes, and deletion removes access to the original and all derivatives.

**Non-functional:** upload success rate > 99.9% on flaky mobile networks; "ready" within ~10 s p99 for normal photos (the question asks for "seconds" at p99, so aim for a p50 of 2-3 s); view p99 < 200 ms globally (the question's contract; thumbnails are the case that matters); 11-nines durability for originals; no unsafe or unauthorized content ever served; delete revokes access within seconds, and the question's bound for removing derivatives and edge copies is one hour.

## Scale estimates

The question says "tens of millions of uploads/day at peak", so this solution uses 50M/day. Every line scales linearly, so 100M/day doubles every number.

| Quantity | Assumption | Result |
|---|---|---|
| Uploads | 50M photos/day | ≈ **580/s average**, 5× peak ≈ 2.9k/s |
| Original size | 3 MB average (50 MB max) | 150 TB/day raw; ~55 PB/year before replication |
| Variants | 5 sizes (thumb 150px … 2048px), WebP/AVIF, e.g. 5 + 15 + 50 + 200 + 500 KB ≈ 0.77 MB | ≈ +25% of original bytes, ~190 TB/day in total |
| Upload bandwidth | 580/s × 3 MB | ≈ 1.7 GB/s ≈ 14 Gbps average ingress; ≈ 70 Gbps at 5× peak |
| Views | 50:1 view:upload, mostly thumbnails | ≈ 29k views/s average, ≈ 145k/s at peak; CDN must serve > 95%, so origin sees ≤ 7k/s |
| Egress | ~40 KB mean per view (assumption, mostly thumbnails) | ≈ 1.2 GB/s (9 Gbps) average, ≈ 5.8 GB/s (46 Gbps) at peak, a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> job |
| Transform work | ~0.5 <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-s per photo to decode once and produce 5 resized, encoded variants (assumption) | 580 decode jobs/s avg, 2.9k/s peak; ≈ 290 cores average, ≈ 1,450 at peak, ≈ 2,400 at 60% utilisation |
| Metadata row | ~1 KB | 50 GB/day (18 TB/year), trivial next to bytes |
| Deletes | assume 0.5% of photos/day | ≈ 250k/day ≈ 3/s, i.e. ~15 variant-URL purges/s (or ~3/s with tag purge) |

What shapes the design: bytes must go **directly to object storage** (70 Gbps at peak through app servers is a waste), **transforms are a large async compute fleet** (2.9k decode jobs/s emitting ~14k resize-and-encode operations/s at peak, with AVIF encodes several times slower than WebP, so generate WebP/JPEG first and AVIF in the background to hold the 10 s target), and **storage cost dominates** (tiering, dedupe, and lifecycle policies matter more than query performance; the 5% <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> miss rate means object storage sees up to 7k reads/s at peak).

## <abbr title="Application Programming Interface">API</abbr>

```http
POST /v1/uploads                       {"filename":"a.jpg","size":3145728,"sha256":"..","content_type":"image/jpeg"}
→ 201 {"upload_id":"up_1","part_size":8388608,
       "parts":[{"n":1,"url":"https://storage/...signed..."}], "expires_at":"..."}
PUT  <signed part URL>                 (client → object storage directly; retry any part)
POST /v1/uploads/{upload_id}/complete  {"parts":[{"n":1,"etag":".."}]}
→ 202 {"media_id":"md_9","state":"PENDING_SCAN"}
GET  /v1/media/{media_id}              → {"state":"READY","variants":{"thumb":"https://cdn/..."}}
DELETE /v1/media/{media_id}            → 202 {"state":"DELETED"}
```

Idempotency: `POST /uploads` with the same `(user, sha256, size)` inside a short window returns the existing session; `complete` is idempotent on `upload_id`.

## Source of truth and flow

```arch
%% caption: Upload bytes go client-to-storage on signed URLs, the metadata DB is the truth for state, an outbox event drives the scan/transform pipeline, and viewers read immutable variants through the CDN.
node client "Client" at 1,0 icon=mobile
node viewer "Viewer" at 3,0 icon=users
node api "API" at 1,1 icon=api sub="small JSON only"
node cdn "CDN" at 3,1 icon=cdn sub="origin shield"
node db "Metadata DB" at 0,2 icon=db sub="Media state + outbox"
node obj "Object storage" at 2,2 icon=blob sub="originals + variants"
node pipe "Scan / transform pipeline" at 1,3 icon=workflow sub="sandboxed workers"
client -> api : "upload, complete"
client:R ==> obj:T : "PUT parts"
api:L -> db:T : "txn"
db:B ..> pipe:L : "outbox event"
pipe:T -> db:R : "READY"
pipe:R -> obj:B : "variants"
viewer:L -> api:R : "signed URL"
viewer -> cdn : "GET variant"
cdn:B -> obj:R : "miss"
```

```arch
%% caption: Bytes flow client-to-storage directly; the API only ever handles small JSON — never the 50 MB payload.
node client "Client" at 0,0
node viewer "Viewer" at 2,0
node api "API" at 0,1
node cdn "CDN" at 2,1
node db "Metadata DB" at 0,2
node obj "Object storage" at 2,2
node pipe "Scan/transform pipeline" at 1,3

client -> api : "POST /uploads\nPOST /complete"
api -> client : "signed URL"
client -> obj : "PUT parts directly"
api -> db : "txn + outbox"
db -> pipe : "event"
pipe -> obj : "read/write variants"
pipe -> db : "READY"

viewer -> api : "request media"
api -> viewer : "auth / signed URL"
viewer -> cdn : "GET variant"
cdn -> obj : "fetch on miss"
cdn -> viewer : "object variant"
```

Metadata database owns `Media(id, owner, visibility, original_key, checksum, state, transform_version, deleted_at)`. Object storage owns bytes. State is explicit: `UPLOADING`, `PENDING_SCAN`, `PROCESSING`, `READY`, `FAILED`, `DELETED`.

Direct multipart upload avoids tying application instances to 50 MB transfers and permits resume. Completion verifies part list/checksum and only activates metadata after object existence is confirmed. Transform jobs use `(media_id, transform_version, variant)` as idempotency key: duplicate events never create conflicting state.

## Design choices

Store originals and immutable derivative keys, such as `media/{id}/v3/800w.webp`; metadata selects current version. This makes <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> caching safe and allows an algorithm change to create v4 without corrupting v3. Do not trust extension/MIME alone: inspect bytes, cap dimensions/decompression, scan under appropriate policy, and isolate unsafe processors.

Deletion is a state transition first: origin denies immediately, signed URL issuance stops, and <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is purged/short-lived. A worker then deletes derivatives/original and records completion. This prevents a slow cleanup job from exposing content. Define retention/legal hold separately from ordinary deletion.

## Deep dive 1: Resumable uploads on bad networks

- **Multipart:** split into 8 MB parts; each part is uploaded and retried independently; the client persists `upload_id` and completed part ETags locally so an app restart resumes rather than restarts.
- **Integrity:** the client sends the whole-file SHA-256 at session creation and per-part checksums; completion verifies both. Silent corruption is caught before the file becomes a `Media`.
- **Abandoned uploads:** sessions expire (e.g., 24 h); an object-store lifecycle rule aborts incomplete multipart uploads so unfinished parts don't accumulate cost.
- **Small files:** under ~5 MB a single signed PUT is simpler; the <abbr title="Application Programming Interface">API</abbr> decides based on `size`.

## Deep dive 2: The transform pipeline

```arch
%% caption: A flagged upload is quarantined before it ever reaches a transform worker or becomes visible.
node outbox "Complete → outbox event" at 0,0
node scan "Scan queue" at 1,0
node scanner "Scanner" at 2,0
node xform "Transform queue" at 3,0
node worker "Worker" at 4,0

outbox -> scan : "event"
scan -> scanner : "dequeue"
scanner -> scanner : "quarantine (flagged)"
scanner -> xform : "enqueue (clean)"
xform -> worker : "dequeue"
worker -> worker : "decode → resize → encode\nwrite keys, mark READY"
```

- **Decode once, emit all variants** in one job; decoding dominates cost for large images.
- **Security:** image decoders are a classic attack surface. Run them in sandboxed workers with no network access, cap pixel dimensions (decompression bombs: a 50 KB PNG can declare 50,000 × 50,000 pixels), strip EXIF GPS by default for privacy, and set <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/memory limits per job.
- **Idempotent writes:** deterministic keys `media/{id}/v{transform_version}/{variant}` mean a retried job overwrites with identical bytes. State moves with a guarded update (`WHERE state = 'PROCESSING' AND transform_version = :v`), so an old duplicate event can't regress a newer state.
- **Priority:** user-facing uploads ahead of backfills (e.g., re-encoding the whole library to AVIF) using separate queues.
- **Autoscaling** on queue age, not <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>; transforms are bursty.

## Deep dive 3: Serving at global scale

- Variants are **immutable**, so <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> responses use `Cache-Control: public, max-age=31536000, immutable` (for public media) — a new transform version is a new URL, never an invalidation for a version change.
- **Deleting public media is the one case that does need a purge.** With a one-year TTL a lost purge would leave a deleted photo visible far beyond the question's one-hour bound. At ~3 deletes/s (about 15 variant URLs/s) a purge is cheap: purge by media tag or key prefix where the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> supports it, retry until acknowledged, alert when a purge is older than 15 minutes, and re-purge everything deleted in the last 24 hours from a reconciliation job. Origin returns `404` for a deleted `media_id` at once, so the exposure is limited to edge copies not yet purged.
- **Private media:** the <abbr title="Application Programming Interface">API</abbr> issues short-lived **signed URLs** (or signed cookies) scoped to the object; the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> verifies the signature at the edge, so authorization doesn't hit origin on every view. Deletion or privacy change stops issuing new signatures; existing ones expire within minutes.
- **Origin shield:** a regional mid-tier cache coalesces concurrent misses so a viral photo doesn't stampede object storage.
- **Responsive delivery:** clients request the smallest variant that fits the display; `Accept` header chooses AVIF/WebP/JPEG.

## Deep dive 4: Storage cost

- **Tiering:** originals move to infrequent-access then archive tiers after N days of no access; thumbnails stay hot. Restore from archive is slow, so keep display-size variants hot.
- **Dedupe:** content hash lets the system store identical bytes once. **Precision:** cross-user dedupe leaks information (a user can probe whether a given file exists by timing or by instant upload) — scope dedupe per user or per tenant unless the privacy review approves otherwise.
- **Re-derivable variants:** variants can be regenerated from originals, so they don't need the same replication/erasure-coding level as originals.

## Failure and operations

Object event duplicate/out-of-order: use guarded state/version. Worker crash: retry from durable queue. Scanner unavailable: retain `PENDING_SCAN`, never expose content prematurely. <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> outage: authorized origin fallback may be limited; do not overload metadata store. Track upload completion, checksum mismatch, scan/transform queue age, failure/retry, ready latency, derivative/orphan count, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> hit rate, delete propagation. Build a local upload session, fake object store, and thumbnail worker; kill worker midway and verify retry.

**Orphan reconciliation:** a periodic job lists object keys and joins against metadata (both directions) to find bytes without metadata (failed completes) and metadata without bytes (bugs). Cheap insurance against silent storage leaks.

## Interview close

"Bytes never touch the <abbr title="Application Programming Interface">API</abbr> tier: clients upload resumable multipart parts straight to object storage with checksums, and metadata only becomes READY after scan and transform. Variants use immutable versioned keys, so the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> caches forever and a new pipeline version is a new URL. Private content uses short-lived signed URLs verified at the edge, and deletion is a state change that revokes access first and cleans up bytes second."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Upload to the nearest region's storage endpoint, write the original there, and replicate it to a second region for durability; run the transform pipeline in the origin region and let the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> pull variants. Metadata has one owner per `media_id` (the upload's home region) with replicas elsewhere. A delete is a tombstone replicated to all regions, then purge and per-region byte deletion, all inside the one-hour bound. If a region fails, uploads go to another region, and the client's resumable session carries part ETags so it can continue.
2. **"What changes at 10× and 100×?"** At 10× peak ingress is about 700 Gbps and the transform fleet about 14,500 cores, so spread uploads over regional endpoints and autoscale on queue age. Storage is ~550 PB/year, so erasure coding, tiering, per-user dedupe and better formats stop being optimisations and become the design. At 100× you also reconsider what you keep: for example, whether variants for old photos are generated lazily on the first view rather than eagerly for all of them.
3. **"A user deletes a photo they shared by mistake and it must be gone everywhere now. Also, the uploader must see their photo immediately."** Delete flips state first, so origin and signed-URL issuance deny at once; edge copies then depend on purge (usually seconds to a minute, vendor-dependent), and private media, served by short-lived signed URLs (say 5 minutes), needs no purge at all. For the uploader, show the client's local copy while state is `PROCESSING`, and generate a small thumbnail first so the first variant is ready in well under a second.
4. **"What dominates cost?"** Storage: ~55 PB/year of originals plus ~14 PB of variants, before replication. Erasure coding around 1.4× instead of 3× replication takes 55 PB from about 165 PB to about 77 PB raw. Then tier originals to infrequent-access and archive after 30-90 days without access (assumption; measure), keep display variants hot, dedupe per user, abort abandoned multipart uploads with a lifecycle rule, and use smaller formats. <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> egress is the second line, driven by hit ratio and variant sizes.
5. **"How is it abused?"** Illegal content, so scan uploads with hash matching against known-bad lists and have a reporting path before anything becomes visible; malware and polyglot files, so inspect bytes and never trust MIME or extension; decompression bombs (a 50 KB PNG declaring 50,000 × 50,000 pixels), so cap pixels and run decoders in sandboxes with <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> and memory limits; storage exhaustion, so per-user quotas and rate limits; and hotlinking, so signed URLs for private media. A poison image that crashes a decoder gets 3 attempts, then `FAILED` with a reason, and never blocks the queue.
6. **"You ship a better encoder (`v4`). How do you roll it out across the library?"** Write `v4` under new immutable keys for all new uploads behind a percentage flag, compare size and quality on a sample, then flip the metadata pointer. For old photos, generate lazily on first view and backfill the rest at low priority: the library grows by 18B photos a year, so re-encoding one year at 0.5 <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-s each is 9B <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-seconds, about 106k core-days, which is roughly 21 days on a dedicated 5,000-core backfill pool. Rollback is flipping the pointer back to `v3`, which still exists.
7. **"Why precompute five variants for every photo? Most are never viewed at 2048 px. Generate on demand and let the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> cache."** On-demand saves storage and compute for variants nobody views, but the first viewer of each pays a decode-and-resize on the request path (a few hundred ms), it needs a hot-path compute fleet, and arbitrary sizes let attackers bust the cache, so you would have to allow only a fixed set of sizes anyway. I would precompute the thumbnail and display size, which serve the large majority of views, and generate the rest lazily.
8. **"Can we publish before scanning to hit 10 seconds?"** Not for other viewers: an unsafe image served even briefly is the failure the requirement forbids. Compromise: make the photo visible to its owner immediately while it stays `PENDING_SCAN` for everyone else, and split the scan into a fast hash-match gate (sub-second, blocks publication) and slower model-based checks that run after publication for lower-risk categories and can take content down.

## Common mistakes

1. **Streaming 50 MB uploads through the <abbr title="Application Programming Interface">API</abbr> tier.** At 70 Gbps peak that is a fleet of proxies for no benefit. Issue signed URLs and let the client write to object storage.
2. **One request per upload with no resume.** On mobile networks a 50 MB single PUT fails often and restarts from zero. Use multipart with persisted part ETags and per-part retry.
3. **Publishing before the scan, or trusting the extension and MIME type.** Unsafe or mislabelled content gets served. Inspect bytes, keep `PENDING_SCAN` invisible, and derive the content type from your own inspection.
4. **Running image decoders in-process without limits.** Decoders are a classic attack surface. Sandbox them, cap pixel dimensions and <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/memory, and strip EXIF location data by default.
5. **Overwriting variants at mutable keys.** The <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> then serves stale bytes and you need invalidations. Use immutable versioned keys and change the URL for a new version.
6. **Treating delete as "remove the bytes".** <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> copies and signed URLs survive. Flip state first, stop issuing URLs, purge, then delete bytes, and reconcile.
7. **Forgetting abandoned multipart uploads.** Incomplete parts silently accumulate cost. Set a lifecycle rule to abort them (for example after 24 h) and reconcile orphans.
8. **Cross-user dedupe without a privacy review.** Instant-upload responses reveal whether someone already stored a file. Dedupe per user or tenant unless privacy signs off.

## Going from L5 to L6

- **Migration and rollout path.** Treat `transform_version` as the rollout unit: canary `v4` on 1% of uploads, compare size and quality, ramp, then backfill old photos lazily and at low priority under a compute budget. Rollback is a metadata pointer flip because old versions still exist.
- **Cost model.** Storage is the bill. Show cost per photo over its life under replication versus erasure coding and under each tiering policy, then egress, then compute. Pair each format decision (for instance AVIF versus WebP) with measured bytes saved on your own corpus rather than a vendor claim.
- **Ownership and blast radius.** Split upload, the scan and transform pipeline, and serving into separately owned services, and give trust and safety ownership of scanning policy. A pipeline outage must not stop uploads: bytes are safe in object storage, state stays `PENDING_SCAN`, and the backlog drains later.
- **Build versus buy.** Object storage and <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> are bought. Decoder libraries (libvips or ImageMagick-class) are reused. Hash-matching for illegal content is an industry-list integration or a specialist vendor. What you build is the state machine, the immutable-key scheme and the delete workflow.
- **What to measure first.** The size and dimension distribution, which variants are actually requested, the view-age curve (how fast views decay), and the deleted share. They decide eager versus lazy variants, tiering ages and how much AVIF is worth.
- **Phased evolution.** Ship direct upload with two eager variants and <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, add scan gating, then lazy generation for the long tail, then tiering and erasure coding, then multi-region.

## Build exercise

Implement upload sessions with parts, a fake object store with ETags, and a transform worker producing two variants under deterministic keys. Test: interrupt an upload after part 2 of 4 and resume; deliver the transform event twice and verify identical final state; delete mid-transform and verify no variant becomes publicly readable. Named assertions:

- `test_resume_after_part_2_of_4`: fail the upload after two parts; assert the resumed session uploads only parts 3 and 4 and completion succeeds.
- `test_complete_is_idempotent`: call `complete` twice; assert one `Media` row and one `PENDING_SCAN` transition.
- `test_duplicate_transform_event_same_state`: deliver the transform event twice; assert identical final state and one set of variant keys.
- `test_old_event_cannot_regress_state`: deliver a `v3` event after `v4` is `READY`; assert the state is unchanged.
- `test_delete_mid_transform_never_readable`: delete while the worker runs; assert no variant is served afterwards and object bytes are removed.
- `test_pixel_cap_rejects_bomb`: submit a tiny file declaring 50,000 × 50,000 pixels; assert it goes to `FAILED` without exhausting worker memory.
- `test_flagged_never_reaches_transform`: mark an upload as flagged; assert it is quarantined and no transform job is enqueued.
