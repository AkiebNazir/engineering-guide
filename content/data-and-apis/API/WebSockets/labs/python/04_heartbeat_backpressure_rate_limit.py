"""
LAB 04 (advanced) - Keeping a WebSocket server healthy: heartbeats, slow consumers, flood control
==================================================================================================
You will learn
  * HALF-OPEN connections: a laptop lid closes, a phone leaves Wi-Fi, a NAT drops its table.
    TCP does NOT tell you. Without heartbeats the server keeps the connection (and its memory) forever.
  * PING/PONG control frames: the server pings every N seconds; no pong within a timeout => close (1011)
    Measured below: with heartbeats a dead peer is detected in ~0.5s, without them it is never detected.
  * SLOW CONSUMERS: one client that reads slowly must not slow down or exhaust memory for everybody.
    Give every client a BOUNDED outgoing queue, and choose a policy when it is full:
        drop oldest (live prices)  |  drop newest  |  disconnect the client (must not lose messages)
  * FLOOD CONTROL: a token bucket per CONNECTION (messages/second). Excess is rejected; persistent
    abusers are disconnected with 1008 (policy violation)

Needs   pip install websockets
Run it  python 04_heartbeat_backpressure_rate_limit.py
"""
import asyncio
import base64
import json
import time

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

# ============================================================== 1. heartbeats ==
async def demo_heartbeat():
    print("== 1. heartbeats: a peer that silently dies ==")

    async def measure(ping_interval, ping_timeout, wait):
        closed = asyncio.Event()
        info = {}

        async def handler(ws):
            t0 = time.perf_counter()
            try:
                async for _ in ws:
                    pass
            except ConnectionClosed as e:
                frame = e.rcvd or e.sent                          # the peer is dead, so WE sent the close frame
                info["code"], info["reason"] = frame.code, frame.reason
            finally:
                info["seconds"] = time.perf_counter() - t0
                closed.set()                                     # the resource cleanup point

        async with serve(handler, "127.0.0.1", 0, ping_interval=ping_interval, ping_timeout=ping_timeout,
                     close_timeout=0.3) as server:      # close_timeout: how long to wait for the peer to finish the close handshake
            port = server.sockets[0].getsockname()[1]
            # A "client" that completes the handshake and then goes silent: it never reads, so it never
            # answers pings - exactly what a frozen app or a dead network path looks like to the server.
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write((f"GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                          f"Sec-WebSocket-Key: {base64.b64encode(b'0123456789abcdef').decode()}\r\n"
                          f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
            await reader.readuntil(b"\r\n\r\n")
            try:
                await asyncio.wait_for(closed.wait(), wait)
                return info
            except asyncio.TimeoutError:
                return None
            finally:
                writer.close()

    with_hb = await measure(ping_interval=0.2, ping_timeout=0.3, wait=3)
    print(f"  ping every 0.2s, timeout 0.3s -> server noticed after {with_hb['seconds']:.2f}s, closed with code {with_hb['code']} ({with_hb['reason']})")
    assert with_hb and with_hb["seconds"] < 1.5 and with_hb["code"] == 1011
    without = await measure(ping_interval=None, ping_timeout=None, wait=1.5)
    print(f"  no heartbeats                 -> after 1.5s the handler is STILL blocked: {'leaked!' if without is None else 'closed'}")
    assert without is None
    print("  In production use intervals of 20-30s: fast enough for NAT timeouts (often 60s), cheap enough for 100k clients.")


# ====================================================== 2. slow consumers / queues ==
class Client:
    """One connection + a bounded outgoing queue + a writer task."""

    def __init__(self, ws, maxsize: int, link_delay: float = 0.0):
        # link_delay models a slow network path. On loopback there is no real bandwidth limit
        # (the kernel swallows tens of MB), so we make the writer take `link_delay` seconds per message.
        self.ws, self.queue, self.dropped, self.link_delay = ws, asyncio.Queue(maxsize=maxsize), 0, link_delay
        self.writer = asyncio.create_task(self._pump())

    def offer(self, message: str):
        """Called by the publisher. NEVER blocks the publisher."""
        if self.queue.full():
            self.queue.get_nowait()                              # policy: drop the OLDEST message
            self.dropped += 1
        self.queue.put_nowait(message)

    async def _pump(self):
        try:
            while True:
                message = await self.queue.get()
                await asyncio.sleep(self.link_delay)
                await self.ws.send(message)
        except ConnectionClosed:
            pass


async def demo_slow_consumer():
    print("\n== 2. a slow consumer must not hurt anyone else (slow link modelled as 50 msg/s) ==")
    clients: list[Client] = []

    async def handler(ws):
        slow = ws.request.path == "/slow"                        # the second client sits behind a slow link
        clients.append(Client(ws, maxsize=20, link_delay=0.02 if slow else 0.0))
        try:
            await ws.wait_closed()
        finally:
            clients[:] = [c for c in clients if c.ws is not ws]

    async with serve(handler, "127.0.0.1", 0) as server:
        url = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        fast_got, slow_got = [], []

        async def fast():
            async with connect(url + "/fast") as ws:
                async for m in ws:
                    fast_got.append(int(m[:4]))

        async def slow():
            async with connect(url + "/slow") as ws:
                async for m in ws:
                    slow_got.append(int(m[:4]))

        tasks = [asyncio.create_task(fast()), asyncio.create_task(slow())]
        while len(clients) < 2:
            await asyncio.sleep(0.01)

        t0 = time.perf_counter()
        for i in range(200):                                      # publisher: 200 messages as fast as it can
            for c in clients:
                c.offer(f"{i:04d}")
            await asyncio.sleep(0.001)
        publish_time = time.perf_counter() - t0
        for _ in range(100):                                      # let the slow one drain what it still has
            if slow_got and slow_got[-1] == 199:
                break
            await asyncio.sleep(0.1)
        for c in clients:
            c.writer.cancel()
        for t in tasks:
            t.cancel()
        by_dropped = sorted(c.dropped for c in clients)
        print(f"  publisher finished 200 messages in {publish_time:.2f}s (never waited for the slow client)")
        print(f"  fast client received {len(fast_got)}/200, in order: {fast_got == sorted(fast_got)}")
        print(f"  slow client received {len(slow_got)}/200, dropped by policy: {by_dropped[-1]}, LAST message seen: {slow_got[-1]} (it is behind, not stale)")
        assert len(fast_got) == 200 and slow_got[-1] == 199 and by_dropped[-1] > 20 and publish_time < 3
        print("  memory per client is bounded by maxsize=20, whatever the publisher does.")


# ================================================================ 3. flood control ==
class Bucket:
    def __init__(self, rate: float, capacity: int):
        self.rate, self.capacity, self.tokens, self.t = rate, capacity, float(capacity), time.monotonic()

    def take(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.t) * self.rate)
        self.t = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


async def demo_flood():
    print("\n== 3. flood control: 5 messages/second, burst 10, 5 strikes and you are out ==")

    async def handler(ws):
        bucket, strikes = Bucket(rate=5, capacity=10), 0
        try:
            async for _ in ws:
                if bucket.take():
                    await ws.send(json.dumps({"ok": True}))
                    continue
                strikes += 1
                if strikes >= 5:
                    await ws.close(code=1008, reason="rate limit exceeded")            # policy violation
                    return
                await ws.send(json.dumps({"error": "rate_limited", "strikes": strikes}))
        except ConnectionClosed:
            pass

    # close_timeout: how long the server waits for the peer to finish the close handshake / drop TCP
    async with serve(handler, "127.0.0.1", 0, close_timeout=0.3) as server:
        async with connect(f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}") as ws:
            for _ in range(30):
                await ws.send("spam")
            ok = limited = 0
            code = None
            try:
                while True:
                    m = json.loads(await asyncio.wait_for(ws.recv(), 1))
                    ok, limited = ok + ("ok" in m), limited + ("error" in m)
            except ConnectionClosed as e:
                code = e.rcvd.code
        print(f"  30 messages in a burst -> {ok} accepted, {limited} rejected with an error, then closed with code {code}")
        assert ok == 10 and limited == 4 and code == 1008


async def main():
    await demo_heartbeat()
    await demo_slow_consumer()
    await demo_flood()
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
