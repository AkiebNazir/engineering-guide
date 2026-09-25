# API Module

Learn the six <abbr title="Application Programming Interface">API</abbr> styles (<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>, GraphQL, <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> + Protobuf, WebSockets, Webhooks, <abbr title="Simple Object Access Protocol - A messaging protocol specification for exchanging structured information in the implementation of web services.">SOAP</abbr>) from theory to
runnable, self-checking code, in both **Python** and **Go**.

## Layout

```
API/
  Fundamentals/          shared knowledge, read first (01-04)
  <Type>/
    Theory.md            EVERYTHING about that API type: concepts, wire format, diagrams, security,
                         pitfalls, check-yourself questions, and a table of the labs
    labs/
      python/            5 labs:  01-02 basics,  03-05 advanced
      golang/            5 labs:  01-02 basics,  03-05 advanced   (each in its own folder: NN_name/main.go)
  go.mod                 one Go module for every Go lab (module dsapractice/api)
  requirements.txt       Python packages for every Python lab
  _archive/              the previous guides and examples, kept for reference (safe to delete)
```

Types: `REST`, `GraphQL`, `Protobuf`, `gRPC`, `WebSockets`, `Webhooks`, `SOAP`.

## Recommended order

1. `Fundamentals/01` to `04`
2. `REST` -> `GraphQL` -> `Protobuf` -> `gRPC` -> `WebSockets` -> `Webhooks` -> `SOAP`
3. For each type: read `Theory.md`, then do the labs in order (Python and Go teach **different** things).

## Running the labs

```bash
cd API
pip install -r requirements.txt            # Python labs (Python 3.11+)
python REST/labs/python/03_jwt_auth_and_scopes.py

go run ./REST/labs/golang/04_rate_limit_middleware      # Go labs (Go 1.25+; the go tool fetches it)
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
- **Generated code is checked in** (Protobuf and <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> stubs). Regenerate with
  `Protobuf/labs/generate.sh` and `gRPC/labs/generate.sh`.

## Lab index

| Type | Python | Go |
| :--- | :--- | :--- |
| **<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>** | stdlib <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> · FastAPI validation + OpenAPI · <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> + scopes + BOLA · ETag / `If-Match` · idempotency keys + cursor pagination | `ServeMux` 1.22 patterns · strict <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> · middleware chain + graceful shutdown · token-bucket rate limiter · <abbr title="Application Programming Interface">API</abbr>-key auth + ownership |
| **GraphQL** | schema + variables · mutations + union errors · DataLoader N+1 · auth + permissions + masking · subscriptions over WebSocket | graphql-go schema · <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> handler + `operationName` · DataLoader from scratch · Relay pagination · depth/cost limits + persisted queries |
| **Protobuf** | wire format by hand · types, presence, oneof · schema evolution · size/speed vs <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> · framing + well-known types | marshal basics · oneof/maps/enums · protojson + Any + FieldMask · reflection + dynamicpb · delimited streams + benchmark |
| **<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>** | unary + status + metadata · four streaming kinds · interceptors (auth, log, rate limit) · deadlines + retries · asyncio + client load balancing | rich errors + metadata · flow control + cancellation · interceptor chain + access policy · mTLS from scratch · health + reflection + graceful shutdown |
| **WebSockets** | handshake + frames by hand · chat rooms · auth + Origin + limits · heartbeats + back-pressure + flood control · reconnect + resume | server from scratch (Hijack) · coder/websocket <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> · hub pattern chat · heartbeats + graceful close · pub/sub scaling + tickets |
| **Webhooks** | HMAC verification · signed sender · retries + DLQ · idempotent async receiver · Standard Webhooks + rotation | receiver + back-pressure · Stripe/GitHub/Slack schemes · delivery worker pool · SSRF-safe sender · breaker + replay + subscriptions |
| **<abbr title="Simple Object Access Protocol - A messaging protocol specification for exchanging structured information in the implementation of web services.">SOAP</abbr>** | envelope by hand · server + generated WSDL · zeep client · WS-Security UsernameToken · <abbr title="Simple Object Access Protocol - A messaging protocol specification for exchanging structured information in the implementation of web services.">SOAP</abbr> 1.1 vs 1.2 + mustUnderstand | `encoding/xml` envelopes · server with typed registry · resilient client · WS-Security in Go · WSDL-driven <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> gateway |
