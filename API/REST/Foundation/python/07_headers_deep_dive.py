"""
FOUNDATION LEVEL 07 - Headers: metadata about the message, not the message itself
====================================================================================
Every level so far used one or two headers without dwelling on them. Headers are
just more "key: value" text lines, the same shape as the request line itself - anyone can add
their own. This level uses them on purpose: content negotiation, a custom
application header, and conditional requests via ETag (a cheap fingerprint).

You will learn
  * self.headers.get("X") reads any request header, case-insensitively
  * a server can offer more than one representation and pick by Accept
  * custom headers (commonly prefixed like X-Request-Id) travel like any other
  * ETag + If-None-Match is how a client says "only send it if it changed" -> 304

Run it   python 07_headers_deep_dive.py
"""
import hashlib
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ARTICLE_TEXT = "REST uses headers for everything HTTP itself needs to say."


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/article":
            self.send_response(404)
            self.end_headers()
            return

        etag = hashlib.sha256(ARTICLE_TEXT.encode()).hexdigest()[:16]
        if self.headers.get("If-None-Match") == etag:
            # The client already has this exact version - tell it so, send NOTHING back.
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return

        wants_json = "application/json" in (self.headers.get("Accept") or "")
        if wants_json:
            body = json.dumps({"text": ARTICLE_TEXT}).encode()
            content_type = "application/json"
        else:
            body = ARTICLE_TEXT.encode()
            content_type = "text/plain"

        request_id = self.headers.get("X-Request-Id", "none")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", etag)
        self.send_header("X-Echo-Request-Id", request_id)   # a custom response header
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def get(base, path, extra_headers):
    req = urllib.request.Request(base + path, headers=extra_headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        # urllib treats ANY non-2xx as an exception, even 304 which is not an error at all.
        return e.code, dict(e.headers), e.read()


def demo(base: str) -> None:
    s, h, b = get(base, "/article", {"Accept": "text/plain", "X-Request-Id": "req-1"})
    print(f"GET /article  Accept=text/plain        -> {s} Content-Type={h['Content-Type']} {b!r}")
    assert h["Content-Type"] == "text/plain"
    assert h["X-Echo-Request-Id"] == "req-1"

    s, h, b = get(base, "/article", {"Accept": "application/json"})
    print(f"GET /article  Accept=application/json  -> {s} Content-Type={h['Content-Type']} {b!r}")
    assert h["Content-Type"] == "application/json"
    etag = h["ETag"]

    s, h, b = get(base, "/article", {"Accept": "text/plain", "If-None-Match": etag})
    print(f"GET /article  If-None-Match=<current>  -> {s} {b!r}   (unchanged -> 304, empty body)")
    assert s == 304 and b == b""
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
