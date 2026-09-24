"""
FOUNDATION LEVEL 06 - The full status-code vocabulary, and CRUD-to-verb mapping
==================================================================================
Levels 00-06 used 200/201/400/404 as they came up naturally. This level is the
deliberate, full picture: which HTTP verb means which CRUD action, and which
status code means what, on purpose, all in one place, on ONE resource.

You will learn
  * POST=Create, GET=Read, PUT=Replace(whole thing), DELETE=Remove
  * 201 Created should carry a Location header pointing at the new resource
  * 204 No Content means "it worked, there is nothing to send back"
  * DELETE is idempotent BY DESIGN: deleting something twice is not an error,
    the resource is simply gone both times
  * 405 Method Not Allowed should carry an Allow header listing what IS allowed

Run it   python 06_status_codes_and_crud_verbs.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOTES: dict[int, dict] = {}
NEXT_ID = 1


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload=None, headers: dict | None = None) -> None:
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        if body:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def note_id(self):
        parts = self.path.strip("/").split("/")
        return int(parts[1]) if len(parts) == 2 and parts[0] == "notes" and parts[1].isdigit() else None

    # ---- Read -------------------------------------------------------------
    def do_GET(self):
        nid = self.note_id()
        if nid is None and self.path == "/notes":
            return self.send_json(200, list(NOTES.values()))
        if nid in NOTES:
            return self.send_json(200, NOTES[nid])
        self.send_json(404, {"error": "note not found"})

    # ---- Create -------------------------------------------------------------
    def do_POST(self):
        global NEXT_ID
        if self.path != "/notes":
            return self.send_json(405, None, {"Allow": "GET"})
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"null")
        note = {"id": NEXT_ID, "text": data["text"]}
        NOTES[NEXT_ID] = note
        NEXT_ID += 1
        # 201 + Location: the client did not choose the id, so tell it where the new thing lives.
        self.send_json(201, note, {"Location": f"/notes/{note['id']}"})

    # ---- Replace --------------------------------------------------------------
    def do_PUT(self):
        nid = self.note_id()
        if nid not in NOTES:
            return self.send_json(404, {"error": "note not found"})
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"null")
        NOTES[nid] = {"id": nid, "text": data["text"]}   # PUT REPLACES the whole thing
        self.send_json(200, NOTES[nid])

    # ---- Remove -------------------------------------------------------------
    def do_DELETE(self):
        nid = self.note_id()
        NOTES.pop(nid, None)          # missing key is fine: idempotent by design
        self.send_json(204)           # worked, nothing to say back

    def log_message(self, *args):
        pass


def call(method, base, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, dict(r.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, dict(e.headers), (json.loads(raw) if raw else None)


def demo(base: str) -> None:
    s, h, b = call("POST", base, "/notes", {"text": "learn REST"})
    print(f"POST /notes         -> {s} Location={h.get('Location')} {b}")
    assert s == 201 and h["Location"] == "/notes/1"

    s, h, b = call("PUT", base, "/notes/1", {"text": "learn REST, for real"})
    print(f"PUT  /notes/1       -> {s} {b}")
    assert s == 200 and b["text"] == "learn REST, for real"

    s, h, _ = call("POST", base, "/notes/1", {"text": "x"})
    print(f"POST /notes/1       -> {s} Allow={h.get('Allow')}   (wrong verb for this path)")
    assert s == 405

    s1, _, _ = call("DELETE", base, "/notes/1")
    s2, _, _ = call("DELETE", base, "/notes/1")
    print(f"DELETE /notes/1 x2  -> {s1}, {s2}   (idempotent: deleting twice is not an error)")
    assert (s1, s2) == (204, 204)
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
