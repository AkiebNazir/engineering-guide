"""
FOUNDATION LEVEL 00 (start here) - A basic WebSocket endpoint, explained end to end
=====================================================================================
If someone says "build me a basic WebSocket endpoint", THIS is what they mean: one
server, one URL, and a connection that stays open and echoes whatever you say into
it. Nothing about protocols, rooms, or auth yet - just enough to watch one
connection be born, carry messages both ways, and die.

THE MENTAL MODEL (read this before the code)
  A WebSocket starts life as an ordinary HTTP GET with an "Upgrade: websocket"
  header. The server answers "101 Switching Protocols" and from that instant the
  same TCP connection stops being HTTP and becomes a two-way message pipe.

  THE CONTRAST WITH REST (../../REST/Foundation) IS THE WHOLE POINT:
    REST      : request -> response -> done. Ask again, and it is a brand new,
                unrelated conversation. Nothing is remembered ("stateless").
    WebSocket : handshake ONCE, then N messages in EITHER direction over that
                one pipe. No URL, no verb, no headers, no status code per
                message - all of that was negotiated a single time, up front.
  This file proves that literally: the server counts how many times its handler
  is entered, we send three messages, and the count is still 1.

You will learn
  * what the upgrade handshake is, and that it happens exactly once per connection
  * that after the upgrade there are no more requests - only messages, both ways
  * the server side shape: one async function per CONNECTION, usually looping
    over incoming messages until the peer goes away
  * that a WebSocket connection is stateful by nature - the handler holds live
    variables for the whole life of that one client
  * that closing is a deliberate act with a code (see level 06), not just "done"

Run it        python 00_single_echo_connection_and_how_it_works.py
Keep serving  python 00_single_echo_connection_and_how_it_works.py --serve
              (then: npx wscat -c ws://localhost:8080/ws   and type something)
"""
import asyncio
import sys

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

# Bumped once per ACCEPTED CONNECTION, not once per message. The demo asserts
# this stays at 1 while three messages fly back and forth - that single number
# is the difference between WebSockets and REST.
HANDSHAKES = {"count": 0}


async def echo_handler(websocket):
    """Runs ONCE per connection. It is entered after the 101 handshake already
    succeeded, and it lives until the client (or we) close the pipe."""
    # websocket.request is the original HTTP upgrade request - the only HTTP
    # that will ever happen on this connection. This server has agreed to serve
    # exactly one path.
    path = websocket.request.path
    if path != "/ws":
        # There is no such thing as a mid-conversation 404 here: a WebSocket
        # either becomes a pipe or it does not. So the equivalent of "no such
        # endpoint" is to refuse the conversation with a close code (level 06).
        # Level 09 shows rejecting it even earlier, before the upgrade finishes.
        await websocket.close(code=1008, reason=f"no websocket endpoint at {path}")
        return

    HANDSHAKES["count"] += 1
    print(f"  [server] connection opened (handler entered, path={path})")

    # "async for" reads one MESSAGE at a time off the open pipe and ends when
    # the peer closes. Each loop turn is NOT a new request - nothing is
    # re-parsed, re-routed or re-authenticated. That work happened once, above.
    async for message in websocket:
        print(f"  [server] received {message!r} -> sending it straight back")
        await websocket.send(f"echo: {message}")

    print("  [server] connection closed (handler returns, pipe is gone)")


async def demo(port: int) -> None:
    url = f"ws://127.0.0.1:{port}/ws"

    # connect() performs the HTTP GET + Upgrade, waits for 101, and hands back
    # an open pipe. This one call is the entire "handshake" cost, paid once.
    async with connect(url) as ws:
        print(f"client   : connected to {url} (101 Switching Protocols happened)")

        await ws.send("hello")
        # recv() waits for ONE whole message. It does not "read bytes" - see level 01.
        reply = await ws.recv()
        print(f"client   : sent 'hello'  -> got {reply!r}")
        assert reply == "echo: hello"

        # Two more round trips on the SAME connection. No new handshake, no new
        # URL, no new headers. This is what "persistent" buys you.
        for text in ("again", "and again"):
            await ws.send(text)
            got = await ws.recv()
            print(f"client   : sent {text!r} -> got {got!r}")
            assert got == f"echo: {text}"

        # Closing is explicit and carries a code. 1000 = "normal closure".
        await ws.close(code=1000, reason="done")

    print(f"client   : closed with code {ws.close_code} reason {ws.close_reason!r}")
    assert ws.close_code == 1000

    # THE PROOF: three messages, one handshake.
    print(f"handshakes on the server for 3 messages: {HANDSHAKES['count']}"
          "   (REST would have needed 3 separate requests)")
    assert HANDSHAKES["count"] == 1

    # A path this server never agreed to serve: the connection is accepted at
    # the TCP level, then immediately closed with a reason. Reading from it
    # raises, which is how a client learns it was refused.
    async with connect(f"ws://127.0.0.1:{port}/nope") as bad:
        try:
            await bad.recv()
            raise AssertionError("expected the server to close this connection")
        except Exception as exc:  # ConnectionClosedError - a handled outcome, not a crash
            print(f"client   : /nope -> closed with {bad.close_code} {bad.close_reason!r}"
                  f" ({type(exc).__name__})")
            assert bad.close_code == 1008

    print("OK")


async def serve_forever() -> None:
    print("listening on ws://localhost:8080/ws  (try: npx wscat -c ws://localhost:8080/ws)")
    async with serve(echo_handler, "127.0.0.1", 8080) as server:
        await server.serve_forever()


async def main() -> None:
    # port 0 = "operating system, hand me any free port", so this demo never
    # collides with something already listening on your machine.
    async with serve(echo_handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        await demo(port)


if __name__ == "__main__":
    if "--serve" in sys.argv:
        asyncio.run(serve_forever())
    else:
        asyncio.run(main())
