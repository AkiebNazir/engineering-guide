"""
LAB 02 (basic) - A chat server: rooms, join/leave, broadcast, and a JSON message protocol
=========================================================================================
You will learn
  * WebSocket gives you a pipe, NOT a protocol: you must invent message shapes yourself.
    A good minimum is a JSON envelope with a `type`:
        {"type": "join",  "room": "go"}
        {"type": "say",   "text": "hello"}                      client -> server
        {"type": "message", "room": "go", "from": "ana", "text": "hello"}   server -> clients
        {"type": "error", "code": "bad_request", "detail": "..."}
  * per-connection state lives in a handler coroutine (one per client) - no threads needed
  * a registry of connections per room; ALWAYS remove a connection in `finally`
    (clients vanish without saying goodbye)
  * broadcasting: send to everyone in the room, skipping the sender if you like
  * validating untrusted input: bad JSON or unknown types must produce an error message, never a crash

        Ana ---say--->  [ server: rooms = {"go": {Ana, Ben}, "py": {Cy}} ]  ---message--> Ben
                                                                            (not to Cy: other room)

Needs   pip install websockets
Run it  python 02_chat_rooms_broadcast.py
Serve   python 02_chat_rooms_broadcast.py --serve      (then: python -m websockets ws://localhost:8765)
"""
import asyncio
import json
import sys
from collections import defaultdict

from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed

ROOMS: dict[str, set] = defaultdict(set)        # room name -> set of connections


def error(code: str, detail: str) -> str:
    return json.dumps({"type": "error", "code": code, "detail": detail})


async def handler(ws):
    name = f"user-{id(ws) % 1000:03d}"
    room: str | None = None
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                kind = msg["type"]
            except (json.JSONDecodeError, KeyError, TypeError):
                await ws.send(error("bad_request", "messages must be JSON objects with a 'type'"))
                continue                                                # a bad message must not kill the connection

            if kind == "hello":
                name = str(msg.get("name", name))[:20]
            elif kind == "join":
                if room:
                    ROOMS[room].discard(ws)
                room = str(msg.get("room", ""))[:30]
                ROOMS[room].add(ws)
                broadcast(ROOMS[room], json.dumps({"type": "notice", "text": f"{name} joined {room}",
                                                   "members": len(ROOMS[room])}))
            elif kind == "say":
                if not room:
                    await ws.send(error("not_in_room", "join a room first"))
                    continue
                payload = json.dumps({"type": "message", "room": room, "from": name, "text": str(msg.get("text", ""))[:500]})
                broadcast(ROOMS[room] - {ws}, payload)                  # everyone in the room except the sender
            else:
                await ws.send(error("unknown_type", f"unknown message type {kind!r}"))
    except ConnectionClosed:
        pass
    finally:                                                            # ALWAYS clean up: clients vanish
        if room:
            ROOMS[room].discard(ws)
            if not ROOMS[room]:
                del ROOMS[room]                                         # do not leak empty rooms
            else:
                broadcast(ROOMS[room], json.dumps({"type": "notice", "text": f"{name} left {room}", "members": len(ROOMS[room])}))


async def client(port: int, name: str, room: str):
    ws = await connect(f"ws://127.0.0.1:{port}")
    await ws.send(json.dumps({"type": "hello", "name": name}))
    await ws.send(json.dumps({"type": "join", "room": room}))
    return ws


async def next_msg(ws, kind: str = "message"):
    while True:                                                         # skip notices until the kind we want
        m = json.loads(await asyncio.wait_for(ws.recv(), 2))
        if m["type"] == kind:
            return m


async def main(port: int = 0):
    async with serve(handler, "127.0.0.1", port) as server:
        port = server.sockets[0].getsockname()[1]
        ana, ben, cy = await client(port, "ana", "go"), await client(port, "ben", "go"), await client(port, "cy", "py")

        print("== broadcast within a room ==")
        await ana.send(json.dumps({"type": "say", "text": "anyone here?"}))
        m = await next_msg(ben)
        print(f"  ben received: [{m['room']}] {m['from']}: {m['text']}")
        assert (m["from"], m["text"], m["room"]) == ("ana", "anyone here?", "go")

        print("\n== rooms are isolated: cy (room py) must NOT hear it ==")
        try:
            await asyncio.wait_for(next_msg(cy), 0.3)
            raise AssertionError("cy received a message from another room")
        except asyncio.TimeoutError:
            print("  cy heard nothing (as intended)")

        print("\n== the sender does not get an echo of their own message ==")
        try:
            await asyncio.wait_for(next_msg(ana), 0.3)
            raise AssertionError("ana received her own message")
        except asyncio.TimeoutError:
            print("  ana got no echo")

        print("\n== bad input produces error messages, not crashes ==")
        await ben.send("this is not json")
        e = await next_msg(ben, "error")
        print("  ->", e["code"], "-", e["detail"])
        await ben.send(json.dumps({"type": "dance"}))
        e = await next_msg(ben, "error")
        print("  ->", e["code"], "-", e["detail"])
        assert e["code"] == "unknown_type"
        await cy.send(json.dumps({"type": "join", "room": "py"}))                       # still alive
        await ben.send(json.dumps({"type": "say", "text": "still connected"}))
        assert (await next_msg(ana))["text"] == "still connected"

        print("\n== a client vanishes: cleanup and notice ==")
        await ben.close()
        n = await next_msg(ana, "notice")
        while "left" not in n["text"]:
            n = await next_msg(ana, "notice")
        print("  ana was told:", n["text"], f"({n['members']} left in room)")
        assert n["members"] == 1
        await asyncio.sleep(0.05)
        print("  rooms on server:", {k: len(v) for k, v in ROOMS.items()})

        await ana.close(); await cy.close()
        await asyncio.sleep(0.1)
        assert not ROOMS, "empty rooms must be removed"
    print("\nOK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        async def forever():
            async with serve(handler, "127.0.0.1", 8765):
                print("chat server on ws://localhost:8765")
                await asyncio.Future()
        asyncio.run(forever())
    else:
        asyncio.run(main())
