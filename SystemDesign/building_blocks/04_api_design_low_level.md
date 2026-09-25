# <abbr title="Application Programming Interface">API</abbr> Design — Low Level

This is the wire-protocol companion to `03_api_design_high_level.md`: once you've chosen a style and modeled the contract, these are the mechanics that make it correct — semantics, caching, connection behavior, serialization, auth, and rate limiting at the protocol level.

## <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> method semantics

| Method | Safe (no side effect) | Idempotent (same effect if repeated) | Typical use |
|---|---|---|---|
| GET | Yes | Yes | Read a resource |
| HEAD | Yes | Yes | Read headers only, no body |
| OPTIONS | Yes | Yes | Discover allowed methods/CORS preflight |
| PUT | No | Yes | Full replace of a resource at a known URL |
| DELETE | No | Yes | Remove a resource (repeating a delete of an already-deleted resource is still "deleted") |
| PATCH | No | Not guaranteed | Partial update — idempotent only if you design it that way (e.g. "set status to X", not "increment counter by 1") |
| POST | No | No (by default) | Create / non-idempotent action — needs an idempotency key to be made safe to retry |

"Idempotent" means *repeating the same request produces the same end state*, not that it's side-effect-free and not that the response bodies are identical. A `DELETE` returning `404` the second time is still idempotent in effect even though the response differs — the resource is gone either way.

## Status codes — when to use which

| Range | Meaning | Notable codes |
|---|---|---|
| 2xx | Success | `200` OK, `201` Created (+`Location` header), `202` Accepted (async work queued), `204` No Content (success, empty body) |
| 3xx | Redirection | `301` moved permanently (cacheable), `304` Not Modified (conditional GET hit) |
| 4xx | Client error — fix the request | `400` malformed, `401` unauthenticated, `403` authenticated but not authorized, `404` not found, `409` conflict (version mismatch/duplicate), `422` semantically invalid, `429` rate limited |
| 5xx | Server error — not the client's fault | `500` unhandled, `502` bad gateway (upstream returned garbage), `503` unavailable (overloaded/draining — often paired with `Retry-After`), `504` gateway timeout |

`401` vs `403` is a common interview trip-up: `401` means "I don't know who you are" (missing/invalid credentials), `403` means "I know who you are and you're not allowed" — don't collapse them, since clients behave differently (re-auth vs. stop retrying).

## Caching headers

```http
GET /catalog/item/42
```

```http
200 OK
Cache-Control: max-age=300, must-revalidate
ETag: "a1b2c3"
```

Subsequent request:

```http
GET /catalog/item/42
If-None-Match: "a1b2c3"
```

```http
304 Not Modified
```

- `Cache-Control: max-age=N` — cacheable for N seconds without revalidation.
- `Cache-Control: no-store` — never cache (sensitive data).
- `ETag` — an opaque fingerprint of the resource; a conditional request (`If-None-Match`) lets the server confirm "still the same" with a cheap `304` instead of re-sending the full body.
- `Retry-After` — on `429`/`503`, tells the caller how long to wait before retrying (seconds or an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> date) — a well-behaved client backs off to at least this, not less.

## Content negotiation

`Accept: application/json` (what the client wants back) and `Content-Type: application/json` (what the client is sending) let one endpoint serve multiple representations. `Accept-Language`, `Accept-Encoding` (gzip/br compression) work the same way. A server that ignores `Accept` and always returns one format is fine for an internal <abbr title="Application Programming Interface">API</abbr>; a public <abbr title="Application Programming Interface">API</abbr> serving multiple client generations often needs this to evolve formats without a version bump.

## Serialization formats compared

| Format | Schema | Size | Speed | Human-readable | Evolution |
|---|---|---|---|---|---|
| <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> | Schema-on-read (none enforced at write) | Larger (text, field names repeated) | Slower to parse | Yes | Very forgiving — extra/missing fields don't break parsing, but nothing enforces the contract |
| Protocol Buffers | Schema-on-write (`.proto` compiled) | Compact (binary, field numbers not names) | Fast | No | Strong, deliberate rules: field numbers are permanent, new fields must be optional, never reuse a retired field number |
| Avro | Schema-on-write, schema travels with data (or via registry) | Compact | Fast | No | Schema evolution rules enforced by a schema registry at write/read time — common in streaming pipelines (see `09_messaging_and_streaming.md`) |
| MessagePack | Schema-on-read, like binary <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> | Compact | Fast | No | Same looseness as <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, just smaller/faster on the wire |

Use <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> for public/browser-facing APIs (universal tooling, debuggable). Use Protobuf/<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> for internal service-to-service calls where you control both ends and want compile-time contract enforcement plus smaller/faster payloads. Use Avro where the schema needs to travel with high-volume streamed data and evolve under registry-enforced compatibility rules. Schema-on-write formats catch a broken contract at serialize time; schema-on-read formats catch it at the consumer, often in production.

## Connection mechanics

- **Keep-alive** (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/1.1): reuse a <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection across multiple requests instead of paying handshake+<abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> cost per request.
- **<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/2 multiplexing**: many logical request/response streams share one <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection — see `02_networking.md` for the head-of-line-blocking trade-off this introduces at the <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> layer.
- **<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> streaming modes**:

```text
unary            client ──1 req──▶ server ──1 resp──▶ client
server-streaming client ──1 req──▶ server ──N resp──▶ client   (e.g. subscribe to updates)
client-streaming client ──N req──▶ server ──1 resp──▶ client   (e.g. upload chunks, then ack)
bidi-streaming   client ──N req──▶ server ──N resp──▶ client   (e.g. live chat, both sides push)
```

Streaming modes matter for <abbr title="Application Programming Interface">API</abbr> design because they change the failure model: a unary call is one deadline, one retry decision; a long-lived bidi stream needs its own heartbeat/reconnect/backpressure story, closer to the WebSocket concerns in `03_api_design_high_level.md`.

## Authentication and authorization at the wire level

| Mechanism | How it works | Good for | Watch out for |
|---|---|---|---|
| <abbr title="Application Programming Interface">API</abbr> key | Static secret sent as header/query param | Server-to-server, simple integrations | No expiry by default, easy to leak in logs/URLs, coarse-grained |
| OAuth2 (authorization code flow) | User authorizes a client app; app exchanges a code for an access token (+ refresh token) via the auth server | Third-party apps acting on a user's behalf | Multiple round trips; token storage/refresh logic is easy to get wrong client-side |
| OAuth2 (client credentials flow) | Service authenticates directly with client ID/secret, no user involved | Service-to-service | Same secret-management concerns as <abbr title="Application Programming Interface">API</abbr> keys |
| <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> (<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Web Token) | Self-contained signed token: header.payload.signature, base64url-encoded | Stateless auth — server verifies signature, no DB lookup needed per request | See pitfalls below |
| mTLS | Both client and server present certificates during <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> handshake | Service-to-service inside a trusted network/mesh | Certificate rotation/distribution is operational overhead |

**<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> structure**: `header.payload.signature`. The payload is **not encrypted**, only signed — never put secrets in it, only claims (subject, expiry, scopes).

```json
// payload (base64url-decoded, not encrypted)
{ "sub": "user_123", "exp": 1735689600, "scope": "orders:read orders:write" }
```

<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> pitfalls that come up repeatedly:

1. **Expiry (`exp`) not checked**, or checked against client time instead of server time.
2. **Algorithm confusion**: a server configured to accept `alg: none` or to verify an `RS256`-signed token using the public key as if it were an `HS256` shared secret — a known real-world exploit class. Pin the expected algorithm server-side; don't trust the `alg` field in the token itself.
3. **Revocation is hard**: a <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> is self-contained and stateless by design, which means there's no cheap way to invalidate one before its `exp` — mitigations are short expiry + refresh tokens, or a server-side denylist (which reintroduces the per-request state lookup you were trying to avoid).

## Rate limiting mechanics — token bucket worked example


```arch
%% caption: Token bucket enforces an average rate limit (refill rate) while allowing short bursts (bucket capacity).
node client "Client" at 0,1 icon=client color=blue
node bucket "Token Bucket\n(Capacity: B)" at 2,1 icon=db color=amber
node refill "Refill Process\n(Rate: r/sec)" at 2,0 icon=timer color=slate
node api "API / Backend" at 4,1 icon=server color=green

refill -> bucket : "adds tokens"
client -> bucket : "request\n(costs 1 token)"
bucket -> api : "token available\n(allow)"
bucket ..> client : "no tokens\n(HTTP 429)"
```
(Adapted from the token-bucket model in the original building-blocks file and the rate-limiter solution — see `solutions/002_rate_limiter_solution.md` for the full system design.)

A bucket holds up to `B` tokens, refills at rate `r` tokens/second, and each request spends 1+ tokens (a cheap read might cost 1, an expensive export might cost 10). This allows a burst up to `B` while enforcing an average rate of `r`.

```text
state per key: (tokens, last_refill_timestamp)

on request:
  elapsed = now - last_refill_timestamp
  tokens = min(B, tokens + elapsed * r)
  if tokens >= cost:
      tokens -= cost
      last_refill_timestamp = now
      allow
  else:
      deny, Retry-After = (cost - tokens) / r
```

This must run as **one atomic operation** (a Lua script in Redis, or a compare-and-swap loop) — reading tokens, computing, then writing back as separate steps lets concurrent requests both read the same stale count and both get admitted, overshooting the limit.

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 12
X-RateLimit-Remaining: 0
```

## Deadlines, timeouts, and cancellation propagation

Every outbound call needs an explicit deadline smaller than the caller's own remaining budget (see the latency-budget example in `02_networking.md`). A **client-side timeout is not server-side cancellation** — if the client gives up waiting, the server may still be doing the work unless it's explicitly told to stop:

- <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> propagates a deadline as part of the call metadata; a well-behaved server checks the context and aborts work if the deadline has passed, and the deadline can be forwarded to the *next* downstream call automatically.
- Plain <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> has no built-in cancellation signal to the server beyond the connection closing (which the server may or may not check for).

Without explicit deadline propagation, a client giving up doesn't stop the server from finishing (and possibly retrying) wasted work — this is why "the client already timed out" and "the request is now safe to ignore" are not the same fact, and why idempotency (see `03_api_design_high_level.md`) is the real safety net, not cancellation.

## Related building blocks

- [00_overview.md](00_overview.md)
- [02_networking.md](02_networking.md)
- [03_api_design_high_level.md](03_api_design_high_level.md)
- [09_messaging_and_streaming.md](09_messaging_and_streaming.md)
- [12_application_resilience_patterns.md](12_application_resilience_patterns.md)
- [14_security.md](14_security.md)
