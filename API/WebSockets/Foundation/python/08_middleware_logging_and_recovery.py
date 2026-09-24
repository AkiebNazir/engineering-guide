"""
FOUNDATION LEVEL 08 - Middleware for a connection, not for a request
========================================================================
Middleware means the same thing here as in REST (../../REST/Foundation/python/
08_middleware_logging_and_recovery.py): a wrapper that adds behaviour around
your real code without editing it. But the SHAPE is different, and the
difference is not cosmetic - it changes what each wrapper can do.

  REST middleware wraps ONE request/response. Scope and lifetime are the same
  thing: the request arrives, the chain runs, a response goes out, everything
  is discarded. One layer, one concept.

  WebSocket middleware has TWO distinct scopes, and you need both:
    * CONNECTION-scoped - runs once at connect, once at disconnect. This is
      where logging, metrics, rate-limit buckets and registry bookkeeping live,
      because those things belong to the client, not to a message.
    * MESSAGE-scoped - runs per inbound message. This is where panic/exception
      recovery must live, because the unit you want to isolate is one message.
      Put recovery at connection scope and a single bad message kills the whole
      session; put it at message scope and the session shrugs it off.

So the pipeline is built out of two different wrapper types:

    with_logging( message_loop( with_recovery( handle_message ) ) )
    ^connection-scoped            ^message-scoped

You will learn
  * the two middleware scopes a persistent connection needs, and why
  * that connection-scoped middleware has a duration - it can time the whole
    session, which a REST middleware can never do
  * exception recovery per message: reply with an error, KEEP the connection
  * that without recovery, one buggy message handler disconnects a user
    (and in Go, an unrecovered panic in a connection goroutine kills the
    entire server process)
  * chaining order still matters, exactly as it did in REST

Run it   python 08_middleware_logging_and_recovery.py
"""
import asyncio
import json
import time
from typing import Awaitable, Callable

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

# Two handler shapes, because there are two scopes.
ConnHandler = Callable[[object], Awaitable[None]]           # gets a connection
MessageHandler = Callable[[object, str], Awaitable[None]]    # gets one message

STATS = {"connections": 0, "recovered": 0}


# ---- the "real" application logic: one message in, replies written out ----
async def handle_message(websocket, raw: str) -> None:
    message = json.loads(raw)
    if message["type"] == "boom":
        raise RuntimeError("simulated bug while handling one message")
    if message["type"] == "echo":
        await websocket.send(json.dumps({"type": "echo", "payload": message["payload"]}))
        return
    raise ValueError(f"unknown type {message['type']!r}")


# ---- MESSAGE-scoped middleware: isolate one message's failure ----
def with_recovery(next_handler: MessageHandler) -> MessageHandler:
    async def wrapped(websocket, raw: str) -> None:
        try:
            await next_handler(websocket, raw)
        except Exception as exc:
            STATS["recovered"] += 1
            print(f"    [recover] {type(exc).__name__}: {exc}")
            print("    [recover] -> error reply sent, CONNECTION KEPT OPEN")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": f"{type(exc).__name__}: {exc}",
            }))
    return wrapped


# ---- the adapter that turns a message handler into a connection handler ----
def message_loop(handle: MessageHandler) -> ConnHandler:
    async def conn_handler(websocket) -> None:
        async for raw in websocket:
            await handle(websocket, raw)
    return conn_handler


# ---- CONNECTION-scoped middleware: runs once at each end of the session ----
def with_logging(next_handler: ConnHandler) -> ConnHandler:
    async def wrapped(websocket) -> None:
        STATS["connections"] += 1
        started = time.perf_counter()
        # A REST middleware cannot print a line like this, because there is no
        # "connect" event to hang it on.
        print(f"  [log] CONNECT   path={websocket.request.path}")
        try:
            await next_handler(websocket)
        finally:
            # `finally`, not just a trailing statement: this must run whether
            # the client left politely, crashed, or was closed by us.
            elapsed = (time.perf_counter() - started) * 1000
            print(f"  [log] DISCONNECT code={websocket.close_code} "
                  f"session lasted {elapsed:.0f}ms")
    return wrapped


# Built once, outside in. Logging is outermost so it brackets the entire
# session; recovery is innermost so its blast radius is exactly one message.
pipeline: ConnHandler = with_logging(message_loop(with_recovery(handle_message)))


async def demo(port: int) -> None:
    async with connect(f"ws://127.0.0.1:{port}/chat") as ws:
        async def call(payload_json: str):
            await ws.send(payload_json)
            return json.loads(await ws.recv())

        print("\n  -- a normal message --")
        reply = await call('{"type": "echo", "payload": "hi"}')
        print("  reply:", reply)
        assert reply["payload"] == "hi"

        print("\n  -- a message whose handler raises --")
        reply = await call('{"type": "boom", "payload": null}')
        print("  reply:", reply)
        assert reply["type"] == "error" and "simulated bug" in reply["payload"]

        print("\n  -- and another, differently broken --")
        reply = await call('{"type": "nope", "payload": null}')
        print("  reply:", reply)
        assert reply["type"] == "error"

        print("\n  -- the session is untouched by either failure --")
        reply = await call('{"type": "echo", "payload": "still connected"}')
        print("  reply:", reply)
        assert reply["payload"] == "still connected"
        assert ws.close_code is None

        await ws.close(code=1000, reason="done")

    # Let the server's logging `finally` run before we read the counters.
    await asyncio.sleep(0.05)
    print(f"\nconnections logged: {STATS['connections']}, "
          f"messages recovered: {STATS['recovered']}")
    assert STATS["connections"] == 1   # connection-scoped: once per client
    assert STATS["recovered"] == 2     # message-scoped: once per bad message
    print("one CONNECT/DISCONNECT pair, two isolated message failures - "
          "that is the two scopes working")
    print("\nOK")


async def main() -> None:
    async with serve(pipeline, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
