"""
FOUNDATION LEVEL 10 - Authorization: what are you allowed to do
====================================================================
Authentication (level 09) established WHO is making the request. Authorization
is a SEPARATE question: is THIS identified caller allowed to do THIS specific
action? Two different users can both pass authentication and still get
different answers here. This level adds a role check on top of level 09's
authentication: any logged-in caller can READ the reports, but only an
"admin" may DELETE one.

You will learn
  * authorization middleware runs AFTER authentication - you need to know who
    they are (req.user) before you can decide what they are allowed to do
  * 403 Forbidden means "we know exactly who you are, and the answer is still
    no" - do not confuse this with 401 (level 09), which means "who even ARE you"
  * role-based access control (RBAC), in its simplest form: look up the
    identified caller's role, compare it against what THIS action requires
  * the SAME endpoint shape (DELETE /reports/{id}) can behave differently
    per caller - that decision lives in middleware, not scattered through
    the handler

Run it   python 10_authorization_role_based_access.py
"""
import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}
REPORTS = {1: {"id": 1, "title": "Q1 report"}}


@dataclass
class Req:
    method: str
    path: str
    headers: dict
    user: dict | None = None


@dataclass
class Res:
    status: int
    body: bytes
    headers: dict = field(default_factory=dict)


Handler = Callable[[Req], Res]


# ---- level 09's authentication middleware, unchanged ----------------------
def with_authentication(next_handler: Handler) -> Handler:
    def wrapped(req: Req) -> Res:
        header = req.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return Res(401, json.dumps({"error": "missing bearer token"}).encode())
        identity = TOKENS.get(header.removeprefix("Bearer "))
        if identity is None:
            return Res(401, json.dumps({"error": "invalid token"}).encode())
        req.user = identity
        return next_handler(req)
    return wrapped


# ---- NEW: authorization middleware - runs only once we know req.user -----
def require_role(role: str) -> Callable[[Handler], Handler]:
    def middleware(next_handler: Handler) -> Handler:
        def wrapped(req: Req) -> Res:
            if req.user["role"] != role:
                return Res(403, json.dumps({"error": f"requires role '{role}'"}).encode())
            return next_handler(req)
        return wrapped
    return middleware


def list_reports(req: Req) -> Res:
    return Res(200, json.dumps(list(REPORTS.values())).encode())


def delete_report(req: Req) -> Res:
    report_id = int(req.path.rsplit("/", 1)[1])
    REPORTS.pop(report_id, None)  # idempotent, same as level 07's DELETE
    return Res(204, b"")


def router(req: Req) -> Res:
    if req.method == "GET" and req.path == "/reports":
        return list_reports(req)                              # ANY authenticated caller may read
    if req.method == "DELETE" and req.path.startswith("/reports/"):
        return require_role("admin")(delete_report)(req)       # only "admin" may delete
    return Res(404, json.dumps({"error": "not found"}).encode())


# Authentication wraps the WHOLE router: req.user must exist before
# require_role can even look at it.
pipeline: Handler = with_authentication(router)


class HttpHandler(BaseHTTPRequestHandler):
    def _handle(self):
        req = Req(method=self.command, path=self.path, headers=dict(self.headers))
        res = pipeline(req)
        self.send_response(res.status)
        if res.body:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(res.body)))
        self.end_headers()
        self.wfile.write(res.body)

    def do_GET(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def log_message(self, *args):
        pass


def call(method, base, path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(base + path, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, (json.loads(raw) if raw else None)


def demo(base: str) -> None:
    s, b = call("GET", base, "/reports", token="bob-token")
    print(f"GET    /reports          (viewer)  -> {s} {b}")
    assert s == 200 and len(b) == 1

    s, b = call("DELETE", base, "/reports/1", token="bob-token")
    print(f"DELETE /reports/1        (viewer)  -> {s} {b}   (authenticated, but not allowed)")
    assert s == 403

    s, b = call("DELETE", base, "/reports/1", token="alice-token")
    print(f"DELETE /reports/1        (admin)   -> {s} {b}")
    assert s == 204

    s, b = call("GET", base, "/reports", token="alice-token")
    print(f"GET    /reports          (admin)   -> {s} {b}   (the delete above really happened)")
    assert s == 200 and len(b) == 0
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), HttpHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
