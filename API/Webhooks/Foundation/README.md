# Webhooks Foundation - ground zero to a complete, secured receiver

This is the on-ramp *before* `../Theory.md` and `../labs/`. Each level is a
tiny, self-contained, runnable file in **both** `python/` and `golang/` -
same lesson, same demo shape, two languages side by side. Every file prints
`OK` when it passes its own built-in checks. Standard library only, in both
languages: `http.server` / `hmac` / `hashlib` in Python, `net/http` /
`crypto/hmac` / `crypto/sha256` in Go - no dependencies to install.

Start at level 00 with one idea: **a webhook is just you running a small <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>
server that someone else's system calls into, unprompted.** You never initiate
the connection - you only have to be ready when it arrives. Everything after
that is a consequence of that one flip.

Run any Python level:  `python Webhooks/Foundation/python/00_single_receiver_endpoint_and_how_it_works.py`
Run any Go level:      `go run ./Webhooks/Foundation/golang/00_single_receiver_endpoint_and_how_it_works`

| # | Level | The one new idea |
|---|---|---|
| 00 | Single receiver endpoint, explained end to end | What "a basic webhook receiver" actually is: one `POST /webhook`, a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> body in, an immediate 200 out |
| 01 | Event envelope + routing by type | `{"type", "id", "data"}`, and dispatching on the `type` FIELD instead of the URL path |
| 02 | Payload validation + response codes | A public URL gets garbage: 400/413 for permanently bad, 500 for temporarily mine, never a hang |
| 03 | Idempotency | At-least-once delivery is a promise, not a bug: dedupe by event id so a redelivery is harmless |
| 04 | Signature verification | HMAC-SHA256 over the RAW body, compared constant-time, before any handler logic runs -> 401 |
| 05 | Fast ACK + timeouts | ACK in milliseconds and defer the slow work, or the sender times out and retries you into duplicates |
| 06 | Retry-aware responses | The same status codes read from the SENDER's chair: 2xx done, 5xx retry me, 4xx never retry |
| 07 | Delivery metadata headers | Delivery id vs event id, and signing `<timestamp>.<body>` to close the replay window |
| 08 | Middleware | Wrapping the receiver instead of editing it: a designed log line + panic recovery -> a deliberate 500 |
| 09 | Authentication | Level 04's signature check, now layered as middleware: one door, short-circuits before dispatch, 401 |
| 10 | Authorization | Many sources, each with its OWN secret and its OWN allowed event types -> 403 for out-of-scope |
| 11 | Complete receiver | Everything above in one file: authenticate -> validate -> authorize -> dedupe -> enqueue -> 202 |
| 12 | Being a sender | The other chair: sign, POST unprompted, retry with exponential backoff, dead-letter the hopeless |
| 13 | Bonus: HMAC by hand | Optional deep dive - a signature is just a keyed hash, built from sha256 alone (read any time after 04) |

**Where to go next:** level 11 is the same shape as
`../labs/python/04_idempotent_async_receiver.py` and
`../labs/golang/01_receiver_net_http` - once level 11 feels easy, `../labs/`
(a SQLite inbox with a UNIQUE constraint, bounded worker pools and
back-pressure, provider signature schemes, secret rotation, dead-letter
queues, SSRF-safe senders, circuit breakers and replay) is the very next step,
not a jump. `../Theory.md` covers the *why* (polling vs webhooks, event
design, delivery guarantees, operating a webhook platform) behind everything
these files do in code.
