"""
FOUNDATION LEVEL 11 - CAPSTONE: the whole thing, behind one real HTTP endpoint
=================================================================================
No new GraphQL ideas here. This is levels 00-10 assembled - schema, arguments,
variables, nested types, a mutation, partial errors, context, middleware,
authentication, authorization - plus the one piece that was deliberately
missing all along: a real network endpoint in front of the engine.

That piece is smaller than you expect, which is the last lesson of Foundation:

    ONE url            POST /graphql            (no route per resource)
    ONE method         POST                     (no verb vocabulary)
    request body       {"query": "...", "variables": {...}}
    response body      {"data": ..., "errors": [...]}
    status             200, even when `errors` is populated

Everything a REST API expresses in URLs and status codes, GraphQL expresses
inside that one body. The HTTP layer here has one job: turn bytes into
`{query, variables}`, build the context from the request (crucially, the
`Authorization` header), call the engine, write JSON back. It contains no
business logic at all - and level 13 shows those bytes with nothing but a
TCP socket, to prove there is no magic left.

Status codes that DO still apply, because they are about the transport rather
than the query: 404 for the wrong path, 405 for the wrong method, 400 for a
body that is not even JSON. Once the body parses, GraphQL takes over.

You will learn
  * the exact HTTP contract of a GraphQL endpoint - all four lines of it
  * where the context comes from in a real request (headers, not thin air)
  * that authentication/authorization live in the schema, not in the router
  * why a field-level failure is still HTTP 200, and what that means for clients
  * that this file is a complete, protected, real GraphQL service in ~200 lines

Run it        python 11_complete_graphql_endpoint.py
Keep serving  python 11_complete_graphql_endpoint.py --serve   (curl -s localhost:8080/graphql -H 'Authorization: Bearer alice-token' -d '{"query":"{ reports { id title } }"}')
"""
import json
import logging
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import strawberry
from graphql import GraphQLError

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

REPORTS: dict[str, dict] = {
    "r1": {"id": "r1", "title": "Q1 uptime", "owner": "alice"},
    "r2": {"id": "r2", "title": "Q2 uptime", "owner": "bob"},
}
next_id = {"n": 3}


# ---- the two checks from levels 09 and 10, unchanged ----------------------
def authenticate(info: strawberry.Info) -> dict:
    user = info.context.get("user")
    if user is None:
        raise GraphQLError("not authenticated", extensions={"code": "UNAUTHENTICATED"})
    return user


def require_role(info: strawberry.Info, role: str) -> dict:
    user = authenticate(info)
    if user["role"] != role:
        raise GraphQLError(f"forbidden: this operation requires the '{role}' role",
                           extensions={"code": "FORBIDDEN", "requiredRole": role})
    return user


# ---- the schema: levels 01-06 --------------------------------------------
@strawberry.type
class Owner:
    name: str
    role: str


@strawberry.type
class Report:
    id: strawberry.ID
    title: str
    owner_name: strawberry.Private[str]

    @strawberry.field
    def owner(self) -> Owner:  # level 04's resolver chain
        return Owner(name=self.owner_name, role=TOKENS.get(f"{self.owner_name}-token", {}).get("role", "unknown"))


def to_report(row: dict) -> Report:
    return Report(id=strawberry.ID(row["id"]), title=row["title"], owner_name=row["owner"])


@strawberry.input
class NewReport:
    title: str


@strawberry.type
class Query:
    @strawberry.field
    def reports(self) -> list[Report]:
        """Public: no token needed (level 09 - the check is per field)."""
        return [to_report(r) for r in REPORTS.values()]

    @strawberry.field
    def report(self, id: strawberry.ID) -> Report | None:
        row = REPORTS.get(str(id))
        return to_report(row) if row else None

    @strawberry.field
    def me(self, info: strawberry.Info) -> str | None:
        user = authenticate(info)
        return f"{user['user']} ({user['role']})"

    @strawberry.field
    def request_id(self, info: strawberry.Info) -> str:
        """Level 07: comes from the context, which the HTTP layer built."""
        return info.context["request_id"]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_report(self, info: strawberry.Info, input: NewReport) -> Report | None:
        user = authenticate(info)                       # level 09
        title = input.title.strip()
        if not title:                                   # level 05's business rule
            raise GraphQLError("title must not be blank", extensions={"code": "BAD_USER_INPUT"})
        rid = f"r{next_id['n']}"
        next_id["n"] += 1
        REPORTS[rid] = {"id": rid, "title": title, "owner": user["user"]}
        return to_report(REPORTS[rid])

    @strawberry.mutation
    def delete_report(self, info: strawberry.Info, id: strawberry.ID) -> bool | None:
        require_role(info, "admin")                     # level 10
        return REPORTS.pop(str(id), None) is not None


schema = strawberry.Schema(Query, Mutation)


# ---- the HTTP layer: the only genuinely new code in this file -------------
class GraphQLHandler(BaseHTTPRequestHandler):
    server_version = "foundation-graphql/1.0"

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Transport-level failures still deserve real status codes: this one
        # is not about the query, it is about the request never reaching it.
        self.send_json(405, {"errors": [{"message": "use POST /graphql"}]})

    def do_POST(self):
        if self.path != "/graphql":
            self.send_json(404, {"errors": [{"message": "no such endpoint"}]})
            return

        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        try:
            request = json.loads(raw or b"{}")
            query = request["query"]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not even a GraphQL request yet, so answer in HTTP's own terms.
            self.send_json(400, {"errors": [{"message": 'body must be JSON with a "query" key'}]})
            return

        # THE CONTEXT (level 07), built from this request and nothing else.
        # This is where the Authorization header (level 09) enters the schema.
        header = self.headers.get("Authorization", "")
        user = TOKENS.get(header.removeprefix("Bearer ")) if header.startswith("Bearer ") else None
        context = {"user": user, "request_id": f"req-{int(time.time() * 1000) % 100000}"}

        # Level 08's middleware, doing its two jobs around the engine.
        started = time.perf_counter()
        try:
            result = schema.execute_sync(query,
                                         variable_values=request.get("variables"),
                                         operation_name=request.get("operationName"),
                                         context_value=context)
            payload = {"data": result.data}
            if result.errors:
                payload["errors"] = [
                    {"message": e.message, "path": e.path, "extensions": e.extensions}
                    for e in result.errors
                ]
        except Exception as exc:  # our own bugs, never the client's problem to read
            print(f"  [recovery] {exc!r}")
            self.send_json(500, {"errors": [{"message": "internal server error"}]})
            return

        elapsed_ms = (time.perf_counter() - started) * 1000
        print(f"  [log] POST /graphql user={user['user'] if user else '-'} "
              f"errors={len(payload.get('errors', []))} {elapsed_ms:.1f}ms")

        # 200 even with errors: the transport succeeded, the message reports
        # what happened inside it. Clients MUST read `errors`, not the status.
        self.send_json(200, payload)

    def log_message(self, *args):
        pass


# ---- the client side of the demo ----------------------------------------
def post(base: str, query: str, variables: dict | None = None, token: str | None = None,
         path: str = "/graphql", method: str = "POST"):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(base + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def run(base: str, title: str, query: str, variables: dict | None = None, token: str | None = None,
        path: str = "/graphql", method: str = "POST"):
    print(f"\n# {title}")
    status, payload = post(base, query, variables, token, path, method)
    print(f"{method} {path} as {token or '<anonymous>'}")
    print(f"body     : {json.dumps({'query': ' '.join(query.split()), 'variables': variables})}")
    print(f"-> HTTP {status} {json.dumps(payload)}")
    return status, payload


def demo(base: str) -> None:
    status, payload = run(base, "1. a public query over real HTTP", "{ reports { id title owner { name role } } }")
    assert status == 200
    assert len(payload["data"]["reports"]) == 2
    assert payload["data"]["reports"][0]["owner"] == {"name": "alice", "role": "admin"}

    status, payload = run(base, "2. context built from the request: a server-side request id", "{ requestId }")
    assert status == 200 and payload["data"]["requestId"].startswith("req-")

    status, payload = run(base, "3. a protected field, anonymous -> HTTP 200 + UNAUTHENTICATED",
                          "{ reports { id } me }")
    assert status == 200, "the transport worked perfectly; only the field failed"
    assert payload["data"]["me"] is None and len(payload["data"]["reports"]) == 2
    assert payload["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    print("   -> a client checking only the status code would call this a success. Read `errors`.")

    status, payload = run(base, "4. the same query with a token", "{ me }", token="bob-token")
    assert payload["data"] == {"me": "bob (viewer)"}

    create = "mutation Create($input: NewReport!) { createReport(input: $input) { id title owner { name } } }"
    status, payload = run(base, "5. an authenticated mutation, as bob", create,
                          {"input": {"title": "Q3 uptime"}}, token="bob-token")
    assert payload["data"]["createReport"]["id"] == "r3"
    assert payload["data"]["createReport"]["owner"]["name"] == "bob"

    status, payload = run(base, "6. the same mutation with blank input -> BAD_USER_INPUT", create,
                          {"input": {"title": "   "}}, token="bob-token")
    assert payload["errors"][0]["extensions"]["code"] == "BAD_USER_INPUT"

    delete = "mutation Delete($id: ID!) { deleteReport(id: $id) }"
    status, payload = run(base, "7. an admin-only mutation, as bob (viewer) -> FORBIDDEN",
                          delete, {"id": "r1"}, token="bob-token")
    assert payload["errors"][0]["extensions"]["code"] == "FORBIDDEN"

    status, payload = run(base, "8. the same mutation as alice (admin) -> allowed",
                          delete, {"id": "r1"}, token="alice-token")
    assert payload["data"] == {"deleteReport": True}

    status, payload = run(base, "9. and the state changed", "{ reports { id title } }")
    assert [r["id"] for r in payload["data"]["reports"]] == ["r2", "r3"]

    # Transport-level failures: these are NOT GraphQL's business.
    status, payload = run(base, "10. wrong path -> a real 404 (not a GraphQL error)",
                          "{ reports { id } }", path="/api/reports")
    assert status == 404

    status, payload = run(base, "11. wrong method -> a real 405", "{ reports { id } }", method="GET")
    assert status == 405

    req = urllib.request.Request(f"{base}/graphql", data=b"this is not json", method="POST")
    try:
        urllib.request.urlopen(req)
        raise AssertionError("expected a 400")
    except urllib.error.HTTPError as e:
        print("\n# 12. a body that is not JSON -> a real 400")
        print(f"-> HTTP {e.code} {e.read().decode()}")
        assert e.code == 400
    print("   -> once the body parses, every other outcome is 200 + {data, errors}")

    print("\nOK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/graphql")
        print("""try: curl -s localhost:8080/graphql -d '{"query":"{ reports { id title } }"}'""")
        print("""     curl -s localhost:8080/graphql -H 'Authorization: Bearer alice-token' \\""")
        print("""       -d '{"query":"mutation($id:ID!){ deleteReport(id:$id) }","variables":{"id":"r1"}}'""")
        ThreadingHTTPServer(("127.0.0.1", 8080), GraphQLHandler).serve_forever()

    # port 0 = "operating system, hand me any free port", so this demo never
    # collides with anything already listening on 8080.
    server = ThreadingHTTPServer(("127.0.0.1", 0), GraphQLHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
