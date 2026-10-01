"""
FOUNDATION LEVEL 02 - A tiny message protocol: routing by "type", not by URL
================================================================================
Here is a problem REST simply does not have. In REST, every request carries its
own address: `GET /books/7` says what to do and what to do it to. A WebSocket
message carries NO url and NO verb - the URL was used up once, during the
handshake. So how does one connection support twenty different operations?

You invent a protocol. Overwhelmingly the convention is a JSON envelope:

    {"type": "<what to do>", "payload": <the data for it>}

and the server switches on `type`. That `type` field is this level's whole
point: it is the WebSocket equivalent of REST's method+path routing, except
YOU define the vocabulary instead of inheriting HTTP's.

You will learn
  * why a WebSocket needs an application-level envelope at all
  * the {"type": ..., "payload": ...} convention, and routing on `type`
  * that replies are just messages too - so you should echo the `type` back
    (or include an id) or the client cannot tell which reply is which
  * an unknown `type` is an application-level error message, NOT a closed
    connection: the session survives, unlike REST where a 404 ends the request
  * where this goes next: matching replies to requests by id is JSON-RPC,
    which ../../labs/golang/02_coder_websocket_json_rpc builds properly

Run it   python 02_message_protocol_typed_routing.py
"""
import asyncio
import json

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve


# Each handler takes the payload and returns the payload to reply with. This is
# a dispatch TABLE, exactly like a REST router's path -> handler map, except
# the key is a made-up string instead of a URL.
def do_upper(payload):
    return payload["text"].upper()


def do_sum(payload):
    return sum(payload["numbers"])


def do_reverse(payload):
    return payload["text"][::-1]


ROUTES = {
    "upper": do_upper,
    "sum": do_sum,
    "reverse": do_reverse,
}


async def protocol_handler(websocket):
    async for raw in websocket:
        message = json.loads(raw)          # level 05 handles this failing
        kind = message.get("type")

        handler = ROUTES.get(kind)
        if handler is None:
            # The client asked for an operation we do not have. In REST this
            # would be a 404 and the request would be over. Here the connection
            # is long-lived and valuable, so we answer and keep listening.
            await websocket.send(json.dumps({
                "type": "error",
                "payload": f"unknown type {kind!r}; known: {sorted(ROUTES)}",
            }))
            continue

        # Echoing the type back is what lets the client correlate a reply with
        # what it asked for - there is no HTTP request/response pairing to lean on.
        await websocket.send(json.dumps({
            "type": kind,
            "payload": handler(message["payload"]),
        }))


async def demo(port: int) -> None:
    async with connect(f"ws://127.0.0.1:{port}") as ws:
        async def call(kind, payload):
            await ws.send(json.dumps({"type": kind, "payload": payload}))
            return json.loads(await ws.recv())

        print("== three different operations, one connection, one handshake ==")
        for kind, payload in [
            ("upper", {"text": "websockets"}),
            ("sum", {"numbers": [1, 2, 3, 4]}),
            ("reverse", {"text": "stressed"}),
        ]:
            reply = await call(kind, payload)
            print(f"  -> {{'type': {kind!r}, 'payload': {payload}}}")
            print(f"  <- {reply}")
            assert reply["type"] == kind

        assert (await call("upper", {"text": "abc"}))["payload"] == "ABC"
        assert (await call("sum", {"numbers": [10, 5]}))["payload"] == 15
        assert (await call("reverse", {"text": "abc"}))["payload"] == "cba"

        print("\n== an unknown type is an ERROR MESSAGE, not a dead connection ==")
        reply = await call("launch_missiles", {})
        print("  <-", reply)
        assert reply["type"] == "error"

        # Still alive, still authenticated, still in the same session - that is
        # the difference between "this message was bad" and "this client is bad".
        reply = await call("upper", {"text": "still here"})
        print("  <-", reply, "  (same connection, unharmed)")
        assert reply["payload"] == "STILL HERE"

        await ws.close(code=1000)
    print("\nOK")


async def main() -> None:
    async with serve(protocol_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
