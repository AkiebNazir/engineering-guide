# <abbr title="Application Programming Interface">API</abbr> Design — High Level

The <abbr title="Application Programming Interface">API</abbr> is the contract your service makes with every caller — browser, mobile app, another team's service, or a third party. Get the contract wrong and you can't fix it without breaking someone; this file is about the contract itself. Wire-level mechanics (status codes, headers, serialization formats, auth tokens) live in `04_api_design_low_level.md`.

## The client is not trusted

The client handles presentation, UX-level input validation, local caching, and retry behavior. It is not a trusted authority for permissions, prices, quantities, or any invariant — a user can modify requests, replay them, or write a custom client that skips your UI entirely. Every rule enforced client-side must also be enforced server-side, or it isn't actually enforced.

## Choosing an <abbr title="Application Programming Interface">API</abbr> style

| Style | Choose it when | Strength | Caution |
|---|---|---|---|
| <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>-like | Public/browser integrations, resource-shaped domain, broad client compatibility | Ubiquitous tooling, cacheable, human-debuggable | Forcing every action into <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> produces awkward endpoints (`POST /orders/{id}/cancel` vs a fake `PATCH` that means five different things) |
| <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>/<abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> | Internal service-to-service calls, need typed contracts/codegen, streaming | Efficient binary schema, generated clients, native streaming | Browser support needs a proxy (<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>-Web); harder to debug ad hoc; deadlines still mandatory, not automatic |
| GraphQL | Many heterogeneous clients need different shapes of the same underlying graph (e.g. mobile wants a thin payload, web wants nested detail) | One endpoint, client-specified shape, avoids over/under-fetching | N+1 query risk if resolvers naively fetch per field; complicates <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> caching (single endpoint, POST-shaped queries) and per-field rate limiting; query cost must be bounded server-side or a client can request an arbitrarily expensive graph traversal |
| WebSocket | Bidirectional, low-latency, server-initiated pushes | Chat, collaboration, live updates | Connection ownership/reconnection/backpressure/offline sync all become your problem |
| Webhook | Notify another system asynchronously, caller doesn't poll | Loose coupling between systems | Must verify signatures, handle retries/duplicates, and the receiver may be down — needs its own retry/DLQ story |
| Queue/event | Caller doesn't need the result synchronously | Buffering, retry, fan-out | Eventual consistency; caller needs a way to check status later |

**GraphQL specifically**: it earns its place when you have multiple client shapes pulling from the same underlying data graph and <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> would otherwise force either chatty multi-endpoint calls or bespoke per-client endpoints. It does *not* earn its place for a single client type or a simple resource <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> <abbr title="Application Programming Interface">API</abbr> — you inherit resolver N+1 risk (a naive resolver for `author` on each of 50 posts issues 50 queries unless batched via a dataloader pattern) and lose the free <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>-level caching and per-route rate limiting that <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> gets from distinct URLs and GET semantics.

## Resource modeling (<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>-ish)

Model nouns, not verbs: `/orders`, `/orders/{id}`, `/orders/{id}/items`. Actions that don't fit <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> get an explicit sub-resource or action endpoint rather than overloading a generic `PATCH`: `POST /orders/{id}/cancel`, not `PATCH /orders/{id} {"status":"cancelled"}` pretending to be a generic update when it's actually a specific state-transition business rule with its own validation.

```text
GET    /orders            list (paginated, filterable)
POST   /orders            create
GET    /orders/{id}       read one
PATCH  /orders/{id}       partial update of genuinely mutable fields
POST   /orders/{id}/cancel   explicit business action, not a fake PATCH
```

## Pagination

Offset/limit pagination (`?offset=200&limit=50`) breaks under concurrent writes: an insert before offset 200 shifts every subsequent page by one, causing skipped or duplicated rows. Use a **stable cursor** instead — an opaque token encoding the last-seen sort key (often `(sort_value, id)` for a tiebreak on ties):

```http
GET /orders?limit=50&cursor=eyJpZCI6MTIzNDUsInRzIjoxNzI2fQ==
```

```json
{ "items": [...], "next_cursor": "eyJpZCI6MTIzOTUsInRzIjoxNzMwfQ==" }
```

The cursor is opaque to the client — you can change its internal encoding without breaking callers, as long as they keep passing back what you gave them.

## Versioning without breaking clients

- Add optional fields; never repurpose an existing field's meaning (a field named `total` that changes from "pre-tax" to "post-tax" silently is a production incident for every consumer, even though the schema "didn't change").
- Additive changes (new optional field, new endpoint, new enum value a client should ignore if unrecognized) don't need a version bump.
- Breaking changes (removing/renaming a field, changing a type, changing required-ness) need a new version (`/v2/orders`) or a deprecation window with both versions live, sunset communicated and enforced by date, not indefinitely.
- Enums are a common trap: adding a new enum value is "additive" to you but breaking to a client with an exhaustive `switch` and no default case — document that enums may grow and clients must handle unknown values gracefully.

## Error contract

Every error response should give a caller enough to act on programmatically, not just a message for a human:

```json
{
  "error": {
    "code": "INSUFFICIENT_INVENTORY",
    "message": "Item book-1 is out of stock.",
    "correlation_id": "8f3e1c2a-...",
    "retryable": false
  }
}
```

- **Code**: stable, machine-matchable string — not the <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> status alone (a 400 could mean a dozen different things; the client needs to distinguish them).
- **Message**: safe to show/log, never a stack trace or internal detail.
- **Correlation ID**: ties the error back to server-side logs/traces for support/debugging (see `15_observability_and_reliability.md`).
- **Retry guidance**: is this transient (retry with backoff) or a permanent rejection (don't retry, fix the request)? Conflating the two causes retry storms against permanently-failing requests.

## Idempotency key pattern

Give every unsafe mutation (anything that isn't naturally idempotent, like `POST /orders`) a client-supplied idempotency key, because a network failure between response and client leaves the client unable to tell whether the mutation actually happened (see `02_networking.md` on <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection breakage after server-side completion — this is the <abbr title="Application Programming Interface">API</abbr>-level answer to that transport-level fact).

```http
POST /v1/orders
Idempotency-Key: 8db8c2f1-4a3e-4b1c-9f2a-...

{ "items": [{"sku":"book-1","quantity":1}] }
```

The server stores the logical outcome keyed by that idempotency key (commonly in the same transaction as the business write, or via an outbox — see `09_messaging_and_streaming.md`). If the client doesn't get a response, it retries with the **same key**: the server recognizes the key, returns the original stored outcome, and does not create a second order. A new key means a genuinely new intended order — the key represents *intent*, not the request body alone (so it should be scoped/expired sensibly; an indefinitely-retained key store grows forever).

## Synchronous vs asynchronous contracts

A synchronous contract (`POST /orders` returns the created order in the response) is simpler for the caller but couples the caller's request lifetime to your full processing time — including anything slow downstream. An asynchronous contract (`POST /orders` returns `202 Accepted` + a status URL, or the caller subscribes to a webhook/event) decouples that, at the cost of the caller needing a polling or callback mechanism and your <abbr title="Application Programming Interface">API</abbr> surface needing a status/result resource. Choose based on whether the *caller* can usefully wait — a checkout confirmation UI usually needs synchronous-feeling UX even if the backend defers work internally (accept fast, confirm fast, finish the slow parts async and notify).

## <abbr title="Application Programming Interface">API</abbr> gateway's role

An <abbr title="Application Programming Interface">API</abbr> gateway centralizes coarse authentication, request routing, quota/rate-limit enforcement, and a consistent edge contract across multiple backend APIs — it is not where business logic lives. See `16_platform_and_infra.md` for gateway/ingress placement in the platform stack and `02_networking.md` for where it sits in the request path relative to the load balancer and <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> termination.

## Related building blocks

- [00_overview.md](00_overview.md)
- [02_networking.md](02_networking.md)
- [04_api_design_low_level.md](04_api_design_low_level.md)
- [09_messaging_and_streaming.md](09_messaging_and_streaming.md)
- [12_application_resilience_patterns.md](12_application_resilience_patterns.md)
- [16_platform_and_infra.md](16_platform_and_infra.md)
