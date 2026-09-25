# net/http — HTTP client and server

`net/http` provides HTTP client and server implementations. It is one of the most widely used packages in the Go standard library, powering everything from simple scrapers to high-throughput microservices.

## When to reach for it vs alternatives already in this repo

- Making HTTP requests → `http.Get`, `http.Post`, or creating an `http.Client` with custom transport.
- Serving HTTP traffic → `http.ListenAndServe`, `http.Server`, and `http.Handler`.
- Connection pooling & timeouts → `http.Transport` and `http.Client.Timeout`.
- Context cancellation → `http.NewRequestWithContext` to tie requests to `context.Context` (see `../GoEngineering` topics).

## Gotchas

| Gotcha | Detail |
|---|---|
| Unbounded default client | The default `http.DefaultClient` has NO timeout. A slow server can hang your goroutine forever. Always set a `Timeout` on custom `http.Client`s. |
| Forgetting to close the body | If you don't `defer resp.Body.Close()`, the underlying TCP connection cannot be reused or freed, leading to connection leaks. |
| Forgetting to read the body | You must read the response body (at least `io.Copy(io.Discard, resp.Body)`) before closing it to allow HTTP keep-alives to reuse the connection. |
| Transport pooling defaults | The default `http.Transport` pools connections. If you create a new `Transport` per request, you destroy connection pooling and exhaust ephemeral ports. |
| Server timeouts | `http.ListenAndServe` defaults to no timeouts (read, write, idle). Malicious or slow clients can tie up server resources. Use a custom `http.Server` struct to set `ReadTimeout`, `WriteTimeout`, and `IdleTimeout`. |

## What the 10 levels cover

Levels 1-3 cover basic client usage (Get, Post) and a basic `http.HandlerFunc` server. Level 4 introduces custom `http.Client` timeouts. Level 5 covers request customization (headers, methods) via `http.NewRequest`. Level 6 demonstrates connection pooling and connection leaks by failing to read/close the body. Level 7 sets up a robust `http.Server` with timeouts. Level 8 covers interop with `context` for request cancellation. Level 9 shows the `Transport` connection pooling gotcha. Level 10 is a capstone: a robust HTTP proxy/client-server pair with timeouts, context cancellation, and proper resource management.
