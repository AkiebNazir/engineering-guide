"""
FOUNDATION LEVEL 07 - Ping, pong, and spotting a connection that died quietly
=================================================================================
Level 06 ended with close code 1006: a connection that disappeared without
saying goodbye. That is not an edge case, it is the normal failure. Laptops
close, phones change network, NAT tables forget you after a few minutes of
silence, load balancers reap idle connections. In every one of those cases
your server still holds an open socket that will never deliver another byte -
a "half-open" connection - and it will sit there for hours unless you check.

TCP will not tell you. It only notices when you try to write. So WebSockets
gives you Ping and Pong: two CONTROL frames whose only job is to be a heartbeat.
Send a ping, and a conforming peer MUST reply with a pong. No reply in time
means the peer is gone, whatever the socket claims.

You will learn
  * ping/pong are control frames, handled BELOW your message loop: you never
    see an incoming ping in your `async for`, the library answers it for you
  * a ping measures latency for free - the round trip is real network time
  * ping_interval / ping_timeout: the library will heartbeat and kill a dead
    connection for you, if you configure it (this is the answer 95% of the time)
  * the application-level alternative: your own idle deadline with
    asyncio.wait_for, useful when you want to require client ACTIVITY, not
    merely client liveness
  * why sending data is not a substitute: you can write into a dead socket
    happily for a long time before the OS admits the truth

Run it   python 07_ping_pong_and_keepalive.py
"""
import asyncio

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

IDLE_LIMIT = 0.3  # absurdly short so the demo is quick; realistically 30-120s


async def echo_handler(websocket):
    """A plain echo server. Note what is NOT here: any ping handling at all.
    The library answers pings underneath us, which is exactly the point."""
    async for message in websocket:
        await websocket.send(f"echo: {message}")


async def strict_handler(websocket):
    """Requires the client to SAY SOMETHING every IDLE_LIMIT seconds.

    This is stricter than ping/pong: a client can answer pings perfectly while
    being a stuck, useless process. Demanding real messages ("activity", not
    "liveness") is an application decision - e.g. a game that requires input.
    """
    while True:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=IDLE_LIMIT)
        except asyncio.TimeoutError:
            print(f"  [server] no message for {IDLE_LIMIT}s -> assuming this client is gone")
            # 1001 "going away" is the polite code for "I am ending this, and
            # it is not your fault exactly" - see level 06.
            await websocket.close(code=1001, reason="idle timeout, no heartbeat")
            return
        except ConnectionClosed:
            return
        await websocket.send(f"ack: {message}")


async def demo(echo_port: int, strict_port: int) -> None:
    print("== 1. a ping is a control frame; it never reaches the message loop ==")
    async with connect(f"ws://127.0.0.1:{echo_port}") as ws:
        # ping() returns a future that resolves when the matching pong arrives.
        pong_waiter = await ws.ping()
        latency = await pong_waiter
        print(f"  ping -> pong round trip: {latency * 1000:.2f} ms")
        print("  the server's handler has no ping code in it at all - "
              "the library replied for it")

        # Proof that the ping did not disturb the message stream: the echo
        # server never saw it, so a normal message still works normally.
        await ws.send("hello")
        reply = await ws.recv()
        print(f"  a normal message still behaves normally: {reply!r}")
        assert reply == "echo: hello"
        await ws.close(code=1000)

    print("\n== 2. letting the library do the heartbeat for you ==")
    # ping_interval: send a ping every N seconds of quiet.
    # ping_timeout:  if no pong within N seconds, close the connection as dead.
    # This pair is the whole answer for most servers - and it is why the demo
    # above got a pong without anyone writing pong code.
    async with connect(
        f"ws://127.0.0.1:{echo_port}", ping_interval=0.05, ping_timeout=0.5
    ) as ws:
        await asyncio.sleep(0.25)  # several automatic ping/pong cycles happen here
        await ws.send("still connected")
        reply = await ws.recv()
        print(f"  after 0.25s of automatic heartbeating: {reply!r}")
        assert reply == "echo: still connected"
        assert ws.close_code is None, "the heartbeat should have kept us alive"
        print("  connection survived, because pongs kept coming back")
        await ws.close(code=1000)

    print("\n== 3. an application-level idle deadline (requiring ACTIVITY) ==")
    async with connect(f"ws://127.0.0.1:{strict_port}") as ws:
        for i in range(3):
            await ws.send(f"heartbeat {i}")
            print("  ", await ws.recv())
            await asyncio.sleep(IDLE_LIMIT / 3)  # comfortably inside the deadline

        print(f"  now going silent for longer than the {IDLE_LIMIT}s deadline...")
        try:
            await ws.recv()
            raise AssertionError("expected the server to hang up on us")
        except ConnectionClosed:
            pass
        print(f"  server closed us: {ws.close_code} {ws.close_reason!r}")
        assert ws.close_code == 1001

    print("\n  note: this client was perfectly healthy and answering pings.")
    print("  It was closed for being IDLE, which is a different rule on purpose.")
    print("\nOK")


async def main() -> None:
    async with serve(echo_handler, "127.0.0.1", 0) as echo_server, \
               serve(strict_handler, "127.0.0.1", 0) as strict_server:
        await demo(
            echo_server.sockets[0].getsockname()[1],
            strict_server.sockets[0].getsockname()[1],
        )


if __name__ == "__main__":
    asyncio.run(main())
