# Web Servers and Proxies

Application servers (a Node.js Express app, Python under Gunicorn or Uvicorn, a Java
service on Tomcat or Netty) are built to run business logic. They are generally poor at
the jobs at the edge of a system: holding thousands of slow client connections,
terminating TLS, serving static files, buffering large uploads and absorbing abusive
traffic. That is why almost every production request passes through a dedicated web
server or **reverse proxy** first. This chapter explains what a reverse proxy is and
does, then goes deep on Nginx (architecture, proxying, TLS, rate limiting, load
balancing), Envoy (dynamic configuration, circuit breaking, outlier detection), HAProxy,
Caddy and the Kubernetes edge (Ingress and the Gateway API), finishing with where each
belongs and how proxy failures show up as 502, 503 and 504 errors.

## Foundations — What is a reverse proxy, and why put one in front of your app?

### Forward proxy versus reverse proxy

A **proxy** is a program that receives a request and makes it again on someone else's
behalf. Which side it works for decides its name:

- A **forward proxy** acts for *clients*. A company's outbound proxy that all employee
  laptops go through (for filtering or caching) is a forward proxy; the website sees the
  proxy, not the laptop.
- A **reverse proxy** acts for *servers*. Clients think they are talking to
  `api.example.com`; in fact they reach Nginx, which picks one of several backend
  servers and relays the request. The client never sees the backends.

### What a reverse proxy does for you

| Job | Why the app should not do it itself |
|---|---|
| **TLS termination** | Certificates, protocol versions and ciphers are configured and rotated in one place; the app speaks plain HTTP on a private network (or mTLS, see §3). |
| **Buffering slow clients** | A phone on a bad network may take 10 s to upload a request. The proxy reads it fully, then hands it to the app in milliseconds, so an app worker is not held hostage. This matters most for thread- or process-per-request servers (Gunicorn sync workers, Puma, Tomcat). |
| **Load balancing** | Spread requests across N app instances and stop sending to broken ones. |
| **Routing** | `/api/*` to the API service, `/static/*` from disk, `/ws` to the WebSocket service; one public hostname, many backends. |
| **Static files** | `sendfile()` from the page cache is far cheaper than going through an interpreter. |
| **Protection** | Rate limits, connection limits, request size limits, header size limits, IP allow lists. |
| **Compression and caching** | gzip/Brotli responses, cache cacheable responses. |
| **Observability** | One access log with status, bytes, upstream latency for every request. |

### Layer 4 versus Layer 7

- An **L4** (transport) proxy or load balancer sees TCP/UDP connections: source and
  destination IP and port. It forwards bytes without understanding them. Fast, protocol
  agnostic (works for Postgres, Redis, MQTT), but cannot route by URL or retry a failed
  HTTP request. Examples: AWS NLB, HAProxy in `mode tcp`, Nginx `stream {}`, Linux IPVS.
- An **L7** (application) proxy parses HTTP: method, path, headers, cookies. It can route
  by path or header, rewrite, retry, rate-limit per user, and terminate TLS. Examples:
  Nginx `http {}`, Envoy, HAProxy `mode http`, AWS ALB. The deeper theory is in
  [Scaling and Load Balancing](../../interview-core/SystemDesign/building_blocks/13_scaling_and_load_balancing.md).

### A request's path through the edge

```arch
%% caption: A typical request path: DNS finds the edge, an L4 load balancer spreads connections, the L7 proxy terminates TLS and routes by path, and app instances only see plain, already-buffered requests.
grid 160x105
node user "Browser" at 1,0 icon=browser sub="https://shop.example.com"
node dns "DNS" at 0,0 icon=dns sub="shop -> LB address"
node l4 "L4 load balancer" at 1,1 icon=lb sub="TCP :443, no TLS here"
group px "Proxy tier (L7)" color=purple icon=proxy
node ng1 "Nginx 1" at 0.5,2 in px icon=nginx sub="TLS, route, limit"
node ng2 "Nginx 2" at 1.5,2 in px icon=nginx sub="identical config"
group apps "Private network" color=blue icon=network
node static "Static files" at 0,3 in apps icon=folder sub="/static/*"
node api "API pool" at 1,3 in apps icon=server sub="/api/* -> :8080 x N"
node ws "WebSocket svc" at 2,3 in apps icon=websocket sub="/ws upgrade"
user ..> dns : "lookup"
user -> l4
l4 -> ng1
l4 -> ng2
ng1 -> static
ng1 -> api
ng2 -> api
ng2 -> ws
```

An everyday example: when you open an online shop, the page HTML comes from the app,
but its CSS, images and JavaScript are served by the proxy from disk or a CDN, your
HTTPS connection ends at the proxy, and if one of the app servers crashes mid-afternoon
the proxy quietly stops sending you there. You never notice any of it, which is the
point.

## 1. Nginx architecture

Nginx runs one **master** process (reads config, binds ports, manages workers) and a
small number of **worker** processes, usually one per CPU core (`worker_processes
auto;`). Each worker is single-threaded and runs an **event loop** on `epoll` (Linux) or
`kqueue` (BSD/macOS): it registers every socket with the kernel and handles whichever
are ready, never blocking on one client. A worker can hold tens of thousands of mostly
idle connections for a few hundred bytes to a few KB of memory each, which is why Nginx
became the default in front of thread-per-request servers. The kernel side of this is
in [Operating Systems & Hardware Symbiosis](../../interview-core/CSFundamentals/01_operating_systems_deep_dive.md) §4.

```nginx
worker_processes auto;
worker_rlimit_nofile 65536;
events {
    worker_connections 8192;     # per worker; a proxied request uses 2 (client + upstream)
}
```

Maximum concurrent proxied clients ≈ `worker_processes × worker_connections / 2`, also
capped by the file-descriptor limit.

### Reloading without dropping connections

`nginx -t` validates the configuration; `nginx -s reload` (or `systemctl reload nginx`,
both send `SIGHUP` to the master) starts **new** workers with the new config, and tells
the old workers to stop accepting and exit once their in-flight requests finish. Existing
connections are not dropped. The real cost of very frequent reloads is different: old
workers stay alive as long as their longest connection (a WebSocket can keep one around
for hours), so memory grows with each reload, and upstream keepalive pools and caches
are rebuilt. That, not dropped connections, is why dynamic environments moved toward
proxies with API-driven configuration (Envoy, §5).

### Configuration structure and `location` matching

Contexts nest: `main` → `events` / `http` → `server` (one per virtual host, chosen by
`listen` + `server_name`, i.e. the `Host` header or TLS SNI) → `location` (chosen by the
request path).

How Nginx picks a `location`, a common interview trap:

1. `location = /exact` — an exact match wins immediately.
2. The longest **prefix** match is remembered. If it is marked `^~`, use it and skip
   regexes.
3. **Regex** locations (`~` case-sensitive, `~*` case-insensitive) are tried in the
   order they appear in the file; the first match wins.
4. Otherwise the remembered longest prefix is used.

## 2. Nginx as a reverse proxy

A realistic API proxy (`/etc/nginx/conf.d/api.conf`):

```nginx
upstream api_backend {
    zone api_backend 64k;                 # shared memory: state is shared across workers
    least_conn;
    server 10.0.1.5:3000 max_fails=3 fail_timeout=10s;
    server 10.0.1.6:3000 max_fails=3 fail_timeout=10s;
    server 10.0.1.7:3000 backup;          # only used when the others are down
    keepalive 64;                         # idle upstream connections kept open per worker
}

map $http_upgrade $connection_upgrade {   # for WebSockets
    default upgrade;
    ''      close;
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name api.example.com;

    ssl_certificate     /etc/nginx/tls/api.example.com.fullchain.pem;
    ssl_certificate_key /etc/nginx/tls/api.example.com.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    client_max_body_size 10m;             # larger uploads get 413
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /static/ {
        root /srv/app;                    # serves /srv/app/static/...
        expires 7d;
        access_log off;
    }

    location /ws {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 1h;
    }

    location / {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;           # required for upstream keepalive
        proxy_set_header Connection "";   # and do not forward "Connection: close"
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;

        proxy_connect_timeout 2s;
        proxy_read_timeout 30s;
        proxy_next_upstream error timeout http_502 http_503;
        proxy_next_upstream_tries 2;      # at most one retry on another server
    }
}
```

Details worth knowing:

- **Headers.** Without `proxy_set_header Host $host`, the backend sees `Host:
  api_backend`. `X-Forwarded-For` carries the client IP chain and `X-Forwarded-Proto`
  tells the app the original request was HTTPS (otherwise it generates `http://`
  redirect URLs). The standardized `Forwarded` header (RFC 7239) carries the same
  information but is less widely consumed. Only trust these headers from your own
  proxies; behind another LB, use `set_real_ip_from` + `real_ip_header` so
  `$remote_addr` is the real client.
- **Keepalive to upstreams** needs all three of `keepalive N` in the upstream,
  `proxy_http_version 1.1`, and a cleared `Connection` header. Without it every request
  opens a new TCP connection to the backend, which costs latency and leaves thousands of
  sockets in `TIME-WAIT`.
- **`proxy_pass` trailing slash.** `location /api/ { proxy_pass http://b; }` forwards
  `/api/users` unchanged. `location /api/ { proxy_pass http://b/; }` replaces the
  matched `/api/` with `/`, so the backend sees `/users`. One character, very different
  behaviour.
- **Retries are only safe for idempotent requests.** By default Nginx will not retry
  a non-idempotent request (POST, PATCH, LOCK) on the next upstream once it has been
  sent; `non_idempotent` in `proxy_next_upstream` overrides that, and you almost never
  want it.
- **Buffering.** `proxy_buffering on` (the default) lets Nginx read a response from
  the app quickly and trickle it to a slow client. Turn it off (or send
  `X-Accel-Buffering: no` from the app) for server-sent events and streaming responses
  such as LLM token streams, or clients see nothing until the end.

## 3. TLS termination

The proxy performs the TLS handshake ([Networking & Distributed Communication](../../interview-core/CSFundamentals/02_networking_deep_dive.md) and
[HTTP & Web Foundations](../../data-and-apis/API/Fundamentals/02_http_and_web_foundations.md) cover the protocol), holds the private
key, and forwards decrypted HTTP. Practical points for 2026:

- **Protocols**: TLS 1.2 and 1.3 only. TLS 1.3 needs one round trip for a new
  handshake (zero with 0-RTT resumption, which is replayable, so only for idempotent
  requests).
- **Certificates** come from an ACME CA such as Let's Encrypt, renewed automatically
  (certbot, acme.sh, cert-manager in Kubernetes, or Caddy's built-in ACME). Publicly
  trusted certificate lifetimes are shrinking in steps under a CA/Browser Forum ballot
  (to 200 days in 2026, eventually 47 days by 2029), so manual renewal is no longer an
  option. Let's Encrypt also ended OCSP in 2025, which makes `ssl_stapling` irrelevant
  for its certificates.
- **SNI** lets one IP serve many hostnames; Nginx picks the `server` block (and
  certificate) from the name the client sends in the ClientHello.
- **HTTP/2** (`http2 on;`, the directive that replaced `listen … http2` in Nginx 1.25.1)
  multiplexes requests over one connection. **HTTP/3** over QUIC (`listen 443 quic;`
  plus an `Alt-Svc` header) has been available since Nginx 1.25.
- **Behind the proxy**: plain HTTP inside a trusted network was the classic setup.
  Zero-trust environments re-encrypt (`proxy_pass https://…` with
  `proxy_ssl_verify on`) or use mutual TLS between every hop, which is what a service
  mesh automates ([Service Mesh (Istio / Linkerd)](12_service_mesh.md)).

## 4. Rate limiting, connection limits and caching

```nginx
# In http {}: one shared-memory zone, keyed by client IP (≈16,000 IPs per MB)
limit_req_zone  $binary_remote_addr zone=login:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=perip:10m;
limit_req_status 429;                    # default is 503, which looks like an outage

server {
    location /login {
        limit_req zone=login burst=20 nodelay;
        limit_conn perip 10;
        proxy_pass http://api_backend;
    }
}
```

`limit_req` is a **leaky bucket**: requests drain at `rate`. `burst=20` lets up to 20
excess requests queue instead of being rejected; `nodelay` serves those burst requests
immediately (while still consuming burst slots), so short spikes are not artificially
delayed. Beyond the burst, requests get the `limit_req_status` code. `limit_conn` caps
concurrent connections per key.

Limits live in each Nginx instance's shared memory, so N proxies allow N × the rate in
total. For a global per-user or per-API-key limit, use a proxy that calls a shared rate
limit service (Envoy's global rate limit service backed by Redis), or do it in an API
gateway (`SystemDesign` rate limiter case study). A proxy rate limit is useful against
brute force and misbehaving clients; it is not DDoS protection, which has to happen
upstream at a CDN or cloud scrubbing service before traffic reaches your servers.

Caching and compression:

```nginx
proxy_cache_path /var/cache/nginx keys_zone=api_cache:50m max_size=5g inactive=10m;

location /api/catalog/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 60s;
    proxy_cache_use_stale error timeout updating http_502 http_503;  # serve stale if backend fails
    proxy_cache_lock on;                                             # one request fills a miss
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://api_backend;
}
gzip on;
gzip_types application/json text/css application/javascript;
```

`proxy_cache_lock` prevents a cache stampede (many simultaneous misses all hitting the
backend), and `proxy_cache_use_stale` keeps serving the last good copy during a backend
outage. The patterns are the same as in [Caching](../../interview-core/SystemDesign/building_blocks/07_caching.md).

## 5. Load balancing and health checks

| Nginx method | Directive | Picks | Use when |
|---|---|---|---|
| Round robin | (default) | next server in turn, respecting `weight=` | requests cost about the same |
| Least connections | `least_conn` | fewest active connections | request durations vary |
| IP hash | `ip_hash` | hash of client IP | crude session stickiness |
| Generic hash | `hash $request_uri consistent` | consistent hash (ketama) of any key | cache locality: same key → same server, little reshuffling when servers change |
| Random two | `random two least_conn` | pick 2 at random, take the less loaded | many proxies each with partial knowledge |

**Health checks** come in two kinds:

- **Passive**: watch real traffic. In Nginx open source, `max_fails=3 fail_timeout=10s`
  marks a server unavailable for 10 s after 3 failures within 10 s. Free, but real users
  absorb the failures that trigger it.
- **Active**: the proxy probes `/healthz` on its own schedule and removes a server
  before users hit it. Available in HAProxy and Envoy open source; in Nginx it is an
  NGINX Plus feature (`health_check`), and in open source you rely on passive checks or
  on the orchestrator removing unhealthy instances.

Nginx open source has resolved `upstream` hostnames only at startup for most of its life;
since 1.27.3 (2024) the `resolve` parameter on `server` (with a `zone` and a `resolver`)
re-resolves DNS at runtime, which helps with backends behind changing DNS records.
Changing the server *list* itself still needs a config reload, or NGINX Plus's API.

## 6. Envoy: the API-driven proxy

**Envoy** (created at Lyft, open-sourced in 2016, a CNCF graduated project) was designed
for microservices where backends appear and disappear every minute. It is the data plane
under Istio, Envoy Gateway, Contour, Gloo and many cloud load balancers, and is written
in C++ with a multi-threaded, event-loop-per-worker model.

### Envoy's vocabulary

| Concept | Meaning |
|---|---|
| **Listener** | an address:port Envoy accepts connections on |
| **Filter chain** | the processing pipeline for a connection: network filters (TCP proxy, the HTTP connection manager) and, inside HTTP, HTTP filters (router, JWT auth, RBAC, rate limit, ext_authz, Wasm/Lua) |
| **Route** | match on host/path/headers → a cluster, plus retries, timeouts, traffic weights |
| **Cluster** | a logical upstream service with its LB policy, circuit breakers, TLS settings |
| **Endpoint** | an individual backend IP:port in a cluster |

### xDS: configuration over an API

Instead of files and reloads, a **control plane** streams configuration to Envoy over
gRPC using the **xDS** APIs: LDS (listeners), RDS (routes), CDS (clusters), EDS
(endpoints), SDS (secrets, i.e. certificates). ADS multiplexes them on one stream so
updates arrive in a safe order. When a pod starts, the control plane pushes a new EDS
update and Envoy adds the endpoint in place; nothing restarts and no connection is
touched. Istio's `istiod`, Envoy Gateway and custom control planes built on
`go-control-plane` all speak xDS. (Envoy also supports a *hot restart* for binary
upgrades, handing over listening sockets to a new process.)

A minimal static configuration (what a control plane would otherwise push):

```yaml
static_resources:
  listeners:
    - name: ingress
      address:
        socket_address: { address: 0.0.0.0, port_value: 8080 }
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                route_config:
                  virtual_hosts:
                    - name: api
                      domains: ["*"]
                      routes:
                        - match: { prefix: "/" }
                          route:
                            cluster: orders
                            timeout: 3s
                            retry_policy:
                              retry_on: "5xx,reset,connect-failure"
                              num_retries: 1
                              per_try_timeout: 1s
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
  clusters:
    - name: orders
      type: STRICT_DNS
      lb_policy: LEAST_REQUEST
      load_assignment:
        cluster_name: orders
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address: { address: orders.internal, port_value: 3000 }
      circuit_breakers:
        thresholds:
          - max_connections: 1000
            max_pending_requests: 200
            max_requests: 1000
            max_retries: 3
      outlier_detection:
        consecutive_5xx: 5
        interval: 10s
        base_ejection_time: 30s
        max_ejection_percent: 50
```

### Circuit breaking versus outlier detection

The owner's description ("if this backend fails 5 times in a row, stop sending it
traffic for 30 seconds") is what Envoy calls **outlier detection**: per-endpoint
ejection based on observed errors (`consecutive_5xx: 5`, `base_ejection_time: 30s`;
the ejection time grows each time the same host is ejected again, and
`max_ejection_percent` stops Envoy from ejecting the whole cluster).

Envoy's **circuit breakers** are something else: per-cluster *concurrency caps*
(`max_connections`, `max_pending_requests`, `max_requests`, `max_retries`). When a cap is
hit, Envoy fails the request immediately with a 503 instead of queueing it. That
protects a struggling upstream from a pile-up and protects the caller from waiting.
`max_retries` works as a retry budget, so retries cannot multiply load during an outage
(a "retry storm"). The general patterns are in
[Application Resilience Patterns](../../interview-core/SystemDesign/building_blocks/12_application_resilience_patterns.md).

### What Envoy offers compared with Nginx open source

Retries with budgets, outlier detection, active health checks, zone-aware and
consistent-hash load balancing (ring hash, Maglev), traffic splitting by weight,
header-based routing, request mirroring, first-class gRPC and HTTP/2 upstreams, a global
rate limit service, external authorization, and very detailed statistics (the admin
endpoint on `:9901/stats`, Prometheus format at `/stats/prometheus`) plus
OpenTelemetry tracing. The price: verbose configuration that is meant to be generated by
a control plane, not written by hand.

## 7. HAProxy and Caddy

**HAProxy** is a load balancer first and a web server not at all. It is known for
throughput, low latency, rich health checking and observability, and is used both at
the edge and for TCP services such as database replica pools.

```text
global
    maxconn 50000

defaults
    mode http
    timeout connect 2s
    timeout client  30s
    timeout server  30s
    option httplog

frontend https_in
    bind :443 ssl crt /etc/haproxy/certs/api.pem alpn h2,http/1.1
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
    default_backend api

backend api
    balance leastconn
    option httpchk GET /healthz
    http-check expect status 200
    server app1 10.0.1.5:3000 check inter 2s fall 3 rise 2
    server app2 10.0.1.6:3000 check inter 2s fall 3 rise 2

listen postgres_replicas
    mode tcp
    bind :5433
    balance roundrobin
    server r1 10.0.2.11:5432 check
    server r2 10.0.2.12:5432 check
```

**Stick tables** (in-memory per-key counters) give per-IP rate limiting and abuse
detection; the **runtime API** (a Unix socket) can drain, disable or re-weight servers
without a reload; `mode tcp` handles any TCP protocol.

**Caddy** is a Go web server whose defining feature is automatic HTTPS: it obtains and
renews certificates via ACME with no configuration. A complete reverse proxy with a real
certificate is two lines (`api.example.com { reverse_proxy 10.0.1.5:3000 10.0.1.6:3000 }`).
Good for small deployments and internal tools. **Traefik** fills a similar niche and
discovers routes from Docker labels and Kubernetes resources.

## 8. The Kubernetes edge: Ingress and the Gateway API

Inside Kubernetes you rarely run a hand-configured Nginx. Instead a **controller**
watches Kubernetes resources and configures a proxy for you.

- **Ingress** (`networking.k8s.io/v1`) is the original API: host and path rules to
  Services. Anything beyond that (timeouts, rewrites, rate limits) is expressed in
  controller-specific annotations, which do not port between controllers. The API is
  frozen: still supported, no new features.
- The community **ingress-nginx** controller, long the most common one, was retired in
  March 2026 after its maintainers announced in November 2025 that it would receive only
  best-effort fixes until then. (NGINX Inc.'s separate NGINX Ingress Controller and
  NGINX Gateway Fabric are different projects.) Clusters still on it should migrate.
- The **Gateway API** (`gateway.networking.k8s.io/v1`, GA since October 2023) is the
  successor: role-oriented resources (`GatewayClass` for the infrastructure provider,
  `Gateway` for the platform team's listeners and certificates, `HTTPRoute` /
  `GRPCRoute` for application teams), with weights, header matching, mirroring and
  timeouts in the core spec. Implementations include Envoy Gateway, Istio, Cilium,
  NGINX Gateway Fabric, Kong, Traefik, HAProxy and the cloud providers' controllers. It
  is also how service meshes are configured for east-west traffic (the GAMMA initiative,
  [Service Mesh (Istio / Linkerd)](12_service_mesh.md)).

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: orders
  namespace: shop
spec:
  parentRefs:
    - name: public-gateway
      namespace: infra
  hostnames: ["api.example.com"]
  rules:
    - matches:
        - path: { type: PathPrefix, value: /orders }
      timeouts:
        request: 10s
      backendRefs:
        - name: orders-v1
          port: 8080
          weight: 90
        - name: orders-v2
          port: 8080
          weight: 10
```

## 9. Which proxy goes where

```arch
%% caption: A common layout: a cloud L4 load balancer at the edge, an L7 gateway tier for TLS and routing, and sidecar or node proxies for service-to-service traffic.
grid 170x100
node int "Internet" at 1.5,0 icon=internet
node edge "L4 load balancer" at 1.5,1 icon=lb sub="NLB / HAProxy tcp"
node gw "L7 gateway" at 1.5,2 icon=gateway sub="Nginx / Envoy Gateway"
group mesh "Kubernetes cluster" color=slate icon=k8s style=dashed
node e1 "Envoy sidecar" at 0,3 in mesh icon=envoy
node e2 "Envoy sidecar" at 3,3 in mesh icon=envoy
node app1 "Service A" at 0,4 in mesh icon=app
node app2 "Service B" at 3,4 in mesh icon=app
int -> edge
edge -> gw : "TCP :443"
gw -> e1:T : "HTTP"
gw -> e2:T : "HTTP"
e1 -> app1 : "localhost"
e2 -> app2 : "localhost"
e1:R <-> e2:L : "mTLS"
```

| | Nginx | Envoy | HAProxy | Caddy |
|---|---|---|---|---|
| Sweet spot | web server + reverse proxy, static files, classic edge | dynamic microservice data plane, mesh, gateways | high-performance L4/L7 load balancing | small sites, automatic HTTPS |
| Configuration | files, reload | xDS API from a control plane (or static YAML) | files, reload, runtime API | Caddyfile / JSON API |
| Active health checks | NGINX Plus only | yes | yes | yes |
| Retries / outlier ejection | basic `proxy_next_upstream`, passive `max_fails` | rich, with budgets and ejection | yes (`retry-on`, `observe`) | basic |
| Serves static files | excellent | not its job | no | yes |
| Observability | access logs, stub_status (more in Plus) | very detailed stats, tracing | detailed stats page, logs | logs, metrics |

## 10. Reading proxy errors in production

When a proxy is in the path, the status code tells you *where* the failure is:

| Code | Nginx meaning | Usual cause | First check |
|---|---|---|---|
| **502 Bad Gateway** | the upstream sent an invalid response or closed the connection | app crashed or restarted mid-request; the app closed an idle keepalive connection just as the proxy reused it | app logs and restarts; make the app's keepalive idle timeout **longer** than the proxy's |
| **503 Service Unavailable** | no upstream available, or a limit hit | all servers marked failed; `limit_req` with the default status; Envoy circuit breaker overflow | upstream health, `max_fails`, breaker stats |
| **504 Gateway Timeout** | upstream did not answer within `proxy_read_timeout` | slow query, overloaded app, deadlock | app latency, DB; do not just raise the timeout |
| **413** | body larger than `client_max_body_size` | uploads | raise per location, or upload directly to object storage |
| **499** (Nginx log only) | client closed the connection before the response | client timeout shorter than server latency, users giving up | compare client and server timeouts |
| **400 / 431** | header too large | huge cookies or JWTs | `large_client_header_buffers` |

The 502-on-reused-connection race is worth remembering: Node.js's default
`keepAliveTimeout` is 5 s, Nginx keeps idle upstream connections for 60 s
(`keepalive_timeout` in the upstream block). The app closes an idle socket at 5 s, and a
request that Nginx sends on it at the same moment gets a reset, surfacing as a sporadic
502. Set the upstream timeout below the app's, or the app's above the proxy's.

Timeouts must also shrink as you go inward: if the client gives up after 30 s, the
gateway after 29 s and the app's database call after 25 s, each layer returns a useful
error before its caller stops listening. When they are inverted, work continues after
nobody is waiting for it.

## Common interview questions

**What is the difference between a forward proxy and a reverse proxy?**
A forward proxy acts for clients (outbound, hides clients from servers); a reverse
proxy acts for servers (inbound, hides and load-balances backends, terminates TLS).

**Why put Nginx in front of a Python or Java app server?**
It buffers slow clients so app workers are not tied up, terminates TLS, serves static
files efficiently, load-balances and health-checks backends, and enforces size, rate and
connection limits.

**L4 versus L7 load balancing?**
L4 forwards TCP/UDP connections by address and port, fast and protocol-agnostic, no
visibility into requests. L7 parses HTTP, so it can route by path or header, retry, rate
limit per user and terminate TLS, at more CPU per request. Note that L4 balances
*connections*: with long-lived HTTP/2 or gRPC connections, all requests on one connection
go to one backend, which is why gRPC often needs L7 balancing.

**How does Nginx handle 10,000 concurrent connections with a few processes?**
An event loop per worker on epoll: non-blocking sockets, the kernel reports which are
ready, and one thread services all of them. Memory per idle connection is small, unlike
a thread per connection.

**Does `nginx -s reload` drop connections?**
No. New workers start with the new config; old workers finish in-flight requests and
exit. Frequent reloads cost memory (old workers linger with long connections) and reset
upstream keepalive pools, which is why fast-changing environments prefer xDS-driven
proxies.

**Why does Envoy fit Kubernetes better than a file-configured proxy?**
Its configuration arrives over the xDS gRPC APIs from a control plane and is applied in
place: endpoint changes, new routes and new certificates without restarts. It also has
retries with budgets, outlier detection, circuit breakers and detailed telemetry built
in.

**What is the difference between circuit breaking and outlier detection in Envoy?**
Circuit breakers cap concurrent connections, pending requests, requests and retries to
a cluster and fail fast when exceeded. Outlier detection ejects individual endpoints that
return consecutive errors for a growing ejection period.

**You see sporadic 502s after enabling upstream keepalive. Why?**
The app closes idle keepalive connections sooner than the proxy expects; the proxy
sends a request on a socket the app is closing. Make the app's idle timeout longer than
the proxy's upstream idle timeout.

**Ingress versus Gateway API?**
Ingress is a minimal, frozen API extended through non-portable annotations. The Gateway
API is its role-oriented successor with traffic splitting, header matching and timeouts
in the spec and wide implementation support; it also configures mesh traffic.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | What a reverse proxy is, forward vs reverse, why TLS terminates at the edge, and how to read an access log line. |
| Junior (L3) | Software Engineer I | L3 | Write an Nginx server block with `proxy_pass`, forwarded headers and TLS; know `nginx -t` and reload; know what 502, 503 and 504 point to. |
| Mid (L4) | Software Engineer II | L4 | Configure upstream keepalive, timeouts, rate limits and caching; explain `location` matching and the `proxy_pass` slash; choose LB algorithms; debug keepalive-race 502s. |
| Senior (L5) | Senior Software Engineer | L5 | Design the edge tier (L4 vs L7, TLS, HTTP/2 and gRPC balancing, global rate limiting), configure Envoy retries, budgets, breakers and outlier detection, and set a coherent timeout chain. |
| Staff+ (L6+) | Staff / Principal Engineer | L6+ | Own the traffic architecture: gateway and mesh choice, Ingress to Gateway API migration, certificate automation at scale, DDoS layering with CDNs, and the failure behaviour of the whole request path. |

## Interview checklist

- [ ] I can explain forward vs reverse proxy and list what a reverse proxy does for an app.
- [ ] I can explain L4 vs L7 load balancing and why long-lived gRPC connections need L7.
- [ ] I can describe Nginx's master/worker event-loop model and what a reload does.
- [ ] I can write a proxy config with upstream keepalive, forwarded headers, timeouts and limited retries.
- [ ] I can explain Nginx `location` matching order and the `proxy_pass` trailing-slash rule.
- [ ] I can configure `limit_req` with burst/nodelay and explain why it is per instance.
- [ ] I can explain passive vs active health checks.
- [ ] I can explain Envoy listeners, routes, clusters and xDS, and circuit breakers vs outlier detection.
- [ ] I can map 502/503/504/499/413 to root causes, including the keepalive race.
- [ ] I can explain Ingress vs Gateway API and the ingress-nginx retirement.

Related: [Scaling and Load Balancing](../../interview-core/SystemDesign/building_blocks/13_scaling_and_load_balancing.md) (algorithms and
autoscaling), [Application Resilience Patterns](../../interview-core/SystemDesign/building_blocks/12_application_resilience_patterns.md)
(timeouts, retries, breakers), [HTTP & Web Foundations](../../data-and-apis/API/Fundamentals/02_http_and_web_foundations.md)
(HTTP and TLS), [Service Mesh (Istio / Linkerd)](12_service_mesh.md) (Envoy as a sidecar), [Kubernetes and Orchestration](02_kubernetes_and_helm.md).
