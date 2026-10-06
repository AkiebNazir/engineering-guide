---
title: "API Gateway Theory"
description: "Master the API gateway: reverse proxying, routing, header hygiene, edge auth and rate limiting, load balancing, health checks, retries and circuit breakers, canary releases, BFF aggregation and caching, with Envoy/Kong configs and Python and Go labs."
---

# API Gateway Theory

## What is an API Gateway?

An **API gateway** is a reverse proxy that sits between clients and your services and applies the same policies to every request: it decides **where** a request goes (routing), **whether** it may go there (authentication, authorization, rate limits), and **how** it gets there safely (timeouts, retries, load balancing, health). Clients see one address and one consistent API; services behind it stay small and do not each re-implement those rules.

It exists because the alternative does not scale. With ten services and three client apps, every service would need its own TLS, token checks, rate limiter, CORS rules, request IDs and access logs, written in different languages by different teams and slightly different in each. The gateway pulls those **cross-cutting concerns** (see [Cross-Cutting Concerns](../Fundamentals/03_cross_cutting_concerns.md)) into one place that one team can operate, measure and harden.

The terms get mixed up, so fix them once:

| Term | What it is | Examples |
| :--- | :--- | :--- |
| **Reverse proxy** | Accepts client connections and forwards them to backends. No opinions. | nginx, HAProxy, `httputil.ReverseProxy` |
| **Load balancer** | A reverse proxy whose main job is spreading traffic over instances (L4 or L7). | AWS ALB/NLB, HAProxy |
| **API gateway** | An L7 reverse proxy **with API policies**: auth, quotas, transformations, developer keys, analytics. | Kong, Envoy Gateway, AWS API Gateway, Apigee, Tyk, KrakenD |
| **Service mesh** | The same proxy features for **east-west** (service-to-service) traffic, as a sidecar or per-node proxy next to every service. | Istio, Linkerd, Cilium |
| **BFF** (Backend for Frontend) | A gateway route or small service shaped for **one** client (web, iOS), often aggregating several calls. | a Node/Go service, GraphQL router |

A rough rule: the **gateway** owns north-south traffic (clients coming in), the **mesh** owns east-west traffic (services calling each other). Both are usually built on the same proxy engine (Envoy).

```arch
%% caption: North-south traffic enters through the gateway; east-west calls between services go through the mesh.
node web "Web app" at 0,0 icon=browser
node ios "iOS app" at 1,0 icon=mobile
node partner "Partner" at 2,0 icon=api
node gw "API gateway" at 1,1 icon=gateway sub="TLS, auth, limits, routing"
group cluster "Service cluster (mesh)" color=blue icon=k8s
node users "users" at 0,2 in cluster icon=service
node orders "orders" at 1,2 in cluster icon=service
node pay "payments" at 2,2 in cluster icon=service
node idp "Identity provider" at 3,1 icon=identity
web -> gw
ios -> gw
partner -> gw
gw -> users
gw -> orders
orders -> pay : "east-west"
gw ..> idp : "JWKS"
```

## What a Gateway Does to One Request

Every request passes through a **filter chain**, cheapest checks first, so abusive traffic is rejected before it costs anything:

```arch
%% caption: The order matters: cheap per-IP limits protect the expensive auth step; the upstream is only touched at the end.
route straight
node c "Client" at 0,0 shape=pill
node tls "TLS termination" at 1,0 shape=box
node ip "Per-IP limit" at 2,0 shape=box color=amber
node authn "Authenticate" at 3,0 shape=box color=red
node route "Match route" at 3,1 shape=box
node authz "Authorize route" at 2,1 shape=box color=red
node quota "Per-consumer quota" at 1,1 shape=box color=amber
node up "Pick instance + proxy" at 0,1 shape=box color=green
c -> tls -> ip -> authn -> route -> authz -> quota -> up
```

| Step | Failure | Status |
| :--- | :--- | :--- |
| No route matches | Unknown path or host | `404` |
| Body larger than the route allows | Rejected before a byte reaches the service | `413` |
| Per-IP limit exceeded | Brute force, scrapers | `429` + `Retry-After` |
| No or invalid credential | Missing, expired, wrong signature, `alg=none` | `401` + `WWW-Authenticate` |
| Valid identity, no permission | Wrong scope or plan | `403` |
| Upstream refused / reset | Instance down | `502` |
| Upstream too slow | Timeout to first byte | `504` |
| Concurrency limit reached | Circuit breaker open | `503` (fail fast) |

## Routing and Header Hygiene

**Routing** matches on host, path prefix (on **segment** boundaries: `/api/users` must not match `/api/usersX`), method and headers; the **longest prefix wins**. The gateway usually **strips the prefix** so `/api/users/42` reaches the users service as `/users/42`.

Headers are where gateways are most often wrong:

*   **Hop-by-hop headers** (`Connection`, `Keep-Alive`, `TE`, `Transfer-Encoding`, `Upgrade`, `Proxy-*`, and any header **named in** `Connection`) belong to one TCP hop and must be removed before forwarding.
*   **`X-Forwarded-For` / `-Proto` / `-Host`** (or the standard `Forwarded` header): the **edge** gateway **replaces** whatever the client sent, because a client can type any IP; proxies **inside** the trusted network append. A service that trusts a client-supplied `X-Forwarded-For` for rate limiting or audit logs can be fooled trivially. Go's `httputil.ReverseProxy` with the legacy `Director` hook keeps the client's value; `Rewrite` + `SetXForwarded()` does not (Go lab 1).
*   **Request IDs**: accept a well-formed `X-Request-Id` (or `traceparent`), otherwise mint one, echo it back, and log it on every line.
*   **Identity headers** (`X-User-Id`, `X-Scopes`): strip any the client sent, then inject trusted ones after authentication. If a service can be reached without the gateway, sign them (Python lab 2) or use mTLS.
*   **Fingerprints**: remove `Server`, `X-Powered-By` from responses; add `X-Content-Type-Options: nosniff`, HSTS and similar security headers once, here.

## Authentication and Rate Limiting at the Edge

The gateway verifies credentials **once** so services receive a trusted identity:

*   **API keys** for server-to-server and partner access: store only a hash, map the key to a **consumer** with a plan.
*   **JWT access tokens** from an OAuth 2.0 / OIDC provider ([OpenID Connect and Single Sign-On](../Fundamentals/05_openid_connect_and_sso.md)): pin the algorithm, verify the signature against the provider's **JWKS** (cached, refreshed on unknown `kid`), check `exp`/`nbf` with a small leeway, `iss` and `aud`. Do not forward the raw token further than needed.
*   **mTLS** for B2B and internal clients.

**Rate limiting** protects capacity and enforces commercial plans. The token bucket (`REST/labs/golang/04_rate_limit_middleware`) is the usual algorithm. The trap: a **local** limit on N gateway replicas lets a client through **N times** the limit when a load balancer spreads its requests. Global limits need a shared counter (Redis, or Envoy's external rate-limit service). A common compromise: a generous local limit as a cheap first line, and an exact global quota per consumer.

## Upstreams: Load Balancing, Health, Retries, Overload

Routing picks a **service**; the upstream layer picks an **instance** and survives bad ones (Envoy: clusters; Kong: upstreams/targets).

| Mechanism | What it does | Key detail |
| :--- | :--- | :--- |
| Round robin | Each instance in turn | Keeps feeding a slow instance its full share |
| Least request / P2C | Pick 2 random instances, send to the one with fewer in-flight requests | Routes around a slow instance almost for free |
| Consistent hash (ring, Maglev) | Same key -> same instance | Sticky sessions, cache locality, canary stickiness |
| Passive health (outlier ejection) | N consecutive 5xx -> eject for a while | Reacts to real traffic, needs traffic to react |
| Active health checks | Poll `/healthz`; hysteresis (2 fails to eject, 2 passes to return) | Lets a **draining** instance leave before it breaks |
| Retries | Retry on a **different** instance, only idempotent requests or ones with an `Idempotency-Key` | A **retry budget** (e.g. retries <= 20% of requests) prevents a retry storm from tripling load during an outage |
| Concurrency limit ("circuit breaker" in Envoy) | Past max in-flight requests, fail fast with `503` | Queueing until everything times out is worse than failing a few fast |
| Timeouts | Connect timeout, time to first byte, idle timeout | A total-request timeout breaks streaming; bound headers, not streams |

## Progressive Delivery: Canary, Sticky Weights, Mirroring

Because every request passes through it, the gateway is where a new version meets real traffic in controlled amounts:

*   **Weighted routing**: 95% to v1, 5% to v2. It must be **sticky**: hash a user id into buckets, so a user does not bounce between versions, and widening from 5% to 25% keeps the first 5% on v2.
*   **Override headers** (`x-canary: always`) for testers and the rollout controller, stripped from untrusted traffic.
*   **Mirroring (shadow traffic)**: send a copy of real `GET`s to a new version, discard its responses, compare offline. Never mirror non-idempotent requests without making the shadow side-effect free.
*   **Automatic rollback**: a controller (Argo Rollouts, Flagger) compares the canary's error rate and latency with the stable version over a window and sets the weight to 0 when it is worse, with a minimum sample size so one error does not decide.

## Aggregation (BFF) and Caching

A **BFF** route answers one client call by calling several services **in parallel**, each with its own deadline, so the page costs the slowest call, not the sum. Decide per part whether it is **required** (fail the call) or **optional** (return `null` and list it as degraded). GraphQL routers ([GraphQL Theory](../GraphQL/Theory.md), federation) are a generalized version of this.

An **edge cache** honours the upstream's `Cache-Control` (`max-age`, `s-maxage`, `private`, `no-store`, `stale-while-revalidate`) and keys on method, URL and the headers listed in `Vary`. Two production details: **stale-while-revalidate** serves the old copy instantly while refreshing in the background, and **request coalescing** turns 100 concurrent misses on an expired key into one upstream call (the cache stampede). Go lab 3 builds both.

## Real-World Scenario & Architecture

**Scenario:** an e-commerce company exposes a public API to partners, serves a web app and a mobile app, and runs about 40 services on Kubernetes.

```arch
%% caption: A typical production layout: CDN/WAF at the edge, a gateway tier, then services in the mesh; state for limits and caches lives outside the gateway replicas.
node users "Clients" at 1,0 icon=users
node cdn "CDN + WAF" at 1,1 icon=cdn sub="TLS, bot rules, static cache"
group gwt "Gateway tier (3+ replicas)" color=purple icon=gateway
node g1 "Gateway" at 0,2 in gwt icon=gateway
node g2 "Gateway" at 1,2 in gwt icon=gateway
node g3 "Gateway" at 2,2 in gwt icon=gateway
node redis "Redis" at 3,2 icon=redis sub="global quotas"
group svc "Services" color=blue icon=k8s
node s1 "catalogue" at 0,3 in svc icon=service
node s2 "orders" at 1,3 in svc icon=service
node s3 "payments" at 2,3 in svc icon=service
node otel "OTel Collector" at 3,3 icon=trace
users -> cdn
cdn -> g1
cdn -> g2
cdn -> g3
g3 -> redis
g1 -> s1
g2 -> s2
g3 -> s3
s3 ..> otel
```

*   The **CDN/WAF** absorbs volumetric attacks and caches static and public responses.
*   The **gateway tier** is stateless and horizontally scaled; quotas live in Redis so limits are global.
*   Config is **declarative** and in git (`configs/envoy.yaml`, `configs/kong.yaml`), deployed like code, reviewed like code.
*   Every gateway emits traces and RED metrics to the OpenTelemetry Collector ([API Observability Theory](../Observability/Theory.md)); the gateway's access log is the single most useful debugging artefact you have.

## Choosing a Gateway

| Option | Strengths | Watch out for |
| :--- | :--- | :--- |
| **Envoy** (raw, or Envoy Gateway / Gloo / Istio ingress) | Fast, programmable filters, first-class gRPC/HTTP2, the data plane most meshes use | Verbose config; you usually want a control plane on top |
| **Kong** (open source or Enterprise/Konnect) | Plugin ecosystem, developer portal, consumers and keys built in | Plugin quality varies; DB vs DB-less modes behave differently |
| **nginx / OpenResty** | Everywhere, very fast, well understood | API features are DIY (Lua or modules) |
| **Cloud managed** (AWS API Gateway, Azure APIM, Google Apigee/API Gateway) | Nothing to run, IAM integration, usage plans | Per-request pricing, latency overhead, vendor lock-in, limits on payload/timeouts |
| **Kubernetes Gateway API** (`Gateway`, `HTTPRoute`) | A portable standard API; many implementations (Envoy Gateway, Istio, Cilium, Kong, NGINX Gateway Fabric) | Advanced policy still lives in implementation-specific extensions |
| **Your own on `httputil.ReverseProxy`** | Full control, tiny | You own every CVE and edge case |

## The Gateway as a Risk

*   **Single point of failure**: run at least three replicas across zones, keep it stateless, test failover.
*   **Latency tax**: each hop adds roughly a millisecond or less for a well-tuned proxy; plugins that call out (auth introspection, external rate limiting) add their own round trip. Measure p99, not the mean.
*   **Business logic creep**: transformations and orchestration pile up in the gateway until it becomes an untested monolith owned by no product team. Keep it to policy; put domain logic in services (or a BFF owned by the client team).
*   **Blast radius of config**: one bad route deploy takes down every API. Validate config in CI, canary the gateway itself, and keep a fast rollback.

## Common Pitfalls

1.  Trusting a client-supplied `X-Forwarded-For` (or `X-User-Id`) anywhere behind the gateway.
2.  Services reachable directly, bypassing the gateway's auth (fix: network policy, mTLS, or signed identity headers).
3.  Local rate limits on N replicas advertised as a global limit.
4.  Retrying `POST` without an idempotency key, or retrying without a budget during an outage.
5.  One total-request timeout that also kills long streams (SSE, gRPC streams, WebSockets).
6.  Round robin in front of instances with uneven latency.
7.  Prefix matching on raw strings (`/api/users` matching `/api/users-admin`).
8.  Non-sticky canary weights: a user sees v1 and v2 alternately.
9.  Caching responses with `Cache-Control: private` or `Authorization` in a shared cache.
10. Putting business rules in gateway plugins "just this once".

## Check Yourself

1.  Why must the **edge** gateway replace `X-Forwarded-For` while internal proxies append to it?
2.  When is `401` correct and when `403`? Where should each be produced?
3.  You run 4 gateway replicas with a local limit of 100 req/min per key. What can one client actually get? How do you fix it?
4.  Why does P2C least-request beat round robin when one instance is slow?
5.  What is a retry budget, and what failure does it prevent?
6.  Why fail fast with `503` at a concurrency limit instead of queueing?
7.  What makes a canary weight "sticky", and why does it matter when you widen the rollout?
8.  What do `stale-while-revalidate` and request coalescing each protect against?
9.  Gateway vs service mesh: which traffic does each own, and why are both often Envoy?
10. Name three things that should **not** live in a gateway.

<details><summary>Answers</summary>

1.  The edge is the first hop you control; anything before it is the client, who can write any value. Inside, each trusted proxy adds the address it saw.
2.  `401`: no or invalid credentials ("who are you?"), with `WWW-Authenticate`. `403`: identity known, action not allowed. Authentication and coarse route authorization at the gateway; fine-grained object ownership (BOLA) in the service, which knows the data.
3.  Up to 400/min when requests are spread across replicas. Use a shared counter (Redis / external rate-limit service), or divide the limit by the replica count as an approximation.
4.  RR ignores load; P2C compares in-flight requests, so a slow instance with a queue is picked less.
5.  A cap on retries as a fraction of requests; without it, a full outage multiplies traffic by (1 + retries) exactly when the backend can least take it (a retry storm).
6.  Queued requests hold memory and connections and time out anyway, dragging healthy requests down with them; a fast `503` lets clients back off or fail over.
7.  Hashing a stable user id into fixed buckets; widening the weight only adds buckets, so existing canary users stay on the canary.
8.  SWR: slow refreshes and upstream latency spikes on expiry (serve stale while refreshing). Coalescing: a stampede of identical misses hitting the origin at once.
9.  Gateway: north-south (clients in). Mesh: east-west (service to service). Envoy is a programmable L7 proxy with good xDS APIs, so both control planes use it.
10. Domain rules (pricing, eligibility), data joins that need a database, long-running workflows; also per-service business validation.

</details>

## Hands-On Labs

Every lab starts its own upstreams and gateway in one process, sends real HTTP through them, prints what happens and asserts the result. **Python and Go cover different ground**, so do both. `configs/envoy.yaml` and `configs/kong.yaml` show how each lab's policies look in real gateways (reference only; nothing needs to be installed).

| # | Python (`Gateway/labs/python/`) | You learn |
| :---: | :--- | :--- |
| 1 | [Reverse proxy and routing](labs/python/01_reverse_proxy_and_routing.py) | A gateway from scratch: host + longest-prefix routing on segment boundaries, prefix stripping, hop-by-hop and `X-Forwarded-*` hygiene, request ids, `404`/`413`/`502`/`504` mapping, JSON access log |
| 2 | [Edge auth and rate limiting](labs/python/02_edge_auth_and_rate_limiting.py) | API keys and HS256 JWT at the edge, `401` vs `403`, per-consumer token buckets with `RateLimit` headers, signed identity propagation, local vs global limits across replicas |
| 3 | [Load balancing health and resilience](labs/python/03_load_balancing_health_and_resilience.py) | Round robin vs P2C, outlier ejection, active health checks with hysteresis, safe retries with a budget, concurrency limits that fail fast |

| # | Go (`Gateway/labs/golang/`) | You learn |
| :---: | :--- | :--- |
| 1 | `01_reverse_proxy_with_httputil` | `httputil.ReverseProxy` done right: `Rewrite` vs `Director` (spoofed `X-Forwarded-For`), `ErrorHandler` 502 vs 504, `ModifyResponse`, transport timeouts, SSE streaming with `FlushInterval` |
| 2 | `02_canary_traffic_shifting_and_mirroring` | Sticky weighted canary by user hash, trusted override header, async traffic mirroring off the critical path, automatic rollback on error rate |
| 3 | `03_aggregation_caching_and_coalescing` | BFF fan-out with per-call deadlines, required vs optional parts, `Cache-Control` + `Vary` caching, stale-while-revalidate, hand-written singleflight against cache stampedes |

```bash
python Gateway/labs/python/02_edge_auth_and_rate_limiting.py
go run ./Gateway/labs/golang/02_canary_traffic_shifting_and_mirroring
```

Python lab 1 also accepts `--serve` to stay up so you can poke it with `curl`.

## Exercises

1.  Put Go lab 1's proxy behind Python lab 2's auth chain (or port the chain to Go middleware) and rate limit per consumer.
2.  Add P2C least-request selection to Go lab 1 with three `users` instances, one of them slow.
3.  Make Go lab 2's rollback also consider p95 latency, using a histogram from `Observability/labs/golang/02_slo_histograms_and_burn_rate_alerts`.
4.  Add `ETag` revalidation (`If-None-Match` -> `304`) to Go lab 3's cache (see [Etag conditional requests](../REST/labs/python/04_etag_conditional_requests.py)).
5.  Translate `configs/envoy.yaml`'s routes into Kubernetes Gateway API `HTTPRoute` objects.

## Where To Go Next

*   **Why these policies exist:** [Cross-Cutting Concerns](../Fundamentals/03_cross_cutting_concerns.md) (auth, rate limiting, idempotency, errors).
*   **Seeing what the gateway does:** [API Observability Theory](../Observability/Theory.md) (traces start at the edge).
*   **The GraphQL version of a gateway:** federation routers in [GraphQL Theory](../GraphQL/Theory.md).
*   **gRPC behind a gateway:** [gRPC Theory](../gRPC/Theory.md) (HTTP/2 end to end, gRPC-Web, transcoding).
