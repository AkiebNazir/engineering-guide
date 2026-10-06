"""
FOUNDATION LEVEL 03 - Broadcasting: one message in, many clients out
========================================================================
This is the level that justifies WebSockets existing. Everything so far was
still one client talking to one server, which HTTP can do perfectly well. Now:
one client sends a message, and EVERY connected client receives it - including
ones that were sitting there silent, having asked for nothing.

REST cannot do this at all. A REST server has no way to reach a client; it can
only answer clients who happen to be asking right now. A WebSocket server, by
contrast, holds a live handle to every connected client, so "tell everyone" is
just a loop over a set.

You will learn
  * the registry pattern: a module-level set of live connections, added on
    connect and - critically - removed in a `finally` so it cannot leak
  * fan-out: one inbound message becomes N outbound messages
  * that a broadcast is fire-and-forget: you must not let one slow or dead
    client block the other nine (hence `asyncio.gather` with exceptions returned)
  * that the sender usually gets its own message back too, because the simplest
    correct rule is "everyone in the room sees everything"
  * where this grows up: a "hub" goroutine/task owning the set, in
    ../../labs/golang/03_hub_pattern_chat and ../../labs/python/02_chat_rooms_broadcast.py

Run it   python 03_broadcasting_to_many_clients.py
"""
import asyncio

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

# Every currently-open connection. THIS is the thing REST does not have: a
# server-side list of clients you can speak to whenever you like.
CLIENTS: set = set()


async def broadcast(message: str) -> int:
    """Send one message to every live client. Returns how many were reached.

    return_exceptions=True matters: if one client died a millisecond ago its
    send() raises, and without this the exception would abort the whole
    broadcast and the remaining clients would silently miss the message.
    """
    targets = list(CLIENTS)
    results = await asyncio.gather(
        *(client.send(message) for client in targets),
        return_exceptions=True,
    )
    return sum(1 for r in results if not isinstance(r, Exception))


async def chat_handler(websocket):
    CLIENTS.add(websocket)
    print(f"  [server] client joined  (now {len(CLIENTS)} connected)")
    try:
        async for message in websocket:
            # One inbound message -> len(CLIENTS) outbound messages.
            reached = await broadcast(f"someone said: {message}")
            print(f"  [server] fanned {message!r} out to {reached} client(s)")
    finally:
        # A `finally` is not optional. Without it the set grows forever with
        # dead connections and every broadcast gets slower and noisier.
        CLIENTS.discard(websocket)
        print(f"  [server] client left    (now {len(CLIENTS)} connected)")


async def demo(port: int) -> None:
    url = f"ws://127.0.0.1:{port}"

    print("== three clients connect; ONE of them speaks ==")
    async with connect(url) as alice, connect(url) as bob, connect(url) as carol:
        # All three are registered server-side now, though only alice will send.
        await alice.send("hi everyone")

        heard = [await c.recv() for c in (alice, bob, carol)]
        for name, text in zip(("alice", "bob  ", "carol"), heard):
            print(f"  {name} received: {text!r}")
        # bob and carol asked for NOTHING. They received it because the server
        # chose to push to them. That is the whole feature.
        assert heard == ["someone said: hi everyone"] * 3

        print("\n== a different client speaks: same fan-out, other direction ==")
        await carol.send("hello back")
        heard = [await c.recv() for c in (alice, bob, carol)]
        print("  all three received:", heard)
        assert heard == ["someone said: hello back"] * 3

    async def wait_for_empty_registry():
        """The server's `finally` blocks run a moment after the clients go, so
        wait for them rather than racing them."""
        for _ in range(500):
            if not CLIENTS:
                return
            await asyncio.sleep(0.01)

    print("\n== after everyone disconnects, the registry is empty again ==")
    await wait_for_empty_registry()
    print(f"  clients still registered: {len(CLIENTS)}")
    assert len(CLIENTS) == 0

    print("\n== fan-out shrinks as clients leave ==")
    async with connect(url) as only_one:
        await only_one.send("just me")
        print("  received:", await only_one.recv())
        assert len(CLIENTS) == 1
    await wait_for_empty_registry()
    assert len(CLIENTS) == 0

    print("\nOK")


async def main() -> None:
    async with serve(chat_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
