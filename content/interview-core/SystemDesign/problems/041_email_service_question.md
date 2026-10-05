# 041 — Design an Email Service

Design a Gmail- or Outlook.com-style email service. It receives mail from the whole internet over SMTP, keeps spam and malware out of the inbox, stores every user's mailbox for years, lets each user search their own mail, keeps web, mobile and IMAP clients in sync, and sends users' outgoing mail so that it actually lands in other providers' inboxes.

## Functional requirements

- Receive inbound mail over SMTP for the service's domains, and for custom domains of business customers.
- Classify every message: inbox, spam folder, or rejected (malware, policy). Users can report spam and "not spam".
- Store mailboxes: messages with attachments, threads (conversations), labels or folders, read and starred flags, drafts, trash, archive.
- Full-text search over a user's own mail (sender, subject, body, attachment names, date and label filters).
- Incremental sync for web, mobile and IMAP clients across several devices, with new-mail push notifications.
- Send mail on behalf of users (compose, reply, forward), with retries to slow or unavailable remote servers and bounce reports to the sender.

## Constraints to assume

- 500M mailboxes, 200M daily active users, each on 2 to 3 devices.
- About 10 billion inbound messages a day are offered to the service's MX servers, more than half of them spam; peak is 3× the average. Mean accepted message size is 75 KB including attachments, with a 25 MB attachment limit.
- Users send about 400M messages a day to other providers.
- An accepted message must never be lost. New mail appears in the recipient's inbox within 10 seconds at p95 and 60 seconds at p99.
- Search returns in under 500 ms at p99. A flag or label change on one device appears on the user's other devices within 5 seconds.
- Reading and writing mail is available 99.9% of the time; receiving mail from the internet must never fail permanently because of an internal outage.
- Spam must not reach the inbox, but losing a real message into the spam folder (a false positive) is worse than letting some spam through.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and the inbound, read and send flows.
5. When the service may reply `250 OK` to a sending server, the spam pipeline, mailbox storage and threading, sync cursors, per-user search, and outbound deliverability.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
