# 036 — Design a Content Delivery Network

Design the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> itself, in the spirit of Akamai, Cloudflare, Fastly or Netflix Open Connect: a global network of edge caches that serves other companies' web assets, downloads and video segments close to their users and shields their origin servers.

## Functional requirements

- Serve <abbr title="Hypertext Transfer Protocol Secure - An extension of HTTP that uses encryption for secure communication over a computer network.">HTTPS</abbr> `GET`/`HEAD` (including range requests) for customer hostnames from the nearest healthy POP, fetching from the customer's origin on a miss.
- Per-customer caching rules: TTLs, cache-key normalisation (query parameters, headers), `stale-while-revalidate` and `stale-if-error`.
- Purge by URL, prefix and tag, visible worldwide in seconds.
- <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> for every hostname, including customer-supplied and automatically issued and renewed certificates.
- Per-customer analytics and billing (bytes, requests, hit ratio, status codes) within minutes.
- Absorb volumetric and application-layer DDoS without taking customers or their origins down.

## Constraints to assume

- About 500 POPs in 100+ countries; 50 Tbps peak egress and 12.5M requests/second at peak (mean response 500 KB).
- 10 billion cacheable objects in a 30-day window (mean 300 KB, 3 PB), Zipf-like popularity. Targets: 92% edge request hit ratio, 90% edge byte hit ratio, at most 1% of edge bytes reaching customer origins.
- 5 million customer hostnames; purge p99 under 5 seconds worldwide; a config change is live worldwide in under 5 minutes through a progressive rollout, an emergency change in under 60 seconds.
- Server-side time-to-first-byte p99 under 50 ms for a cache hit; 99.99% success on cacheable requests.
- A POP loss, a control-plane outage or an origin outage must not become a customer outage for content that is already cached.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Request steering (<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> versus anycast), the cache hierarchy with placement inside a POP and hot-object handling, cache-key design and request collapsing, purge at scale, <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> and certificate management, and the split between control plane and data plane, including origin-failure behaviour.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
