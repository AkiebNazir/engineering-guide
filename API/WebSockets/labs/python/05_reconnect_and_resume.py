"""
LAB 05 (advanced) - Connections WILL drop: reconnect with backoff and resume without loss or duplicates
=======================================================================================================
You will learn
  * mobile networks, deploys, load balancers and laptops closing all cut WebSockets. A robust client
    treats a dropped connection as NORMAL, not as an error.
  * the three ingredients of a lossless live feed:
        1. SEQUENCE NUMBERS on every server event            (so both sides can say "I have up to #41")
        2. a server-side REPLAY BUFFER of recent events       (so a reconnecting client can catch up)
        3. a RESUME handshake:  client -> {"type":"resume","last_seq":41}
                                server -> replays 42, 43, ... then continues live
  * client-side DEDUPLICATION: replay + live overlap is possible, so drop seq <= last_seq
  * GAP handling: if the buffer no longer holds the client's position, tell it to do a full resync
  * reconnecting politely: exponential backoff with FULL JITTER so 50,000 clients do not stampede the
    server the moment it comes back

    events:   1 2 3 4 5 6 7 8 9 ...
    client:   1 2 3 4 [x drop x]            reconnects, sends last_seq=4
    server:                     replays 5 6 7 8 (missed while offline) then live 9 10 ...

Needs   pip install websockets
Run it  python 05_reconnect_and_resume.py
"""
import asyncio
import json
import random

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

random.seed(3)


# ================================================================= server ====
class Feed:
    """An append-only event log with a bounded replay buffer."""

    def __init__(self, buffer_size: int = 500):
        self.events: list[dict] = []
        self.first_seq = 1                               # oldest seq still in the buffer
        self.buffer_size = buffer_size
        self.subscribers: set = set()

    def publish(self, payload: str):
        seq = (self.events[-1]["seq"] + 1) if self.events else 1
        self.events.append({"seq": seq, "data": payload})
        if len(self.events) > self.buffer_size:
            self.events.pop(0)
            self.first_seq = self.events[0]["seq"]
        for ws in list(self.subscribers):
            asyncio.get_running_loop().create_task(self._push(ws, self.events[-1]))

    async def _push(self, ws, event):
        try:
            await ws.send(json.dumps(event))
        except ConnectionClosed:
            self.subscribers.discard(ws)


FEED = Feed()


def make_handler(feed: Feed):
    async def handler(ws):
        await serve_client(ws, feed)
    return handler


async def serve_client(ws, FEED: Feed):
    try:
        hello = json.loads(await asyncio.wait_for(ws.recv(), 2))
        last = int(hello.get("last_seq", 0))
        if last + 1 < FEED.first_seq and FEED.events:                   # the client is too far behind for a replay
            await ws.send(json.dumps({"type": "reset", "oldest": FEED.first_seq}))
            last = FEED.first_seq - 1
        # replay what the client missed, THEN join the live stream. There is no await between the
        # replay list being built and subscribing, so no event can slip through the gap.
        missed = [e for e in FEED.events if e["seq"] > last]
        FEED.subscribers.add(ws)
        for e in missed:
            await ws.send(json.dumps(e))
        await ws.wait_closed()
    except (ConnectionClosed, asyncio.TimeoutError):
        pass
    finally:
        FEED.subscribers.discard(ws)


# ================================================================= client ====
class ResilientClient:
    def __init__(self, url: str, base=0.05, cap=0.4):
        self.url, self.base, self.cap = url, base, cap
        self.last_seq = 0
        self.received: list[int] = []
        self.duplicates = 0
        self.resets = 0
        self.connects = 0
        self.delays: list[float] = []

    async def run(self, stop: asyncio.Event):
        attempt = 0
        while not stop.is_set():
            try:
                async with connect(self.url) as ws:
                    self.connects += 1
                    attempt = 0                                          # a good connection resets the backoff
                    await ws.send(json.dumps({"type": "resume", "last_seq": self.last_seq}))
                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("type") == "reset":                   # our position fell off the buffer
                            self.resets += 1
                            self.last_seq = msg["oldest"] - 1            # a real app would refetch a snapshot here
                            continue
                        if msg["seq"] <= self.last_seq:
                            self.duplicates += 1                         # replay overlapped with live: ignore
                            continue
                        self.last_seq = msg["seq"]
                        self.received.append(msg["seq"])
            except (ConnectionClosed, OSError):
                pass
            if stop.is_set():
                return
            # FULL JITTER: sleep a random time in [0, min(cap, base * 2^attempt)]
            delay = random.uniform(0, min(self.cap, self.base * 2 ** attempt))
            self.delays.append(delay)
            attempt += 1
            await asyncio.sleep(delay)


# ================================================================== demo =====
async def main():
    async with serve(make_handler(FEED), "127.0.0.1", 0) as server:
        url = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        client = ResilientClient(url)
        stop = asyncio.Event()
        task = asyncio.create_task(client.run(stop))

        async def producer():                                           # 300 events, one every 10ms
            for i in range(300):
                FEED.publish(f"event-{i}")
                await asyncio.sleep(0.01)

        async def chaos():                                              # cut the connection abruptly 3 times
            for _ in range(3):
                await asyncio.sleep(0.7)
                for ws in list(server.connections):
                    ws.transport.abort()                                 # no close frame: like a network drop
                print(f"  -- connection killed at ~seq {client.last_seq} --")

        print("== 300 events, connection killed 3 times ==")
        await asyncio.gather(producer(), chaos())
        await asyncio.sleep(0.8)                                        # let the client catch up
        stop.set()
        task.cancel()

        got = client.received
        print(f"  connects: {client.connects}   duplicates dropped: {client.duplicates}   resets: {client.resets}")
        print(f"  reconnect delays (s): {[round(d, 3) for d in client.delays]}")
        print(f"  received {len(got)} events, first {got[0]}, last {got[-1]}")
        assert client.connects >= 4, "should have reconnected after each kill"
        assert got == list(range(1, 301)), "every event exactly once, in order"
        print("  => no loss, no duplicates, in order, across 3 network failures")

        print("\n== a client that was away too long gets a RESET instead of silently missing events ==")
        small = Feed(buffer_size=10)
        for i in range(50):
            small.publish(f"e{i}")
        print(f"  the server only remembers seq {small.first_seq}..{small.events[-1]['seq']}")
        async with serve(make_handler(small), "127.0.0.1", 0) as tiny:
            async with connect(f"ws://127.0.0.1:{tiny.sockets[0].getsockname()[1]}") as ws:
                await ws.send(json.dumps({"type": "resume", "last_seq": 3}))      # "I have everything up to 3"
                first = json.loads(await ws.recv())
                print("  client resumes from seq 3, server answers:", first)
                assert first == {"type": "reset", "oldest": 41}
                replay = [json.loads(await ws.recv())["seq"] for _ in range(10)]
                print("  then replays what it still has:", replay[0], "...", replay[-1])
                assert replay == list(range(41, 51))
        print("  => the client learns it MISSED 4..40 and must refetch a snapshot, instead of silently skipping them")

        print("\n== why FULL JITTER? 1000 clients reconnecting after an outage ==")
        def spread(jitter: bool, attempt=3, base=0.05):
            ds = [(random.uniform(0, base * 2 ** attempt) if jitter else base * 2 ** attempt) for _ in range(1000)]
            buckets = {}
            for d in ds:
                buckets[int(d * 100)] = buckets.get(int(d * 100), 0) + 1        # 10ms buckets
            return max(buckets.values())
        no_j, with_j = spread(False), spread(True)
        print(f"  busiest 10ms window without jitter: {no_j} reconnects at once; with jitter: {with_j}")
        assert no_j == 1000 and with_j < 200
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
