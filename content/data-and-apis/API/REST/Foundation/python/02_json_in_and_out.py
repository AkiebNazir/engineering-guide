"""
FOUNDATION LEVEL 02 - Speaking JSON instead of plain text
===========================================================
Real APIs exchange structured data, not plain sentences. JSON is just a text
format (plain text, the way HTTP itself is plain text) with its own tiny grammar for numbers,
strings, lists and objects. Python's `json` module converts between that text
and native dict/list objects.

You will learn
  * json.dumps(obj) -> str of JSON text ; json.loads(text) -> Python object back
  * Content-Type: application/json tells the CLIENT how to interpret the bytes -
    the server does not enforce anything by setting this header, it is advisory
  * why we still send Content-Length even though the body is now JSON, not plain text

Run it   python 02_json_in_and_out.py
"""
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/profile":
            # A Python dict goes out as a JSON OBJECT (curly braces).
            return self.send_json(200, {"name": "Ada", "languages": ["Go", "Python"]})
        self.send_json(404, {"error": "not found"})

    def log_message(self, *args):
        pass


def demo(base: str) -> None:
    with urllib.request.urlopen(f"{base}/profile") as r:
        content_type = r.headers.get("Content-Type")
        raw_bytes = r.read()

    print(f"raw bytes on the wire : {raw_bytes!r}")
    print(f"Content-Type header   : {content_type}")

    # This is the whole point of level 02: turn wire-format text back into a
    # real Python object you can index into, exactly like any other dict.
    parsed = json.loads(raw_bytes)
    print(f"parsed Python object   : {parsed!r}  (type={type(parsed).__name__})")

    assert content_type == "application/json"
    assert parsed == {"name": "Ada", "languages": ["Go", "Python"]}
    assert parsed["languages"][0] == "Go"
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
