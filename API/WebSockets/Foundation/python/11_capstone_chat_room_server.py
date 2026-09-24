"""
FOUNDATION LEVEL 11 (capstone) - A real chat-room server
============================================================
Everything from levels 00-10, assembled into one program that does something
you would actually ship: a chat server with rooms, authentication, broadcast,
a moderator action, and clean shutdown.

Nothing new is introduced here. That is the point - if this file reads as
obvious, Foundation has done its job and ../../labs/ is the next step, not a
jump. Read it as a map of where each earlier level ended up:

  level 00  one handler per connection, living for the whole session
  level 02  every message is {"type": ..., "payload": ...}, routed on `type`
  level 03  a registry of live connections, so we can fan out to a room
  level 04  the server pushes join/leave notices nobody asked for
  level 05  bad messages get an error reply, never a dropped session
  level 06  every ending has a deliberate close code
  level 07  the library heartbeats for us (ping_interval on serve)
  level 08  connection-scoped logging, message-scoped recovery
  level 09  a token in the query string, checked before the upgrade
  level 10  `kick` is admin-only, and refusals come back as messages

You will learn
  * how the pieces compose: auth decides WHO, the room registry decides WHERE,
    the type table decides WHAT, and the role table decides WHETHER
  * per-room fan-out rather than per-server: the registry is a dict of sets
  * that state (who is in which room) lives naturally in the server's memory
    because connections are long-lived - the thing REST forbids by design
  * a moderation action that closes SOMEONE ELSE'S connection with a code
  * that cleanup belongs in `finally`, so a crash still empties the room

Run it        python 11_capstone_chat_room_server.py
Keep serving  python 11_capstone_chat_room_server.py --serve
              (then: npx wscat -c "ws://localhost:8080/ws?token=alice-token&room=lobby")
"""
import asyncio
import http
import json
import sys
from collections import defaultdict
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "member"},
    "carol-token": {"user": "carol", "role": "member"},
}

PERMISSIONS = {
    "say": {"admin", "member"},
    "who": {"admin", "member"},
    "kick": {"admin"},           # moderation: members must not have this
}

# room name -> set of live connections in it. The whole reason a chat server
# needs WebSockets: this dict lets us speak to people who are not asking.
ROOMS: dict[str, set] = defaultdict(set)


def authenticate(connection, request):
    """Level 09: authenticate and pick a room BEFORE the upgrade completes."""
    params = parse_qs(urlparse(request.path).query)
    identity = TOKENS.get(params.get("token", [""])[0])
    if identity is None:
        return connection.respond(http.HTTPStatus.UNAUTHORIZED, "invalid token\n")
    room = params.get("room", ["lobby"])[0]
    connection.identity = {**identity, "room": room}
    return None


async def send_to_room(room: str, message: dict, exclude=None) -> int:
    """Level 03: fan out to one room, tolerating clients that just died."""
    targets = [c for c in ROOMS[room] if c is not exclude]
    results = await asyncio.gather(
        *(c.send(json.dumps(message)) for c in targets), return_exceptions=True
    )
    return sum(1 for r in results if not isinstance(r, Exception))


async def handle_message(websocket, raw: str) -> None:
    """One message. Raising in here is safe - the recovery wrapper catches it."""
    me = websocket.identity
    room = me["room"]

    message = json.loads(raw)                                    # level 05
    kind = message.get("type")
    if kind not in PERMISSIONS:
        raise ValueError(f"unknown type {kind!r}; known: {sorted(PERMISSIONS)}")
    if me["role"] not in PERMISSIONS[kind]:                      # level 10
        await websocket.send(json.dumps({
            "type": "error",
            "payload": {"code": "forbidden",
                        "detail": f"role {me['role']!r} may not {kind!r}"},
        }))
        return

    if kind == "say":
        text = message.get("payload")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("payload must be a non-empty string")
        await send_to_room(room, {"type": "said",
                                  "payload": {"from": me["user"], "text": text}})

    elif kind == "who":
        members = sorted(c.identity["user"] for c in ROOMS[room])
        await websocket.send(json.dumps({"type": "who", "payload": members}))

    elif kind == "kick":
        target_name = message.get("payload")
        victim = next((c for c in ROOMS[room]
                       if c.identity["user"] == target_name), None)
        if victim is None:
            raise ValueError(f"nobody called {target_name!r} is in {room!r}")
        # Closing someone ELSE's connection, with a code that explains itself.
        await victim.close(code=4003, reason=f"kicked by {me['user']}")
        await send_to_room(room, {"type": "kicked",
                                  "payload": {"user": target_name,
                                              "by": me["user"]}})


async def connection_handler(websocket):
    """Level 08: connection-scoped logging and room bookkeeping outside,
    message-scoped recovery inside."""
    me = websocket.identity
    room = me["room"]
    ROOMS[room].add(websocket)
    print(f"  [log] JOIN  {me['user']} ({me['role']}) -> room {room!r} "
          f"(now {len(ROOMS[room])})")

    # Level 04: an unsolicited push to everyone already here.
    await send_to_room(room, {"type": "joined", "payload": me["user"]}, exclude=websocket)

    try:
        async for raw in websocket:
            try:
                await handle_message(websocket, raw)
            except Exception as exc:
                # One bad message must not cost this user their session.
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"code": "bad_message", "detail": str(exc)},
                }))
    except ConnectionClosed:
        pass
    finally:
        ROOMS[room].discard(websocket)
        print(f"  [log] LEAVE {me['user']} code={websocket.close_code} "
              f"(room {room!r} now {len(ROOMS[room])})")
        await send_to_room(room, {"type": "left", "payload": me["user"]})


async def demo(port: int) -> None:
    def url(token, room="lobby"):
        return f"ws://127.0.0.1:{port}/ws?token={token}&room={room}"

    async def call(ws, kind, payload=None):
        await ws.send(json.dumps({"type": kind, "payload": payload}))
        return json.loads(await ws.recv())

    print("== an unauthenticated client never gets in (level 09) ==")
    try:
        async with connect(url("forged")):
            raise AssertionError("expected 401")
    except Exception as exc:
        print(f"  forged token -> {type(exc).__name__}: upgrade refused")

    print("\n== three authenticated clients join the lobby ==")
    async with connect(url("alice-token")) as alice, \
               connect(url("bob-token")) as bob, \
               connect(url("carol-token")) as carol:

        # alice and bob each get a "joined" push for the people after them.
        assert json.loads(await alice.recv())["payload"] == "bob"
        assert json.loads(await alice.recv())["payload"] == "carol"
        assert json.loads(await bob.recv())["payload"] == "carol"

        reply = await call(alice, "who")
        print("  who -> ", reply["payload"])
        assert reply["payload"] == ["alice", "bob", "carol"]

        print("\n== bob says something; everyone in the room hears it (level 03) ==")
        await bob.send(json.dumps({"type": "say", "payload": "hello lobby"}))
        heard = [json.loads(await c.recv()) for c in (alice, bob, carol)]
        for name, m in zip(("alice", "bob  ", "carol"), heard):
            print(f"  {name} <- {m['type']}: {m['payload']}")
        assert all(m["payload"] == {"from": "bob", "text": "hello lobby"} for m in heard)

        print("\n== a bad message costs one message, not the session (level 05) ==")
        reply = await call(bob, "say", "")
        print("  empty say  ->", reply["payload"]["detail"])
        assert reply["payload"]["code"] == "bad_message"
        reply = await call(bob, "teleport", None)
        print("  bad type   ->", reply["payload"]["detail"])
        assert reply["payload"]["code"] == "bad_message"

        print("\n== moderation is admin-only (level 10) ==")
        reply = await call(bob, "kick", "carol")
        print("  bob kicking carol   ->", reply["payload"]["detail"])
        assert reply["payload"]["code"] == "forbidden"

        # carol is untouched: a refused kick has no victim.
        reply = await call(carol, "who")
        assert "carol" in reply["payload"]
        print("  carol is still here:", reply["payload"])

        print("\n== alice CAN kick, and carol learns why (level 06) ==")
        await alice.send(json.dumps({"type": "kick", "payload": "carol"}))
        try:
            await carol.recv()
            raise AssertionError("expected carol to be closed")
        except ConnectionClosed:
            pass
        print(f"  carol closed with {carol.close_code} {carol.close_reason!r}")
        assert carol.close_code == 4003

        # The room gets TWO pushes now: the "kicked" announcement we sent, and
        # the "left" notice from carol's own `finally` block. Their relative
        # order is not guaranteed - two independent tasks are writing - so a
        # correct client must handle events as a SET, never as a script.
        for name, ws in (("alice", alice), ("bob  ", bob)):
            seen = {json.loads(await ws.recv())["type"] for _ in range(2)}
            print(f"  {name} saw: {sorted(seen)}")
            assert seen == {"kicked", "left"}

        reply = await call(alice, "who")
        print("  who -> ", reply["payload"])
        assert reply["payload"] == ["alice", "bob"]

        await alice.close(code=1000, reason="done")
        await bob.close(code=1000, reason="done")

    print("\n== rooms are empty again once everyone leaves ==")
    for _ in range(50):
        if not any(ROOMS.values()):
            break
        await asyncio.sleep(0.01)
    print("  occupants left in every room:", {r: len(c) for r, c in ROOMS.items()})
    assert not any(ROOMS.values())
    print("\nOK")


async def serve_forever() -> None:
    print("listening on ws://localhost:8080/ws")
    print('  try: npx wscat -c "ws://localhost:8080/ws?token=alice-token&room=lobby"')
    print('  then: {"type":"say","payload":"hi"}   /   {"type":"who"}')
    async with serve(connection_handler, "127.0.0.1", 8080,
                     process_request=authenticate, ping_interval=20) as server:
        await server.serve_forever()


async def main() -> None:
    # ping_interval is level 07's keepalive, switched on with one argument.
    async with serve(connection_handler, "127.0.0.1", 0,
                     process_request=authenticate, ping_interval=20) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    if "--serve" in sys.argv:
        asyncio.run(serve_forever())
    else:
        asyncio.run(main())
