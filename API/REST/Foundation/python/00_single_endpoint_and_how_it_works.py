"""
FOUNDATION LEVEL 00 (start here) - A basic REST API endpoint, explained end to end
=====================================================================================
If someone says "build me a basic REST API endpoint", THIS is what they mean: one
server, one URL, a canned response. Nothing about JSON, routing, or databases yet -
just enough to see the whole request/response loop happen once, so every later
level is "add one more piece" instead of "understand everything at once".

THE MENTAL MODEL (read this before the code)
  A REST API is two separate programs talking over a network:
    - the SERVER starts, then does nothing but wait for connections on one port
    - the CLIENT (a browser, curl, another program) opens a connection, sends a
      short request, and waits for a reply
  Nothing is remembered between requests - each one is a fresh, unrelated
  conversation. That is what "stateless" means (see ../../Theory.md).

You will learn
  * what "listening on a port" actually means: one program, one door, on this machine
  * what an "endpoint" is: a specific URL path this server has agreed to answer
  * the exact request/response loop: verb + path in -> status code + body out
  * why the SAME client code works whether it is curl, a browser, or another
    program calling this - the server does not know or care who is asking
  * that "no such endpoint" is a normal, handled outcome (404), not a crash

Run it        python 00_single_endpoint_and_how_it_works.py
Keep serving  python 00_single_endpoint_and_how_it_works.py --serve   (then: curl -i localhost:8080/ping)
"""
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    # do_GET runs exactly once per incoming GET request. By the time this
    # method starts, the library has already read the request off the
    # network socket and parsed it into method / path / headers for you -
    # that parsing step is what the bonus level (13) shows happening by hand,
    # with nothing but raw bytes, once this feels easy.
    def do_GET(self):
        # self.path is the exact URL path the client asked for, e.g. "/ping".
        # This server has agreed to answer exactly ONE path - everything else
        # is "not found", which is a normal, expected outcome, not an error
        # in our code.
        if self.path != "/ping":
            self.send_response(404)  # "I understood you, but I have nothing at that address"
            self.end_headers()
            return

        body = b"pong\n"
        self.send_response(200)                             # step 1: the status line ("it worked")
        self.send_header("Content-Type", "text/plain")       # step 2: headers, one call per line...
        self.send_header("Content-Length", str(len(body)))   #         ...telling the client how to read the body
        self.end_headers()                                   # step 3: the blank line that ends the headers
        self.wfile.write(body)                                # step 4: the body itself

    def log_message(self, *args):
        pass  # silence the default per-request console line, to keep the demo output clean


def demo(base: str) -> None:
    # This function IS "the client". curl, a browser's address bar, and this
    # code all do the exact same three things: open a connection, send a
    # request, read back a response. There is nothing special about any of
    # them - they all speak the same plain-text protocol.
    with urllib.request.urlopen(f"{base}/ping") as response:
        status, body = response.status, response.read()

    print(f"request  : GET {base}/ping")
    print(f"response : {status} {body!r}")
    # 200 means "the server understood the request AND was able to fulfil it".
    assert status == 200
    assert body == b"pong\n"

    # Now ask for a path this server never agreed to answer. urllib treats any
    # non-2xx status as an exception - that is a urllib quirk, not an HTTP rule.
    try:
        urllib.request.urlopen(f"{base}/does-not-exist")
        raise AssertionError("expected a 404, got a success instead")
    except urllib.error.HTTPError as e:
        print(f"request  : GET {base}/does-not-exist")
        print(f"response : {e.code}   (an endpoint this server never agreed to answer - not a crash)")
        assert e.code == 404

    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080  (try: curl -i localhost:8080/ping)")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

    # port 0 = "operating system, hand me any free port" - so this demo never
    # collides with something else already listening on 8080 on your machine.
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
