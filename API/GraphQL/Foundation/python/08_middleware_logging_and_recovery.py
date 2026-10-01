"""
FOUNDATION LEVEL 08 - Middleware: code that wraps every execution
=====================================================================
Levels 00-07 called `schema.execute_sync(...)` directly. Real services never
do: every request first passes through a stack of concerns that have nothing
to do with your schema - logging, timing, metrics, request ids, crash
recovery, and (next two levels) authentication and authorization.

A middleware is a WRAPPER: a function that takes "the thing that executes a
request" and returns a NEW thing with the same shape, which runs code before
and/or after calling the original. Because the shape is unchanged, wrappers
stack, and your schema never learns any of it exists.

    execute = with_logging(with_recovery(run_query))
              ^ outermost                ^ the real work

Note the two DIFFERENT safety nets in this file, because conflating them is
the classic confusion:
  1. the ENGINE's per-field net. A resolver that raises is caught by GraphQL
     itself and turned into an `errors[]` entry (level 06). Sibling fields
     still resolve. You get this for free.
  2. YOUR net, `with_recovery`. It catches bugs in the request-handling code
     AROUND execution - the parts GraphQL knows nothing about. Without it, a
     single malformed request can take the whole process down.

You will learn
  * a middleware has the same shape as what it wraps: request in, response out
  * chaining: wrapping a wrapper, in a chosen order
  * that a resolver blowing up is already contained by the engine - the query
    still returns a clean, partial answer and the process stays up
  * that a crash OUTSIDE execution needs your own recovery, or the process dies
  * that ORDER matters: with logging OUTSIDE recovery the crash is still
    logged; swap them and the log line silently disappears

Run it   python 08_middleware_logging_and_recovery.py
"""
import json
import logging
import time
from typing import Callable

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

# Middleware talks in whole requests and whole responses, not in fields.
Request = dict          # {"query": "...", "variables": {...}}
Response = dict         # {"data": ..., "errors": [...]}
Execute = Callable[[Request], Response]

log_lines: list[str] = []


@strawberry.type
class Query:
    @strawberry.field
    def healthy(self) -> bool:
        return True

    @strawberry.field
    def boom(self) -> str | None:
        # A real bug in a resolver: an unhandled exception, not a returned error.
        raise RuntimeError("resolver blew up")

    @strawberry.field
    def slow(self) -> str:
        time.sleep(0.02)  # just enough for the timing middleware to have something to print
        return "done"


schema = strawberry.Schema(Query)


# ---- the innermost layer: the only part that knows about GraphQL ----------
def run_query(request: Request) -> Response:
    # Deliberately written the naive way, exactly as a first draft usually is:
    # it TRUSTS the request to have a "query" key. A client that posts
    # {"variables": {...}} and nothing else makes this line raise KeyError.
    # That is the realistic crash `with_recovery` exists to contain.
    query = request["query"]
    result = schema.execute_sync(query, variable_values=request.get("variables"))
    response: Response = {"data": result.data}
    if result.errors:
        response["errors"] = [{"message": e.message, "path": e.path} for e in result.errors]
    return response


# ---- middleware 1: what ran, and how long it took ------------------------
def with_logging(next_execute: Execute) -> Execute:
    def wrapped(request: Request) -> Response:
        start = time.perf_counter()
        response = next_execute(request)          # <- everything inside happens here
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_count = len(response.get("errors", []))
        line = f"[log] {' '.join(request.get('query', '<no query>').split())} -> " \
               f"{error_count} error(s) in {elapsed_ms:.1f}ms"
        log_lines.append(line)
        print("  " + line)
        return response
    return wrapped


# ---- middleware 2: turn any escaped crash into a clean GraphQL error -----
def with_recovery(next_execute: Execute) -> Execute:
    def wrapped(request: Request) -> Response:
        try:
            return next_execute(request)
        except Exception as exc:
            # Never leak the exception text to the client in a real service -
            # log it, and hand back something deliberately vague.
            print(f"  [recovery] caught {exc!r} - the process stays up, this ONE request fails")
            return {"data": None, "errors": [{"message": "internal server error"}]}
    return wrapped


# Built once, outside in. Logging is OUTERMOST so it also sees requests that
# recovery had to rescue - see demo 4 for what happens if you swap them.
execute: Execute = with_logging(with_recovery(run_query))


def run(title: str, request: Request, pipeline: Execute = None):
    print(f"\n# {title}")
    response = (pipeline or execute)(request)
    print(f"response : {json.dumps(response)}")
    return response


if __name__ == "__main__":
    res = run("1. a normal request: the log line is the only visible difference",
              {"query": "{ healthy slow }"})
    assert res["data"] == {"healthy": True, "slow": "done"}
    assert "0 error(s)" in log_lines[-1] and "ms" in log_lines[-1]

    # Safety net 1 (the engine's). The resolver raised, and yet: the process
    # is alive, `healthy` still answered, and the failure is a normal error.
    res = run("2. a resolver that blows up: contained by the engine, per field",
              {"query": "{ healthy boom }"})
    assert res["data"] == {"healthy": True, "boom": None}
    assert res["errors"][0]["path"] == ["boom"]
    assert "1 error(s)" in log_lines[-1]
    print("   -> one bad resolver is a partial response, not a dead server (level 06's rule)")

    # Safety net 2 (ours). This crash happens in run_query, before the engine
    # is ever involved - GraphQL cannot help, so with_recovery must.
    res = run("3. a malformed request that crashes OUR code, not a resolver",
              {"variables": {"x": 1}})
    assert res == {"data": None, "errors": [{"message": "internal server error"}]}
    assert log_lines[-1].startswith("[log] <no query>"), "logging still ran: it wraps recovery"
    print("   -> without with_recovery this KeyError would have escaped and killed the process")

    # Order. Same two middlewares, wrapped the other way round.
    wrong_order: Execute = with_recovery(with_logging(run_query))
    before = len(log_lines)
    print("\n# 4. the SAME two middlewares, chained in the wrong order")
    res = wrong_order({"variables": {"x": 1}})
    print(f"response : {json.dumps(res)}")
    assert res == {"data": None, "errors": [{"message": "internal server error"}]}
    assert len(log_lines) == before, "the crash escaped with_logging before it could log anything"
    print("   -> the request still failed cleanly, but NOTHING was logged: the exception")
    print("      escaped with_logging at its `next_execute(request)` call, so the code after")
    print("      that call never ran. Outermost middleware sees the most.")

    # Still alive after all of the above - which is the entire point.
    res = run("5. the process survived every failure above", {"query": "{ healthy }"})
    assert res["data"] == {"healthy": True}

    print(f"\nlog lines collected: {len(log_lines)}")
    print("OK")
