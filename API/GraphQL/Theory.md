---
title: "GraphQL Theory"
description: "Master GraphQL: schema (SDL), queries, mutations, subscriptions, variables, fragments, resolvers, N+1 and DataLoader, errors, pagination, security, federation, with Python and Go examples."
---

# GraphQL Theory

<div data-viz="api-graphql"></div>

## What is GraphQL?
GraphQL is a query language for APIs that solves the over-fetching and under-fetching problems of <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>. Clients send a query to a single endpoint (`/graphql`) explicitly defining the shape of the data they want.

It was built at Facebook (2012, open-sourced 2015) because the mobile news feed needed data from many sources in one round trip over slow networks. It is defined by a **specification**, not a library; Apollo, Strawberry, gqlgen, graphql-go, and others implement it.

### <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> vs GraphQL
*   **Over-fetching (<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>):** You hit `/users/1` and get back the user's name, email, address, phone number, and history, even though you only wanted to render their name on the UI.
*   **Under-fetching (<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>):** You want a user's name and their top 5 recent posts. You have to hit `/users/1` and then `/users/1/posts`, requiring multiple network roundtrips.
*   **GraphQL Solution:** You send a single query to a single endpoint (`/graphql`), explicitly defining the shape of the data you want.

> **Key idea:** In <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> the **server** decides the shape of the response. In GraphQL the **client** decides. The server only decides what is *possible* (the schema).

## The Core Components
1.  **Schema:** A strongly-typed definition of all possible data and operations.
2.  **Query:** A read-only operation requested by the client.
3.  **Mutation:** A write operation (Create, Update, Delete) requested by the client.
4.  **Subscription:** A long-lived operation; the server pushes results when events happen (usually over WebSockets).
5.  **Resolver:** The backend function that actually fetches the data for a specific field in the schema.

## The Type System (SDL)

The schema is written in the **Schema Definition Language**. It is the contract, and it is both documentation and validator.

```graphql
# Scalars: Int, Float, String, Boolean, ID   (plus custom ones like DateTime)

enum Role { ADMIN  EDITOR  READER }

interface Node { id: ID! }                       # a shared shape

type User implements Node {
  id: ID!                                        # ! = non-null
  name: String!
  email: String
  role: Role!
  posts(first: Int = 10, after: String): PostConnection!   # fields can take arguments
}

type Post implements Node {
  id: ID!
  title: String!
  body: String!
  author: User!
  tags: [String!]!                               # non-null list of non-null strings
  publishedAt: String
}

union SearchResult = User | Post                 # "one of these types"

type PostConnection {                            # pagination wrapper (see "Pagination: Connections")
  edges: [PostEdge!]!
  pageInfo: PageInfo!
}
type PostEdge { cursor: String!  node: Post! }
type PageInfo { hasNextPage: Boolean!  endCursor: String }

input CreatePostInput {                          # input types are for arguments only
  title: String!
  body: String!
  tags: [String!]
}

type Query {
  me: User
  post(id: ID!): Post
  posts(first: Int = 10, after: String): PostConnection!
  search(text: String!): [SearchResult!]!
}

type Mutation {
  createPost(input: CreatePostInput!): Post!
  deletePost(id: ID!): Boolean!
}

type Subscription {
  postCreated: Post!
}
```

Reading the modifiers:

| Notation | Meaning |
| :--- | :--- |
| `String` | Nullable string (may be `null`) |
| `String!` | Never null |
| `[String]` | Nullable list of nullable strings |
| `[String!]!` | Non-null list of non-null strings (the usual choice) |

> ⚠️ **Nullability is a design decision.** If a `String!` field's resolver fails, GraphQL sets that field to null, sees the violation, and **nulls the nearest nullable parent**. Overusing `!` on fields that can fail turns a small error into a big hole in the response.

## Operations by Example

### Query: ask for exactly what you need

```graphql
query GetPost {
  post(id: "10") {
    title
    author { name }
    tags
  }
}
```

```json
{ "data": { "post": { "title": "Hello", "author": { "name": "Ana" }, "tags": ["intro"] } } }
```

The response mirrors the query. No extra fields, no missing fields.

### Variables: never build queries with string concatenation

```graphql
query GetPost($id: ID!, $withAuthor: Boolean = true) {
  post(id: $id) {
    title
    author @include(if: $withAuthor) { name }
  }
}
```

Sent over <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> as **one <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> body**:

```http
POST /graphql HTTP/1.1
Content-Type: application/json

{
  "query": "query GetPost($id: ID!, $withAuthor: Boolean = true) { post(id: $id) { title author @include(if: $withAuthor) { name } } }",
  "variables": { "id": "10", "withAuthor": false },
  "operationName": "GetPost"
}
```

Variables keep the query text constant (cacheable, allow-listable) and prevent injection.

### Aliases and fragments

```graphql
query Compare {
  first:  post(id: "10") { ...PostCard }       # alias: same field twice, different args
  second: post(id: "11") { ...PostCard }
}

fragment PostCard on Post {                    # reusable field selection
  id
  title
  author { name }
}
```

### Directives

`@include(if:)` and `@skip(if:)` toggle fields; `@deprecated(reason:)` in the schema marks fields clients should stop using (this is how GraphQL evolves without version numbers).

### Mutation: changing data

```graphql
mutation Create($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title                  # ask for the new state in the same round trip
  }
}
```

Rule: top-level **query** fields may run in parallel; top-level **mutation** fields run **one after another** in the order written.

### Subscription: server push

```graphql
subscription { postCreated { id title } }
```

The client opens a WebSocket (the `graphql-transport-ws` protocol), and the server sends a message each time a post is created. See `WebSockets/`.

### Introspection: the <abbr title="Application Programming Interface">API</abbr> describes itself

```graphql
{ __schema { types { name kind } } }
{ __type(name: "Post") { fields { name type { name } } } }
```

This powers GraphiQL/Playground, autocomplete, and client code generation. Disable it in production for private APIs if you do not want to advertise your schema.

## How a Query Executes

```arch
%% caption: A query is parsed and validated first; only a valid query walks the resolver tree.
grid 220x80
node a "HTTP POST /graphql" at 0,0 shape=pill color=slate
node b "Parse" at 0,1 sub="text into an AST"
node c "Validate against schema" at 0,2 color=amber sub="unknown field? wrong type?"
node e1 "Return errors" at 1,2 color=red sub="no resolver runs"
node d "Execute" at 0,3 sub="walk the tree from the root"
group res "Resolvers" color=blue icon=tree
node r1 "Query.post resolver" at 0,4 in res color=blue
node r2 "Post.author resolver" at 0,5 in res color=blue
node r3 "User.name" at 0,6 in res color=blue sub="default resolver reads the property"
node f "Assemble JSON" at 0,7 shape=pill color=green sub="in the shape of the query"
a -> b -> c
c -> e1 : "invalid"
c -> d : "valid"
d -> r1 -> r2 -> r3 -> f
```

A **resolver** has the signature `(parent, args, context, info)`. Each field of each type may have one. If you do not write one, the default resolver reads `parent.fieldName`. Only the fields the client asked for run, and that is where the efficiency comes from.

### Python (Strawberry)

```python
import strawberry

@strawberry.type
class Author:
    id: int
    name: str

@strawberry.type
class Post:
    id: int
    title: str
    author_id: strawberry.Private[int]          # internal, not exposed in the schema

    @strawberry.field
    def author(self) -> Author:                 # resolver: runs only if the query asks for `author`
        return Author(id=self.author_id, name=AUTHORS[self.author_id])

@strawberry.type
class Query:
    @strawberry.field
    def post(self, id: int) -> Post | None:
        p = POSTS.get(id)
        return Post(**p) if p else None

schema = strawberry.Schema(Query)
```

Serve it with `from strawberry.asgi import GraphQL; app = GraphQL(schema)` and run under `uvicorn`.

### Go (graphql-go)

```go
authorType := graphql.NewObject(graphql.ObjectConfig{
	Name: "Author",
	Fields: graphql.Fields{
		"id":   &graphql.Field{Type: graphql.Int},
		"name": &graphql.Field{Type: graphql.String},
	},
})
postType := graphql.NewObject(graphql.ObjectConfig{
	Name: "Post",
	Fields: graphql.Fields{
		"title": &graphql.Field{Type: graphql.String},
		"author": &graphql.Field{
			Type: authorType,
			Resolve: func(p graphql.ResolveParams) (any, error) { // runs once per Post
				return authors[p.Source.(Post).AuthorID], nil
			},
		},
	},
})
query := graphql.NewObject(graphql.ObjectConfig{
	Name: "Query",
	Fields: graphql.Fields{
		"posts": &graphql.Field{
			Type:    graphql.NewList(postType),
			Resolve: func(graphql.ResolveParams) (any, error) { return posts, nil },
		},
	},
})
schema, _ := graphql.NewSchema(graphql.SchemaConfig{Query: query})
res := graphql.Do(graphql.Params{Schema: schema, RequestString: `{ posts { title author { name } } }`})
// {"data":{"posts":[{"author":{"name":"Ana"},"title":"Hello"}, ...]}}
```

Go also has **gqlgen** (schema-first: you write SDL, it generates typed resolvers) which is the common production choice; the labs use graphql-go because it needs no code generation step, and every concept transfers directly.

## The N+1 Problem and DataLoader

The classic trap. Query: 100 posts, each with its author.

```
resolver posts        -> 1 query:  SELECT * FROM posts LIMIT 100
resolver Post.author  -> runs 100 times: SELECT * FROM users WHERE id = ?     <- 100 queries!
Total: 1 + N = 101 queries
```

**DataLoader** collects every `.load(key)` made during one tick of the event loop, then calls one batch function.

```arch
node r "Resolvers (x100)" at 0,0 icon=server color=blue
node l "DataLoader" at 1,0 icon=process color=teal
node db "Database" at 2,0 icon=db color=purple

r -> l : "load(1)"
r -> l : "load(2)"
r -> l : "load(1)"

node dedup "dedupe keys + batch" at 1,1 shape=card color=amber
l -> dedup -> l

l -> db : "SELECT WHERE id IN (1,2)"
db -> l : "2 rows"

node order "results in SAME ORDER as keys" at 0.5,1 shape=text
l -> order -> r
```

```python
from strawberry.dataloader import DataLoader

async def load_authors(keys: list[int]) -> list[Author]:
    rows = await db.fetch("SELECT * FROM users WHERE id = ANY($1)", keys)   # ONE query
    by_id = {r["id"]: Author(**r) for r in rows}
    return [by_id[k] for k in keys]          # must return one result per key, in key order

# create the loader PER REQUEST (it caches; sharing it would leak data between users)
context = {"author_loader": DataLoader(load_fn=load_authors)}

@strawberry.field
async def author(self, info: strawberry.Info) -> Author:
    return await info.context["author_loader"].load(self.author_id)
```

Result for three posts by two authors: **1 batched call** instead of 3. Python lab 3 (`labs/python/03_dataloader_n_plus_1.py`) counts the queries and Go lab 3 (`labs/golang/03_dataloader_batching`) builds the loader from scratch.

> ⚠️ **The two DataLoader rules:** (1) the batch function must return results in the **same order and count** as the keys; (2) create loaders **per request**, never globally.

## Errors: <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> 200 Does Not Mean Success

GraphQL responses always have a `data` and/or an `errors` key. Errors are **field-level and partial**.

```json
{
  "data": { "post": null },
  "errors": [{
    "message": "Post 99 not found",
    "path": ["post"],
    "extensions": { "code": "NOT_FOUND" }
  }]
}
```

*   **Validation errors** (unknown field, wrong type) -> no `data`, request rejected before execution.
*   **Resolver errors** -> partial `data` plus `errors` with the `path` of the failed field.
*   Transport failures (auth, rate limits, malformed <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>) may still use `401` / `429` / `400`.
*   Put a stable machine code in `extensions.code`; clients should not parse `message`.
*   For expected business failures consider **result types** rather than errors: `union CreatePostResult = Post | ValidationError`.

> ⚠️ Monitoring tip: because errors ride on `200`, ordinary <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> error-rate dashboards see nothing. Track `errors` per operation name.

## Pagination: Connections

The Relay convention, used by GitHub's <abbr title="Application Programming Interface">API</abbr> and many others:

```graphql
{
  posts(first: 2, after: "cursor-2") {
    edges { cursor node { id title } }
    pageInfo { hasNextPage endCursor }
  }
}
```

`edges` wrap each item with its cursor, `pageInfo` tells you whether to continue. Same cursor idea as <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> (see `Fundamentals/03_cross_cutting_concerns.md`).

## Security and Performance

Because the client controls the query, a malicious or careless client can ask for something ruinous:

```graphql
{ users { friends { friends { friends { friends { name } } } } } }   # exponential fan-out
```

| Defence | What it does |
| :--- | :--- |
| **Depth limit** | Reject queries nested deeper than N (e.g. 7) |
| **Complexity / cost analysis** | Assign a cost per field (`list x first`), reject above a budget |
| **Pagination limits** | Require `first`, cap it at 100 |
| **Timeouts** | Bound execution time |
| **Persisted queries** | Clients send a hash of a pre-registered query; the server refuses unknown ones. Best defence for first-party apps, and enables GET + <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> caching |
| **Auth in resolvers** | Authorise per field/object, not just per endpoint (BOLA applies here too) |
| **Disable introspection** in production for private APIs | Reduces reconnaissance |

## Caching: The Trade-Off

<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> gets <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> caching free because every resource has a URL and uses `GET`. GraphQL usually sends `POST /graphql`, so CDNs cannot cache by default. Options: persisted queries over `GET`, client-side normalised caches (Apollo, Relay cache by `__typename:id`), response caching per resolver, and `@cacheControl` hints.

## Schema Evolution Without Versions

*   **Add** fields and types freely; old clients never asked for them.
*   **Deprecate** with `@deprecated(reason: "Use fullName")`, track usage in your gateway, remove when usage is zero.
*   **Avoid** changing a field's type or nullability; that is a breaking change.

## Federation: One Graph, Many Teams

```arch
%% caption: Federation: one router composes a supergraph from subgraphs owned by different teams.
node c "Client" at 1,0 icon=client
node r "Router / Gateway" at 1,1 icon=gateway sub="supergraph"
group sg "Subgraphs" color=purple icon=graph
node u "Users subgraph" at 0,2 in sg icon=graphql
node p "Posts subgraph" at 1,2 in sg icon=graphql
node i "Inventory subgraph" at 2,2 in sg icon=graphql
c -> r
r -> u
r -> p
r -> i
```

Each team owns a **subgraph** that contributes types and fields; the router plans the query, calls the needed subgraphs, and merges results. Apollo Federation is the common standard. It is powerful but adds operational weight; do not start here.

## Real-World Scenario & Architecture

**Scenario:** A Blogging platform where a mobile app wants to fetch a post title and the author's name in one request.

```arch
node c "Client" at 0,0 icon=client color=slate
node gql "GraphQL Server" at 1,0 icon=server color=blue
node db "Databases" at 2,0 icon=db color=purple

c -> gql : "POST /graphql"
gql -> db : "Fetch Post 1"
gql -> db : "Fetch User (Author)"
gql -> c : "{ 'data': ... }"
```

## When to Use GraphQL (and When Not To)

| Use it when | Avoid it when |
| :--- | :--- |
| Many clients (web, iOS, Android, TV) need different slices of the same data | A simple <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> <abbr title="Application Programming Interface">API</abbr> with one client |
| Screens need nested data from several services | Public <abbr title="Application Programming Interface">API</abbr> where <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> caching and simple `curl` access matter |
| Frontend teams iterate faster than backend teams can ship endpoints | File uploads and streaming binary data are central |
| You want a typed, self-documenting contract | Service-to-service calls between backends (prefer <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>) |

## Common Pitfalls

1.  **N+1 queries** because resolvers hit the database one by one. Use DataLoader.
2.  **No depth/complexity limits.**
3.  **A global DataLoader** that caches across users.
4.  **Exposing the database schema 1:1** as the GraphQL schema.
5.  **Making everything non-null**, so one failure blanks large parts of the response.
6.  **Treating mutations as <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr>** (`updateUser`) instead of intent (`changeEmail`, `suspendUser`).
7.  **Ignoring auth inside resolvers.**

## Check Yourself

> ❓ **Question 1:** A GraphQL request fails one field but returns <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> 200. How does the client know, and why is this designed so?
>
> ❓ **Question 2:** 50 posts each ask for their author and your logs show 51 <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> queries. Diagnose it and fix it.
>
> ❓ **Question 3:** Why do query fields run in parallel but mutation fields run serially?
>
> ❓ **Question 4:** How do you remove a field with no `/v2`?

**Answers**

1.  Read the `errors` array (with `path`). GraphQL returns partial data when part of the graph succeeds, so a single failing field does not discard everything else.
2.  N+1: one query for posts plus one `Post.author` query per post. Add a per-request DataLoader keyed by author id, so all lookups become one `IN` query.
3.  Reads have no side effects so order does not matter. Writes may depend on each other (`createUser` then `createProfile`), so their order must be deterministic.
4.  Mark it `@deprecated`, monitor field usage, notify clients, and delete only when usage reaches zero.

## Hands-On Labs

Every lab is one file that runs on its own and prints what happens. Labs 1-2 teach the basics; labs 3-5 are the production topics. **Python and Go cover different ground**, so do both.

Run from the `API/` folder (Python: `pip install -r requirements.txt` first).

| # | Python (`GraphQL/labs/python/`) | You learn |
| :---: | :--- | :--- |
| 1 | `01_schema_queries_variables.py` | Schema as SDL, arguments, variables, aliases, fragments, `@include`, introspection, nullable vs non-null failures |
| 2 | `02_mutations_and_input_validation.py` | Input types, unions for expected errors, serial execution of mutations |
| 3 | `03_dataloader_n_plus_1.py` | 51 queries becoming 2, the two DataLoader rules, why a shared loader leaks stale data |
| 4 | `04_auth_permissions_and_masking.py` | Context from <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> headers, permission classes, field- and object-level rules (BOLA), error masking, disabling introspection |
| 5 | `05_subscriptions_over_websocket.py` | Async-generator subscriptions, the `graphql-transport-ws` messages on the wire, cleanup on disconnect |

| # | Go (`GraphQL/labs/golang/`) | You learn |
| :---: | :--- | :--- |
| 1 | `01_schema_and_resolvers` | graphql-go schema in code, `ResolveParams`, enums, `NonNull`, partial results |
| 2 | `02_http_handler_and_variables` | The <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> request shape, `operationName`, status-code contract, safe `GET`, context into resolvers |
| 3 | `03_dataloader_batching` | A generic `Loader[K, V]` built from scratch using graphql-go thunks |
| 4 | `04_relay_pagination` | Connections, opaque cursors, keyset stability, guard rails |
| 5 | `05_depth_cost_limits_persisted_queries` | <abbr title="Abstract Syntax Tree. A tree representation of the abstract syntactic structure of source code written in a programming language.">AST</abbr>-based depth and cost limits, persisted queries and APQ |

```bash
python GraphQL/labs/python/03_dataloader_n_plus_1.py
go run ./GraphQL/labs/golang/05_depth_cost_limits_persisted_queries
```

## Exercises

1.  Write SDL for a movie database (`Movie`, `Actor`, `Review`) with a Relay-style `movies(first, after)`.
2.  Add a depth limit (see Go lab 5) to the Strawberry schema in Python lab 1 using `strawberry.extensions.QueryDepthLimiter`.
3.  Add a `Post.comments` field to Python lab 3 and make it a second DataLoader (one-to-many: the batch function returns a *list* per key).
4.  Take Go lab 2's handler and make it reject any query whose cost (Go lab 5) is over budget.
5.  Wrap two <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> endpoints of your choice behind a GraphQL schema (a "backend for frontend").

## Where To Go Next

*   **Related:** `WebSockets/` (the transport under subscriptions), `REST/` (compare trade-offs), `gRPC/` (typed service-to-service calls).
*   **Shared toolbox:** `Fundamentals/03_cross_cutting_concerns.md` and `Fundamentals/04_choosing_the_right_api.md`.
