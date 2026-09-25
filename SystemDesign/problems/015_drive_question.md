# 015 — Design a Cloud Drive

Design a file storage service like Drive/Dropbox that supports uploads, folders, sharing, versioning, and multi-device sync.

## Functional requirements

- A user uploads files into a folder hierarchy and can share a file or folder with other users at a given permission level.
- Every edit creates a retrievable version; a user can restore a previous version.
- A deleted file or folder is recoverable for a grace period before permanent removal.
- Files sync automatically across a user's devices, including large files via resumable/chunked upload.
- Two devices editing the same file offline must reach a defined, predictable conflict resolution when reconnected.

## Constraints to assume

- 50 million active users, 2 billion files, average file 4 MB.
- 200,000 uploads/second at peak, files up to 5 GB.
- Sync propagation to other devices p99 under 10 seconds for small files.
- Deleted items recoverable for 30 days.
- Version history retained for at least 100 versions or 90 days per file.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Chunking/versioning strategy and conflict-resolution policy for offline concurrent edits.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
