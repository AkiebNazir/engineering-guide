"""
FOUNDATION BONUS - GraphQL has no special transport (optional, read last)
=============================================================================
Levels 11 and 12 used http.server and urllib, and never asked what those
libraries do underneath. This file answers that, and makes one point:

    there is nothing about GraphQL on the wire. Nothing at all.

No GraphQL content type is required, no handshake, no framing, no custom
protocol. A GraphQL request is an ordinary HTTP POST whose body happens to be
JSON with a "query" string in it. To prove it, this file talks to a real
GraphQL endpoint with nothing but a TCP socket, typing every byte of the
request by hand, and then parses the response text by hand too.

This is optional. Nothing in levels 00-12 depends on it. It exists to answer
"but what is the client library actually doing for me?" once you are curious.
If you read REST/Foundation's level 13, this is the same exercise - and the
sameness IS the lesson.

You will learn
  * the exact bytes of a GraphQL request: request line, headers, blank line,
    JSON body - and that the body is the only part that knows about GraphQL
  * why Content-Length is mandatory: it is the only way the server knows where
    the body ends (the socket itself does not say)
  * how to split a raw response into status line / headers / body by hand
  * that `{"data": ..., "errors": ...}` is just text in that body, and the
    status line says 200 even when `errors` is populated

Run it   python 13_bonus_raw_http_over_tcp.py
"""
import json
import logging
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)


# ---- an ordinary GraphQL endpoint, exactly like level 11's -----------------
@strawberry.type
class Query:
    @strawberry.field
    def greet(self, name: str) -> str:
        return f"hello, {name}"

    @strawberry.field
    def flaky(self) -> str | None:
        raise RuntimeError("upstream is down")


schema = strawberry.Schema(Query)


class GraphQLHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # so Connection: close is honoured explicitly

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        request = json.loads(raw or b"{}")
        result = schema.execute_sync(request.get("query", ""),
                                     variable_values=request.get("variables"))
        payload = {"data": result.data}
        if result.errors:
            payload["errors"] = [{"message": e.message, "path": e.path} for e in result.errors]
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


# ---- the client, with no client library of any kind -----------------------
def raw_graphql_post(host: str, port: int, query: str, variables: dict | None = None) -> str:
    """Send a GraphQL request as raw bytes over TCP and return the raw
    response TEXT. This is the whole of what `requests`/urllib does for you."""
    # The body first, because we need its exact byte length for the header.
    body = json.dumps({"query": query, "variables": variables or {}}).encode()

    # Every line ends with CRLF ("\r\n"), and a BLANK line separates the
    # headers from the body. Get either wrong and the server hangs waiting.
    request_text = (
        f"POST /graphql HTTP/1.1\r\n"          # the request line: method, path, version
        f"Host: {host}:{port}\r\n"             # mandatory in HTTP/1.1
        f"Content-Type: application/json\r\n"  # what the body is
        f"Content-Length: {len(body)}\r\n"     # HOW LONG the body is - not optional
        f"Connection: close\r\n"               # "answer, then hang up" - keeps this demo simple
        f"\r\n"                                # the blank line: headers end here
    ).encode() + body                          # ...and the body follows immediately

    print("---- raw request bytes sent by the client ----")
    print(request_text.decode())

    sock = socket.create_connection((host, port), timeout=2)
    sock.sendall(request_text)

    # Read until the server hangs up. We asked for Connection: close, so an
    # empty read means "that was all of it".
    chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
    sock.close()
    return b"".join(chunks).decode()


def parse_raw_response(response_text: str) -> tuple[str, str, str]:
    """Split a raw HTTP response into its three parts, by hand."""
    head, body = response_text.split("\r\n\r\n", 1)   # the same blank line, in reverse
    status_line, header_block = head.split("\r\n", 1)
    return status_line, header_block, body


def demo(host: str, port: int) -> None:
    response_text = raw_graphql_post(host, port, 'query Greet($n: String!) { greet(name: $n) }',
                                     {"n": "Ada"})
    print("---- raw response bytes received by the client ----")
    print(response_text)

    status_line, header_block, body = parse_raw_response(response_text)
    print(f"status line : {status_line}")
    print(f"headers     : {' | '.join(header_block.splitlines())}")
    print(f"body (text) : {body}")

    assert status_line == "HTTP/1.1 200 OK", status_line
    assert f"Content-Length: {len(body)}" in header_block, "the length told the truth"

    # Only NOW does anything GraphQL-specific happen: we decode the body.
    payload = json.loads(body)
    print(f"body (json) : {json.dumps(payload)}")
    assert payload == {"data": {"greet": "hello, Ada"}}
    print("   -> the socket, the headers, and HTTP itself never knew this was GraphQL")

    # Same wire, a field-level failure. The status line does not change.
    response_text = raw_graphql_post(host, port, "{ greet(name: \"Ada\") flaky }")
    status_line, header_block, body = parse_raw_response(response_text)
    print("---- a request whose FIELD failed ----")
    print(f"status line : {status_line}")
    print(f"body (text) : {body}")
    payload = json.loads(body)
    assert status_line == "HTTP/1.1 200 OK", "200, with errors in the body - level 06's rule, on the wire"
    assert payload["data"] == {"greet": "hello, Ada", "flaky": None}
    assert payload["errors"][0]["path"] == ["flaky"]
    print("   -> HTTP said 'delivered successfully'. The message itself described a failure.")
    print("      That is exactly why a GraphQL client must read the body, not the status.")

    print("\nOK")


if __name__ == "__main__":
    # port 0 = "operating system, hand me any free port".
    server = ThreadingHTTPServer(("127.0.0.1", 0), GraphQLHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo("127.0.0.1", server.server_port)
    server.shutdown()
