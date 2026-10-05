# 024 — Design a Collaborative Document Editor (Google Docs)

Design a web-based document editor where several people can edit the same document at the same time and see each other's changes and cursors in real time.

## Functional requirements

- Create, open, and edit rich-text documents in the browser.
- Multiple users edit concurrently; every user converges to the same document content.
- Collaborators see each other's cursors, selections, and presence within about a second.
- Full revision history; restore any earlier version.
- Share documents with view, comment, or edit permissions; revoking access takes effect immediately.
- Users can keep editing briefly while offline; changes sync when they reconnect.

## Constraints to assume

- 100 million documents created per year; 10 million daily active editors.
- Typical document: 50 KB of content; up to 100 simultaneous editors on a popular document, rarely more.
- Keystroke-to-remote-display latency under 200 ms at p95 within a region.
- No acknowledged edit may be lost.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: concurrent connections, operation rate, and storage for content and history.
3. API and wire protocol between client and server.
4. Baseline architecture: connection handling, document sessions, storage.
5. Concurrency control: operational transformation vs CRDTs, and your choice.
6. Revision history, snapshots, offline editing, permissions, and failure handling.
7. One explicit trade-off you would revisit for a document with thousands of simultaneous editors.

Do not open the solution until you have made and explained your own design.
