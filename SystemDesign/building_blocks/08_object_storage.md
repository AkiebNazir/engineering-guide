# Object Storage

Object storage (S3-like) holds large, unstructured blobs — images, video, documents, backups, exports — as opaque objects addressed by key, with metadata but no query language. It is not a database and not a filesystem; treat it as durable, cheap, horizontally-scaled bytes-at-rest, and keep everything queryable (owner, status, content hash, size, access rules) in your actual database instead.

## Why not a DB BLOB or a filesystem on one box

| Option | Problem |
|---|---|
| BLOB column in the relational DB | Bloats table/index size, slows backups and replication (the whole row set now includes megabytes of binary), and burns transactional-database capacity on something that doesn't need transactions or joins. |
| Filesystem on a single application/box | Not durable past that box (no built-in replication), doesn't scale past that disk, and ties file availability to that specific instance being up — breaks the "any healthy instance can serve" property of a stateless app tier. |
| Object storage | Durable by replication across the service, scales independently of the app tier, and the app never touches the bytes directly — it just authorizes access. |

The rule: your database holds the *fact* that an object exists and its metadata; object storage holds the *bytes*. Losing the bytes and losing the fact are different failure modes and should be handled separately.

## Direct/presigned upload flow


```arch
%% caption: By generating a presigned URL, the API server authorizes the upload without handling the large payload bytes itself.
node client "Client" at 0,1 icon=client color=blue
node api "API Server\n(Generates URL)" at 2,0 icon=server color=slate
node obj "Object Storage\n(S3 / GCS)" at 2,2 icon=db color=green

client -> api : "1. Request upload URL"
api ..> client : "2. Signed URL"
client ==> obj : "3. Direct PUT bytes"
```
Routing large file bytes through your application servers wastes their capacity on pass-through I/O and pushes bandwidth cost onto infrastructure that should be doing business logic. Let the client upload directly to object storage instead, authorized by a short-lived signed URL.

```arch
%% caption: The API server never sees the file bytes — it only issues authorization, the same shape as the CDN/edge principle.
node c "Client" at 0,0 icon=user color=slate
node api "API" at 1,0 icon=server color=purple
node obj "Object storage" at 0,1 icon=folder color=blue
node w "Async worker" at 1,1 icon=process color=teal
node db "DB" at 2,1 icon=db color=orange
c -> api : "I want to upload a file"
node auth "authorize, gen signed URL" at 2,0 shape=text
api -> auth -> api
api -> c : "signed URL + key"
c -> obj : "PUT bytes directly"
obj -> w : "object created event"
node proc "validate → scan → transform" at 1,2 shape=text
w -> proc -> w
w -> db : "status PENDING → READY"
```

The <abbr title="Application Programming Interface">API</abbr> server never sees the file bytes — it only issues authorization. This is the same shape as the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>/edge principle: keep large-byte traffic off the tier that runs your business logic.

## Content validation after upload

Never trust a client-supplied MIME type, filename, or file extension — a client can label anything `image/png` and it's just a request header, not a guarantee about the bytes. After upload, a worker must:

- Sniff the actual content type from the byte signature (magic bytes), not the client's claimed `Content-Type`.
- Reject or re-derive the extension/type from the real content, not the filename.
- Run malware/virus scanning before the object is marked usable, for anything a user can upload and another user can later retrieve.
- Enforce size limits server-side (signed URL can cap size, and the worker double-checks).

The object's DB row should stay in a `PENDING`/`UNVERIFIED` state — not linkable or servable to other users — until validation completes and flips it to `READY`. This closes the gap where a client uploads something malicious and other users could fetch it before scanning finishes.

## Event-driven post-processing

Object storage upload events are the natural trigger for everything that has to happen to the object before it's usable: thumbnailing an image, transcoding a video into multiple resolutions, extracting text from a document, running a malware scanner. This keeps heavy transformation work off the request path entirely — the upload succeeds immediately, and derivative generation happens asynchronously.

```arch
%% caption: Heavy transformation work stays off the request path entirely — the upload already succeeded before any of this runs.
node obj "Object storage" at 1,0 icon=folder color=blue
node q "Queue" at 1,1 icon=doc color=slate
obj -> q : "object created event"
node thumb "Thumbnail generator" at 0,2 icon=process color=teal
q -> thumb : "dequeue"
node thumb_t "writes derivative obj + DB row" at 0,3 shape=text
thumb -> thumb_t -> thumb
node scan "Malware scanner" at 1,2 icon=process color=red
q -> scan : "dequeue"
node scan_t "flips status or quarantines" at 1,3 shape=text
scan -> scan_t -> scan
node trans "Transcoder" at 2,2 icon=process color=purple
q -> trans : "dequeue"
node trans_t "writes resolution variants" at 2,3 shape=text
trans -> trans_t -> trans
```

See `09_messaging_and_streaming.md` for the queue/worker mechanics (visibility timeout, retries, DLQ) that make this reliable — an object storage event is just another producer into that same async-work machinery.

## Lifecycle tiers and expiry

Object storage classes typically split into hot (frequent access, higher per-GB cost), cool/infrequent-access (cheaper storage, retrieval fee), and archive (cheapest storage, slow/expensive retrieval, meant for compliance retention or backups nobody expects to read soon). Define a lifecycle policy per object class up front:

| Tier | Use for | Cost shape |
|---|---|---|
| Hot | Actively served user content (profile photos, current catalog images). | Higher storage cost, cheap/fast retrieval. |
| Cool/infrequent | Older content still occasionally accessed (past order invoices). | Lower storage cost, retrieval fee applies. |
| Archive | Compliance retention, backups, rarely-if-ever read. | Lowest storage cost, slow and costly to retrieve. |

Automate the transition (e.g., "move to cool after 90 days of no access") and set explicit expiry for anything with a retention policy — logs, temp exports, expired user uploads — rather than relying on someone to remember to delete it manually.

## Multipart / resumable upload

For large files (video, large datasets), a single PUT is fragile — one network blip and the whole upload restarts. Multipart upload splits the file into chunks uploaded independently (and in parallel), each acknowledged separately, with a final "complete multipart upload" call that stitches the parts together server-side. This bounds retry cost to one failed chunk instead of the whole file, and enables resuming an interrupted upload from where it left off rather than from zero. Use it above a size threshold (commonly a low tens-of-MB cutoff) — below that, the coordination overhead isn't worth it.

## Delete propagation to derivatives

Deleting an object is rarely just one object. A user photo might have a thumbnail, a few resized variants, and a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>-cached copy. Deleting the source object without propagating to its derivatives leaves orphaned data (a compliance problem for user-requested deletion) and dangling references (a correctness problem — code that expects the thumbnail to exist). Track derivative relationships in the DB (a `parent_object_id` or similar), and make delete a workflow: mark source deleted → enqueue derivative cleanup → invalidate any <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> cache entries → confirm all derivatives gone before considering the delete complete. Treat "delete" the same way you'd treat any other multi-step operation with partial-failure risk — see the saga pattern in `12_application_resilience_patterns.md`.

## Related building blocks

- [09_messaging_and_streaming.md](09_messaging_and_streaming.md)
- [05_databases.md](05_databases.md)
- [14_security.md](14_security.md)
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)
- [16_platform_and_infra.md](16_platform_and_infra.md)
