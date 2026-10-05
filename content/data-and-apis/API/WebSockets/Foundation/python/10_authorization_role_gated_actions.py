"""
FOUNDATION LEVEL 10 - Authorization: what this connection is allowed to DO
==============================================================================
Level 09 answered "who is this?" once, at the door. Authorization answers a
different question - "may they do THIS?" - and it must be answered again for
every single message, because different messages demand different rights.

That split is more visible here than in REST. A REST server checks permissions
per request, so authentication and authorization tend to run back to back in
the same middleware and blur together. In a WebSocket the two are separated in
TIME: identity is established once, at connect; permission is evaluated over
and over, per message, for the hours that follow. Identity is a property of the
connection; permission is a property of the action.

The other WebSocket-specific rule: a refusal is a MESSAGE, not a disconnect.
REST has a natural place to put "no" - a 403 response, and the request is over.
Here, the client is still sitting on an open connection, so you must answer on
it. Silently ignoring a forbidden message is the worst option of all: the
client cannot tell "denied" from "lost".

You will learn
  * authentication (level 09) vs authorization: recognised vs permitted, and
    why 401's WebSocket analogue happens at connect while 403's happens per message
  * a permission table mapping message type -> allowed roles
  * replying with an error message on the SAME connection, never a silent drop
  * that the connection stays fully usable after a refusal - the client can go
    straight on doing the things it IS allowed to do
  * when a refusal SHOULD escalate to a close: repeated abuse, which is a
    statement about the client rather than about one message (close 1008)

Run it   python 10_authorization_role_gated_actions.py
"""
import asyncio
import http
import json
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

# The whole authorization policy, in one readable place. Keeping it as DATA
# rather than scattering `if role == ...` through handlers is what makes a
# policy auditable.
PERMISSIONS = {
    "read":      {"admin", "viewer"},
    "broadcast": {"admin"},           # admin-only: it reaches every other client
    "kick":      {"admin"},           # admin-only: it disconnects someone
}

STRIKE_LIMIT = 3  # forbidden attempts tolerated before we stop being polite


def authenticate_upgrade(connection, request):
    token = parse_qs(urlparse(request.path).query).get("token", [""])[0]
    identity = TOKENS.get(token)
    if identity is None:
        return connection.respond(http.HTTPStatus.UNAUTHORIZED, "invalid token\n")
    connection.identity = identity   # level 09's job, done
    return None


async def authorizing_handler(websocket):
    strikes = 0
    role = websocket.identity["role"]

    async for raw in websocket:
        message = json.loads(raw)
        kind = message.get("type")
        allowed_roles = PERMISSIONS.get(kind, set())

        if role not in allowed_roles:
            strikes += 1
            print(f"  [server] DENIED {websocket.identity['user']} ({role}) -> {kind!r}"
                  f"  [strike {strikes}/{STRIKE_LIMIT}]")
            # The refusal travels back down the same pipe the request came up.
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {
                    "code": "forbidden",
                    "detail": f"role {role!r} may not {kind!r}; "
                              f"allowed: {sorted(allowed_roles) or 'nobody'}",
                },
            }))
            if strikes >= STRIKE_LIMIT:
                # Now we are judging the CLIENT, not the message - so a close
                # is the right response, where a single denial was not.
                await websocket.close(code=1008, reason="too many forbidden attempts")
                return
            continue

        print(f"  [server] ALLOWED {websocket.identity['user']} ({role}) -> {kind!r}")
        await websocket.send(json.dumps({
            "type": kind,
            "payload": f"{kind} performed by {websocket.identity['user']}",
        }))


async def demo(port: int) -> None:
    base = f"ws://127.0.0.1:{port}"

    async def call(ws, kind):
        await ws.send(json.dumps({"type": kind}))
        return json.loads(await ws.recv())

    print("== the admin may do everything ==")
    async with connect(f"{base}?token=alice-token") as ws:
        for kind in ("read", "broadcast", "kick"):
            reply = await call(ws, kind)
            print(f"  alice {kind:10} -> {reply['type']}: {reply['payload']}")
            assert reply["type"] == kind
        await ws.close(code=1000)

    print("\n== the viewer is authenticated, but not permitted ==")
    async with connect(f"{base}?token=bob-token") as ws:
        # Identity is not in question - bob got through level 09's door.
        reply = await call(ws, "read")
        print(f"  bob   read       -> {reply['type']}: {reply['payload']}")
        assert reply["type"] == "read"

        reply = await call(ws, "broadcast")
        print(f"  bob   broadcast  -> {reply['type']}: {reply['payload']['detail']}")
        assert reply["type"] == "error" and reply["payload"]["code"] == "forbidden"

        # THE POINT: the refusal did not end the session. bob is still here,
        # still authenticated, and can carry on with what he may do.
        reply = await call(ws, "read")
        print(f"  bob   read       -> {reply['type']}: {reply['payload']}"
              "   (still connected after being refused)")
        assert reply["type"] == "read"
        assert ws.close_code is None
        await ws.close(code=1000)

    print("\n== repeated abuse IS about the client, so it earns a close ==")
    async with connect(f"{base}?token=bob-token") as ws:
        for attempt in range(1, STRIKE_LIMIT + 1):
            reply = await call(ws, "kick")
            print(f"  attempt {attempt} -> {reply['payload']['code']}")
            assert reply["type"] == "error"
        try:
            await ws.recv()
            raise AssertionError("expected a close after the strike limit")
        except ConnectionClosed:
            pass
        print(f"  after {STRIKE_LIMIT} strikes -> closed {ws.close_code} {ws.close_reason!r}")
        assert ws.close_code == 1008
    print("\nOK")


async def main() -> None:
    async with serve(authorizing_handler, "127.0.0.1", 0,
                     process_request=authenticate_upgrade) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
