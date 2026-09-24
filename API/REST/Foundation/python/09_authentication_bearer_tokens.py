"""
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Middleware (level 08) is the mechanism; authentication is one specific thing
people put in it. Authentication answers exactly ONE question: "do we
recognize this request at all?" It says NOTHING about what that caller is
allowed to do - that is level 10, authorization, and it is a deliberately
separate concept.

This checks a bearer token against a hardcoded lookup table. Real systems
verify a signed JWT or look a token up in a database (see
../../labs/python/03_jwt_auth_and_scopes.py) - the SHAPE of the check is
identical: reject before the real handler ever runs if the token is
missing or unknown.

You will learn
  * the "Authorization: Bearer <token>" header convention
  * authentication middleware runs BEFORE the real handler, and can
    short-circuit the whole chain by returning a response of its own
  * 401 Unauthorized means specifically "we do not know who you are" -
    never confuse it with 403 (level 10), which means the opposite problem
  * attaching the identified caller onto the request so the real handler
    (and level 10's authorization check) can use it without re-checking the token

Run it   python 09_authentication_bearer_tokens.py
"""
import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

# A stand-in for "who is allowed in", the way a real system would consult a
# database or verify a signed token instead of this dict.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}


@dataclass
class Req:
    method: str
    path: str
    headers: dict
    user: dict | None = None  # filled in BY the authentication middleware, not by the caller


@dataclass
class Res:
    status: int
    body: bytes
    headers: dict = field(default_factory=dict)


Handler = Callable[[Req], Res]


def with_authentication(next_handler: Handler) -> Handler:
    def wrapped(req: Req) -> Res:
        header = req.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return Res(401, json.dumps({"error": "missing bearer token"}).encode())

        token = header.removeprefix("Bearer ")
        identity = TOKENS.get(token)
        if identity is None:
            return Res(401, json.dumps({"error": "invalid token"}).encode())

        req.user = identity              # now every handler downstream knows who this is
        return next_handler(req)
    return wrapped


def dispatch(req: Req) -> Res:
    if req.path == "/whoami":
        return Res(200, json.dumps(req.user).encode())   # req.user was set by the middleware above
    return Res(404, b'{"error": "not found"}')


pipeline: Handler = with_authentication(dispatch)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        res = pipeline(Req(method="GET", path=self.path, headers=dict(self.headers)))
        self.send_response(res.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(res.body)))
        self.end_headers()
        self.wfile.write(res.body)

    def log_message(self, *args):
        pass


def get(base, path, headers=None):
    req = urllib.request.Request(base + path, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    s, b = get(base, "/whoami")
    print(f"GET /whoami  (no header)              -> {s} {b}")
    assert s == 401

    s, b = get(base, "/whoami", {"Authorization": "Bearer not-a-real-token"})
    print(f"GET /whoami  Authorization: Bearer bad -> {s} {b}")
    assert s == 401

    s, b = get(base, "/whoami", {"Authorization": "Bearer alice-token"})
    print(f"GET /whoami  Authorization: Bearer alice-token -> {s} {b}")
    assert s == 200 and b["user"] == "alice" and b["role"] == "admin"

    s, b = get(base, "/whoami", {"Authorization": "Bearer bob-token"})
    print(f"GET /whoami  Authorization: Bearer bob-token   -> {s} {b}")
    assert s == 200 and b["user"] == "bob" and b["role"] == "viewer"
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), HttpHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
