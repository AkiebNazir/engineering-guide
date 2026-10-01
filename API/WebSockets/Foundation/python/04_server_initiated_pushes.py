"""
FOUNDATION LEVEL 04 - The server speaks first: unsolicited pushes
=====================================================================
Level 03's broadcast was still triggered by a client message. This level
removes even that. Here the server sends messages that NO client asked for,
on a timer, driven entirely by something happening on the server side.

This is the capability REST fundamentally lacks. With HTTP, a server can only
ever answer; if it has news, it must wait to be asked (polling) or hold a
request open (long polling). With a WebSocket, the connection is already open
in both directions, so the server just... writes.

You will learn
  * a connection handler can run a background task that WRITES while the main
    loop READS - full duplex means genuinely simultaneous, not taking turns
  * asyncio.create_task + a `finally` cancel: the standard way to own a
    per-connection background job without leaking it when the client leaves
  * that the client must be built to accept messages at any time (a `recv`
    loop), not to expect one reply per send
  * why this replaces polling entirely: the client stops asking "anything new?"
    and the server stops answering "no" thousands of times
  * an important footgun: two tasks writing to one connection need care -
    concurrent sends on the same connection must not interleave mid-message

Run it   python 04_server_initiated_pushes.py
"""
import asyncio
import json

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

TICK_INTERVAL = 0.05  # tiny, so the demo finishes fast; a real one might be 1-30s


async def ticker(websocket) -> None:
    """A background job that pushes a message every TICK_INTERVAL forever.

    Nothing here reads from the client. It is purely the server having news
    and delivering it - a metrics update, a price change, a job finishing.
    """
    n = 0
    while True:
        await asyncio.sleep(TICK_INTERVAL)
        n += 1
        await websocket.send(json.dumps({"type": "tick", "payload": n}))


async def push_handler(websocket):
    # Start pushing IMMEDIATELY, before the client has said a single word.
    task = asyncio.create_task(ticker(websocket))
    try:
        # Meanwhile the same handler still reads. Reading and writing happen
        # at the same time on the same connection: that is "full duplex".
        async for raw in websocket:
            message = json.loads(raw)
            # Pretend answering takes real work (a database call, say). The
            # ticker keeps pushing throughout - which is exactly the situation
            # the client below must be written to survive.
            await asyncio.sleep(TICK_INTERVAL * 2.5)
            await websocket.send(json.dumps({
                "type": "pong",
                "payload": message["payload"],
            }))
    finally:
        # If the client vanishes, cancel the pusher or it lives on trying to
        # write into a dead connection forever.
        task.cancel()


async def demo(port: int) -> None:
    async with connect(f"ws://127.0.0.1:{port}") as ws:
        print("== the client connects and then says NOTHING ==")
        ticks = []
        for _ in range(3):
            message = json.loads(await ws.recv())
            print(f"  <- pushed by the server, unrequested: {message}")
            ticks.append(message["payload"])
        # We sent zero messages and received three. REST cannot produce this.
        assert ticks == [1, 2, 3]

        print("\n== pushes keep arriving WHILE the client does its own asking ==")
        await ws.send(json.dumps({"type": "ping", "payload": "are you there"}))

        # The crucial client-side lesson: the next message off the pipe might
        # be our answer, or it might be another tick. A WebSocket client must
        # be written as an event loop ("handle whatever arrives"), never as
        # "send, then assume the next message is my reply".
        saw_pong = False
        more_ticks = 0
        for _ in range(6):
            message = json.loads(await ws.recv())
            if message["type"] == "pong":
                print(f"  <- our own answer arrived: {message}")
                saw_pong = True
                break
            more_ticks += 1
            print(f"  <- another unrequested tick while we waited: {message}")

        assert saw_pong, "the reply to our ping should have arrived"
        print(f"  (ticks that interleaved before our reply: {more_ticks})")
        # If this were REST, nothing could possibly have arrived between our
        # request and its response. Here, things did.
        assert more_ticks >= 1, "a tick should have arrived before the pong"

        await ws.close(code=1000)
    print("\nOK")


async def main() -> None:
    async with serve(push_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
