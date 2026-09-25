# 015 — Cloud Drive / File Sync: Full System Design Solution

## Goal and contract

A drive service stores files durably, lets users organize them into folders, shares them by ACL, keeps version history, and syncs the same view of the world across multiple devices — including devices that were offline and edited locally. The invariant is not "last write wins is fine" — it is: every accepted write produces a new immutable version, current-version metadata is transactionally consistent with the folder/ACL graph, and an offline edit never silently destroys another device's concurrent edit.

Assume (the first five come from the question; the rest are labelled assumptions):

- **50 million active users, 2 billion files, average file 4 MB**, so a logical corpus of 8 PB.
- **200,000 uploads/second at peak**, files up to **5 GB** (5 GiB used for arithmetic).
- Sync propagation to other devices **p99 under 10 s** for small files.
- Deleted items recoverable for **30 days**; version history retained for **at least 100 versions or 90 days** per file.
- Devices can be offline for days before reconnecting. Assumption: 2.5 devices per user, 30% online at the peak.

The core split is: **object storage holds immutable, content-addressed bytes (chunks)**, **a transactional store holds mutable metadata** (folder tree, current version pointer, ACL pointers, trash state, per-namespace change journal). Nothing about which chunk key exists implies who may read it — permission is decided by metadata lookup at URL-issuance time, never by knowledge of a storage key or a content hash.

**How I read the 200k/s constraint.** Taken literally as whole 4 MB files, 200,000 uploads/s is 800 GB/s (6.4 Tbps, 69 PB/day), which would re-create the entire 8 PB corpus in 2.8 hours, roughly 10,000× the growth a 30%-per-year corpus implies (2.4 PB/year ≈ 76 MB/s). So I read it as a **peak rate of upload operations (version commits plus their chunk uploads) that lasts minutes**, dominated by edits of existing files, and I design two planes for it: the **control plane** (metadata commits and "which chunks do you already have" checks) is sized for the full 200k/s, and the **data plane** (bytes that actually cross the wire) is sized for a stated fraction of the literal number, because chunk-level deduplication and delta sync mean most of an edit is not re-sent. If the interviewer says the literal figure is intended, the answer changes in scale, not in shape, and I say so with the arithmetic below.

## Estimates

- **Corpus**: 2B files × 4 MB = **8 PB logical**, or 40 files and 160 MB per active user on average (the mean hides a heavy tail: most files are tiny, a few are gigabytes). So bytes live in an object-storage-class system; metadata is a few terabytes (below).
- **Versions and storage**: assume 30% of files are edited, 5 extra versions each, and each edit changes ~10% of the file's chunks: 2B × 0.3 × 5 = 3B extra versions, adding 3B × 0.4 MB ≈ **1.2 PB** because unchanged chunks are shared, for **~9.2 PB logical**. Assume cross-file deduplication removes another 20% (assumption; measure it): **~7.4 PB unique**. With erasure coding at 1.5× overhead that is **~11 PB raw**; three-way replication would need ~22 PB. So chunk-level versions, deduplication, and erasure coding are cost decisions worth about 11 PB of disks, and we keep ~10% hot and tier the rest.
- **The literal peak**: 200k × 4 MB = **800 GB/s = 6.4 Tbps**. Since dedup and delta mean only a fraction *r* of the bytes are new, the planning point is **r = 10%: 80 GB/s ≈ 640 Gbps** (r = 1% would be 8 GB/s, r = 100% is the literal figure). Spread over 20 ingest regions that is ~4 GB/s (32 Gbps) each, and at ~0.4 GB/s of sustained ingest per storage node (assumption) about **200 storage nodes**. Verifying every chunk's hash at ~1.5 GB/s per core (assumption) is ~53 cores at full load, ~160 at a third. So ingest is bandwidth- and disk-bound, not <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound. Because a peak lasts minutes, we add **priority lanes** (small interactive files ahead of bulk imports) and `429 Retry-After` backpressure rather than provisioning for every bulk import to finish in seconds.
- **Commit path (control plane)**: treat all 200k/s as version commits at the worst case. Each commit writes ~4 rows (version, file pointer update, journal entry, quota) = **800k row writes/s**. Over 256 metadata shards that is ~780 commits/s and ~3.1k row writes/s per shard. A single namespace serializes its commits on one row (like any hot row, ~1.5 ms each, so ~670/s), which is fine for a personal namespace and not for an org-wide shared folder with thousands of uploaders. So metadata shards by namespace, per-user commit rates are capped, and hot shared namespaces get batched commits.
- **Metadata volume**: 2B file rows × ~1 KB = 2 TB; (2B + 3B) version rows × ~300 B = 1.5 TB; per-version chunk lists ~0.7 TB flat (much less with the shared manifest pages below); a journal of 100M commits/day (assumption) × ~200 B = 20 GB/day, 1.8 TB over 90 days. About **6 TB, ~18 TB replicated**. So sharding is for throughput, not for size.
- **Chunk index**: 7.4 PB unique ÷ ~1 MB average chunk ≈ **7.4B chunks** × 44 B (32 B hash plus location) ≈ **0.32 TB**, sharded by hash prefix. At a 256 KB average it would be 29B chunks and 1.3 TB; at a 4 MB fixed block, 1.8B and 0.08 TB. So the index fits in a sharded key-value store with room to spare at 1 MB, and the chunk size is a trade-off between index size and delta efficiency, not a capacity wall.
- **Sync connections**: 50M users × 2.5 devices = 125M devices; 30% online is **37.5M concurrent connections**, ~375 gateways at ~100k connections each (about 2 GB of state per gateway at ~20 KB per connection, assumption). A notification is ~50 bytes ("namespace X is at seq N"). At the literal 200k commits/s and ~2 other devices per namespace that is 400k pokes/s, ~1.1k/s per gateway; a jittered 5-minute safety poll from every online device is 37.5M ÷ 300 = **125k cheap requests/s**. So notification is a light fan-out service, and the journal, not the push, is the source of truth.
- **Sync latency budget** (targets): chunk PUT 150 ms + commit 50 ms + journal to pub/sub 200 ms + coalescing up to 1 s + change pull 100 ms + chunk GET 150 ms ≈ **1.7 s typical**, leaving ~6× headroom inside the 10 s p99 for retries and backlog.

## Core mechanisms

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Object storage per version | Every saved edit writes a brand-new immutable object; nothing is overwritten. | Always, for file bytes. | Storage cost grows without a version <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr>/retention policy. |
| Content-addressed chunks with version manifests | A file version is an ordered list of chunk hashes; chunks are stored once by hash and shared by every version and file that contains them. | Editable files where most of a new version is unchanged, and any fleet where duplicates are common. | Needs chunk-level <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr>, a hash-verification step, and a scoped dedup policy (see the privacy side channel below). |
| Relational metadata (current pointer, folder, ACL) | Transactional row per file: current version id, parent folder id, owner, ACL, trash flag. | Always, for anything that must be atomically consistent. | Cannot hold GB-scale content itself. |
| Change cursor / event log | Monotonic per-namespace sequence number bumped on every metadata mutation. | Powering device sync and search indexing. | Needs careful compaction so old cursors remain resolvable. |
| Resumable direct upload | Client uploads straight to object storage via a signed URL, chunk by chunk, with resume from the still-missing chunks. | Any file above a few MB. | Requires a separate "commit" step so storage isn't a silent source of truth before metadata exists. |
| Outbox on metadata commit | Metadata transaction writes an outbox row atomically with the version/folder change (here, the journal entry doubles as the outbox). | Driving sync feed, search indexing, antivirus scanning. | Adds a relay worker and at-least-once delivery to reason about. |
| Relation-tuple authorization graph | Permissions stored as `object#relation@subject` tuples with inheritance through folders and groups. | Sharing with individuals, groups, and folders at scale. | Deep nesting and cache invalidation; needs consistency tokens to avoid the "new enemy" problem. |

## <abbr title="Application Programming Interface">API</abbr>

```text
POST /v1/uploads                                  # begin, or resume, an upload session
  { ns_id, parent_id, name, base_version_id, size, mtime, chunker_id,
    chunks: [{hash, len}, ...] }                   # first 1,000 entries, rest via PUT /manifest pages
  → 200 { session_id, missing: [hash...], upload_urls: { hash: signed_put_url }, expires_at }
  → 403 { code: "QUOTA_EXCEEDED" }   413 (over 5 GiB)   429 (Retry-After: per-user or ingest backpressure)

PUT  {signed_put_url}                              # one chunk, at most 4 MiB, server recomputes SHA-256
  → 204 | 409 { code: "HASH_MISMATCH" }

POST /v1/uploads/{session_id}/commit               # Idempotency-Key: <commit_token>
  { base_version_id }
  → 201 { file_id, version_id, seq }               # fast-forward: base was the current version
  → 201 { file_id, version_id, seq, conflict: { copy_file_id, name } }   # base was stale: saved as a conflict copy
  → 422 { code: "CHUNKS_MISSING", missing: [...] }

GET  /v1/files/{file_id}                           → metadata, current version, rev
GET  /v1/files/{file_id}/content?version_id=…      → { manifest, download_urls: { hash: signed_get_url } }   # ACL checked here
GET  /v1/files/{file_id}/versions?limit=50&cursor=…
POST /v1/files/{file_id}/restore   { version_id }  # creates a NEW version pointing at the old manifest, zero bytes copied
POST /v1/files/{file_id}/move | rename | trash | untrash   { expected_rev, … }   # guarded by rev, idempotent

GET  /v1/changes?ns_id=…&cursor=…&limit=500&wait=30        # long-poll change feed
  → 200 { entries: [{seq, op, file_id, parent_id, name, version_id, manifest_hash, size, rev, deleted}],
          next_cursor, has_more }
  → 410 { reset: true }        # cursor older than the journal horizon or from a previous epoch: resync from a snapshot
GET  /v1/notify                                    # WebSocket or SSE, server sends { ns_id, seq } pokes

POST   /v1/shares   { object, subject, role }      # creates a relation tuple
DELETE /v1/shares/{share_id}
```

- **Cursor** is `(epoch, seq)` and opaque to the client. The epoch changes on a disaster-recovery failover, so a device whose cursor is ahead of the server (it saw writes that were lost) is told to reset and merge instead of silently missing history.
- **Idempotency**: the commit is keyed by a client-generated `commit_token`; a retried commit returns the same version. Begin-upload is idempotent on `(device_id, parent_id, name, manifest hash)`, so a restarted client gets the same session with the still-missing chunks.
- **Quota counts logical bytes**, never deduplicated physical bytes, so quota changes cannot leak whether a chunk already existed (see the dedup section).
- **Errors**: `429` for per-user commit limits and ingest backpressure, `409 HASH_MISMATCH` on a corrupt or lying chunk upload, `403` on ACL denial (returned in constant time whether or not the object exists), `410` for a stale cursor.

## Data model

| Entity | Key and shape | Role | Partitioning |
|---|---|---|---|
| `namespaces` | `ns_id` → `owner, type (PERSONAL/SHARED), root_folder_id, cursor_seq, epoch, quota_used` | A unit of consistency: one user's tree, or one shared folder | Hash of `ns_id` across 256 shards |
| `files` | `(ns_id, file_id)` → `parent_id, name, current_version_id, state (ACTIVE/TRASHED), trashed_at, rev`, unique `(ns_id, parent_id, folded name)` | **Source of truth** for the tree; identity is `file_id`, the path is derived from parent pointers | With the namespace |
| `versions` | `(ns_id, file_id, version_id)` → `seq, manifest_hash, size, base_version_id, device_id, author, created_at, mtime` | Immutable version history | With the namespace |
| `manifest_nodes` | `node_hash` → up to 64 `(child_hash, len)` entries; the root is the version's `manifest_hash` | Content-addressed hash tree of chunk hashes; shared across versions and files | By hash prefix |
| `chunk_index` | `(scope, chunk_hash)` → `physical_id, extent, offset, len, created_at` | Logical-to-physical mapping; `scope` is the tenant or user for client-visible dedup | By hash prefix |
| Chunk store | `physical_id` → immutable bytes | **Source of truth** for content; erasure-coded, checksummed | Storage-node placement, not by user |
| `journal` | `(ns_id, seq)` → `op, file_id, version_id, at` | Per-namespace change feed **and** outbox for indexing, scanning, and notifications | With the namespace; retained 90 days |
| `upload_sessions` | `session_id` → `ns_id, target, base_version_id, manifest, state, expires_at` (TTL 24 h) | Resumable upload state | By `session_id` |
| ACL tuples | `object#relation@subject` | Authorization graph (Zanzibar-style, see below) | Separate ACL service, sharded by object |

The **chunk index and chunk store are shared infrastructure**; everything user-visible (files, versions, journal, quota) lives in the namespace shard. **Rename and move are O(1)**: children point at `parent_id`, so moving a folder with a million files updates one row, never a path prefix on every descendant.

## Architecture and data flow

```arch
%% caption: Chunks land in the store before metadata knows the file exists, and only the metadata commit, a compare-and-set on the base version, decides what the current version is.
grid 5x4
node dev "Device A" at 0,1
node store "Chunk Store" at 2,0
node api "Metadata API" at 1,2
node idx "Chunk Index" at 2,3
node meta "Namespace Shard" at 2,2
node relay "Journal Relay" at 3,2
node notif "Notify Gateways" at 4,2
node dev2 "Device B" at 4,1

dev -> store
dev -> api
api -> idx
api -> meta
meta -> relay
relay -> notif
notif -> dev2
dev2 -> api
dev2 -> store
```

The hard decision is where the upload "commits." Bytes land in object storage before metadata says the file exists — this trades a window where storage holds an orphan chunk for the ability to resume huge uploads without holding open a database transaction for minutes. The metadata transaction, not the chunk PUT, is the source of truth for existence; a chunk referenced by no committed version is garbage, not a file. Direct upload reduces <abbr title="Application Programming Interface">API</abbr>-server bandwidth (bytes never transit the app tier) but concentrates authorization at two points: the metadata commit and the issuance of signed URLs, which must be scoped to exactly the chunks a caller may write or read, and short-lived, so they cannot be replayed to overwrite or fetch unrelated content.

**One write, end to end.** The client chunks the file, hashes each chunk, and calls `POST /uploads` with the hash list. The <abbr title="Application Programming Interface">API</abbr> asks the chunk index which hashes are missing *in the caller's scope*, and returns signed PUT URLs for those only, so an unchanged 5 GB file costs one round trip and zero bytes. The client uploads missing chunks in parallel (4–8 at a time); the storage tier recomputes each SHA-256 and rejects a mismatch. `commit` runs one transaction on the namespace shard: verify every chunk is present, <abbr title="Compare-And-Swap. An atomic instruction used in multithreading to achieve synchronization by comparing and potentially modifying a memory location.">CAS</abbr> `files.current_version_id` from `base_version_id` to the new version, insert the `versions` row, allocate `seq` from the namespace row, append the `journal` row, and update quota, all together. A retried commit with the same token returns the same version. A relay publishes the journal row to notifications, search indexing, and antivirus scanning.

**One read, end to end.** Device B is poked with `(ns_id, seq)`, calls `GET /changes?cursor=C`, and applies entries in `seq` order. For each new version it diffs the manifest against its local chunk cache and calls `GET content` for the missing chunks only. The <abbr title="Application Programming Interface">API</abbr> checks the ACL at that moment, then issues short-lived signed GET URLs for exactly the chunks listed in that manifest. Chunk keys are content hashes, so they are shareable across files, but a hash is never sufficient to fetch anything: URLs are issued only for chunks in a manifest the caller may read.

## Capacity and storage

The derivation is in Estimates; the decisions it forces are these. About 7.4 PB of unique chunks is object-storage-tier scale — this is not a database concern; object storage is chosen precisely because it scales past any single database's row-blob limits, and erasure coding at ~1.5× halves the disk bill against triple replication. Metadata is the scaling constraint that matters for query latency: folder listing and sync must be indexed per namespace, not a table scan filtered by owner. At 200k commits/s in the worst case, the finalize-metadata transaction is the hot path — keep it to a small number of row writes plus the journal append, not a cascading recomputation of folder size or shared-with counts inline (those are asynchronous projections built from the journal).

Shard metadata by **namespace id**, so one user's folder tree and change cursor live on one partition and a folder listing or a sync-cursor read is single-shard. A shared folder is its own namespace; a personal tree that mounts shared folders reads several namespaces. A cross-namespace move (from a personal tree into a shared folder) is rare and is a two-step saga (add in the target, tombstone in the source, both idempotent). Do not implement "list changes since cursor" as an unindexed scan over the global version table — the per-namespace journal is the ordered log a device cursor walks forward from. Do not treat the object key as capability-bearing: a leaked or predictable key must not grant read access without a metadata/ACL check, because keys can leak through logs, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> caches, or forwarded links; for content-addressed keys that is even more important, since anyone who knows a file's hash could otherwise ask for it.

Tier storage by access: ~10% of bytes are recent and hot on the fast tier; the rest moves to a cold class after 90 days without access (assumption). Chunk garbage collection and version pruning free physical bytes only after the 30-day trash window and the version-retention rules below.

## Chunking strategy

**The problem.** A 5 GB file cannot be one PUT (one blip restarts it), and an edit to a 100 MB file should not re-upload 100 MB. The unit of transfer, resume, integrity, and deduplication needs to be smaller than a file and stable across edits.

| Approach | How it works | Gives | Costs |
|---|---|---|---|
| Whole-file objects | One object per version | Simplest | Every edit re-sends everything; no resume; no dedup; version storage is O(versions × size) |
| **Fixed-size blocks** (for example 4 MiB) | Cut at multiples of the block size | O(1) boundary math, trivially fast, a stable resume unit, and an overwrite in place changes one block | The **boundary-shift problem**: inserting a few bytes near the start moves every later boundary, so every later block hashes differently and is re-uploaded |
| **Content-defined chunking (CDC)** | Slide a rolling hash over the bytes and cut where the hash matches a mask, within min and max sizes | Boundaries follow content, so an insertion changes only the chunks around it; strong dedup across versions and files | <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> on the client (battery), variable chunk sizes, more metadata than big fixed blocks; parameters must be identical everywhere for dedup to work |

Two published anchors: content-defined chunking with Rabin fingerprints for bandwidth-saving file sync was described in the Low-Bandwidth Network File System (LBFS, SOSP 2001), and FastCDC (USENIX ATC 2016) reports a Gear-hash-based variant that is several times faster than Rabin-based chunking with nearly the same deduplication ratio. Dropbox has publicly described 4 MB blocks identified by SHA-256 hashes (its engineering blog and the Magic Pocket write-up, circa 2014–2016), which is the fixed-block end of this spectrum.

**Worked example (100 MB file, insert 10 KB at the start):** fixed 4 MiB blocks re-upload **all 25 blocks (100 MB)**; CDC with a 1 MB average re-uploads **the one or two chunks around the edit (about 1–2 MB, 1–2%)**. A 10 KB edit in the middle re-uploads one 4 MiB block (4%) with fixed blocks and one or two ~1 MB chunks with CDC.

**Block-size trade-offs (average chunk size, for 7.4 PB unique):**

| Average chunk | Chunks | Index at 44 B each | Requests for a 5 GiB file | Re-sent per small edit |
|---|---|---|---|---|
| 256 KB | 29B | 1.3 TB | 20,480 | ≤ ~0.5 MB |
| **1 MB** | 7.4B | 0.32 TB | 5,120 | ≤ ~2 MB |
| 4 MB (fixed) | 1.8B | 0.08 TB | 1,280 | up to ~4–8 MB |

**Decision.** Use CDC with a FastCDC-style Gear rolling hash: minimum 256 KB, **average 1 MB**, maximum 4 MB, for files above ~8 MB; smaller files are a single chunk. For types where edits rewrite everything or content is already compressed (video, images, most archives) the client uses fixed 4 MiB blocks and skips the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> cost. The client records a `chunker_id` (algorithm and parameters) in the manifest, and the policy can evolve without re-chunking old data: new versions use the new chunker, and old chunks stay valid. This trades client <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> and more metadata than a fixed 4 MB scheme for delta uploads that are ~50× smaller on insert-heavy edits and for higher dedup; the cost is acceptable because CDC is only run on files large enough to matter and the index is 0.32 TB. Dedup only works if every client chunks the same way, so the `chunker_id` is part of the contract and a change of parameters is a versioned rollout.

## Block-level dedup and its privacy side channel

**The problem.** Deduplicating by content hash saves storage and bandwidth, but a global "have you seen this hash" answer is an oracle: an attacker uploads (or merely queries) the hash of a specific file, and an instant "already exists" tells them that *some user in the system* stores that file. This is the confirmation-of-a-file attack in Harnik, Pinkas, and Shulman-Peleg, "Side Channels in Cloud Services: Deduplication in Cloud Storage" (IEEE Security and Privacy, 2010). A client that skips the upload on a hash match, with no proof it holds the content, can also be handed content it never had by anyone who learns the hash; the mitigation is a proof of ownership (Halevi et al., CCS 2011).

| Scope | Savings | Privacy | Costs |
|---|---|---|---|
| Per user | Lowest (the user's own duplicates only) | No cross-user signal | Poor for shared corpora and copies across folders of many users |
| Per tenant (an organisation or a consumer account) | Good for enterprises (the same documents across employees) | Signal is limited to people who already trust each other | Consumer accounts across tenants are not deduplicated |
| Global, client-visible | Highest | Has-chunk oracle; needs proof of ownership | The leak above, plus quota and timing leaks |
| **Client-visible dedup per scope; storage-level dedup globally underneath** (chosen) | Bandwidth savings inside the scope; physical storage savings across all scopes | No oracle: the index answer for a caller is always scoped to that caller | Cross-tenant duplicates cost upload bandwidth, but not storage |

**Decision.** The **logical index** is keyed `(scope, chunk_hash)`, and `begin upload` only ever reports chunks missing *within the caller's scope*, and never confirms a chunk it holds for someone else. The **physical store** dedups by content hash underneath: when a cross-scope duplicate arrives, the server accepts the upload, sees the hash exists physically, and adds a second logical reference to the same bytes. The uploader cannot observe the difference (identical latency budget, and quota counts logical bytes), so there is no oracle, while storage still keeps one copy. Where a client-visible cross-scope shortcut is wanted for very large files, require a proof of ownership: the server challenges with a random sample of chunk offsets and the client returns salted hashes of those ranges. This trades some ingest bandwidth for cross-tenant duplicates (bounded by the 20% dedup assumption, roughly half of which is cross-tenant, so about 1 PB of bytes re-sent once) for removing a privacy leak; the cost is acceptable because the privacy failure is an incident and the bandwidth is a line item.

**Never trust the client's hash.** The chunk store recomputes SHA-256 on ingest and rejects a mismatch. Without it, an attacker uploads garbage under the hash of a popular chunk, and every later "dedup hit" on that hash serves the garbage to other users (dedup poisoning). This costs ~53 cores at the peak (derived above), which is cheap insurance.

**Rate-limit the probes.** `begin upload` reveals which of a caller's own chunks are missing; cap and audit the number of distinct hashes a user can query per hour, so the endpoint cannot be used to enumerate the store.

## Version manifests and hash structure

A version is the ordered list of its chunk hashes plus their lengths. Storing that list flat costs 5,120 × 32 B = **164 KB for a 5 GiB file at 1 MiB chunks**, and 100 versions of it would be 16 MB, almost all of it repeated. A hash tree fixes that.

```arch
%% caption: A manifest is a tree of content-addressed nodes, so a new version of a large file writes only the nodes on the path to the changed chunks and shares every other node with older versions.
route straight
grid 230x80
node root "Version manifest root" at 0,1.5 color=blue sub="manifest_hash = version content id"
node p1 "Page 1" at 1,0.5 color=blue sub="up to 64 chunk entries"
node p2 "Page 2" at 1,2 color=blue
node pn "Page N" at 1,3 color=slate sub="unchanged, shared with v41"
node c1 "chunk hash + len" at 2,0 shape=box color=green
node c2 "chunk hash + len" at 2,1 shape=box color=green
node c3 "chunk hash + len" at 2,2 shape=box color=amber sub="edited in v42"
root -> p1
root -> p2
root -> pn
p1 -> c1
p1 -> c2
p2 -> c3
```

- **Structure.** Chunk hashes are grouped 64 per page, pages are hashed, and pages are grouped again until one root remains; `manifest_hash` is that root and doubles as the version's **content id**. A 5 GiB file is 5,120 leaf entries, 80 pages, 2 inner nodes, and 1 root (three levels at fan-out 64). Small files (up to 64 chunks) inline their manifest in the version row.
- **Cheap versions.** Editing one chunk changes one leaf page, its parents, and the root: about 2.4 KB of new manifest instead of 164 KB, roughly 70× less metadata per version. Identical pages are stored once because nodes are content-addressed.
- **Whole-file dedup for free.** Two files with equal content and chunker produce the same root, so a copy or a re-upload costs one metadata row and zero bytes. `restore` points a new version at an old root: zero bytes copied.
- **Diff and range reads.** Comparing two versions descends only into differing pages, so the diff is proportional to what changed rather than to the file. A range read of gigabyte 3 fetches one leaf page and verifies it up to the root.
- **Integrity end to end.** The client verifies each chunk's hash and the path to the root after download, so a corrupt replica or a lying URL is detected and refetched.
- **Where a flat hash list is enough.** For a file of a few hundred chunks, a flat list plus a root hash is fine; the tree earns its keep on very large files with many versions. State that choice when asked.
- **Namespace-level Merkle tree (repair only).** A Merkle tree over the folder tree lets a device and the server compare a single root and descend to the divergent subtrees (the same anti-entropy idea as in [Consensus and coordination](../building_blocks/19_consensus_and_coordination.md) and [Specialized data structures](../building_blocks/20_specialized_data_structures.md)). I would **not** maintain it on every commit: updating the root makes every commit in a namespace serialize on it. Build snapshots lazily from the journal and use them only when a cursor is unusable (reset, restored device).

## Sync: change feed, notifications, and delta sync

**The problem.** A device must converge to the server's state, quickly for small files (p99 under 10 s) and correctly after days offline, without asking the server "what do you have?" for every file.

**Change cursors.** Each namespace has a monotonic `seq`, allocated **inside the commit transaction** while holding the namespace row lock, so `seq` order is commit order. If a sequence number were allocated before commit and became visible after a later one, a device that already read past it would never see it: a lost update. A device stores `(epoch, seq)` per namespace, pulls `GET /changes?cursor=…` in pages of 500, and applies entries in order; renames, moves, deletes, and restores are all journal entries, so tombstones propagate through the same feed. The journal is retained 90 days; a device offline longer, or with a cursor from a previous epoch, gets `410 reset` and does a snapshot-based resync using the lazily built namespace tree.

**Notifications are pokes, not data.**

```arch
%% caption: The journal is the truth and the push path is only a hint, so losing a notification delays a device by one poll interval and never loses a change.
node commit "Commit txn" at 0,0 icon=db sub="version plus journal row"
group push "Push path (hint)" color=pink icon=notify style=dashed
node relay "Journal relay" at 0,1 in push icon=sync
node topic "Pub-sub topic" at 0,2 in push icon=topic sub="per namespace"
node gw "Gateway" at 0,3 in push icon=gateway sub="per subscriber group"
node ws "Device WebSocket" at 0,4 in push icon=websocket
node timer "Safety poll" at 1,3 icon=timer sub="every 5 min, jittered"
node pull "GET changes since cursor" at 1,4 icon=api
node reconnect "Reconnect" at 2,4 icon=connection
node journal "Journal" at 1,5 icon=db
commit -> relay -> topic -> gw -> ws
ws -> pull
pull -> journal
timer -> pull
reconnect -> pull
```

The relay publishes `(ns_id, seq)` per namespace, coalesced up to ~1 s. Each gateway subscribes to the namespaces its connected devices use, so a commit in a shared folder with 100k members sends one message per gateway (at most ~375), and each gateway fans out locally. A lost or duplicated poke is harmless: the device compares `seq` with its cursor and pulls. Reconnects, a 5-minute safety poll (125k requests/s across the fleet), and app foregrounding also pull, so the push path is an optimisation for latency, never a correctness dependency. Long-polling is the fallback transport for networks that block WebSockets.

**Delta sync.** Both directions transfer only chunks the other side lacks: the uploader after the missing-chunk check, and the downloader by diffing manifests against its local chunk cache. In-chunk binary deltas (the rsync algorithm, Tridgell and Mackerras, 1996) would save more on very large fixed blocks; at a ~1 MB average CDC chunk the residual waste is bounded, so I would skip that complexity at first.

## Conflicts and offline edits

Every device submits an edit with the **base version it started from**. The commit is a compare-and-set: `UPDATE files SET current_version_id=:new, rev=rev+1 WHERE file_id=:f AND current_version_id=:base`.

| Situation | Behavior |
|---|---|
| Base equals the current version | Fast-forward: the new version becomes current. |
| Base is stale (another device already committed) | Rowcount is 0. The commit still succeeds, but the late edit is saved as a **conflict copy** (`name (conflicted copy from <device> <date>).ext`) in the same folder, in the same transaction, and both versions are kept. No data is lost, and a person picks the winner. |
| Edit versus delete | The device edited a file that another device trashed. Preserve the edit: restore the file or save a conflict copy. Losing an edit is worse than resurrecting a file. |
| Two moves that would create a cycle | Both are in one namespace shard, so they serialize; the second sees that the target is now its own descendant and is rejected as a conflict. |
| Two files with the same name | Names are unique per folder; a collision gets a numeric suffix, and identity is always `file_id`. |
| Structured collaborative documents | Use operational transformation or a CRDT ([024 — Collaborative Document Editor](024_collaborative_document_editor_solution.md)); opaque files use copies, because the server cannot merge bytes it does not understand. |

The server-order rule ("first to commit wins, the loser becomes a copy") is deterministic and needs no clocks, so device clock skew never matters; `mtime` is metadata, not an ordering key.

## Versions, trash, and retention

- **Version pruning.** Versions are kept for **at least 100 versions or 90 days**. I read that as a guarantee of both, and prune a version only when it is *both* older than 90 days *and* beyond the newest 100. A file edited 100 times in a day keeps all of them for 90 days; a rarely edited file keeps everything up to 90 days and the newest 100. Rapid autosaves from one device are coalesced into one version within a short window (say 1 minute). A pruned version releases its manifest root; chunks are freed by garbage collection.
- **Trash.** Delete is a metadata transition (`state = TRASHED`, `trashed_at`, and a tombstone in the journal), never an object deletion. Deleting a folder flips **one** row, and children are treated as trashed by their ancestor at read time, so deleting a million-file tree is O(1); restoring it flips the row back. After **30 days** a purge job hard-deletes the rows and releases the manifest references. Legal or admin holds extend it.
- **Chunk garbage collection.** A chunk is deletable when no manifest node references it and it is older than the longest upload session plus a margin (48 h). I use periodic mark-and-sweep over the manifest graph with that grace period, because per-chunk reference counts on every commit would add write amplification on 7.4B chunks and can drift; reference counts, if used, are an optimization verified by the sweep. The grace period is what makes it safe against an in-flight upload whose chunks are not yet referenced.
- **Mass-delete guard.** A device issuing more than N deletes per minute is held for confirmation server-side, because a buggy client or ransomware is the likeliest way to hit the 30-day trash window at scale.

## Sharing and the ACL graph

Sharing is a graph, not a column. Model permissions as **relation tuples** (`folder:F#viewer@user:U`, `folder:F#viewer@group:G#member`, `file:X#parent@folder:F`), with rules such as "a viewer of the parent folder is a viewer of the file", in a dedicated authorization service. This is the model described in Google's Zanzibar paper (USENIX ATC 2019); the summary of its tuples, namespace configuration, zookies, and the Leopard index is in [Google papers](../building_blocks/24_google_papers.md), and open-source systems that implement it are covered under [Security](../building_blocks/14_security.md).

- **Check on every read path, not just at share time.** `GET content` calls `check(user, read, file)`, which walks the parent chain and expands groups. The result decides whether signed chunk URLs are issued at all; the URLs live 5 minutes, so revocation takes effect at the next issuance.
- **Sharing a folder with a group is one tuple**, not a copy of an ACL onto a million descendants. Moving a file between folders changes its `parent` tuple and therefore its inherited permissions.
- **The "new enemy" problem.** Remove someone's access, then add sensitive content to the folder: a stale cached ACL must not let them see the new content. Zanzibar's answer is a consistency token (zookie) recorded with the content change: later checks are evaluated at least as fresh as it. In Drive terms, record a token with the file version and pass it in the `check`.
- **Caching.** ACL decisions are cached briefly (seconds to a minute); the freshness token bypasses the cache when it matters. A shared namespace's journal entries carry the ACL epoch, so members' devices refetch their permissions when it changes.
- **Link sharing** is a tuple whose subject is an unguessable link secret, subject to expiry and revocation like any other.

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Upload interrupted mid-transfer | Resume: re-run `begin upload` (idempotent) and upload only the still-missing chunks; each chunk is its own retry unit, so a lost connection costs at most one chunk, never the file. |
| Client commits a version, but network drops before ack | Commit is idempotent on the client-supplied `commit_token`; retrying the finalize call is safe and returns the same version. |
| Offline device edits a file also edited elsewhere | Detect via the base-version compare-and-set at commit; the late edit is saved as a conflict copy rather than silently overwriting the newer server version. |
| Orphan chunks (uploaded, never committed) | Garbage collection reclaims chunks unreferenced by any manifest after the grace period (48 h). |
| Delete then restore from trash | Delete is a metadata state transition (trash flag + tombstone in the journal), not object deletion; hard-delete only after the 30-day window, and the tombstone propagates through the same change feed so other devices remove their local copies. |
| Shared folder ACL revoked mid-sync | Metadata/ACL check at every content-URL issuance, not only at share time; URLs expire in 5 minutes, so a device with cached state cannot keep pulling after revocation beyond that window. |
| Malicious or oversized upload | Enforce quota and the 5 GiB cap at begin and at commit; run asynchronous antivirus and content scanning from the journal before a file is exposed to other grantees when policy requires it. Scan results are cached by `manifest_hash`, so identical content is scanned once. |
| Corrupt or forged chunk | Storage recomputes hashes on ingest (rejects mismatch) and the client verifies on download; bit rot is repaired from erasure-coded stripes. |
| Metadata shard down | Namespaces on that shard reject writes (their reads may serve from a replica); the other 255/256 are unaffected. Devices retry with backoff and resume from their cursors. |
| Notification tier down | Devices fall back to polling their cursors (tighten the interval to ~30 s during the outage); the sync <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> degrades, correctness does not. |
| Hot shared namespace (thousands of uploaders) | Per-namespace commit rate is bounded by its row lock (~670/s); batch commits into one transaction, cap per-user rates, and if needed split a giant shared drive into sub-namespaces. |
| Region failure | Metadata replicates synchronously across three zones and asynchronously to a second region; chunks are erasure-coded across zones and copied to the second region. On failover the epoch increments; a device whose cursor is ahead of the server's history gets `410 reset` and re-uploads local changes it has not seen acknowledged. Expect seconds of lost commits, never silent divergence. |
| Bad deploy (server or **client**) | Roll out by shard behind <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> guards and a kill switch. A client bug that re-uploads everything or mass-deletes is the most likely cause of a 200k/s spike: per-user rate limits, the mass-delete guard, and dedup (a re-upload of unchanged files is a metadata-only no-op) contain it. |
| Storage abuse (illegal content, quota gaming, using the service as a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>) | Per-account quota on logical bytes, egress limits and per-link download throttles, content scanning, and takedown by `manifest_hash` (which also covers every duplicate). |
| Enumerating hashes to probe the store | Scoped index answers, per-user probe limits, and constant-time responses; see the dedup section. |

## Observability and interview close

Measure **sync propagation latency** (commit time to applied-on-another-device) p50/p99 for small files, notification lag, journal relay lag per shard, commit latency p99, chunk PUT error and hash-mismatch rate, dedup hit rate per scope, orphan-chunk bytes and <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> lag, conflict-copy rate per 1,000 commits, ACL check p99 and denial rate, cursor-reset rate, upload-resume success rate, and bytes stored per logical byte. The one paging alert is **small-file sync propagation p99 above 10 s** (the stated <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> burning); ticket-level signals are journal lag on any shard, <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> falling behind orphan growth, and a spike in ACL denials (a possible authorization bug or scraping).

Interview close: "I split immutable, content-addressed chunks from transactional metadata because content and consistency scale differently. The change cursor and outbox are what let offline devices sync deterministically and what let me turn a metadata write into fan-out to search and antivirus without doing it inline. Conflicting offline edits become a new version plus a conflict copy, never a silent overwrite, because losing a user's edit is worse than asking them to merge."

Trade-off to state: "I chunk with content-defined boundaries and deduplicate per scope on the client-visible path and globally underneath, so edits and copies cost little and there is no has-chunk oracle, at the cost of client <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>, a stateful chunk index, and re-sent bytes for cross-tenant duplicates; the cost is acceptable because the index is 0.32 TB and the leak would be an incident."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Each namespace has a home region that owns its writes; the journal and metadata replicate asynchronously, and chunks are erasure-coded within a region and copied to a second. Cross-region users read from a nearby replica (read your writes via the cursor token) and commit to the home region, paying one RTT. A region failure promotes the replica and bumps the epoch (see failure table). Dedup indexes stay per region, with a background pass that unifies physical duplicates.
2. **"What changes at 10× and 100× scale?"** At 10×, the object store and index grow linearly (the index is 3.2 TB, still sharded by hash prefix), and metadata needs more shards (2,560 namespaces-per-shard groups). Notification gateways scale by connection count (3.75k). At 100×, split into independent cells by user cohort, move to a two-level chunk index (a hot in-memory filter plus the store), and accept that the corpus tier becomes a cold-storage economics problem: measure the access distribution and push 95%+ to a colder class.
3. **"What if I need stronger consistency, such as immediate read-your-writes for everything?"** Pin a user's requests to their namespace's home shard and read the journal from the primary; the cost is lost read replicas and lower availability during failover. I would keep eventual consistency between devices (seconds) and give strong read-your-writes only for the device that wrote, using the returned `seq`.
4. **"What dominates cost?"** Storage: 7.4 PB unique, ~11 PB raw with erasure coding. Each 1% of extra dedup is ~74 TB, about 110 TB raw. Then egress. The levers are chunk size and CDC quality, tiering the cold 90%, erasure-coding parameters, and pruning versions, in that order. Metadata is ~6 TB and a rounding error.
5. **"How do you defend against abuse?"** Per-account quota on logical bytes, rate limits on begin/commit per user, ingest backpressure, mass-delete guard, content scanning and takedown by content hash, per-link egress limits, and the scoped, rate-limited chunk-existence check.
6. **"What if I want end-to-end encryption?"** Then the server cannot dedup (ciphertext differs), scan, index, preview, or merge. Convergent encryption (the key derived from the content) preserves dedup but reintroduces the confirmation-of-a-file leak. State the trade-off: offering E2EE as a tier that gives up server-side features and cross-user dedup is the honest answer.
7. **"Why not just use object versioning on whole files and skip chunking?"** It works for small files and is the right first version. It fails the stated numbers: every edit of a 100 MB file re-uploads 100 MB (versus ~1–2 MB), a 5 GB upload cannot resume, version storage is O(versions × size), and duplicates are stored repeatedly. I would ship whole-file first and add chunking behind a client flag; see the migration bullet below.
8. **"What if the interviewer says global client-visible dedup is table stakes?"** Show the oracle attack and the poisoning risk, then offer the compromise already in the design: global dedup at the storage layer, scoped answers on the wire, plus proof of ownership if the interviewer needs a cross-scope shortcut for very large files. I would concede that within one enterprise tenant, dedup can be fully visible.

## Common mistakes

1. **Not sanity-checking the constraints.** 200k uploads/s × 4 MB is 6.4 Tbps and refills the corpus in 2.8 hours. State what the number must mean and design for it explicitly, rather than sizing infrastructure from an impossible figure or silently substituting another.
2. **Fixed-size blocks for editable files.** An insertion shifts every later boundary, so every later block is re-sent. Use content-defined chunking where edits are common.
3. **Trusting the client's chunk hash.** A malicious upload under a popular hash poisons every future dedup hit. Recompute on ingest.
4. **Global, client-visible dedup.** The "already exists" answer is a has-file oracle across all users. Scope the answer, and dedup physically underneath.
5. **Last-write-wins for offline edits.** A stale device overwrites a newer version and the user loses work. Compare-and-set on the base version, and keep the loser as a conflict copy.
6. **Allocating the change sequence outside the commit transaction.** A later commit can become visible with a lower sequence than one a device already read past, so the device misses it. Allocate the `seq` under the namespace lock in the same transaction.
7. **Rewriting paths or ACLs on rename and share.** Folder rename by updating every descendant's path, or sharing by copying an ACL onto every child, is O(n). Use parent pointers and inherited relation tuples.
8. **Treating the push notification as the source of truth.** A lost poke then loses a change. The journal is truth; push is a hint; poll and reconnect always pull.

## Going from L5 to L6

- **Migration path.** Ship whole-file versions and the change journal first (correct and simple), then add chunked uploads behind a client capability flag: new versions are chunked, old files are chunked lazily when touched or in a background pass, and the chunk index is built from what is stored. Keep both readers until the old path is idle. Every step is reversible because chunks and manifests are additive.
- **Cost model.** Storage is the bill: express the design as levers (average chunk size, dedup scope, erasure coding, cold-tier fraction, version retention) and price each in petabytes and in dollars per year. A 1% dedup gain is ~74 TB; a 10-point cold-tier shift moves ~0.7 PB from the fast tier.
- **Ownership and blast radius.** Split the system into metadata service (namespace shards), block service (chunk store and index), sync and notification service, authorization service (Zanzibar-style), and a scanning pipeline, each with its own on-call and quotas. A namespace shard failure affects 1/256 of users; a chunk-store failure is absorbed by erasure coding; authorization must fail closed with a cache-served degraded mode.
- **The client is half the system.** The chunker, cache, and sync engine ship to millions of devices you do not control. A protocol version, staged client rollouts, and a server-side kill switch and rate limits are part of the design, because a client bug is your largest possible traffic spike.
- **Build versus buy.** Buy the object store to start; at large scale, building your own block store can pay for itself (Dropbox has described moving off a public cloud store onto its own Magic Pocket system, 2016). The authorization graph is a place to adopt an open-source Zanzibar-style system (SpiceDB, OpenFGA) rather than build one. The metadata service, the commit protocol, and the client sync engine are where the correctness lives, so build those.
- **What to measure first.** The real file-size distribution (median versus mean), how much of each edit is new (which decides chunker choice and the real "r" behind the 200k/s), dedup ratio at each scope, the share of bytes in already-compressed formats, offline duration, and the actual meaning and duration of the peak.

## Build exercise

Implement versioned metadata (current pointer + immutable version chain) over a small in-memory store, plus a per-namespace change cursor; simulate two "devices" editing the same file offline from the same base version and assert the sync step produces a conflict copy instead of data loss. Then add a content-defined chunker and a content-addressed chunk store with a hash-tree manifest. Named assertions:

- `test_offline_conflict_makes_copy_not_overwrite`: two devices edit from base v1; assert one becomes v2, the other a conflict copy, and both contents are retrievable.
- `test_cdc_insert_reuploads_few_chunks`: insert 10 KB at the start of a 50 MB file; assert CDC re-sends at most 2 chunks while fixed 4 MiB blocks re-send every block.
- `test_dedup_second_upload_sends_zero_bytes`: upload the same file twice; assert the second `begin upload` reports no missing chunks and the commit writes one metadata row.
- `test_chunk_hash_is_verified_on_ingest`: upload bytes under a wrong hash; assert `HASH_MISMATCH` and that the index never records the hash.
- `test_no_cross_scope_oracle`: user A uploads a chunk; assert user B's `begin upload` reports it missing (and B's upload succeeds without storing a second physical copy).
- `test_commit_retry_is_idempotent`: replay a commit with the same token 5 times; assert one version and one journal entry.
- `test_sequence_order_is_commit_order`: run 100 concurrent commits to one namespace while a reader polls; assert the reader never observes a `seq` gap it later fills.
- `test_folder_delete_and_restore_is_constant_rows`: trash a folder with 10,000 files; assert one row changed and restore brings all files back.
- `test_version_prune_keeps_100_or_90_days`: create 150 versions over 10 days and 20 versions over 200 days; assert the first keeps all 150 and the second keeps 100 within the union rule.
- `test_revoked_share_stops_new_urls`: revoke access, then request content; assert no signed URL is issued, and that URLs issued before revocation expire within the TTL.
- `test_stale_cursor_forces_reset`: present a cursor from an old epoch; assert `410 reset` and that a snapshot resync converges to the server state.
