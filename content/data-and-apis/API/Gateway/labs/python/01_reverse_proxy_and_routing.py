"""
LAB 01 (basic) - A working API gateway in one file: routing, header hygiene, errors, access log
===============================================================================================
An API gateway is a reverse proxy with opinions. Clients talk to ONE address; the gateway decides
which service answers, rewrites the request on the way, and turns upstream failures into clean errors.

    client --> [ gateway :edge ] --/api/users/*---> users service
                                 --/api/orders/*--> orders service
                                 --/api/orders/export--> reports service   (longer prefix wins)
                                 --Host: admin.*--> admin service

You will learn
  * ROUTING: host + longest path-prefix match on SEGMENT boundaries (/api/users must not match
    /api/usersX), and prefix stripping (/api/users/42 reaches the service as /users/42)
  * HEADER HYGIENE, the part people get wrong:
      - hop-by-hop headers (Connection, Keep-Alive, TE, Transfer-Encoding, Upgrade, ...) and any header
        NAMED in Connection belong to one TCP hop and must not be forwarded
      - X-Forwarded-For / -Proto / -Host: the EDGE gateway REPLACES what the client sent (a client can
        type any IP it likes); proxies further inside APPEND
      - X-Request-Id: accept a well-formed one, otherwise mint one; echo it back; log it
  * FAILURE MAPPING: no route -> 404, upstream refused -> 502, upstream too slow -> 504,
    body too large -> 413 before a single byte reaches the service
  * a structured ACCESS LOG line per request (the gateway's most valuable output)

Standard library only (http.server + http.client).
Run it   python 01_reverse_proxy_and_routing.py
Serve    python 01_reverse_proxy_and_routing.py --serve   (gateway on :8080, try the curl lines it prints)
"""
import http.client
import json
import re
import socket
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
              "te", "trailer", "transfer-encoding", "upgrade", "proxy-connection"}
MAX_BODY = 64 * 1024                                   # per-route in real gateways; one number here
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")  # never trust an arbitrary client string in logs


# ================================================================ upstream services ==
def make_service(name: str, delay: float = 0.0):
    """A tiny backend that reports exactly what it received, so the demo can prove what the gateway sent."""
    class Service(BaseHTTPRequestHandler):
        def _answer(self):
            time.sleep(delay)
            n = int(self.headers.get("Content-Length") or 0)
            body = json.dumps({"service": name, "method": self.command, "path": self.path,
                               "headers": {k.lower(): v for k, v in self.headers.items()},
                               "body_len": len(self.rfile.read(n))}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Server", f"{name}/1.4.2 (internal)")  # a detail the edge should not leak
            self.end_headers()
            self.wfile.write(body)
        do_GET = do_POST = do_PUT = do_DELETE = _answer

        def log_message(self, *_):
            pass
    return Service


def start(handler, port: int = 0) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ================================================================ the gateway ==
@dataclass
class Route:
    name: str
    prefix: str                  # path prefix, matched on segment boundaries
    upstream: tuple[str, int]
    strip: str = ""              # prefix removed before forwarding
    host: str | None = None      # match Host header (without port) when set
    timeout: float = 2.0         # upstream response timeout


def match(routes: list[Route], host: str, path: str) -> Route | None:
    """Host routes first, then longest prefix. '/api/users' matches '/api/users' and '/api/users/..',
    never '/api/usersX'."""
    host = host.split(":")[0].lower()
    best = None
    for r in routes:
        if r.host and r.host != host:
            continue
        on_boundary = path == r.prefix or path.startswith(r.prefix.rstrip("/") + "/")
        if not on_boundary:
            continue
        key = (r.host is not None, len(r.prefix))
        if best is None or key > (best.host is not None, len(best.prefix)):
            best = r
    return best


ACCESS_LOG: list[dict] = []


def make_gateway(routes: list[Route]):
    class Gateway(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _reply(self, status: int, payload: dict, rid: str, extra: dict | None = None):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Request-Id", rid)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _proxy(self):
            started = time.perf_counter()
            rid = self.headers.get("X-Request-Id", "")
            if not REQUEST_ID_RE.match(rid):
                rid = uuid.uuid4().hex                      # mint one; a malformed id is replaced, not logged
            route = match(routes, self.headers.get("Host", ""), self.path.split("?")[0])
            status, upstream_ms = self._forward(route, rid)
            ACCESS_LOG.append({"request_id": rid, "method": self.command, "path": self.path,
                               "route": route.name if route else None, "status": status,
                               "upstream_ms": upstream_ms,
                               "total_ms": round((time.perf_counter() - started) * 1000, 1)})

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _proxy

        def _forward(self, route: Route | None, rid: str) -> tuple[int, float | None]:
            if route is None:
                self._reply(404, {"error": "no_route", "path": self.path}, rid)
                return 404, None
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:                          # decided from the header: the body is never read
                self._reply(413, {"error": "body_too_large", "limit": MAX_BODY}, rid, {"Connection": "close"})
                self.close_connection = True
                return 413, None
            body = self.rfile.read(length) if length else None

            # --- build the upstream request headers ---
            nominated = {h.strip().lower() for h in self.headers.get("Connection", "").split(",") if h.strip()}
            headers = {}
            for k, v in self.headers.items():
                lk = k.lower()
                if lk in HOP_BY_HOP or lk in nominated or lk.startswith("x-forwarded-") or lk == "forwarded":
                    continue                               # hop-by-hop, or client-supplied forwarding claims
                headers[k] = v
            headers["X-Forwarded-For"] = self.client_address[0]   # EDGE: replace, never append client input
            headers["X-Forwarded-Proto"] = "http"
            headers["X-Forwarded-Host"] = self.headers.get("Host", "")
            headers["X-Request-Id"] = rid
            path = self.path
            if route.strip and path.startswith(route.strip):
                path = path[len(route.strip):] or "/"

            t0 = time.perf_counter()
            conn = http.client.HTTPConnection(*route.upstream, timeout=route.timeout)
            try:
                conn.request(self.command, path, body=body, headers=headers)
                resp = conn.getresponse()
                data = resp.read()
            except (ConnectionRefusedError, ConnectionResetError, http.client.RemoteDisconnected):
                self._reply(502, {"error": "bad_gateway", "route": route.name}, rid)
                return 502, None
            except (socket.timeout, TimeoutError):
                self._reply(504, {"error": "upstream_timeout", "route": route.name,
                                  "timeout_s": route.timeout}, rid)
                return 504, round((time.perf_counter() - t0) * 1000, 1)
            finally:
                conn.close()
            upstream_ms = round((time.perf_counter() - t0) * 1000, 1)

            # --- relay the response, minus hop-by-hop and internal details ---
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() in HOP_BY_HOP or k.lower() in ("server", "content-length", "date"):
                    continue
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Request-Id", rid)
            self.send_header("Via", "1.1 lab-gateway")
            self.end_headers()
            self.wfile.write(data)
            return resp.status, upstream_ms

        def version_string(self):
            return "lab-gateway"

        def log_message(self, *_):
            pass
    return Gateway


# ================================================================ demo ==
def call(port: int, method: str, path: str, headers: dict | None = None, body: bytes | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        r = conn.getresponse()
        raw = r.read()
        return r.status, dict(r.getheaders()), (json.loads(raw) if raw else None)
    finally:
        conn.close()


def build(ports: dict[str, int] | None = None) -> tuple[list[Route], dict]:
    ports = ports or {}
    names = ("users", "orders", "reports", "admin")
    ups = {n: start(make_service(n), ports.get(n, 0)) for n in names}
    ups["slow"] = start(make_service("slow", delay=1.5), ports.get("slow", 0))
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    dead_port = s.getsockname()[1]
    s.close()                                              # nothing listens there any more
    a = lambda n: ("127.0.0.1", ups[n].server_port)
    routes = [
        Route("users", "/api/users", a("users"), strip="/api"),
        Route("orders", "/api/orders", a("orders"), strip="/api"),
        Route("reports", "/api/orders/export", a("reports"), strip="/api/orders"),
        Route("admin", "/", a("admin"), host="admin.example.test"),
        Route("slow", "/api/slow", a("slow"), strip="/api", timeout=0.3),
        Route("dead", "/api/legacy", ("127.0.0.1", dead_port), strip="/api"),
    ]
    return routes, ups


def demo():
    routes, _ = build()
    gw = start(make_gateway(routes))
    p = gw.server_port

    print("-- routing + prefix strip --")
    st, h, b = call(p, "GET", "/api/users/42")
    print(f"GET /api/users/42          -> {st} served by {b['service']}, upstream saw path {b['path']}")
    assert st == 200 and b["service"] == "users" and b["path"] == "/users/42"
    st, _, b = call(p, "GET", "/api/orders/export?fmt=csv")
    print(f"GET /api/orders/export     -> {b['service']} (longest prefix beats /api/orders), path {b['path']}")
    assert b["service"] == "reports" and b["path"] == "/export?fmt=csv"
    st, _, b = call(p, "GET", "/api/orders/7")
    assert b["service"] == "orders"
    st, _, b = call(p, "GET", "/api/usersX")
    print(f"GET /api/usersX            -> {st} (prefix match is on segment boundaries)")
    assert st == 404
    st, _, b = call(p, "GET", "/dashboard", {"Host": "admin.example.test:8080"})
    print(f"GET /dashboard Host=admin  -> {b['service']} (host routes win)")
    assert b["service"] == "admin"

    print("\n-- header hygiene --")
    st, h, b = call(p, "GET", "/api/users/1", {
        "X-Forwarded-For": "6.6.6.6",               # client claims to be someone else
        "Connection": "keep-alive, X-Internal-Debug",  # nominates X-Internal-Debug as hop-by-hop
        "X-Internal-Debug": "1", "Keep-Alive": "timeout=5", "Accept": "application/json"})
    seen = b["headers"]
    print("upstream X-Forwarded-For  :", seen.get("x-forwarded-for"), "(client's 6.6.6.6 dropped)")
    print("upstream got hop-by-hop?  :", {k: k in seen for k in ("keep-alive", "x-internal-debug")})
    print("end-to-end header kept    : accept =", seen.get("accept"))
    assert seen["x-forwarded-for"] == "127.0.0.1" and "6.6.6.6" not in json.dumps(seen)
    assert "keep-alive" not in seen and "x-internal-debug" not in seen and seen["accept"] == "application/json"
    print("response Server header    :", h.get("Server"), "| Via:", h.get("Via"), "(internal version hidden)")
    assert "internal" not in (h.get("Server") or "") and h.get("Via") == "1.1 lab-gateway"

    print("\n-- request ids --")
    _, h, b = call(p, "GET", "/api/users/1", {"X-Request-Id": "req-abc12345"})
    assert h["X-Request-Id"] == "req-abc12345" == b["headers"]["x-request-id"]
    _, h, b = call(p, "GET", "/api/users/1", {"X-Request-Id": "<script>alert(1)</script>"})
    print("well-formed id kept, malformed replaced by", h["X-Request-Id"])
    assert REQUEST_ID_RE.match(h["X-Request-Id"]) and h["X-Request-Id"] == b["headers"]["x-request-id"]

    print("\n-- failure mapping --")
    t = time.perf_counter()
    st, _, b = call(p, "GET", "/api/slow/report")
    print(f"slow upstream (1.5s, route timeout 0.3s) -> {st} {b['error']} after {time.perf_counter() - t:.2f}s")
    assert st == 504 and time.perf_counter() - t < 1.2
    st, _, b = call(p, "GET", "/api/legacy/thing")
    print(f"nothing listening                         -> {st} {b['error']}")
    assert st == 502
    st, _, b = call(p, "POST", "/api/orders", {"Content-Type": "application/json"}, b"x" * (MAX_BODY + 1))
    print(f"body of {MAX_BODY + 1} bytes                      -> {st} {b['error']}")
    assert st == 413
    st, _, b = call(p, "POST", "/api/orders", {"Content-Type": "application/json"}, b'{"sku":"A1"}')
    assert st == 200 and b["body_len"] == 12 and b["method"] == "POST"

    print("\n-- access log (last 3 lines) --")
    for line in ACCESS_LOG[-3:]:
        print(" ", json.dumps(line))
    assert {"request_id", "route", "status", "upstream_ms", "total_ms"} <= set(ACCESS_LOG[-1])
    assert [x["status"] for x in ACCESS_LOG[-3:]] == [502, 413, 200]
    gw.shutdown()
    print("\nOK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        routes, _ = build({"users": 9001, "orders": 9002, "reports": 9003, "admin": 9004, "slow": 9005})
        print("gateway on http://localhost:8080  (upstreams on 9001-9005)")
        print("  curl -i localhost:8080/api/users/42")
        print("  curl -i -H 'X-Forwarded-For: 6.6.6.6' localhost:8080/api/orders/7")
        print("  curl -i localhost:8080/api/slow/x      # 504 after 0.3s")
        ThreadingHTTPServer(("127.0.0.1", 8080), make_gateway(routes)).serve_forever()
    demo()
