# GraphQL Foundation - ground zero to a complete, secured GraphQL endpoint

This is the on-ramp *before* `../Theory.md` and `../labs/`. Each level is a
tiny, self-contained, runnable file in **both** `python/` and `golang/` -
same lesson, same demo shape, two languages side by side. Every file prints
`OK` when it passes its own built-in checks.

Levels 00-10 call the schema **directly, in this process** - no <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> server,
no port, no curl - so you study GraphQL itself without transport noise in the
way. Level 11 puts the same schema behind a real `POST /graphql` endpoint,
level 12 calls one, and the bonus level 13 does it with nothing but a <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr>
socket, to prove GraphQL has no special wire format at all.

Run any Python level:  `python GraphQL/Foundation/python/00_single_field_and_how_it_works.py`
Run any Go level:      `go run ./GraphQL/Foundation/golang/00_single_field_and_how_it_works`

| # | Level | The one new idea |
|---|---|---|
| 00 | Single field, explained end to end | What "a basic GraphQL endpoint" actually is: a schema, a resolver, a query, and `{data, errors}` |
| 01 | Multiple fields + scalar types | The client picks which fields it wants; unrequested resolvers never run. Int/Float/String/Boolean/ID, and `!` |
| 02 | Field arguments | A field as a function: typed arguments the engine validates before your resolver runs |
| 03 | Variables | The same query text reused with different values - cacheable, escape-free, the shape a real client posts |
| 04 | Nested object types | The resolver chain: one resolver's return value becomes the next resolver's parent |
| 05 | Mutations + input validation | Writes live on `Mutation` and run serially; schema validation vs your own business rules |
| 06 | Errors + partial responses | `data` AND `errors` in one response; error `path`; how `!` makes a null propagate to the parent |
| 07 | Context | Request-scoped data (request id, caller, db handle) reaching every resolver at any depth, per request |
| 08 | Middleware | Wrapping execution instead of editing it: logging + panic recovery, chained, and why order matters |
| 09 | Authentication | "Who is this?" - bearer tokens resolved into the context, `extensions.code = UNAUTHENTICATED` (the 401) |
| 10 | Authorization | "What may they do?" - a role check on one mutation, `FORBIDDEN` (the 403), kept distinct from 401 |
| 11 | Complete, protected endpoint | Everything above behind a real `POST /graphql`: public query, authenticated mutation, admin-only mutation |
| 12 | Being a client | Calling a GraphQL <abbr title="Application Programming Interface">API</abbr> by hand: `{query, variables}` + Bearer header, retry a 503, never retry a 200 |
| 13 | Bonus: raw <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> over <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> | Optional deep dive - a GraphQL request typed byte by byte over a socket (read any time after level 11) |

**Where to go next:** level 11 is the same shape as
`../labs/python/01_schema_queries_variables.py` and
`../labs/golang/02_http_handler_and_variables` - once level 11 feels easy,
`../labs/` is the very next step, not a jump: it picks up exactly where
Foundation stops, with dataloaders and the N+1 problem, Relay cursor
pagination, depth/complexity limits, persisted queries, field-level
permissions and masking, and subscriptions over WebSockets.
`../Theory.md` covers the *why* (schema design, nullability as a contract,
the single-endpoint trade-off, caching without <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> verbs, federation)
behind everything these files do in code.
