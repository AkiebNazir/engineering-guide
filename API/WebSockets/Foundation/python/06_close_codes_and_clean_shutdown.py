"""
FOUNDATION LEVEL 06 - Close codes: the vocabulary for ENDING a conversation
===============================================================================
REST has status codes to describe one answer. WebSockets has close codes to
describe one ending. They are not the same tool: a status code says "here is
what happened to your request", a close code says "here is why this whole
relationship is over". A long-lived connection needs that second vocabulary,
because "goodbye" can mean a dozen different things.

A clean close is a HANDSHAKE, not a hang-up: one side sends a Close frame with
a code and a reason, the other echoes a Close frame back, and only then does
the TCP connection drop. That is why the client below can read the code the
server chose - the close was a message, and messages carry data.

You will learn
  * the codes that matter in practice: 1000 normal, 1001 going away,
    1003 unsupported data, 1008 policy violation, 1009 too big, 1011 internal error
  * that 1005 and 1006 are NEVER sent on the wire - they are local placeholders
    meaning "no code given" and "the connection died without a close frame"
  * the difference between a CLEAN close (both sides agreed) and an abort
  * the 4000-4999 range, which is yours: application-specific close codes
  * how a client inspects the code: ws.close_code, or the exception raised by
    recv() - ConnectionClosedOK for 1000/1001, ConnectionClosedError otherwise

Run it   python 06_close_codes_and_clean_shutdown.py
"""
import asyncio

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

# The reason string is capped at 123 bytes by the protocol - it is a hint for a
# human reading logs, never a place to put structured data.
CLOSERS = {
    "bye":      (1000, "normal closure - we are done, nothing is wrong"),
    "shutdown": (1001, "going away - server is restarting"),
    "binary":   (1003, "unsupported data - this endpoint only accepts text"),
    "rude":     (1008, "policy violation - you broke a rule of this service"),
    "huge":     (1009, "message too big"),
    "crash":    (1011, "internal error - our bug, not yours"),
    "custom":   (4001, "app-specific: your subscription expired"),
}


async def closing_handler(websocket):
    async for message in websocket:
        if message in CLOSERS:
            code, reason = CLOSERS[message]
            # close() sends a Close frame and WAITS for the peer's Close frame
            # back. That round trip is what makes it "clean".
            await websocket.close(code=code, reason=reason)
            return
        if message == "abort":
            # The opposite of clean: rip the TCP connection away with no Close
            # frame at all. The peer cannot learn a code, so it reports 1006.
            # Real causes: a crashed process, a dropped wifi, a killed pod.
            websocket.transport.abort()  # not awaited: it is an instant, rude teardown
            return
        await websocket.send(f"echo: {message}")


async def demo(port: int) -> None:
    url = f"ws://127.0.0.1:{port}"

    print("== every close code is a deliberate statement about why we are done ==")
    for trigger, (expected_code, expected_reason) in CLOSERS.items():
        async with connect(url) as ws:
            await ws.send(trigger)
            try:
                await ws.recv()
                raise AssertionError("expected the server to close")
            except (ConnectionClosedOK, ConnectionClosedError) as exc:
                # ConnectionClosedOK for 1000/1001; ConnectionClosedError for the
                # rest. Both carry the code - the library just sorts them into
                # "expected ending" vs "something was wrong".
                kind = type(exc).__name__
            print(f"  {trigger:9} -> {ws.close_code} {ws.close_reason!r}")
            print(f"  {'':9}    raised {kind}")
            assert ws.close_code == expected_code
            assert ws.close_reason == expected_reason

    print("\n== a clean close is mutual: both sides end up agreeing on the code ==")
    async with connect(url) as ws:
        await ws.send("ping")
        assert await ws.recv() == "echo: ping"
        # This time the CLIENT initiates. The server's `async for` ends, its
        # handler returns, and the library completes the close handshake.
        await ws.close(code=1000, reason="client is done")
    print(f"  client-initiated close -> {ws.close_code} {ws.close_reason!r}")
    assert ws.close_code == 1000

    print("\n== 1006: no close frame ever arrived (the connection just vanished) ==")
    async with connect(url) as ws:
        await ws.send("abort")
        try:
            await ws.recv()
        except ConnectionClosedError:
            pass
    print(f"  aborted connection -> close_code {ws.close_code}"
          "   (1006 is invented locally; it was never sent by anyone)")
    assert ws.close_code == 1006
    print("  this is the case level 07's keepalive exists to detect")
    print("\nOK")


async def main() -> None:
    async with serve(closing_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
