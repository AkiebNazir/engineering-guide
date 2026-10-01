"""
LAB 03 (advanced) - Securing a WebSocket: Origin checks, three ways to authenticate, size limits
================================================================================================
You will learn
  * Browsers do NOT apply CORS to WebSockets. Any web page can open a socket to your server and the
    browser attaches the user's COOKIES. Without an Origin check that is Cross-Site WebSocket
    Hijacking (CSWSH): evil.com talks to your API as the logged-in user.
  * the browser WebSocket API cannot set an Authorization header, so how do you authenticate?
        A. token in the URL query   ws://host/ws?token=...   simple, BUT ends up in access logs/history
        B. token in Sec-WebSocket-Protocol                    works during the handshake, not logged as URL
        C. authenticate with the FIRST MESSAGE + a timeout     the connection exists, but is unauthenticated
                                                               until proven (so enforce a deadline!)
        (D. a short-lived one-time TICKET from an HTTP endpoint - see the Go track, lab 5)
  * rejecting during the HANDSHAKE (HTTP 401/403, cheapest: no socket is ever opened) vs after it
    (close code 4401 - application codes live in 4000-4999)
  * limiting message size (close code 1009) so one client cannot send a 1 GB "message"
  * close codes:  1000 normal, 1008 policy violation, 1009 message too big, 4xxx yours

Needs   pip install websockets
Run it  python 03_auth_origin_and_limits.py
"""
import asyncio
import json
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed, InvalidStatus

TOKENS = {"tok-alice": "alice", "tok-bob": "bob"}
ALLOWED_ORIGINS = ["https://app.example.com"]
access_log: list[str] = []                       # what an ordinary web server would write to disk


def user_from_query(request) -> str | None:
    token = parse_qs(urlparse(request.path).query).get("token", [""])[0]
    return TOKENS.get(token)


def user_from_subprotocol(request) -> str | None:
    offered = [p.strip() for p in request.headers.get("Sec-WebSocket-Protocol", "").split(",")]
    return TOKENS.get(offered[1]) if len(offered) == 2 and offered[0] == "bearer" else None


def process_request(connection, request):
    """Runs during the HTTP handshake. Return a response to REFUSE; return None to allow."""
    access_log.append(f"GET {request.path}")                            # note: includes the query string!
    path = urlparse(request.path).path
    if path == "/ws-query" and not user_from_query(request):
        return connection.respond(HTTPStatus.UNAUTHORIZED, "invalid token\n")
    if path == "/ws-subprotocol" and not user_from_subprotocol(request):
        return connection.respond(HTTPStatus.UNAUTHORIZED, "invalid token\n")
    return None


def select_subprotocol(connection, subprotocols):
    return "bearer" if "bearer" in subprotocols else None              # we never echo the token back


async def handler(ws):
    path = urlparse(ws.request.path).path
    if path == "/ws-query":
        user = user_from_query(ws.request)
    elif path == "/ws-subprotocol":
        user = user_from_subprotocol(ws.request)
    else:                                                               # C: authenticate with the first message
        try:
            first = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))    # DEADLINE for the auth message
            user = TOKENS.get(first.get("token")) if first.get("type") == "auth" else None
        except (asyncio.TimeoutError, json.JSONDecodeError, AttributeError):
            user = None
        if not user:
            await ws.close(code=4401, reason="authentication required")
            return
    await ws.send(json.dumps({"type": "welcome", "user": user}))
    try:
        async for message in ws:
            await ws.send(json.dumps({"type": "echo", "user": user, "len": len(message)}))
    except ConnectionClosed:
        pass                                                            # abnormal closes (e.g. 1009) are routine, not bugs


async def attempt(label: str, url: str, **kw):
    """Try to connect; report the outcome the way a client would see it."""
    try:
        async with connect(url, **kw) as ws:
            return ws
    except InvalidStatus as e:
        print(f"  {label:<38} refused in HANDSHAKE: HTTP {e.response.status_code}")
        return e.response.status_code


async def main():
    async with serve(handler, "127.0.0.1", 0, origins=ALLOWED_ORIGINS, process_request=process_request,
                     select_subprotocol=select_subprotocol, subprotocols=["bearer"], max_size=1024) as server:
        base = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        good_origin = {"Origin": "https://app.example.com"}

        print("== 1. Origin check (defence against Cross-Site WebSocket Hijacking) ==")
        r = await attempt("Origin: https://evil.example.net", f"{base}/ws-query?token=tok-alice",
                          additional_headers={"Origin": "https://evil.example.net"})
        assert r == 403
        async with connect(f"{base}/ws-query?token=tok-alice", additional_headers=good_origin) as ws:
            print("  Origin: https://app.example.com        accepted:", json.loads(await ws.recv()))
        print("  (non-browser clients send no Origin at all, so Origin is NOT authentication - it only")
        print("   protects users whose BROWSER attaches their cookies to a cross-site request)")

        print("\n== 2. Auth A: token in the query string ==")
        r = await attempt("no token", f"{base}/ws-query", additional_headers=good_origin)
        assert r == 401
        async with connect(f"{base}/ws-query?token=tok-bob", additional_headers=good_origin) as ws:
            print("  valid token                            accepted:", json.loads(await ws.recv()))
        print("  server access log now contains:", access_log[-1], " <- the SECRET is in your logs!")
        assert "tok-bob" in access_log[-1]

        print("\n== 3. Auth B: token in Sec-WebSocket-Protocol ==")
        r = await attempt("bad subprotocol token", f"{base}/ws-subprotocol", subprotocols=["bearer", "nope"],
                          additional_headers=good_origin)
        assert r == 401
        async with connect(f"{base}/ws-subprotocol", subprotocols=["bearer", "tok-alice"], additional_headers=good_origin) as ws:
            print("  valid token                            accepted:", json.loads(await ws.recv()), "| negotiated:", ws.subprotocol)
        print("  server access log now contains:", access_log[-1], " <- no secret in the URL")
        assert "tok-alice" not in access_log[-1]

        print("\n== 4. Auth C: the first message, with a deadline ==")
        async with connect(f"{base}/ws-first", additional_headers=good_origin) as ws:
            await ws.send(json.dumps({"type": "auth", "token": "tok-alice"}))
            print("  sent auth message                      accepted:", json.loads(await ws.recv()))
        async with connect(f"{base}/ws-first", additional_headers=good_origin) as ws:
            await ws.send(json.dumps({"type": "auth", "token": "wrong"}))
            try:
                await ws.recv()
            except ConnectionClosed as e:
                print(f"  wrong token                            closed AFTER handshake: code {e.rcvd.code} {e.rcvd.reason!r}")
                assert e.rcvd.code == 4401
        async with connect(f"{base}/ws-first", additional_headers=good_origin) as ws:
            try:
                await asyncio.wait_for(ws.recv(), 2)                      # say nothing: the server's 0.5s deadline fires
            except ConnectionClosed as e:
                print(f"  silent client                          closed by the auth deadline: code {e.rcvd.code}")
                assert e.rcvd.code == 4401

        print("\n== 5. message size limit (max_size=1024) ==")
        async with connect(f"{base}/ws-query?token=tok-alice", additional_headers=good_origin) as ws:
            await ws.recv()
            await ws.send("x" * 500)
            print("  500 bytes                              ->", json.loads(await ws.recv()))
            await ws.send("x" * 5000)
            try:
                await ws.recv()
            except ConnectionClosed as e:
                print(f"  5000 bytes                             -> server closed with code {e.rcvd.code} (message too big)")
                assert e.rcvd.code == 1009
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
