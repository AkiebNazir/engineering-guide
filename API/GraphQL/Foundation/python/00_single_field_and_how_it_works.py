"""
FOUNDATION LEVEL 00 (start here) - A basic GraphQL endpoint, explained end to end
=====================================================================================
If someone says "build me a basic GraphQL endpoint", THIS is what they mean: one
schema with one field, one function behind that field. The client sends the text
`{ hello }`, and gets back `{"data": {"hello": "world"}}`. Nothing about HTTP,
databases, or nested types yet - just enough to watch the whole ask/answer loop
happen once, so every later level is "add one more piece" instead of "understand
everything at once".

THE MENTAL MODEL (read this before the code)
  GraphQL is not a server, and not a network protocol. It is three things:
    - a SCHEMA: the complete list of fields a client is allowed to ask for,
      and what type each one returns. This is the contract.
    - a QUERY: a little document the CLIENT writes, naming which of those
      fields it wants. The response comes back in the same shape as the query.
    - an EXECUTION ENGINE: reads the query, checks it against the schema, then
      calls one RESOLVER function per requested field and assembles the answers.
  A "resolver" is nothing exotic: it is a normal function whose return value
  becomes that field's value in the response.

  Because it is just an engine, we can call it DIRECTLY in this process - no
  port, no socket, no curl. That is exactly what levels 00-10 do, so you can
  study GraphQL itself without HTTP noise in the way. In production the same
  engine sits behind a single HTTP POST endpoint (level 11 builds that for
  real, and level 13 proves there is nothing magic about the wire).

  {data, errors} is GraphQL's version of REST's "status code + body": `data`
  holds whatever resolved successfully, `errors` lists what went wrong. Unlike
  REST, the two arrive TOGETHER - a request can be half-successful (level 06).

  Nothing is remembered between calls. Each execution is a fresh, unrelated
  conversation: resolvers run again from scratch (see ../../Theory.md).

You will learn
  * what a schema is (the contract) and what a resolver is (a plain function)
  * that a query is written by the CLIENT, and the response mirrors its shape
  * what `{data, errors}` means, and why it replaces REST's status codes
  * that asking for a field the schema does not have is a normal, handled
    outcome - rejected before a single resolver runs (GraphQL's "404")
  * that GraphQL rides over ordinary HTTP, and needs it no more than this file does

Run it        python 00_single_field_and_how_it_works.py
Keep serving  python 00_single_field_and_how_it_works.py --serve   (then: curl -s localhost:8080/graphql -d '{"query":"{ hello }"}')
"""
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)  # keep the demo output clean

# Proves resolvers really do run per execution, and that nothing is cached
# or remembered between calls.
resolver_calls = {"hello": 0}


# This class IS the schema's "Query" type. Every method decorated with
# @strawberry.field becomes a field a client is allowed to ask for; the
# method itself is that field's resolver; the return type annotation
# (-> str) becomes the field's type in the contract (String!).
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        # A resolver is called ONLY when the client asks for its field. It
        # could read a database, call another service, or - here - just
        # return a constant. The engine does not care where the value came from.
        resolver_calls["hello"] += 1
        return "world"


schema = strawberry.Schema(Query)


def run(title: str, query: str):
    """Execute a query against the schema, in-process. No network involved."""
    result = schema.execute_sync(query)
    # This dict is exactly what a GraphQL HTTP endpoint would send back as JSON.
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {query}")
    print(f"response : {json.dumps(payload)}")
    return result


def demo() -> None:
    print("=== the schema, printed as SDL - this IS the contract ===")
    print(schema.as_str())

    result = run("1. the whole point: ask for a field, get that field back", "{ hello }")
    assert result.data == {"hello": "world"}
    assert not result.errors, "a successful execution has no errors entry at all"

    # Run the identical query again. Same answer, but the resolver ran a
    # SECOND time - the engine kept nothing from last time.
    run("2. the same query again - stateless: the resolver runs again", "{ hello }")
    print(f"hello resolver calls so far: {resolver_calls['hello']}")
    assert resolver_calls["hello"] == 2, "each execution is independent - nothing is cached"

    # Now ask for something the schema never promised. GraphQL checks the
    # whole query against the schema BEFORE running anything, so this is
    # caught for free - you never wrote this check. This is the moral
    # equivalent of REST's 404, except it is one uniform mechanism for
    # every mistake, not a status code per situation.
    result = run("3. a field the schema does not have - rejected before any resolver runs", "{ goodbye }")
    assert result.data is None
    assert "Cannot query field 'goodbye'" in result.errors[0].message
    assert resolver_calls["hello"] == 2, "nothing resolved: validation failed first"
    print("   -> data is null, errors explains why. Nothing crashed.")

    print("\nOK")


# ---------------------------------------------------------------------------
# Optional: the exact same schema, behind one real HTTP POST endpoint, so you
# can curl it. This is a preview - level 11 builds it properly, and level 13
# shows the raw bytes underneath. Notice how little there is to it: read a
# JSON body, hand `query` to the engine, write `{data, errors}` back as JSON.
# ---------------------------------------------------------------------------
class GraphQLHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        request = json.loads(body or b"{}")
        result = schema.execute_sync(request.get("query", ""))
        payload = {"data": result.data}
        if result.errors:
            payload["errors"] = [{"message": e.message} for e in result.errors]
        out = json.dumps(payload).encode()
        self.send_response(200)  # GraphQL says 200 even for field errors - see level 06
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/graphql")
        print("""try: curl -s localhost:8080/graphql -d '{"query":"{ hello }"}'""")
        ThreadingHTTPServer(("127.0.0.1", 8080), GraphQLHandler).serve_forever()

    demo()
