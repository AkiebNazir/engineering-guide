"""
FOUNDATION LEVEL 05 - Validating a message without destroying the session
=============================================================================
Level 02 called `json.loads(raw)` and trusted the result completely. Send that
server the text "hello" and it raises, the handler dies, and the connection
goes with it. On a REST server that would cost one request. Here it costs the
whole session: the client's auth, its room membership, its scroll position -
all gone because of one typo in one message.

So WebSocket validation has a different DEFAULT than REST validation. In REST,
isolation is free: every request is separate, so a 400 naturally affects only
that request. In WebSockets, isolation is something you must build on purpose.
The rule: a bad MESSAGE gets an error reply; only a bad CLIENT gets closed.

You will learn
  * validate in layers: is it JSON -> is it an object -> does it have `type` ->
    is the payload shaped right for that type
  * reply with a structured error message and KEEP READING (the whole point)
  * the exception to the rule: when a peer is clearly not speaking your
    protocol at all, closing with 1003/1008 is correct (level 06)
  * that the library itself enforces some rules for you - e.g. a text frame
    with invalid UTF-8 is a protocol violation it closes with 1007, before
    your code ever sees it
  * never let an unexpected exception escape the per-message handler - level 08
    turns that idea into reusable middleware

Run it   python 05_payload_validation_without_dropping.py
"""
import asyncio
import json

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

# type -> what its payload must look like, as a validator returning an error
# string (or None if the payload is fine).
SCHEMAS = {
    "sum": lambda p: (
        None if isinstance(p, list) and p and all(isinstance(n, (int, float)) for n in p)
        else "payload must be a non-empty list of numbers"
    ),
    "upper": lambda p: None if isinstance(p, str) else "payload must be a string",
}


def validate(raw) -> tuple[dict | None, str | None]:
    """Turn raw wire data into (message, error). Exactly one will be None."""
    if not isinstance(raw, str):
        return None, "expected a text message, got binary"
    try:
        message = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"not valid JSON: {exc.msg}"
    if not isinstance(message, dict):
        return None, "expected a JSON object at the top level"

    kind = message.get("type")
    if kind not in SCHEMAS:
        return None, f"unknown type {kind!r}; known: {sorted(SCHEMAS)}"
    if "payload" not in message:
        return None, "missing 'payload'"

    problem = SCHEMAS[kind](message["payload"])
    if problem:
        return None, f"bad payload for type {kind!r}: {problem}"
    return message, None


async def validating_handler(websocket):
    async for raw in websocket:
        message, error = validate(raw)
        if error:
            # An error REPLY, not a close. The client is told precisely what
            # was wrong and may immediately try again on the same connection.
            await websocket.send(json.dumps({"type": "error", "payload": error}))
            continue

        result = (sum(message["payload"]) if message["type"] == "sum"
                  else message["payload"].upper())
        await websocket.send(json.dumps({"type": message["type"], "payload": result}))


async def demo(port: int) -> None:
    async with connect(f"ws://127.0.0.1:{port}") as ws:
        async def send_raw(raw):
            await ws.send(raw)
            return json.loads(await ws.recv())

        print("== five different kinds of broken message, one surviving connection ==")
        broken = [
            ("not JSON at all", "hello there"),
            ("JSON, but not an object", "[1, 2, 3]"),
            ("object with no type", '{"payload": 1}'),
            ("unknown type", '{"type": "nope", "payload": 1}'),
            ("right type, wrong payload shape", '{"type": "sum", "payload": "seven"}'),
        ]
        for label, raw in broken:
            reply = await send_raw(raw)
            print(f"  {label:32} -> {reply['type']}: {reply['payload']}")
            assert reply["type"] == "error"

        print("\n== and the connection is still perfectly usable ==")
        reply = await send_raw('{"type": "sum", "payload": [1, 2, 3]}')
        print("  valid sum   ->", reply)
        assert reply["payload"] == 6
        reply = await send_raw('{"type": "upper", "payload": "still alive"}')
        print("  valid upper ->", reply)
        assert reply["payload"] == "STILL ALIVE"

        # Five protocol violations in a row did not cost this client its session.
        assert ws.close_code is None, "connection should still be open"
        print("  connection state: still open after 5 rejected messages")

        await ws.close(code=1000)
    print("\nOK")


async def main() -> None:
    async with serve(validating_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
