"""
FOUNDATION LEVEL 09 - Authentication: checked once, at the door
===================================================================
Authentication answers exactly ONE question: "do we recognise this peer at
all?" It says nothing about what they may do - that is level 10, authorization,
and it is deliberately a separate idea.

What is different from REST is WHEN. A REST client proves who it is on every
single request, so there is nowhere else to put the check. A WebSocket client
proves who it is ONCE, and that identity then covers every message for the
entire life of the connection - possibly hours. Authenticate at the door and
you never pay for it again; get it wrong and an imposter has a long, warm seat.

TWO PLACES TO DO IT, and both are shown below:
  A) DURING the handshake, before the upgrade completes. The best option: an
     unauthenticated peer never gets a WebSocket at all, just an HTTP 401.
     Downside: browsers cannot set headers on `new WebSocket(...)`, so the
     token has to ride in the query string (and therefore in access logs) or
     in a cookie, or be a short-lived single-use "ticket".
  B) As the FIRST MESSAGE after connecting. The connection exists but is not
     usable until it arrives; a deadline stops an anonymous peer squatting.
     This is what browsers usually end up doing.

You will learn
  * rejecting before the upgrade, with `process_request` -> a real HTTP 401
  * that a client sees a failed upgrade as an InvalidStatus exception, not a
    closed WebSocket - because there never was a WebSocket
  * the first-message variant, and closing with 1008 when the token is bad
  * why an auth deadline is mandatory in variant B (else you have a free
    resource for anyone who can open a socket)
  * attaching the identity to the connection object so every later message and
    level 10's role check can use it without re-verifying anything

Run it   python 09_authentication_at_connect_time.py
"""
import asyncio
import http
import json
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed, InvalidStatus

# A stand-in for "who is allowed in". A real system verifies a signed JWT or
# looks the token up in a store - see ../../labs/python/03_auth_origin_and_limits.py.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

AUTH_DEADLINE = 0.3  # seconds a client gets to send its auth message (variant B)


# =========================== variant A: at the door ===========================
def authenticate_upgrade(connection, request):
    """Runs BEFORE the 101 response. Return None to allow the upgrade, or an
    HTTP response to refuse it - in which case no WebSocket is ever created."""
    token = parse_qs(urlparse(request.path).query).get("token", [""])[0]
    identity = TOKENS.get(token)
    if identity is None:
        print(f"  [server] refusing upgrade: token={token!r}")
        return connection.respond(http.HTTPStatus.UNAUTHORIZED, "invalid or missing token\n")

    # Stash the identity on the connection. Every message for the rest of this
    # connection's life is now attributable, with no further token checks.
    connection.identity = identity
    print(f"  [server] upgrade allowed for {identity['user']} ({identity['role']})")
    return None


async def gated_handler(websocket):
    async for _ in websocket:
        # No auth code here at all: if this line runs, the peer is authenticated.
        await websocket.send(json.dumps(websocket.identity))


# ====================== variant B: first message after connect ======================
async def first_message_auth_handler(websocket):
    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=AUTH_DEADLINE)
    except asyncio.TimeoutError:
        # Without this deadline, anyone could hold connections open for free.
        print("  [server] no auth message in time -> closing 1008")
        await websocket.close(code=1008, reason="authentication timeout")
        return
    except ConnectionClosed:
        return

    message = json.loads(raw)
    identity = TOKENS.get(message.get("payload", "")) if message.get("type") == "auth" else None
    if identity is None:
        # 1008 policy violation is the conventional close code for "you failed
        # a rule of this service", authentication very much included.
        await websocket.close(code=1008, reason="authentication failed")
        return

    websocket.identity = identity
    await websocket.send(json.dumps({"type": "welcome", "payload": identity}))

    async for raw in websocket:
        await websocket.send(json.dumps({"type": "whoami", "payload": websocket.identity}))


async def demo(gated_port: int, first_msg_port: int) -> None:
    gated = f"ws://127.0.0.1:{gated_port}"

    print("== A. authenticated during the handshake: rejected peers get HTTP, not WS ==")
    for label, query in [("no token", ""), ("bad token", "?token=forged")]:
        try:
            async with connect(gated + query):
                raise AssertionError("expected the upgrade to be refused")
        except InvalidStatus as exc:
            print(f"  {label:10} -> HTTP {exc.response.status_code} "
                  f"{exc.response.reason_phrase} (no WebSocket was ever created)")
            assert exc.response.status_code == 401

    for token, expected in [("alice-token", "admin"), ("bob-token", "viewer")]:
        async with connect(f"{gated}?token={token}") as ws:
            await ws.send("who am I?")
            identity = json.loads(await ws.recv())
            print(f"  {token:12} -> upgraded; server knows us as {identity}")
            assert identity["role"] == expected
            await ws.close(code=1000)

    print("\n  the identity was checked ONCE and covered the whole session:")
    async with connect(f"{gated}?token=alice-token") as ws:
        for i in range(3):
            await ws.send(f"message {i}")
            assert json.loads(await ws.recv())["user"] == "alice"
        print("  3 messages, still alice, zero further token checks")
        await ws.close(code=1000)

    print("\n== B. authenticated by the first message, with a deadline ==")
    first = f"ws://127.0.0.1:{first_msg_port}"

    async with connect(first) as ws:
        await ws.send(json.dumps({"type": "auth", "payload": "bob-token"}))
        welcome = json.loads(await ws.recv())
        print("  good token  ->", welcome)
        assert welcome["type"] == "welcome" and welcome["payload"]["user"] == "bob"
        await ws.send(json.dumps({"type": "whoami"}))
        print("  later message still knows us:", json.loads(await ws.recv()))
        await ws.close(code=1000)

    async with connect(first) as ws:
        await ws.send(json.dumps({"type": "auth", "payload": "forged"}))
        try:
            await ws.recv()
            raise AssertionError("expected a close")
        except ConnectionClosed:
            pass
        print(f"  bad token   -> closed {ws.close_code} {ws.close_reason!r}")
        assert ws.close_code == 1008

    async with connect(first) as ws:
        print(f"  saying nothing for {AUTH_DEADLINE}s...")
        try:
            await ws.recv()
            raise AssertionError("expected a close")
        except ConnectionClosed:
            pass
        print(f"  no auth at all -> closed {ws.close_code} {ws.close_reason!r}")
        assert ws.close_code == 1008
    print("\nOK")


async def main() -> None:
    async with serve(gated_handler, "127.0.0.1", 0,
                     process_request=authenticate_upgrade) as gated, \
               serve(first_message_auth_handler, "127.0.0.1", 0) as first:
        await demo(
            gated.sockets[0].getsockname()[1],
            first.sockets[0].getsockname()[1],
        )


if __name__ == "__main__":
    asyncio.run(main())
