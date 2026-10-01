"""
FOUNDATION LEVEL 11 - Putting it all together: one complete, PROTECTED CRUD resource
========================================================================================
Nothing new here. Every idea from levels 00-10 - routing, JSON, path params,
query params, body validation, real status codes, headers, middleware,
authentication, and authorization - combined on one resource, end to end.
Reads are public; writes require a valid bearer token (level 09); deleting
requires the "admin" role specifically (level 10). This is deliberately the
same shape as ../../labs/python/01_crud_stdlib.py and
../../labs/python/03_jwt_auth_and_scopes.py: once this feels easy, those labs
(real JWTs, OpenAPI validation, ETags, cursor pagination) are the very next
step, not a jump.

You will learn
  * how the previous 10 small lessons compose into one real-looking, real-
    SECURED API
  * that "a REST API" is not one big new idea - it is these small ideas,
    layered together, in a deliberate order (route -> validate -> authenticate
    -> authorize -> act)

Run it        python 11_complete_in_memory_crud.py
Keep serving  python 11_complete_in_memory_crud.py --serve   (curl -i localhost:8080/tasks)
"""
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TASKS: dict[int, dict] = {}
NEXT_ID = 1

# level 09/10's identity table, unchanged in shape - a real service verifies
# a signed JWT or looks a token up in a database instead of this dict.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}


class Handler(BaseHTTPRequestHandler):
    # ---- shared helpers (level 02 + 06 + 07) --------------------------------
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

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return True, json.loads(self.rfile.read(length) or b"null")
        except json.JSONDecodeError:
            return False, None

    def task_id_from_path(self, path: str):
        parts = path.strip("/").split("/")
        return int(parts[1]) if len(parts) == 2 and parts[0] == "tasks" and parts[1].isdigit() else None

    # ---- level 09's authentication check, reused as a plain method ---------
    def authenticate(self):
        """Returns the identity dict for a valid bearer token, or None."""
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        return TOKENS.get(header.removeprefix("Bearer "))

    def log_message(self, *args):
        pass

    # ---- Read: public, collection with a query filter (levels 01 + 04) -----
    def do_GET(self):
        split = urllib.parse.urlsplit(self.path)
        task_id = self.task_id_from_path(split.path)

        if split.path == "/tasks":
            query = urllib.parse.parse_qs(split.query)
            results = list(TASKS.values())
            if "done" in query:
                wanted = query["done"][0] == "true"
                results = [t for t in results if t["done"] == wanted]
            return self.send_json(200, results)

        if task_id in TASKS:
            return self.send_json(200, TASKS[task_id])
        self.send_json(404, {"error": "task not found"})

    # ---- Create: authenticated + body validation + 201/Location -----------
    def do_POST(self):
        global NEXT_ID
        if self.path != "/tasks":
            return self.send_json(405, {"error": "POST is only allowed on /tasks"}, {"Allow": "GET"})
        # level 09: writes require SOMEONE to be identified - reads never did.
        if self.authenticate() is None:
            return self.send_json(401, {"error": "missing or invalid bearer token"})
        ok, data = self.read_json_body()
        if not ok or not isinstance(data, dict) or not data.get("title"):
            return self.send_json(400, {"error": "'title' is required"})
        task = {"id": NEXT_ID, "title": data["title"], "done": bool(data.get("done", False))}
        TASKS[NEXT_ID] = task
        NEXT_ID += 1
        self.send_json(201, task, {"Location": f"/tasks/{task['id']}"})

    # ---- Replace: authenticated (levels 06 + 09) ----------------------------
    def do_PUT(self):
        if self.authenticate() is None:
            return self.send_json(401, {"error": "missing or invalid bearer token"})
        task_id, (ok, data) = self.task_id_from_path(self.path), self.read_json_body()
        if task_id not in TASKS:
            return self.send_json(404, {"error": "task not found"})
        if not ok or not isinstance(data, dict) or not data.get("title"):
            return self.send_json(400, {"error": "PUT replaces the whole task: 'title' is required"})
        TASKS[task_id] = {"id": task_id, "title": data["title"], "done": bool(data.get("done", False))}
        self.send_json(200, TASKS[task_id])

    # ---- Remove: authenticated AND authorized (levels 06 + 09 + 10) --------
    def do_DELETE(self):
        identity = self.authenticate()
        if identity is None:
            return self.send_json(401, {"error": "missing or invalid bearer token"})
        if identity["role"] != "admin":
            return self.send_json(403, {"error": "requires role 'admin'"})
        TASKS.pop(self.task_id_from_path(self.path), None)  # idempotent, same as level 06
        self.send_json(204)


def call(method, base, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, dict(r.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, dict(e.headers), (json.loads(raw) if raw else None)


def demo(base: str) -> None:
    s, _, b = call("POST", base, "/tasks", {"title": "learn REST from zero"})
    print(f"POST /tasks  (no token)             -> {s} {b}   (writes need authentication)")
    assert s == 401

    s, h, b = call("POST", base, "/tasks", {"title": "learn REST from zero"}, token="bob-token")
    print(f"POST /tasks  (bob, viewer)          -> {s} Location={h.get('Location')} {b}")
    assert s == 201 and b["done"] is False

    call("POST", base, "/tasks", {"title": "already done", "done": True}, token="bob-token")

    s, _, b = call("GET", base, "/tasks?done=true")
    print(f"GET  /tasks?done=true  (public, no token) -> {s} {b}")
    assert len(b) == 1 and b[0]["title"] == "already done"

    s, _, b = call("PUT", base, "/tasks/1", {"title": "learn REST from zero", "done": True}, token="bob-token")
    print(f"PUT  /tasks/1  (bob, viewer)         -> {s} {b}")
    assert b["done"] is True

    s, _, b = call("DELETE", base, "/tasks/1", token="bob-token")
    print(f"DELETE /tasks/1  (bob, viewer)       -> {s} {b}   (authenticated, but wrong role)")
    assert s == 403

    s1, _, _ = call("DELETE", base, "/tasks/1", token="alice-token")
    s2, _, _ = call("DELETE", base, "/tasks/1", token="alice-token")
    print(f"DELETE /tasks/1 x2  (alice, admin)   -> {s1}, {s2}")
    assert (s1, s2) == (204, 204)
    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
