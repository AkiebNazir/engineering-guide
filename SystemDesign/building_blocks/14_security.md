# Security

Security is not a module you add at the end. It is a property every boundary either has or does not: authentication, authorization, input validation, encryption, and auditability at each hop where trust changes. A design that gets availability and consistency right but treats security as a checkbox has not actually answered the prompt.

## Authentication vs authorization — two different questions

| Question | Answer type | Failure if skipped |
|---|---|---|
| Authentication (AuthN): who is making this call? | A verified identity — user, service, workload. | Anyone can claim to be anyone. |
| Authorization (AuthZ): is this identity allowed to do this action on this resource? | Allow/deny against a policy tied to a specific resource. | Any authenticated caller can act on any object. |

These are separate checks, and both must run on every request that crosses a trust boundary — not just at login and not just at the edge. A gateway that authenticates a <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> and forwards the request is not authorizing anything; each downstream service still owns "can this identity touch this resource."

## Re-check at every service boundary

```arch
%% caption: Each hop re-authorizes independently — a verified claim propagates downstream, never a plain header a compromised upstream could tamper with.
node c "Client" at 0,0 icon=user
node gw "Gateway" at 1,0 icon=gateway color=slate
node a "Service A" at 2,0 icon=server color=blue
node b "Service B" at 3,0 icon=server color=teal

c -> gw : "request + token"
node step1 "Authenticate" at 1,1 shape=card sub="authenticate token, coarse rate limit"
gw -> step1 -> a : "forward verified identity claims"

node step2 "Authorize" at 2,1 shape=card sub="does this user own order_id?"
a -> step2 -> b : "call with own identity + propagated context"

node step3 "Authorize AGAIN" at 3,1 shape=card sub="does this user/service have this scope?"
b -> step3 -> b
b -> a : "response"
a -> c : "response"
```

Never trust a caller-supplied `tenant_id`, `user_id`, or role header as authorization input. If the client can set it, the client can forge it. Derive identity from a verified token/session at the boundary that terminates it, and propagate it downstream as a signed or otherwise trusted claim (e.g., a service-to-service <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr>, mTLS identity) — not as a plain header a compromised upstream could tamper with. This is the direct mechanism behind IDOR (insecure direct object reference): `GET /orders/12345` returning order 12345 because the ID was well-formed, without checking that the caller's identity owns it.

## Least privilege and resource-level checks

- Grant the minimum scope a workload needs, not "read-write on everything" because it was convenient during setup.
- A tenant-scoped system needs a resource-level check, not just a role check: "is this user an admin" is not the same question as "is this user an admin *of this tenant*." Cross-tenant leakage is one of the most common real-world authorization bugs — a query missing a `WHERE tenant_id = :caller_tenant` clause is a security bug, not a correctness edge case.
- Prefer deny-by-default policy: an explicit allow rule per resource/action, not an implicit allow unless something blocks it.

## Secrets and workload identity

| Practice | Why |
|---|---|
| No hard-coded secrets in code/config/images | A leaked repo or image layer should not leak credentials. |
| Secret manager (Vault, cloud KMS-backed store) | Centralizes rotation, access audit, and revocation. |
| Short-lived credentials over static ones | A leaked static <abbr title="Application Programming Interface">API</abbr> key is valid until manually revoked; a leaked 15-minute token expires itself. |
| Workload identity (e.g., a service's cloud IAM role, not an embedded key) | Removes the secret-distribution problem entirely for service-to-service and service-to-cloud-resource calls. |
| Never log secrets, tokens, or full PII | Logs are widely read, widely retained, and rarely encrypted at the same level as the primary store. |

## Encryption

- **In transit:** <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> between every hop that crosses a network boundary, including internal service-to-service traffic if that traffic can cross a host/zone boundary you do not fully control. Termination at a load balancer does not imply the hop behind it is safe by default — decide deliberately.
- **At rest:** encrypt durable storage (database volumes, object storage, backups). This mainly protects against a stolen disk/snapshot/backup, not against a compromised application identity that already has legitimate query access — encryption at rest is not a substitute for authorization.

## Input validation is a security boundary, not just UX

Client-side validation improves the experience for honest clients. It does nothing for a client that skips your UI and calls the <abbr title="Application Programming Interface">API</abbr> directly. Every input needs server-side validation, because the server is the actual trust boundary:

- Reject malformed input rather than "helpfully" coercing it — coercion is where injection lives.
- Bound sizes (payload size, array length, string length) so validation itself cannot be a resource-exhaustion vector.
- Treat user-controlled strings used in a query, command, URL, or file path as adversarial by default: parameterize queries, never string-concatenate <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>; allowlist redirect targets and file paths; never let a server fetch a user-supplied URL without restricting destination (see SSRF below).

## Threats worth naming explicitly in an interview

| Threat | What it is | Primary defense |
|---|---|---|
| Injection (<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>, command, log) | Untrusted input is interpreted as code/structure instead of data. | Parameterized queries, strict input schemas, no string-built commands. |
| SSRF (server-side request forgery) | Server is tricked into making a request to an internal/unintended target using attacker-supplied input (e.g., a "fetch this image URL" feature). | Allowlist destinations, block internal/metadata <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> ranges, no redirects followed blindly. |
| IDOR / broken object-level authorization | Caller accesses an object by guessing/changing an ID, without a per-resource ownership check. | Authorize every object access against the caller's identity, not just authenticate the caller. |
| Secrets in logs | Tokens, passwords, or PII written to logs that are broadly readable/retained. | Structured logging with an explicit denylist/allowlist of loggable fields; scrub before write. |

## Data classification, retention, deletion, audit — checklist for any data flow

For every piece of data a design introduces, answer:

```text
Classification:  public / internal / confidential / regulated (PII, payment, health)?
Who may read it:  which identities/roles, under what authorization check?
Where does it live:  primary store, cache, logs, backups, analytics copies?
Encryption:  in transit? at rest? field-level for the most sensitive fields?
Retention:  how long is it kept, and why that duration?
Deletion:  how does a deletion request propagate to every copy (cache, backups, derived indexes)?
Audit:  is access to this data logged, and can you answer "who read record X on date Y"?
External sharing:  does any third party receive this data, under what agreement?
```

An interview answer that names encryption but skips deletion propagation (backups, caches, downstream analytics) has not actually closed the loop — "we deleted the row" is not true if three other copies still exist.

## OAuth 2.0, OpenID Connect, and <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> trade-offs

These three are constantly conflated in interviews. Keep them apart:

| Standard | Question it answers | Output |
|---|---|---|
| **OAuth 2.0** | *Authorization delegation:* may this app act on this user's resources, with this scope? | An **access token** (and optionally a refresh token) |
| **OpenID Connect (OIDC)** | *Authentication* on top of OAuth: who is the user? | An **ID token** (a signed <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> with `sub`, `iss`, `aud`, `exp`) plus a `userinfo` endpoint |
| **<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr>** | A *token format*: a signed (JWS) or encrypted (JWE) <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> claim set | Used by both, but tokens can also be opaque strings |

**Flows to know:**
- **Authorization Code + PKCE** — the default for web, mobile, and single-page apps. The browser gets a short-lived code; the client exchanges it (with the PKCE verifier) for tokens. Never put tokens in URLs.
- **Client Credentials** — service-to-service with no user.
- **Device Authorization** — TVs and CLIs ("go to this URL and enter code ABCD").
- Implicit flow and password grant are deprecated.

**<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> access tokens vs opaque tokens:**

| | Self-contained <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> | Opaque token + introspection |
|---|---|---|
| Validation | Local signature check (fast, no network) | Call the auth server or a cache |
| Revocation | Hard: valid until `exp` unless you keep a denylist | Immediate |
| Size | Larger (claims in every request) | Small |
| Typical choice | Short-lived access tokens (5-15 min) + refresh tokens | Sessions needing instant logout or high-risk scopes |

<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> pitfalls to name: verify the signature with an allowlisted algorithm (reject `alg: none` and algorithm confusion), always check `iss`, `aud`, `exp`/`nbf`, rotate signing keys via a published JWKS with `kid`, don't put secrets or excessive PII in claims (JWS is signed, not encrypted), and store browser tokens in `HttpOnly`, `Secure`, `SameSite` cookies rather than `localStorage` to limit XSS token theft.

## Key management and envelope encryption


```arch
%% caption: Envelope encryption secures data locally with a unique Data Key, which is itself encrypted by a Master Key in a secure KMS.
node kms "KMS\n(Holds Master KEK)" at 0,0 icon=lock color=red
node app "Application" at 2,0 icon=app color=blue
node db "Storage\n(DB / S3)" at 4,0 icon=db color=slate

app -> kms : "1. Generate Data Key\n(DEK)"
kms ..> app : "2. returns Plain DEK\n& Encrypted DEK"
app -> app : "3. Encrypt data\nwith Plain DEK"
app ==> db : "4. Store Ciphertext\n+ Encrypted DEK"
```
Encrypting everything with one master key that the application holds is not key management. The standard pattern is **envelope encryption**:

```text
KMS / HSM holds the KEY-ENCRYPTION KEY (KEK) — never leaves the KMS
    │
    │ encrypt/decrypt small data keys only
    ▼
DATA-ENCRYPTION KEY (DEK), random per object/file/tenant
    │ encrypts the actual data locally (AES-256-GCM)
    ▼
store: ciphertext + ENCRYPTED DEK (wrapped by the KEK) side by side
```

- **Why:** bulk data never goes to the KMS (fast, cheap); the KMS enforces access control and audit on unwrap; a stolen disk holds only wrapped DEKs.
- **Rotation:** rotate the KEK by re-wrapping DEKs (cheap); rotating DEKs requires re-encrypting data (expensive, done lazily or on schedule). Keep old KEK versions for decryption until everything is re-wrapped.
- **Per-tenant or per-user keys** enable **crypto-shredding**: delete the key and every copy of that tenant's data, including backups and immutable logs, becomes unreadable.
- **Customer-managed keys (CMEK):** enterprise customers control the KEK in their own KMS project and can revoke access.
- **Separation of duties:** the identity that can read ciphertext should not automatically be able to unwrap keys.

## Deletion requirements (GDPR, CCPA) end to end

"Delete my account" must reach every copy, within a stated deadline (GDPR requires erasure without undue delay, generally within one month of the request). A deletion design names each location and its mechanism:

| Where the data lives | Mechanism |
|---|---|
| Primary databases | Hard delete, or soft delete followed by a scheduled hard-delete job with a deadline |
| Caches | Invalidate on delete; TTLs as a backstop |
| Search indexes and read models | Consume the deletion event from the outbox/CDC stream |
| Object storage (photos, attachments) | Delete objects; lifecycle rules for versions |
| Analytics warehouse / data lake | Partition by user or date so deletes don't rewrite petabytes; or pseudonymize with a per-user key and destroy the key |
| Logs | Minimize PII in logs; short retention; tokenize identifiers |
| Backups | Can't be edited cheaply: expire within the retention window, or crypto-shred per-user keys |
| Third-party processors | Propagate deletion via their APIs; record confirmation |
| <abbr title="Machine Learning">ML</abbr> training data / features | Remove from future training sets; document model retraining policy |

Implementation pattern: a **deletion orchestrator** (a saga) records the request, fans out a `UserDeleted` event, tracks acknowledgement from every registered data owner, retries failures, and produces an auditable completion record. Legal holds and financial record-keeping obligations override deletion for specific data; the system must represent those exceptions explicitly.

## Abuse and spam prevention

Rate limiting stops volume; abuse systems stop *bad actors* who stay under the limits:
- **Signals:** account age, device fingerprint, <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> reputation and ASN, velocity (actions per minute per account/device/<abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>), graph signals (many accounts sharing devices or payment instruments), content classifiers.
- **Actions, graded:** allow → add friction (CAPTCHA, phone verification) → shadow-limit (content visible only to the sender) → block. Graded responses make it harder for attackers to learn thresholds.
- **Architecture:** a synchronous low-latency risk check on the request path with a strict timeout and a fail-open or fail-closed policy per action, plus asynchronous deeper analysis that can retroactively remove content and ban accounts.
- **Feedback loop:** user reports and reviewer decisions become labels for the classifiers.

## Abuse and rate limiting

Admission control against abusive/excessive traffic (token bucket rate limiting, WAF rules, DDoS absorption) is edge and traffic-control concern, not identity/authorization concern — covered in `02_networking.md`. The two are complementary: rate limiting stops a caller from doing *too much* of something they're otherwise allowed to do; authorization stops them from doing something they're never allowed to do at all.

## Related building blocks

- [02_networking.md](02_networking.md) — WAF, DDoS protection, and rate limiting at the edge.
- [15_observability_and_reliability.md](15_observability_and_reliability.md) — audit trails and alerting are an observability concern as much as a security one.
- [17_decision_framework.md](17_decision_framework.md) — the worksheet's security/tenant/privacy line ties directly to the checklist above.
