"""
FOUNDATION LEVEL 04 - Query parameters: /books?author=...&limit=...
======================================================================
A path parameter (level 03) identifies WHICH resource. A query parameter
filters or shapes a COLLECTION: /books?author=Hunt&limit=1. It lives after the
"?" and is never part of routing - two requests to different query strings hit
the exact same handler and route.

You will learn
  * urllib.parse.urlsplit/parse_qs split "/books?author=Hunt&limit=1" into the
    path ("/books") and the query dict ({"author": ["Hunt"], "limit": ["1"]})
  * every query value arrives as a STRING (and as a LIST, because a key can
    repeat: ?tag=a&tag=b) - you convert types yourself, same as level 03's id
  * missing query params should have sane defaults, not KeyErrors

Run it   python 04_query_parameters.py
"""
import json
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOOKS = [
    {"id": 1, "title": "SICP", "author": "Abelson"},
    {"id": 2, "title": "The Pragmatic Programmer", "author": "Hunt"},
    {"id": 3, "title": "Effective Go", "author": "Hunt"},
]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        split = urllib.parse.urlsplit(self.path)
        if split.path != "/books":
            return self.send_json(404, {"error": "not found"})

        query = urllib.parse.parse_qs(split.query)  # {"author": ["Hunt"], "limit": ["1"]}
        results = BOOKS
        if "author" in query:
            wanted = query["author"][0]
            results = [b for b in results if b["author"] == wanted]

        limit = int(query["limit"][0]) if "limit" in query else len(results)
        self.send_json(200, results[:limit])

    def log_message(self, *args):
        pass


def get(base, path):
    with urllib.request.urlopen(f"{base}{path}") as r:
        return r.status, json.loads(r.read())


def demo(base: str) -> None:
    s, b = get(base, "/books")
    print(f"GET /books                      -> {s} {len(b)} book(s)")
    assert (s, len(b)) == (200, 3)

    s, b = get(base, "/books?author=Hunt")
    print(f"GET /books?author=Hunt          -> {s} {[x['title'] for x in b]}")
    assert len(b) == 2 and all(x["author"] == "Hunt" for x in b)

    s, b = get(base, "/books?author=Hunt&limit=1")
    print(f"GET /books?author=Hunt&limit=1  -> {s} {[x['title'] for x in b]}")
    assert len(b) == 1
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
