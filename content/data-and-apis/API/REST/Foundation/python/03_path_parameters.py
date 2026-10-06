"""
FOUNDATION LEVEL 03 - Path parameters: /books/{id}
=====================================================
So far every path was a fixed string. Real resources are addressed by an ID
that lives INSIDE the path: /books/7 means "the book whose id is 7". The
server has to parse that out of self.path itself (no framework magic yet).

You will learn
  * splitting self.path on "/" to pull a variable segment out by hand
  * why an id that is not a valid integer is a 404 (or 400), never a crash
  * this is exactly what frameworks like Flask/FastAPI's "/books/{id}" or Go's
    "/books/{id}" syntax do FOR you under the hood - you are doing it by hand once
    so the magic later is not mysterious

Run it   python 03_path_parameters.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOOKS = {
    1: {"id": 1, "title": "Structure and Interpretation of Computer Programs"},
    2: {"id": 2, "title": "The Pragmatic Programmer"},
}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def book_id_from_path(self):
        """'/books/7' -> 7 ; '/books/abc' -> None ; '/books' -> None."""
        parts = self.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "books" and parts[1].isdigit():
            return int(parts[1])
        return None

    def do_GET(self):
        book_id = self.book_id_from_path()
        if book_id is None:
            return self.send_json(400, {"error": "expected /books/<integer id>"})
        if book_id not in BOOKS:
            return self.send_json(404, {"error": f"no book with id {book_id}"})
        self.send_json(200, BOOKS[book_id])

    def log_message(self, *args):
        pass


def get(base, path):
    try:
        with urllib.request.urlopen(f"{base}{path}") as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    s, b = get(base, "/books/1")
    print(f"GET /books/1   -> {s} {b}")
    assert (s, b["title"]) == (200, BOOKS[1]["title"])

    s, b = get(base, "/books/999")
    print(f"GET /books/999 -> {s} {b}   (well-formed id, does not exist)")
    assert s == 404

    s, b = get(base, "/books/abc")
    print(f"GET /books/abc -> {s} {b}   (not even an id -> 400, never a crash)")
    assert s == 400
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
