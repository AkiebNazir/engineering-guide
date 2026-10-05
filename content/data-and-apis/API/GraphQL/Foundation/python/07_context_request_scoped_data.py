"""
FOUNDATION LEVEL 07 - Context: handing request-scoped data to every resolver
================================================================================
A resolver deep in the tree often needs something that belongs to the REQUEST,
not to the schema: who is calling, a request id for logs, the open database
connection, the loaded config. You cannot pass it as a field argument - it is
not the client's business, and you would have to thread it through every
level. You must not put it in a global - two requests running at once would
overwrite each other.

The answer is the CONTEXT: one object built per execution, handed to the
engine, and made available to every resolver at every depth, untouched. In
strawberry you receive it as `info.context` by declaring an
`info: strawberry.Info` parameter; the Go equivalent is the standard
`context.Context` on `p.Context`. Same idea, same lifetime: created when the
request arrives, discarded when the response is sent.

This is the mechanism levels 08, 09 and 10 are built on: middleware writes
into the context, resolvers read from it. Learn it here, in isolation, with
nothing else going on.

You will learn
  * how to build a context per execution and pass it to the engine
  * how to read it from a resolver (`info.context`) at any depth
  * that the context is per-request: two concurrent executions never see
    each other's values - proven below with real threads
  * what belongs in it (request id, caller identity, db handle, loaders) and
    what does not (anything the client should be sending as an argument)
  * that `info` also carries the field's own path and selected sub-fields

Run it   python 07_context_request_scoped_data.py
"""
import json
import logging
import threading

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

# Every resolver that reads the context appends what it saw here, so the demo
# can prove which execution's value each resolver got.
seen: list[tuple[str, str]] = []


@strawberry.type
class Trace:
    @strawberry.field
    def request_id(self, info: strawberry.Info) -> str:
        # Two levels down from the root, and the context is exactly the same
        # object the top-level resolver saw. Nobody passed it along by hand.
        seen.append(("trace.requestId", info.context["request_id"]))
        return info.context["request_id"]

    @strawberry.field
    def path(self, info: strawberry.Info) -> str:
        # `info` carries more than the context: this is where the engine is
        # currently working in the response tree.
        return ".".join(str(p) for p in info.path.as_list())


@strawberry.type
class Query:
    @strawberry.field
    def whoami(self, info: strawberry.Info) -> str:
        # The caller identity was put here by whoever built the context - the
        # HTTP layer in a real service (level 11). The resolver just reads it.
        return info.context["caller"]

    @strawberry.field
    def request_id(self, info: strawberry.Info) -> str:
        seen.append(("requestId", info.context["request_id"]))
        return info.context["request_id"]

    @strawberry.field
    def trace(self) -> Trace:
        return Trace()

    @strawberry.field
    def db_rows(self, info: strawberry.Info) -> int:
        # A stand-in for the real reason context exists: shared, expensive,
        # per-request resources. Opening a connection per resolver would be a bug.
        return info.context["db"]["rows"]


schema = strawberry.Schema(Query)


def build_context(request_id: str, caller: str) -> dict:
    """Called ONCE per incoming request. In level 11 this runs inside the HTTP
    handler, reading the request id and the Authorization header off the wire."""
    return {"request_id": request_id, "caller": caller, "db": {"rows": 42}}


def run(title: str, query: str, context: dict):
    result = schema.execute_sync(query, context_value=context)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message, "path": e.path} for e in result.errors]
    print(f"\n# {title}")
    print(f"context  : {json.dumps({k: v for k, v in context.items() if k != 'db'})}")
    print(f"query    : {' '.join(query.split())}")
    print(f"response : {json.dumps(payload)}")
    return result


if __name__ == "__main__":
    # Note: `requestId` is NOT an argument the client supplies. It is not in
    # the query at all as input - it comes from beside the query.
    r = run("1. a resolver reading a value the client never sent",
            "{ requestId whoami }", build_context("req-001", "alice"))
    assert r.data == {"requestId": "req-001", "whoami": "alice"}

    r = run("2. the same context, seen identically two levels down",
            "{ requestId trace { requestId path } }", build_context("req-002", "alice"))
    assert r.data["requestId"] == "req-002"
    assert r.data["trace"]["requestId"] == "req-002"
    assert r.data["trace"]["path"] == "trace.path"
    print("   -> no plumbing: the nested resolver did not receive it from its parent")

    r = run("3. a shared per-request resource (a fake db handle) instead of a value",
            "{ dbRows }", build_context("req-003", "bob"))
    assert r.data == {"dbRows": 42}

    # The point of per-request scope: run two executions at the same time, in
    # different threads, and neither sees the other's request id. A global
    # variable could not do this.
    seen.clear()
    results: dict[str, object] = {}

    def execute_in_thread(rid: str) -> None:
        res = schema.execute_sync("{ requestId trace { requestId } }",
                                  context_value=build_context(rid, "concurrent"))
        results[rid] = res.data

    threads = [threading.Thread(target=execute_in_thread, args=(f"req-{i}",)) for i in (10, 11, 12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("\n# 4. three executions at once, in three threads")
    for rid, data in sorted(results.items()):
        print(f"  {rid} -> {json.dumps(data)}")
        assert data == {"requestId": rid, "trace": {"requestId": rid}}
    print("   -> every resolver saw its OWN request's context. This is why it is not a global.")

    # Nothing leaked across threads: each pair of observations agrees.
    assert len(seen) == 6
    assert all(value in results for _, value in seen)

    print("\nOK")
