# <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> Foundation - ground zero to a complete, secured <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> service

This is the on-ramp *before* `../Theory.md` and `../labs/`. Each level is a
tiny, self-contained, runnable file in **both** `python/` and `golang/` -
same lesson, same demo shape, two languages side by side. Every file prints
`OK` when it passes its own built-in checks.

Every level that needs a contract owns its **own** small `.proto` in `proto/`,
so no level depends on another level's types. The generated stubs are committed,
so the levels run straight out of a fresh clone.

Run any Python level:  `python gRPC/Foundation/python/00_single_unary_rpc_end_to_end.py`
Run any Go level:      `go run ./gRPC/Foundation/golang/00_single_unary_rpc_end_to_end`
Regenerate the stubs:  `./gRPC/Foundation/generate.sh`  (only needed if you EDIT a `.proto`)

| # | Level | The one new idea |
|---|---|---|
| 00 | Single unary <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr>, explained end to end | What "a basic <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> endpoint" actually is: one `.proto`, generated stubs, one server, one client call - <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>'s request/response loop with a strict binary contract instead of a URL+<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> convention |
| 01 | The `.proto` contract | The contract-first workflow: edit the `.proto`, regenerate, *then* write code; field numbers are the wire identity |
| 02 | Unary request and response fields | The generated types *are* the "<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> in / <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> out" step - typed fields, zero values, no parsing |
| 03 | Server-streaming <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> | One request, many responses: `stream` on the return type, and `yield` / `Send` |
| 04 | Client-streaming <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> | Many requests, one response: `stream` on the request, half-close, one answer at the end |
| 05 | Bidirectional streaming | Both directions stream independently - the fourth and last <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> shape |
| 06 | Status codes | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>'s deliberate error vocabulary, mapped against <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>'s <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> codes, and which codes are retryable |
| 07 | Metadata | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>'s headers: request metadata in, initial and *trailing* metadata out - things <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/1.1 cannot do |
| 08 | Middleware = **interceptors** | Wrapping every <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> instead of editing handlers: logging + panic recovery, chained, with order mattering |
| 09 | Authentication | "Who is this?" - a token read from metadata in an interceptor; missing or invalid -> `UNAUTHENTICATED` |
| 10 | Authorization | "What may they do?" - a role check in a *second* interceptor layered on 09; wrong role -> `PERMISSION_DENIED` |
| 11 | Complete, protected service | Everything above, combined: a public read <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr>, an authenticated write, an admin-only delete |
| 12 | Being a client | Calling a service instead of serving one: deadlines on every call, and retrying `UNAVAILABLE` with exponential backoff |
| 13 | Bonus: generated code and raw wire bytes | Optional deep dive - what protoc actually emitted, and level 00's message hand-decoded with no protobuf library (read any time after level 00) |

**Where to go next:** level 11 is the same shape as
`../labs/golang/03_interceptor_chain` and
`../labs/python/03_interceptors_auth_logging_ratelimit.py` - once level 11 feels
easy, `../labs/` (rich `errdetails` error payloads, mTLS service identity,
streaming flow control and cancellation, deadline propagation across hops,
health checking, server reflection, graceful shutdown, asyncio servers and
client-side load balancing) is the very next step, not a jump.
`../Theory.md` covers the *why* (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/2 framing, the four <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> shapes, channel
and connection management, when <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> beats <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> and when it does not) behind
everything these files do in code. For the other half of the story - the
message and wire format itself, rather than the <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> layer built on top of it -
read `../../Protobuf/Foundation`, which is what level 13 is a one-page preview of.
