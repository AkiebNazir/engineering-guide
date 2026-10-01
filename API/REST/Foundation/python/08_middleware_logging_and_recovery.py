"""
FOUNDATION LEVEL 08 - Middleware: code that wraps every request
===================================================================
Levels 00-07 put everything a request needed inside one handler function.
Middleware is a WRAPPER: a function that takes a handler and returns a new
handler that runs code before and/or after calling the original - without
touching the original's code at all. This is exactly how logging, auth
(levels 09-10), rate limiting, and CORS get added to real frameworks like
Gin/Echo (see ../../labs/golang) without editing every single route.

You will learn
  * a middleware has the SAME shape as a handler: it takes a request, returns
    a response - it just also gets to call "the next thing" in between
  * chaining: wrapping a wrapper in a wrapper, in a chosen order
  * ORDER matters: logging placed OUTSIDE timing sees the total time;
    placed INSIDE, it would miss whatever wraps it
  * recovering from a crash INSIDE one request, so it does not take down
    every other in-flight (or future) request on the same server

Run it   python 08_middleware_logging_and_recovery.py
"""
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

# A tiny stand-in for "the request" and "the response" - just enough fields
# to demonstrate the wrapping idea, independent of http.server's own classes.


@dataclass
class Req:
    method: str
    path: str


@dataclass
class Res:
    status: int
    body: bytes
    headers: dict = field(default_factory=dict)


Handler = Callable[[Req], Res]
Middleware = Callable[[Handler], Handler]


# ---- the "real" application logic, with zero knowledge of logging/recovery ----
def dispatch(req: Req) -> Res:
    if req.path == "/ping":
        return Res(200, b"pong\n")
    if req.path == "/boom":
        raise RuntimeError("simulated bug in a handler")  # on purpose, to prove recovery works
    return Res(404, b"not found\n")


# ---- middleware #1: logs method, path, status, and how long it took ----
def with_logging(next_handler: Handler) -> Handler:
    def wrapped(req: Req) -> Res:
        start = time.perf_counter()
        res = next_handler(req)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  [log] {req.method} {req.path} -> {res.status} ({elapsed_ms:.2f}ms)")
        return res
    return wrapped


# ---- middleware #2: catches ANY exception from everything it wraps ----
def with_recovery(next_handler: Handler) -> Handler:
    def wrapped(req: Req) -> Res:
        try:
            return next_handler(req)
        except Exception as exc:
            print(f"  [recovery] caught {exc!r} - server stays up, this ONE request becomes a 500")
            return Res(500, b"internal server error\n")
    return wrapped


# The chain is built once, outside in: logging sees everything, including
# failures that recovery converts into a clean 500. If you swapped the
# order (recovery outside logging), a crash would skip the log line entirely -
# try it, and see with_logging's print disappear on /boom.
pipeline: Handler = with_logging(with_recovery(dispatch))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        res = pipeline(Req(method="GET", path=self.path))
        self.send_response(res.status)
        for k, v in res.headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(res.body)))
        self.end_headers()
        self.wfile.write(res.body)

    def log_message(self, *args):
        pass


def get(base, path):
    try:
        with urllib.request.urlopen(f"{base}{path}") as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def demo(base: str) -> None:
    s, b = get(base, "/ping")
    print(f"GET /ping -> {s} {b!r}")
    assert (s, b) == (200, b"pong\n")

    s, b = get(base, "/boom")
    print(f"GET /boom -> {s} {b!r}   (the handler raised - recovery turned it into a clean 500)")
    assert s == 500

    # The crash above must NOT have taken the server down for anyone else.
    s, b = get(base, "/ping")
    print(f"GET /ping -> {s} {b!r}   (server is still alive after the previous crash)")
    assert (s, b) == (200, b"pong\n")
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), HttpHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
