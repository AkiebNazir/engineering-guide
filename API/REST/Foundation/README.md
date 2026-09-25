# REST Foundation - ground zero to a complete, secured CRUD <abbr title="Application Programming Interface">API</abbr>

This is the on-ramp *before* `../Theory.md` and `../labs/`. Each level is a
tiny, self-contained, runnable file in **both** `python/` and `golang/` -
same lesson, same demo shape, two languages side by side. Every file prints
`OK` when it passes its own built-in checks.

Run any Python level:  `python REST/Foundation/python/00_single_endpoint_and_how_it_works.py`
Run any Go level:      `go run ./REST/Foundation/golang/00_single_endpoint_and_how_it_works`

| # | Level | The one new idea |
|---|---|---|
| 00 | Single endpoint, explained end to end | What "a basic REST <abbr title="Application Programming Interface">API</abbr> endpoint" actually is: one route, one canned response, the full request/response loop |
| 01 | Routing: paths and methods | Decide what to do based on path + verb; 404 / 405 |
| 02 | JSON in and out | Encode/decode structured data instead of plain text |
| 03 | Path parameters | `/books/{id}` - a variable segment inside the URL |
| 04 | Query parameters | `/books?author=...` - filtering a collection, not identifying one resource |
| 05 | Request body + validation | Read POST/PUT bodies; reject bad input with 400, never crash |
| 06 | Status codes + CRUD verbs | The full deliberate vocabulary: POST/GET/PUT/DELETE, 201+Location, 204, idempotent DELETE |
| 07 | Headers deep dive | Content negotiation (Accept), custom headers, ETag/If-None-Match -> 304 |
| 08 | Middleware | Wrapping a handler instead of editing it: logging + panic recovery, chained in order |
| 09 | Authentication | "Who is this?" - bearer tokens, 401 Unauthorized, attaching the identity to the request |
| 10 | Authorization | "What are they allowed to do?" - role checks on top of authentication, 403 Forbidden |
| 11 | Complete, protected CRUD | Everything above, combined: public reads, authenticated writes, admin-only delete |
| 12 | Being a client | Calling an <abbr title="Application Programming Interface">API</abbr> instead of serving one: timeouts, retries, exponential backoff |
| 13 | Bonus: raw HTTP over TCP | Optional deep dive - what a framework is actually doing for you underneath (read any time after level 00) |

**Where to go next:** level 11 is the same shape as `../labs/python/01_crud_stdlib.py`
and `../labs/golang/01_servemux_basics` / `02_json_crud_validation` - once
level 11 feels easy, `../labs/` (real JWTs, OpenAPI validation, rate limiting,
cursor pagination, Gin/Echo frameworks) is the very next step, not a jump.
`../Theory.md` covers the *why* (REST's constraints, resource design,
HATEOAS, caching) behind everything these files do in code.
