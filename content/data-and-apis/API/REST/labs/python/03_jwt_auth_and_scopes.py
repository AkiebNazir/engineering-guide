"""
LAB 03 (advanced) - Authentication, authorization and object ownership
=======================================================================
You will learn
  * how a JWT (HS256) is built and verified - written by hand so nothing is magic
  * 401 (who are you?) vs 403 (you may not) vs 404 (hide what you do not own)
  * scopes as a FastAPI dependency:  Depends(require_scope("orders:write"))
  * BOLA / IDOR - the #1 API vulnerability: checking "logged in" but not "is it YOURS?"
  * attacks a verifier must reject: tampered payload, expired token, `alg: none`

Needs   pip install fastapi httpx
Run it  python 03_jwt_auth_and_scopes.py
(In production use a maintained library such as PyJWT or Authlib - never roll your own.)
"""
import base64
import hashlib
import hmac
import json
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

SECRET = b"change-me-and-load-from-env"
ISSUER = "https://auth.example.com"


# ------------------------------------------------------------ JWT by hand ---
def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_jwt(claims: dict, ttl: int = 900) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    claims = {"iss": ISSUER, "iat": int(time.time()), "exp": int(time.time()) + ttl, **claims}
    signing_input = f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(claims).encode())}"
    sig = hmac.new(SECRET, signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{b64url(sig)}"


def verify_jwt(token: str) -> dict:
    try:
        head_b64, body_b64, sig_b64 = token.split(".")
        header = json.loads(b64url_decode(head_b64))
        if header.get("alg") != "HS256":              # rejects alg=none and algorithm-confusion tricks
            raise ValueError("unexpected algorithm")
        expected = hmac.new(SECRET, f"{head_b64}.{body_b64}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, b64url_decode(sig_b64)):   # constant-time compare
            raise ValueError("bad signature")
        claims = json.loads(b64url_decode(body_b64))
        if claims["exp"] < time.time():
            raise ValueError("token expired")
        if claims["iss"] != ISSUER:
            raise ValueError("wrong issuer")
        return claims
    except (ValueError, KeyError) as e:               # also covers bad base64 / json / split
        raise HTTPException(401, f"invalid token: {e}", headers={"WWW-Authenticate": "Bearer"})


# ------------------------------------------------------------ dependencies --
def current_user(authorization: str = Header(default="")) -> dict:
    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        raise HTTPException(401, "missing bearer token", headers={"WWW-Authenticate": "Bearer"})
    return verify_jwt(token)                          # 401 when anything is wrong


def require_scope(scope: str):
    def checker(user: dict = Depends(current_user)) -> dict:
        if scope not in user.get("scope", "").split():
            raise HTTPException(403, f"requires scope {scope}")       # authenticated but not allowed
        return user
    return checker


# ------------------------------------------------------------------- app ----
app = FastAPI()
ORDERS = {1: {"id": 1, "owner": "alice", "item": "book"}, 2: {"id": 2, "owner": "bob", "item": "lamp"}}
USERS = {"alice": "pw-alice", "bob": "pw-bob"}


@app.post("/login")
def login(creds: dict):
    if USERS.get(creds.get("username")) != creds.get("password"):
        raise HTTPException(401, "invalid credentials")               # generic on purpose
    scope = "orders:read orders:write" if creds["username"] == "alice" else "orders:read"
    return {"access_token": sign_jwt({"sub": creds["username"], "scope": scope}), "token_type": "bearer"}


@app.get("/orders/{order_id}")
def get_order(order_id: int, user: dict = Depends(require_scope("orders:read"))):
    order = ORDERS.get(order_id)
    if not order or order["owner"] != user["sub"]:    # ownership check on EVERY object access
        raise HTTPException(404, "order not found")   # 404 (not 403): do not reveal it exists
    return order


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, user: dict = Depends(require_scope("orders:write"))):
    if ORDERS.get(order_id, {}).get("owner") != user["sub"]:
        raise HTTPException(404, "order not found")
    del ORDERS[order_id]


def demo():
    c = TestClient(app)
    tok = lambda u: {"Authorization": "Bearer " + c.post("/login", json={"username": u, "password": f"pw-{u}"}).json()["access_token"]}

    print("no token          ->", c.get("/orders/1").status_code, "(401: who are you?)")
    assert c.get("/orders/1").status_code == 401
    assert c.post("/login", json={"username": "alice", "password": "wrong"}).status_code == 401

    print("alice, own order  ->", c.get("/orders/1", headers=tok("alice")).status_code)
    assert c.get("/orders/1", headers=tok("alice")).json()["item"] == "book"

    r = c.get("/orders/2", headers=tok("alice"))
    print("alice, bob's order->", r.status_code, "(404: BOLA blocked, existence hidden)")
    assert r.status_code == 404

    r = c.delete("/orders/2", headers=tok("bob"))
    print("bob DELETE        ->", r.status_code, r.json()["detail"], "(403: authenticated, lacks scope)")
    assert r.status_code == 403

    # ---- attacks -----------------------------------------------------------
    good = tok("alice")["Authorization"].split()[1]
    head, body, sig = good.split(".")
    forged_claims = json.loads(b64url_decode(body)); forged_claims["scope"] = "orders:read orders:write admin"
    tampered = f"{head}.{b64url(json.dumps(forged_claims).encode())}.{sig}"
    none_header = b64url(b'{"alg":"none"}')
    none_alg = f"{none_header}.{body}."
    expired = sign_jwt({"sub": "alice", "scope": "orders:read"}, ttl=-10)
    for name, bad in [("tampered payload", tampered), ("alg=none", none_alg), ("expired", expired)]:
        r = c.get("/orders/1", headers={"Authorization": f"Bearer {bad}"})
        print(f"attack {name:<17}->", r.status_code, r.json()["detail"])
        assert r.status_code == 401
    print("OK")


if __name__ == "__main__":
    demo()
