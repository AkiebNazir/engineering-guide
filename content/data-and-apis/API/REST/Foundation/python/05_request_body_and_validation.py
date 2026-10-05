"""
FOUNDATION LEVEL 05 - Reading a request body, and rejecting bad input
========================================================================
GET requests carry data in the URL (levels 03-04). POST/PUT carry data in the
BODY instead, after the request's headers end. The server has to
(1) know how many bytes to read via Content-Length, (2) parse them as JSON,
and (3) VALIDATE the shape before trusting any of it.

You will learn
  * Content-Length tells you exactly how many body bytes to self.rfile.read()
  * malformed JSON must not crash the server - catch json.JSONDecodeError
  * "well-formed JSON" is not the same as "valid data" - a dict without the
    required key is still just wrong, and that is a 400, not a 500

Run it   python 05_request_body_and_validation.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USERS = []


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        """Returns (ok, data_or_error_message)."""
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        if not raw:
            return False, "request body is empty"
        try:
            return True, json.loads(raw)
        except json.JSONDecodeError:
            return False, "request body is not valid JSON"

    def do_POST(self):
        if self.path != "/users":
            return self.send_json(404, {"error": "not found"})

        ok, data = self.read_json_body()
        if not ok:
            return self.send_json(400, {"error": data})          # data holds the parse error
        if not isinstance(data, dict) or "email" not in data:
            return self.send_json(400, {"error": "'email' is required"})

        USERS.append(data)
        self.send_json(201, data)

    def log_message(self, *args):
        pass


def post(base, path, raw_body: bytes):
    req = urllib.request.Request(base + path, data=raw_body, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    s, b = post(base, "/users", json.dumps({"email": "ada@example.com"}).encode())
    print(f"POST /users  {{'email': ...}}   -> {s} {b}")
    assert s == 201

    s, b = post(base, "/users", json.dumps({"name": "no email field"}).encode())
    print(f"POST /users  {{'name': ...}}    -> {s} {b}   (missing required field)")
    assert s == 400

    s, b = post(base, "/users", b"{this is not json")
    print(f"POST /users  <garbage bytes>    -> {s} {b}   (parse error, not a crash)")
    assert s == 400
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
