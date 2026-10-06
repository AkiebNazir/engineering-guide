# API Module

Learn the six API styles (REST, GraphQL, gRPC + Protobuf, WebSockets, Webhooks, SOAP) from theory to
runnable, self-checking code, in both **Python** and **Go**, plus the two things that sit around every
one of them: the **API gateway** in front, and **observability** (OpenTelemetry tracing, metrics, SLOs).

## Layout

```
content/data-and-apis/API/
  Fundamentals/          shared knowledge, read first (01-05)
  <Type>/
    Theory.md            EVERYTHING about that API type: concepts, wire format, diagrams, security,
                         pitfalls, check-yourself questions, and a table of the labs
    Foundation/
      python/            14 levels, 00-13: one small runnable file per idea
      golang/            14 levels, 00-13 (each in its own folder: NN_name/main.go)
    labs/
      python/            5-7 labs: 01-02 basics, the rest advanced (exact counts in the table below)
      golang/            5-8 labs, different topics from Python (each in its own folder: NN_name/main.go)
  Gateway/               Theory.md, labs/ (3 Python + 3 Go), configs/ (envoy.yaml, kong.yaml: the labs as real config)
  Observability/         Theory.md, labs/ (2 Python + 2 Go), no backend needed (in-memory exporters)
  go.mod                 one Go module for every Go lab (module dsapractice/api)
  requirements.txt       Python packages for every Python lab
  _archive/              the previous guides and examples, kept for reference (safe to delete)
```

Types: `REST`, `GraphQL`, `Protobuf`, `gRPC`, `WebSockets`, `Webhooks`, `SOAP`. Around them: `Gateway`, `Observability`.

## Recommended order

1. `Fundamentals/01` to `05`
2. `REST` -> `GraphQL` -> `Protobuf` -> `gRPC` -> `WebSockets` -> `Webhooks` -> `SOAP`
3. For each type: read `Theory.md`, climb the `Foundation/` ladder, then do the labs in order (Python and Go teach **different** things).
4. `Gateway` -> `Observability`: the infrastructure every style runs behind.

## Running the labs

```bash
cd content/data-and-apis/API
pip install -r requirements.txt            # Python labs (Python 3.11+)
python REST/labs/python/03_jwt_auth_and_scopes.py

go run ./REST/labs/golang/04_rate_limit_middleware      # Go labs (Go 1.25+; the go tool fetches it)
go run ./Protobuf/Foundation/golang/13_bonus_decode_wire_format_by_hand
python Observability/labs/python/01_otel_tracing_and_metrics_through_an_api.py
go run -race ./WebSockets/labs/golang/03_hub_pattern_chat
```

## Conventions every lab follows

- **Self-contained and self-checking.** A lab starts its own server on a free port (port `0`), calls it,
  prints what happens, asserts the result and ends with `OK`. Labs that are natural to poke at with
  `curl` also accept `--serve` (Python) or `-serve` (Go).
- **The docstring / header comment is the lesson**: what you will learn, the picture, how to run it.
- **The tests prove the claim at runtime**: races are really raced, attacks are really attempted,
  benchmarks are really measured.
- **Go labs use the latest `net/http`**: Go 1.22+ `ServeMux` patterns (`"GET /users/{id}"`),
  `r.PathValue`, `http.MaxBytesReader`, `http.ResponseController`, `Server.Shutdown`.
- **Generated code is checked in** (Protobuf and gRPC stubs). Regenerate with
  `Protobuf/labs/generate.sh` and `gRPC/labs/generate.sh`.

## Lab index

| Type | Labs (Py / Go) | Python | Go |
| :--- | :---: | :--- | :--- |
| **REST** | 6 / 8 | stdlib CRUD · FastAPI validation + OpenAPI · JWT + scopes + BOLA · ETag / `If-Match` · idempotency keys + cursor pagination · consumer-driven contracts (Pact) | `ServeMux` 1.22 patterns · strict JSON CRUD · middleware chain + graceful shutdown · token-bucket rate limiter · API-key auth + ownership · Gin CRUD · Echo CRUD · provider verification + can-i-deploy |
| **GraphQL** | 7 / 7 | schema + variables · mutations + union errors · DataLoader N+1 · auth + permissions + masking · subscriptions over WebSocket · operation contract testing · federation: subgraphs + router | graphql-go schema · HTTP handler + `operationName` · DataLoader from scratch · Relay pagination · depth/cost limits + persisted queries · operation manifests + schema checks · federation `_entities` by hand + query planning |
| **Protobuf** | 5 / 5 | wire format by hand · types, presence, oneof · schema evolution · size/speed vs JSON · framing + well-known types | marshal basics · oneof/maps/enums · protojson + Any + FieldMask · reflection + dynamicpb · delimited streams + benchmark |
| **gRPC** | 5 / 5 | unary + status + metadata · four streaming kinds · interceptors (auth, log, rate limit) · deadlines + retries · asyncio + client load balancing | rich errors + metadata · flow control + cancellation · interceptor chain + access policy · mTLS from scratch · health + reflection + graceful shutdown |
| **WebSockets** | 5 / 5 | handshake + frames by hand · chat rooms · auth + Origin + limits · heartbeats + back-pressure + flood control · reconnect + resume | server from scratch (Hijack) · coder/websocket JSON RPC · hub pattern chat · heartbeats + graceful close · pub/sub scaling + tickets |
| **Webhooks** | 5 / 5 | HMAC verification · signed sender · retries + DLQ · idempotent async receiver · Standard Webhooks + rotation | receiver + back-pressure · Stripe/GitHub/Slack schemes · delivery worker pool · SSRF-safe sender · breaker + replay + subscriptions |
| **SOAP** | 5 / 5 | envelope by hand · server + generated WSDL · zeep client · WS-Security UsernameToken · SOAP 1.1 vs 1.2 + mustUnderstand | `encoding/xml` envelopes · server with typed registry · resilient client · WS-Security in Go · WSDL-driven JSON gateway |
| **Gateway** | 3 / 3 | reverse proxy + routing + header hygiene · edge auth + rate limiting · load balancing, health, retries, overload | `httputil.ReverseProxy` done right · canary, sticky weights, mirroring, rollback · BFF aggregation, caching, coalescing |
| **Observability** | 2 / 2 | OpenTelemetry tracing + RED metrics through three services · trace context, baggage, head vs tail sampling | OTel middleware + `RoundTripper` + context rule · histograms, SLOs, burn-rate alerts |

Every one of the seven API styles also has a 14-level `Foundation/` ladder (00-13) in both languages.
