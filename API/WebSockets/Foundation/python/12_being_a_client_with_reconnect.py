"""
FOUNDATION LEVEL 12 - Being the client: reconnecting is not optional
========================================================================
Levels 00-11 were all SERVER code. Flip the lens: you are the client now, and
you have a problem REST clients do not have.

A REST client's retry logic is per call. One request fails, you retry that one
request, and nothing else in your program knows or cares - each call stands
alone (see ../../REST/Foundation/python/12_being_a_client.py).

A WebSocket client's connection IS its state. When it drops - and it WILL drop:
wifi, sleep, a deploy, a load balancer's idle timeout - you do not lose one
call, you lose the session: your authentication, your room membership, your
subscriptions, and any messages sent while you were away. So a real WebSocket
client is not "connect and read". It is a LOOP that reconnects forever, with
backoff, and re-establishes its session state every time it gets back in.

You will learn
  * the reconnect loop: connect -> use -> on failure, wait, then connect again
  * exponential backoff with a cap, so a server that is down does not get
    hammered by every client at once the moment it starts recovering
  * JITTER: without a random offset, ten thousand clients dropped by the same
    deploy all reconnect in the same millisecond (the "thundering herd")
  * resubscribing: on reconnect you must redo the setup handshake (auth, room
    join) - the server remembers nothing about the connection that died
  * the gap problem: messages sent while you were disconnected are simply gone
    unless the protocol has sequence numbers (../../labs/python/05_reconnect_and_resume.py)

Run it   python 12_being_a_client_with_reconnect.py
"""
import asyncio
import json
import random

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed, WebSocketException

BASE_DELAY = 0.02   # tiny so this demo finishes fast; realistically 0.5-1s
MAX_DELAY = 0.2     # realistically 30-60s
DROPS_BEFORE_STABLE = 2

# Server-side bookkeeping so the demo can prove what happened.
SERVER = {"connections": 0}


async def flaky_handler(websocket):
    """Drops the first DROPS_BEFORE_STABLE connections abruptly, then behaves.

    This imitates a server being rolled out, or a proxy reaping connections -
    not a broken server. Note it drops them with NO close frame, which is the
    realistic case and the one that yields close code 1006.
    """
    SERVER["connections"] += 1
    n = SERVER["connections"]

    # Every connection must re-authenticate: the server kept nothing.
    raw = await websocket.recv()
    hello = json.loads(raw)
    if hello.get("type") != "subscribe":
        await websocket.close(code=1008, reason="expected subscribe first")
        return
    await websocket.send(json.dumps({"type": "subscribed", "payload": hello["payload"]}))

    if n <= DROPS_BEFORE_STABLE:
        print(f"  [server] connection #{n}: dropping it abruptly (no close frame)")
        websocket.transport.abort()
        return

    print(f"  [server] connection #{n}: this one will stay up")
    async for raw in websocket:
        message = json.loads(raw)
        await websocket.send(json.dumps({"type": "echo", "payload": message["payload"]}))


def backoff_delay(attempt: int) -> float:
    """Exponential backoff, capped, with jitter.

    attempt 0 -> ~BASE_DELAY, 1 -> ~2x, 2 -> ~4x, ... never above MAX_DELAY.
    The jitter is the part people forget, and the part that saves the server:
    it spreads a herd of reconnecting clients out over a window instead of
    letting them arrive in one synchronised spike.
    """
    capped = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    return capped * (0.5 + random.random() / 2)   # 50-100% of the capped delay


async def resilient_client(url: str, room: str, want: int) -> tuple[list, list]:
    """Stay connected until `want` echo replies have been collected.

    This function is the deliverable of this level: the shape every production
    WebSocket client has.
    """
    received: list[str] = []
    delays: list[float] = []
    attempt = 0

    while len(received) < want:
        if attempt:
            delay = backoff_delay(attempt - 1)
            delays.append(delay)
            print(f"  [client] reconnecting in {delay * 1000:.0f}ms "
                  f"(attempt {attempt + 1})")
            await asyncio.sleep(delay)
        attempt += 1

        try:
            async with connect(url) as ws:
                # RE-ESTABLISH THE SESSION. The server that just accepted us
                # has never heard of us before, even if we were talking to the
                # same process 20ms ago. Authentication, subscriptions, room
                # membership: all of it must be redone, every single time.
                await ws.send(json.dumps({"type": "subscribe", "payload": room}))
                ack = json.loads(await ws.recv())
                assert ack["type"] == "subscribed"
                print(f"  [client] connected and re-subscribed to {ack['payload']!r}")

                # A successful connection resets the backoff, so the next
                # unrelated failure starts from a short delay again.
                attempt = 0

                while len(received) < want:
                    await ws.send(json.dumps({"type": "work", "payload": len(received)}))
                    reply = json.loads(await ws.recv())
                    received.append(reply["payload"])
                    print(f"  [client] got reply {reply['payload']}")

        except (ConnectionClosed, WebSocketException, OSError) as exc:
            # This is the ONLY correct reaction to a dropped WebSocket: note
            # it, back off, and go round the loop. Crashing here would mean
            # your app dies every time someone walks into a lift.
            print(f"  [client] connection lost: {type(exc).__name__} "
                  f"(close code {getattr(exc, 'code', None)}) - will retry")
            attempt = max(attempt, 1)

    return received, delays


async def demo(port: int) -> None:
    print(f"== the server will abruptly drop the first {DROPS_BEFORE_STABLE} "
          "connections; the client must not care ==")
    received, delays = await resilient_client(
        f"ws://127.0.0.1:{port}", room="prices", want=3
    )

    print(f"\nserver accepted {SERVER['connections']} connections "
          f"to deliver {len(received)} replies")
    assert received == [0, 1, 2], received
    # One connection per drop, plus the one that finally stuck.
    assert SERVER["connections"] == DROPS_BEFORE_STABLE + 1

    print(f"backoff delays used: {[f'{d * 1000:.0f}ms' for d in delays]}")
    assert len(delays) == DROPS_BEFORE_STABLE
    print("  both are short, because each drop came AFTER a successful connect -")
    print("  and success resets the backoff. Delays only grow while failures")
    print("  are consecutive, which is exactly the behaviour you want.")

    print("\n== so, for a server that stays down: the delays grow and the cap holds ==")
    # Shown without jitter so the doubling is obvious; the real delays above
    # are each a random 50-100% of these.
    for attempt in range(8):
        capped = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
        print(f"  attempt {attempt + 1}: up to {capped * 1000:6.0f}ms"
              f"{'   <- capped' if capped == MAX_DELAY else ''}")
        assert capped <= MAX_DELAY

    print("\n== jitter spreads a herd out instead of synchronising it ==")
    herd = sorted(backoff_delay(3) for _ in range(5))
    print("  5 clients, same attempt number, different waits:",
          [f"{d * 1000:.0f}ms" for d in herd])
    assert herd[0] != herd[-1], "jitter should not produce identical delays"
    print("\nOK")


async def main() -> None:
    async with serve(flaky_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    random.seed(7)  # deterministic output for a teaching file
    asyncio.run(main())
