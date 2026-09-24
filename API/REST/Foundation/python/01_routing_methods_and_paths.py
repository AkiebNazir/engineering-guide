"""
FOUNDATION LEVEL 01 - Routing: many paths, many methods
=========================================================
Level 01 answered every path the same way. A real API looks at self.path and
the request method, and decides what to do - that decision-making is "routing".

You will learn
  * self.path is the exact string the client asked for
  * do_GET / do_POST / do_DELETE are separate methods - the library already
    routes by VERB for you; routing by PATH inside each one is still your job
  * an unmatched path must reply 404 (Not Found), not silently do the wrong thing
  * an unmatched verb on a KNOWN path must reply 405 (Method Not Allowed)

Run it   python 01_routing_methods_and_paths.py
"""
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Two "pages" this tiny server knows about. Everything else is 404.
ROUTES = {
    "/": b"welcome\n",
    "/about": b"a foundation-level REST server\n",
}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ROUTES:
            return self.reply(200, ROUTES[self.path])
        self.reply(404, b"not found\n")

    def do_DELETE(self):
        # DELETE is only meaningful on a known page in this toy example.
        if self.path in ROUTES:
            return self.reply(405, b"you cannot delete a static page\n")
        self.reply(404, b"not found\n")

    def log_message(self, *args):
        pass


def call(method: str, url: str):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def demo(base: str) -> None:
    s, b = call("GET", f"{base}/")
    print(f"GET /       -> {s} {b!r}")
    assert (s, b) == (200, ROUTES["/"])

    s, b = call("GET", f"{base}/about")
    print(f"GET /about  -> {s} {b!r}")
    assert (s, b) == (200, ROUTES["/about"])

    s, b = call("GET", f"{base}/nope")
    print(f"GET /nope   -> {s} {b!r}   (unknown path -> 404)")
    assert s == 404

    s, b = call("DELETE", f"{base}/about")
    print(f"DELETE /about -> {s} {b!r}   (known path, wrong verb -> 405)")
    assert s == 405
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
