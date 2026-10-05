# net/http — HTTP clients and servers

`net/http` is Go's HTTP client and server in one package, and it's production-grade:
many Go services put `http.Server` directly on the network with no framework in front.
On the client side it gives you `http.Client` (policy: timeout, redirects, cookies) on top
of `http.Transport` (mechanism: connection pooling, keep-alives, TLS, HTTP/2). On the
server side it gives you the `http.Handler` interface, a router (`http.ServeMux`, which
since Go 1.22 matches methods and path wildcards), and `http.Server` with its timeouts
and graceful shutdown. `net/http/httptest` runs real servers on a free loopback port,
or calls handlers with no socket at all, which is how every level here runs without
fixed ports or outside network access.

## When to reach for it vs alternatives already in this repo

- Calling an HTTP API → one shared `*http.Client` with a `Timeout`, requests built with
  `http.NewRequestWithContext` (levels 3, 4, 9). Never `http.Get` in long-running code:
  it uses `http.DefaultClient`, which has no timeout.
- Serving HTTP → `http.Server{...}` with at least `ReadHeaderTimeout` set, a
  `http.ServeMux` with `"GET /items/{id}"`-style patterns, and middleware as
  `func(http.Handler) http.Handler` (levels 2, 5, 7). A third-party router is only needed
  for things like regex constraints or route groups.
- Many requests to the same host from many goroutines → tune the `Transport`
  (`MaxIdleConnsPerHost`), and always drain and close response bodies (level 6).
- JSON request/response bodies → pair with `encoding/json` streaming
  (`json.NewDecoder(r.Body)`), capped with `http.MaxBytesReader` (level 8, and
  `../09_encoding_json`).
- Timeouts and cancellation that span several calls → `context` (level 4); the deep dive
  is `../../GoEngineering/32_context_and_timeouts_deep_dive`.
- Custom dialers, raw TCP, DNS and connection-level tricks → `net`, covered in
  `../../GoEngineering/34_network_programming_custom_dialers`.
- A whole production service (config, logging, metrics, graceful shutdown wired together)
  → `../../GoEngineering/01_rest_api_service` and `25_production_service_capstone`.
  REST design itself (status codes, idempotency, versioning) is in `../../API/REST`.

## Client vs Transport vs Server: who owns what

| Type | Owns | Create |
|---|---|---|
| `http.Client` | Overall `Timeout`, redirect policy, cookie jar | Once per process (or per upstream), shared by all goroutines |
| `http.Transport` | The connection pool, keep-alives, dial/TLS/response-header timeouts, HTTP/2 | Once, inside the client. A new Transport per request means a new pool per request: no reuse at all |
| `http.Server` | Listener, `ReadHeaderTimeout`/`ReadTimeout`/`WriteTimeout`/`IdleTimeout`, `Shutdown` | Once per listening address |
| `http.Handler` | What happens for one request | `http.HandlerFunc(fn)` or a type with `ServeHTTP` |

## Gotchas

| Gotcha | Detail |
|---|---|
| `http.DefaultClient` (and `http.Get`/`http.Post`) has no timeout | `Timeout: 0` means wait forever once connected. A stuck upstream pins your goroutines: level 9 shows 20 calls still blocked after a second, goroutines 2 → 102. Use your own `&http.Client{Timeout: ...}`. |
| A non-2xx status is not an error | `client.Do` returns `err == nil` for a 404 or 500. Check `resp.StatusCode`. Level 4. |
| An unread, closed body kills the connection | Keep-alive reuse happens only if the body was read to EOF before `Close`. Level 6 measured 1 connection for 300 requests when draining, 300 when not. `io.Copy(io.Discard, resp.Body)` before `Close`. |
| Forgetting `resp.Body.Close()` leaks | The connection and its read goroutine stay allocated until the body is closed. `defer resp.Body.Close()` right after the error check. |
| `MaxIdleConnsPerHost` defaults to 2 | 50 concurrent requests to one host keep only 2 idle connections afterwards; the rest are closed and re-dialled next time. Level 6 measured 934 new connections vs 50 with `MaxIdleConnsPerHost: 50`. |
| `http.ListenAndServe` sets no server timeouts | A client that sends headers slowly holds a connection forever (slowloris). Always set `ReadHeaderTimeout`. Level 7. |
| `WriteTimeout` also bounds your handler | It runs from the end of reading the request headers to the end of writing the response, so a slow handler or a long streaming response is cut off. Size it for your slowest endpoint, or use `http.ResponseController` to extend it per request. |
| `Shutdown` doesn't close hijacked or long-lived connections | It stops the listener, closes idle connections and waits for active ones. WebSockets and SSE need their own shutdown signal (`Server.RegisterOnShutdown`). Brand-new connections that haven't sent a request are waited for up to 5 seconds (level 10's comment). |
| `ListenAndServe` returns `http.ErrServerClosed` after `Shutdown` | That's the normal exit. Treat any *other* error as fatal. |
| `WriteHeader` after writing the body is ignored | The first `Write` sends a 200 implicitly. Set headers, then `WriteHeader`, then write the body. Headers set after that are silently dropped. |
| Request bodies are unbounded by default | Wrap them in `http.MaxBytesReader` before decoding. Level 8. |
| Retrying non-idempotent requests | A `POST` that timed out may have succeeded on the server. Retry only `GET`/`PUT`/`DELETE` (or requests carrying an idempotency key). Level 10. |

## What the 10 levels cover

Level 1 is a handler, an `httptest` server and one `GET`, closing the body. Level 2
routes with Go 1.22+ `ServeMux` patterns: methods, `{id}` wildcards and `PathValue`,
`{path...}`, `{$}`, precedence, automatic 405s and conflict detection. Level 3 builds
client requests properly: `NewRequestWithContext`, `url.Values`, headers, a JSON body,
one shared client. Level 4 triggers each kind of client failure (404 as a non-error,
connection refused, `Client.Timeout`, context deadline, cancellation) and tells them
apart with `errors.Is`/`errors.As`. Level 5 writes middleware: request IDs through the
context, a status-recording `ResponseWriter` wrapper for logging, and panic recovery.
Level 6 measures connection reuse by counting new TCP connections on the server:
drained vs undrained bodies, `DisableKeepAlives`, and `MaxIdleConnsPerHost` under
concurrent bursts. Level 7 shows a slowloris connection held open by a server without
timeouts and closed by `ReadHeaderTimeout`, then a graceful `Shutdown` that lets an
in-flight request finish. Level 8 is interop with `encoding/json` and `errors`: a strict
JSON endpoint with `MaxBytesReader`, `DisallowUnknownFields` and proper 400/413/415/422
responses, tested with `httptest.NewRecorder`. Level 9 is the production trap:
`http.DefaultClient` hanging on a stuck upstream, fixed with a client timeout. Level 10
is a capstone key/value service with a tuned, retrying client, ending in a clean
shutdown.
