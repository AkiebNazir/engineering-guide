"""
LAB 01 (basic) - A REST API with nothing but the Python standard library
=========================================================================
You will learn
  * what an HTTP server actually does: parse request line -> route -> write status + headers + body
  * mapping CRUD onto HTTP verbs:  POST=create, GET=read, PUT=replace, DELETE=remove
  * the status codes that matter: 200, 201 (+Location), 204, 404, 405, 400

Run it        python 01_crud_stdlib.py            (self-contained demo, then exits)
Keep serving  python 01_crud_stdlib.py --serve    (then try: curl -i localhost:8080/tasks)
"""
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TASKS: dict[int, dict] = {}   # our "database"
NEXT_ID = 1


class TaskHandler(BaseHTTPRequestHandler):
    # ---- helpers ---------------------------------------------------------
    def send_json(self, status: int, payload=None, headers: dict | None = None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"null")
        except json.JSONDecodeError:
            return None

    def task_id(self):
        """'/tasks/7' -> 7 ; '/tasks' -> None"""
        parts = self.path.strip("/").split("/")
        return int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else None

    def log_message(self, *args):   # silence default per-request logging
        pass

    # ---- verbs -----------------------------------------------------------
    def do_GET(self):
        if self.path == "/tasks":
            return self.send_json(200, list(TASKS.values()))
        tid = self.task_id()
        if tid in TASKS:
            return self.send_json(200, TASKS[tid])
        self.send_json(404, {"error": "task not found"})

    def do_POST(self):
        global NEXT_ID
        if self.path != "/tasks":
            return self.send_json(405, {"error": "POST is only allowed on /tasks"}, {"Allow": "GET, PUT, DELETE"})
        data = self.read_json()
        if not isinstance(data, dict) or not data.get("title"):
            return self.send_json(400, {"error": "title is required"})
        task = {"id": NEXT_ID, "title": data["title"], "done": bool(data.get("done", False))}
        TASKS[NEXT_ID] = task
        NEXT_ID += 1
        self.send_json(201, task, {"Location": f"/tasks/{task['id']}"})   # 201 + where it lives

    def do_PUT(self):
        tid, data = self.task_id(), self.read_json()
        if tid not in TASKS:
            return self.send_json(404, {"error": "task not found"})
        if not isinstance(data, dict) or not data.get("title"):
            return self.send_json(400, {"error": "PUT replaces the whole task: title is required"})
        TASKS[tid] = {"id": tid, "title": data["title"], "done": bool(data.get("done", False))}
        self.send_json(200, TASKS[tid])

    def do_DELETE(self):
        TASKS.pop(self.task_id(), None)          # idempotent: deleting twice is fine
        self.send_json(204)


# ------------------------------------------------------------------ demo ----
def call(method: str, url: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, dict(r.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, dict(e.headers), (json.loads(raw) if raw else None)


def demo(base: str):
    s, h, b = call("POST", f"{base}/tasks", {"title": "learn REST"})
    print(f"POST /tasks          -> {s} Location={h['Location']} body={b}")
    assert s == 201 and h["Location"] == "/tasks/1"

    s, _, b = call("GET", f"{base}/tasks/1")
    print(f"GET  /tasks/1        -> {s} {b}")
    assert s == 200 and b["title"] == "learn REST"

    s, _, b = call("PUT", f"{base}/tasks/1", {"title": "learn REST", "done": True})
    print(f"PUT  /tasks/1        -> {s} {b}")
    assert b["done"] is True

    s, _, b = call("POST", f"{base}/tasks", {"title": ""})
    print(f"POST /tasks (bad)    -> {s} {b}")
    assert s == 400

    s, h, _ = call("POST", f"{base}/tasks/1", {"title": "x"})
    print(f"POST /tasks/1        -> {s} Allow={h['Allow']}")
    assert s == 405

    s1, _, _ = call("DELETE", f"{base}/tasks/1")
    s2, _, _ = call("DELETE", f"{base}/tasks/1")
    s3, _, _ = call("GET", f"{base}/tasks/1")
    print(f"DELETE x2, then GET  -> {s1}, {s2}, {s3}   (idempotent delete, then gone)")
    assert (s1, s2, s3) == (204, 204, 404)
    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080")
        ThreadingHTTPServer(("127.0.0.1", 8080), TaskHandler).serve_forever()
    server = ThreadingHTTPServer(("127.0.0.1", 0), TaskHandler)      # port 0 = pick a free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
