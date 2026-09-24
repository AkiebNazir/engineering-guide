"""
FOUNDATION LEVEL 12 - Being the client: calling a GraphQL endpoint by hand
==============================================================================
Levels 00-11 were all SERVER code. You will spend at least as much time on the
other side: calling someone else's GraphQL API. This level flips the lens. The
server here is a stripped-down copy of level 11 (deliberately made flaky), and
the interesting code is the CLIENT.

No client library is used, on purpose. There is nothing to install: a GraphQL
request is one HTTP POST with a JSON body you can build in four lines.

    {"query": "query Q($id: ID!) { ... }", "variables": {"id": "r1"}}

The GraphQL-specific trap for clients, and the main reason this level exists:
**HTTP 200 does not mean success.** A field can fail while the transport
worked perfectly (level 06), so every response needs TWO checks - the status
code, and then `errors`. And the two failure kinds want opposite handling:
  - HTTP 5xx / connection refused / timeout -> transient. Retry with backoff.
  - HTTP 200 with `errors` -> the server understood you and says no (bad
    query, blank title, FORBIDDEN). Retrying is pointless, and for a mutation
    it can be actively harmful.

You will learn
  * how to build a `{query, variables}` POST body and a Bearer header by hand
  * to check the status code AND `errors` - never just one of them
  * exponential backoff for genuinely transient failures, and a retry budget
  * why a `data`-less 200 must NOT be retried, though a 503 should be
  * that partial data (`data` and `errors` together) is a normal thing a
    client has to decide about, not a bug

Run it   python 12_being_a_client.py
"""
import json
import logging
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import strawberry
from graphql import GraphQLError

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

TOKENS = {"alice-token": {"user": "alice", "role": "admin"}}
attempts = {"count": 0}


# ---- "someone else's API": a small, deliberately flaky level-11 endpoint ----
@strawberry.type
class Report:
    id: strawberry.ID
    title: str


@strawberry.type
class Query:
    @strawberry.field
    def report(self, id: strawberry.ID) -> Report | None:
        return Report(id=id, title="Q1 uptime") if str(id) == "r1" else None

    @strawberry.field
    def me(self, info: strawberry.Info) -> str | None:
        user = info.context.get("user")
        if user is None:
            raise GraphQLError("not authenticated", extensions={"code": "UNAUTHENTICATED"})
        return user["user"]


schema = strawberry.Schema(Query)


class FlakyGraphQLHandler(BaseHTTPRequestHandler):
    """Answers POST /graphql, but 503s the first two calls - a real service
    warming up, briefly overloaded, or mid-deploy. Not actually broken."""

    def do_POST(self):
        attempts["count"] += 1
        if attempts["count"] <= 2:
            self.reply(503, {"errors": [{"message": "temporarily unavailable"}]})
            return

        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        request = json.loads(raw or b"{}")
        header = self.headers.get("Authorization", "")
        user = TOKENS.get(header.removeprefix("Bearer ")) if header.startswith("Bearer ") else None
        result = schema.execute_sync(request.get("query", ""),
                                     variable_values=request.get("variables"),
                                     context_value={"user": user})
        payload = {"data": result.data}
        if result.errors:
            payload["errors"] = [{"message": e.message, "path": e.path, "extensions": e.extensions}
                                 for e in result.errors]
        self.reply(200, payload)  # 200 even when `errors` is populated

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


# ---- THE CLIENT: this is the part worth reading ---------------------------
class GraphQLError200(Exception):
    """The server answered 200 and said no. Not retryable."""

    def __init__(self, errors: list[dict], data):
        super().__init__("; ".join(e.get("message", "?") for e in errors))
        self.errors, self.data = errors, data


def graphql_post(url: str, query: str, variables: dict | None = None, token: str | None = None,
                 timeout: float = 2.0) -> tuple[int, dict]:
    """One attempt. Builds the request by hand - this is the entire protocol."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")   # level 09, from the client's side
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        # urllib raises on any non-2xx. That is a urllib quirk, not HTTP's rule.
        return e.code, json.loads(e.read() or b"{}")


def graphql_call(url: str, query: str, variables: dict | None = None, token: str | None = None,
                 max_attempts: int = 5, allow_partial: bool = False):
    """Call a GraphQL endpoint properly: retry transport failures, never retry
    a GraphQL error, and return `data` only once it is trustworthy."""
    for attempt in range(1, max_attempts + 1):
        try:
            status, payload = graphql_post(url, query, variables, token)
        except (urllib.error.URLError, TimeoutError) as exc:
            # The server did not answer at all - retryable, same as a 5xx.
            if attempt == max_attempts:
                raise
            wait = 0.05 * 2 ** (attempt - 1)
            print(f"  attempt {attempt}: no answer ({exc}), backing off {wait:.2f}s")
            time.sleep(wait)
            continue

        if status >= 500:
            # TRANSIENT: the server is having a bad moment, not refusing us.
            if attempt == max_attempts:
                raise RuntimeError(f"giving up after {attempt} attempts, last status {status}")
            wait = 0.05 * 2 ** (attempt - 1)      # 0.05s, 0.1s, 0.2s, 0.4s ...
            print(f"  attempt {attempt}: HTTP {status}, backing off {wait:.2f}s before retrying")
            time.sleep(wait)
            continue

        if status != 200:
            # 400/404/405: our request is malformed. It will be next time too.
            raise RuntimeError(f"HTTP {status}: {payload}")

        # HTTP 200 - the transport is done, now READ THE BODY. This check is
        # the one people forget, and the whole reason this level exists.
        errors = payload.get("errors")
        if errors and not (allow_partial and payload.get("data")):
            raise GraphQLError200(errors, payload.get("data"))
        return payload.get("data"), errors or []

    raise RuntimeError("unreachable")


REPORT_QUERY = """
query GetReport($id: ID!) {
  report(id: $id) { id title }
}
"""


def demo(url: str) -> None:
    print("# 1. the first two calls fail with 503 - the client retries, backing off")
    data, errors = graphql_call(url, REPORT_QUERY, {"id": "r1"})
    print(f"   -> data: {json.dumps(data)}")
    assert data == {"report": {"id": "r1", "title": "Q1 uptime"}} and not errors
    assert attempts["count"] == 3, "expected exactly 2 transient failures then a success"
    print("   -> succeeded on attempt 3. A client that gave up after one 503 would have failed.")

    print("\n# 2. a GraphQL error arrives as HTTP 200 - and must NOT be retried")
    before = attempts["count"]
    try:
        graphql_call(url, "{ me }")
        raise AssertionError("expected the call to raise")
    except GraphQLError200 as e:
        print(f"   -> HTTP 200, errors: {json.dumps(e.errors)}")
        assert e.errors[0]["extensions"]["code"] == "UNAUTHENTICATED"
    assert attempts["count"] == before + 1, "exactly ONE attempt: retrying would be pointless"
    print("   -> one attempt only. The server understood us; a second identical ask changes nothing.")

    print("\n# 3. the same query WITH the Authorization header")
    data, errors = graphql_call(url, "{ me }", token="alice-token")
    print(f"   -> data: {json.dumps(data)}")
    assert data == {"me": "alice"}

    print("\n# 4. a null result is a legitimate answer, not a failure")
    data, errors = graphql_call(url, REPORT_QUERY, {"id": "does-not-exist"})
    print(f"   -> data: {json.dumps(data)}")
    assert data == {"report": None} and not errors

    print("\n# 5. partial data: the caller decides whether it is usable")
    data, errors = graphql_call(url, "{ report(id: \"r1\") { title } me }", allow_partial=True)
    print(f"   -> data: {json.dumps(data)}")
    print(f"   -> errors: {json.dumps(errors)}")
    assert data["report"] == {"title": "Q1 uptime"} and data["me"] is None and errors
    print("   -> with allow_partial=False this same response would have raised. Both are valid")
    print("      policies - what is NOT valid is ignoring `errors` and using `data` blindly.")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), FlakyGraphQLHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/graphql")
    server.shutdown()
