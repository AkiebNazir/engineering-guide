# 035 — Design a Distributed Object Store

Design the storage service itself, in the style of Amazon S3, Google Cloud Storage or Azure Blob Storage: a regional service that stores immutable blobs of any size under a bucket and key, keeps them for years without losing any, and lists them back by prefix.

## Functional requirements

- `PUT`, `GET` (including byte ranges), `HEAD` and `DELETE` of objects addressed by bucket and key, with overwrite of an existing key.
- Multipart upload for large objects: upload parts in parallel and in any order, then complete or abort.
- `LIST` a bucket by prefix, with an optional delimiter (folder-style listing) and pagination, in key order.
- Optional per-bucket versioning, conditional writes (create only if absent, replace only if unchanged), and lifecycle rules that expire objects or old versions after N days.
- Strong read-after-write consistency: after a successful `PUT` or `DELETE`, every later `GET`, `HEAD` and `LIST` sees it.
- Integrity: a client can supply a checksum on upload and always gets back exactly the bytes it wrote.

## Constraints to assume

- 200 billion objects and 100 PB of logical data in one region today, growing by about 3 PB a month net of deletes. Objects range from 0 bytes to 5 TB; median about 30 KB, mean 500 KB.
- Peak 1,000,000 `GET`/s (mean 250 KB returned), 100,000 `PUT`/s (mean 100 KB), 20,000 `LIST`/s and 20,000 `DELETE`/s. The daily average is about half of peak.
- Designed durability of 99.999999999% (11 nines) per object per year. The region has 3 zones: an object must survive the loss of a whole zone, and reads and writes must stay available through it. 99.99% monthly availability.
- p99 time to first byte under 100 ms for a `GET` of an object under 1 MB; p99 under 200 ms for a 1 MB `PUT`; p99 under 200 ms for a 1,000-key `LIST` page.
- Storage server for sizing: 24 × 20 TB HDDs (about 120 random reads/s and 200 MB/s sequential each), NVMe for journals and indexes, 2 × 25 GbE.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates, including the disk and server count and whether capacity or IOPS binds.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Erasure coding versus replication with the durability arithmetic, the metadata index kept separate from data placement, small-object packing, repair and its bandwidth, garbage collection after deletes and overwrites, and `LIST` at scale with strong consistency.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
