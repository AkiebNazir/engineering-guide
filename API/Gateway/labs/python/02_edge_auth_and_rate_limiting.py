"""
LAB 02 (basic) - Auth and rate limiting at the edge, and passing identity to services safely
=============================================================================================
The gateway is the one place every request passes, so it is where you check WHO is calling and
HOW MUCH they may call - once, consistently - instead of in every service.

    request -> [1 per-IP limit] -> [2 authenticate] -> [3 authorize route] -> [4 per-consumer limit] -> service
                  429                 401                   403                     429
    cheap checks first: the per-IP limit protects the (more expensive) auth step from brute force.

You will learn
  * two credential kinds at the edge:
      - API keys: store only sha256(key), look up by hash, map to a CONSUMER with a plan
      - JWT (HS256 here, by hand): pin the algorithm (reject "none" and anything unexpected), verify
        the signature in constant time, then exp / nbf (with small leeway), iss and aud
  * 401 vs 403: 401 + WWW-Authenticate = "who are you?"; 403 = "I know you, and no"
  * per-consumer TOKEN BUCKETS sized by plan, with 429 + Retry-After and the RateLimit headers
  * IDENTITY PROPAGATION: strip every identity header the client sent, inject trusted ones, and SIGN
    them so a service reached directly (bypassing the gateway) rejects the forged header
  * why LOCAL limits on N gateway replicas let a client through N times the limit, and how a shared
    counter (Redis in production) fixes it

Standard library only.
Run it   python 02_edge_auth_and_rate_limiting.py
"""
import base64
import hashlib
import hmac
import http.client
import json
import math
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

JWT_SECRET = b"dev-only-jwt-secret-change-me"
JWT_ISS, JWT_AUD = "https://auth.example.test", "orders-api"
GATEWAY_SIGNING_KEY = b"gateway-to-service-key"        # shared by the gateway and its services only
IDENTITY_HEADERS = ("x-consumer-id", "x-scopes", "x-user-id", "x-gateway-signature")


# ================================================================ credentials ==
def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_jwt(claims: dict, alg: str = "HS256", key: bytes = JWT_SECRET) -> str:
    head = b64url(json.dumps({"alg": alg, "typ": "JWT"}).encode())
    body = b64url(json.dumps(claims).encode())
    sig = b64url(hmac.new(key, f"{head}.{body}".encode(), hashlib.sha256).digest()) if alg == "HS256" else ""
    return f"{head}.{body}.{sig}"


class AuthError(Exception):
    pass


def verify_jwt(token: str, now: float, leeway: int = 30) -> dict:
    try:
        head_s, body_s, sig_s = token.split(".")
        header = json.loads(b64url_decode(head_s))
        claims = json.loads(b64url_decode(body_s))
    except Exception:
        raise AuthError("malformed token")
    if header.get("alg") != "HS256":                     # PIN the algorithm; never read it from the token
        raise AuthError(f"alg {header.get('alg')!r} not allowed")
    expected = hmac.new(JWT_SECRET, f"{head_s}.{body_s}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, b64url_decode(sig_s)):
        raise AuthError("bad signature")
    if claims.get("exp", 0) + leeway < now:
        raise AuthError("expired")
    if claims.get("nbf", 0) - leeway > now:
        raise AuthError("not yet valid")
    if claims.get("iss") != JWT_ISS or JWT_AUD not in ([claims.get("aud")] if isinstance(claims.get("aud"), str) else claims.get("aud", [])):
        raise AuthError("wrong issuer or audience")
    return claims


@dataclass
class Consumer:
    id: str
    plan: str
    scopes: set[str]


PLANS = {"free": (5, 1.0), "pro": (20, 10.0)}          # (burst, refill tokens/second)
API_KEYS = {  # sha256(key) -> consumer. The plaintext key is shown to the customer once and never stored.
    hashlib.sha256(b"key_free_4f9a").hexdigest(): Consumer("acme-free", "free", {"orders:read"}),
    hashlib.sha256(b"key_pro_77c1").hexdigest(): Consumer("globex-pro", "pro", {"orders:read", "orders:write"}),
}


def authenticate(headers, now: float) -> Consumer | None:
    """Returns None for anonymous; raises AuthError for a credential that is present but bad."""
    if key := headers.get("X-Api-Key"):
        c = API_KEYS.get(hashlib.sha256(key.encode()).hexdigest())
        if not c:
            raise AuthError("unknown api key")
        return c
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        claims = verify_jwt(auth[7:], now)
        return Consumer(claims["sub"], claims.get("plan", "free"), set(claims.get("scope", "").split()))
    return None


# ================================================================ rate limiting ==
class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def now(self) -> float:
        return self.t


class BucketStore:
    """A token-bucket table. One instance per gateway = LOCAL limits; one shared instance = GLOBAL.
    In production the shared one is Redis (a Lua script does read-refill-spend atomically)."""
    def __init__(self, clock: Clock):
        self.clock, self.lock, self.buckets = clock, threading.Lock(), {}

    def take(self, key: str, burst: int, rate: float) -> tuple[bool, int, float]:
        with self.lock:
            now = self.clock.now()
            tokens, last = self.buckets.get(key, (float(burst), now))
            tokens = min(burst, tokens + (now - last) * rate)
            ok = tokens >= 1
            if ok:
                tokens -= 1
            self.buckets[key] = (tokens, now)
            retry = 0.0 if ok else (1 - tokens) / rate
            return ok, int(tokens), retry


# ================================================================ gateway + service ==
ROUTES = {  # (method, prefix) -> required scope; None = public
    ("GET", "/orders"): "orders:read",
    ("POST", "/orders"): "orders:write",
    ("GET", "/public"): None,
}


def sign_identity(consumer_id: str, scopes: str, rid: str) -> str:
    return hmac.new(GATEWAY_SIGNING_KEY, f"{consumer_id}|{scopes}|{rid}".encode(), hashlib.sha256).hexdigest()


def make_gateway(upstream_port: int, store: BucketStore, clock: Clock):
    class Gateway(BaseHTTPRequestHandler):
        def _reply(self, status, payload, headers=None):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _handle(self):
            # 1. coarse per-IP limit (runs before any crypto)
            ok, _, retry = store.take(f"ip:{self.client_address[0]}", 50, 25.0)
            if not ok:
                return self._reply(429, {"error": "too_many_requests"}, {"Retry-After": str(max(1, math.ceil(retry)))})
            # 2. authenticate
            try:
                consumer = authenticate(self.headers, clock.now())
            except AuthError as e:
                return self._reply(401, {"error": "invalid_credentials", "detail": str(e)},
                                   {"WWW-Authenticate": 'Bearer realm="api", error="invalid_token"'})
            # 3. authorize the route
            route = next(((m, p) for (m, p) in ROUTES if m == self.command and self.path.startswith(p)), None)
            if route is None:
                return self._reply(404, {"error": "no_route"})
            scope = ROUTES[route]
            if scope and consumer is None:
                return self._reply(401, {"error": "authentication_required"}, {"WWW-Authenticate": 'Bearer realm="api"'})
            if scope and scope not in consumer.scopes:
                return self._reply(403, {"error": "insufficient_scope", "required": scope})
            # 4. per-consumer limit, sized by plan
            if consumer:
                burst, rate = PLANS[consumer.plan]
                ok, remaining, retry = store.take(f"consumer:{consumer.id}", burst, rate)
                rl = {"RateLimit-Policy": f'"{consumer.plan}";q={burst};w={round(burst / rate)}',
                      "RateLimit": f'"{consumer.plan}";r={remaining};t={math.ceil(retry)}'}
                if not ok:
                    return self._reply(429, {"error": "rate_limited", "plan": consumer.plan},
                                       {**rl, "Retry-After": str(max(1, math.ceil(retry)))})
            # 5. forward with a TRUSTED, SIGNED identity
            fwd = {k: v for k, v in self.headers.items()
                   if k.lower() not in IDENTITY_HEADERS and k.lower() not in ("authorization", "x-api-key", "host")}
            rid = self.headers.get("X-Request-Id", "rid-" + str(time.perf_counter_ns()))
            cid, scopes = (consumer.id, " ".join(sorted(consumer.scopes))) if consumer else ("anonymous", "")
            fwd.update({"X-Consumer-Id": cid, "X-Scopes": scopes, "X-Request-Id": rid,
                        "X-Gateway-Signature": sign_identity(cid, scopes, rid)})
            conn = http.client.HTTPConnection("127.0.0.1", upstream_port, timeout=2)
            n = int(self.headers.get("Content-Length") or 0)
            conn.request(self.command, self.path, body=self.rfile.read(n) if n else None, headers=fwd)
            r = conn.getresponse()
            self._reply(r.status, json.loads(r.read()), rl if consumer else None)
            conn.close()

        do_GET = do_POST = _handle

        def log_message(self, *_):
            pass
    return Gateway


class OrdersService(BaseHTTPRequestHandler):
    """Trusts X-Consumer-Id ONLY when the gateway signature over it verifies. Defence in depth: in
    production this is mTLS between gateway and service, a signed JWT from the gateway, or both."""
    def _handle(self):
        cid, scopes, rid = (self.headers.get(h, "") for h in ("X-Consumer-Id", "X-Scopes", "X-Request-Id"))
        good = hmac.compare_digest(sign_identity(cid, scopes, rid), self.headers.get("X-Gateway-Signature", ""))
        status, payload = (200, {"consumer": cid, "scopes": scopes}) if good else (401, {"error": "not via gateway"})
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = _handle

    def log_message(self, *_):
        pass


def start(handler) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def call(port, method, path, headers=None, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(method, path, body=body, headers=headers or {})
    r = conn.getresponse()
    out = r.status, dict(r.getheaders()), json.loads(r.read())
    conn.close()
    return out


# ================================================================ demo ==
def demo():
    clock = Clock()
    svc = start(OrdersService)
    gw = start(make_gateway(svc.server_port, BucketStore(clock), clock))
    p = gw.server_port
    now = clock.now()
    good = make_jwt({"sub": "user-17", "iss": JWT_ISS, "aud": JWT_AUD, "exp": now + 300, "scope": "orders:read", "plan": "pro"})

    print("-- authentication (401) and authorization (403) --")
    cases = [
        ("public route, anonymous", "GET", "/public/status", {}, 200),
        ("no credentials", "GET", "/orders", {}, 401),
        ("valid JWT, orders:read", "GET", "/orders", {"Authorization": f"Bearer {good}"}, 200),
        ("valid JWT, POST needs orders:write", "POST", "/orders", {"Authorization": f"Bearer {good}"}, 403),
        ("alg=none token", "GET", "/orders",
         {"Authorization": "Bearer " + make_jwt({"sub": "x", "iss": JWT_ISS, "aud": JWT_AUD, "exp": now + 300}, alg="none")}, 401),
        ("signed with another key", "GET", "/orders",
         {"Authorization": "Bearer " + make_jwt({"sub": "x", "iss": JWT_ISS, "aud": JWT_AUD, "exp": now + 300}, key=b"guess")}, 401),
        ("expired 10 min ago", "GET", "/orders",
         {"Authorization": "Bearer " + make_jwt({"sub": "x", "iss": JWT_ISS, "aud": JWT_AUD, "exp": now - 600, "scope": "orders:read"})}, 401),
        ("token for another audience", "GET", "/orders",
         {"Authorization": "Bearer " + make_jwt({"sub": "x", "iss": JWT_ISS, "aud": "billing-api", "exp": now + 300, "scope": "orders:read"})}, 401),
        ("unknown API key", "GET", "/orders", {"X-Api-Key": "key_guess"}, 401),
        ("pro API key may write", "POST", "/orders", {"X-Api-Key": "key_pro_77c1"}, 200),
    ]
    for label, m, path, h, want in cases:
        st, hdrs, b = call(p, m, path, h)
        extra = b.get("detail") or b.get("required") or b.get("consumer") or b.get("error", "")
        print(f"  {label:36s} -> {st} {extra}")
        assert st == want, (label, st, b)
        if st == 401:
            assert "WWW-Authenticate" in hdrs

    print("\n-- identity propagation --")
    st, _, b = call(p, "GET", "/orders", {"X-Api-Key": "key_free_4f9a", "X-Consumer-Id": "globex-pro", "X-Scopes": "admin"})
    print("  client sent X-Consumer-Id: globex-pro, service saw:", b)
    assert b == {"consumer": "acme-free", "scopes": "orders:read"}
    st, _, b = call(svc.server_port, "GET", "/orders", {"X-Consumer-Id": "globex-pro", "X-Scopes": "admin"})
    print("  same forged headers sent straight to the service ->", st, b["error"])
    assert st == 401

    print("\n-- per-consumer token bucket (free plan: burst 5, 1 token/s; clock frozen) --")
    statuses, last = [], None
    for _ in range(7):
        st, last, _ = call(p, "GET", "/orders", {"X-Api-Key": "key_free_4f9a"})
        statuses.append(st)
    print("  7 calls in the same instant:", statuses)
    print("  headers on the 429:", {k: last[k] for k in ("RateLimit-Policy", "RateLimit", "Retry-After")})
    # the identity-propagation call above already spent 1 token, so 4 more pass
    assert statuses == [200] * 4 + [429] * 3 and last["Retry-After"] == "1"
    clock.t += 2.0
    st, h, _ = call(p, "GET", "/orders", {"X-Api-Key": "key_free_4f9a"})
    print("  2 s later:", st, "RateLimit:", h["RateLimit"])
    assert st == 200
    st, _, _ = call(p, "GET", "/orders", {"X-Api-Key": "key_pro_77c1"})
    assert st == 200, "one consumer's exhaustion never affects another"

    print("\n-- local vs global limits with 3 gateway replicas behind a load balancer --")
    burst = PLANS["free"][0]
    for mode in ("local", "global"):
        c2 = Clock()
        shared = BucketStore(c2)
        stores = [BucketStore(c2) for _ in range(3)] if mode == "local" else [shared] * 3
        allowed = sum(stores[i % 3].take("consumer:acme-free", *PLANS["free"])[0] for i in range(30))
        print(f"  {mode:6s}: 30 requests round-robined over 3 replicas -> {allowed} allowed (plan says {burst})")
        assert allowed == (3 * burst if mode == "local" else burst)

    gw.shutdown()
    svc.shutdown()
    print("\nOK")


if __name__ == "__main__":
    demo()
