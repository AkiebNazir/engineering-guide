"""
LAB 05 (advanced) - GraphQL subscriptions: server push over WebSockets
======================================================================
You will learn
  * a subscription field is an ASYNC GENERATOR: every `yield` becomes one message to the client
  * publish/subscribe inside the server: a mutation publishes an event, subscribers receive it
  * the wire protocol (graphql-transport-ws) - you will see the raw JSON messages:

        client                                   server
          |--- connection_init ----------------->|
          |<-- connection_ack -------------------|
          |--- subscribe {id, query} ----------->|
          |<-- next {id, data} ------------------|   (once per event)
          |<-- next {id, data} ------------------|
          |--- complete {id} ------------------->|   (client unsubscribes)

  * cleanup: when the client leaves, the generator is cancelled - remove the subscriber queue
    or every disconnected client leaks memory

Needs   pip install "strawberry-graphql[fastapi]" fastapi httpx websockets
Run it  python 05_subscriptions_over_websocket.py
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

import strawberry
from fastapi import FastAPI
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)


# ------------------------------------------------------------ tiny pub/sub --
class Broker:
    """One asyncio.Queue per subscriber. In production this is Redis pub/sub or Kafka."""

    def __init__(self):
        self.subscribers: set[asyncio.Queue] = set()

    def publish(self, message: dict):
        for q in list(self.subscribers):
            q.put_nowait(message)

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(q)
        try:
            while True:
                yield await q.get()
        finally:                                  # runs on disconnect / cancel
            self.subscribers.discard(q)


broker = Broker()


@strawberry.type
class Message:
    room: str
    text: str


@strawberry.type
class Query:
    @strawberry.field
    def subscriber_count(self) -> int:
        return len(broker.subscribers)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def send(self, room: str, text: str) -> Message:
        broker.publish({"room": room, "text": text})
        return Message(room=room, text=text)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def messages(self, room: str) -> AsyncGenerator[Message, None]:
        async for event in broker.subscribe():
            if event["room"] == room:             # server-side filtering: only what this client asked for
                yield Message(**event)


schema = strawberry.Schema(Query, mutation=Mutation, subscription=Subscription)


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(GraphQLRouter(schema, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]), prefix="/graphql")
    return app


def show(direction: str, msg: dict):
    print(f"  {direction} {json.dumps(msg)}")


def demo_protocol():
    """Drive the real wire protocol through a WebSocket, like a browser would."""
    client = TestClient(build_app())
    with client.websocket_connect("/graphql", subprotocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]) as ws:
        ws.send_json({"type": "connection_init"});                       show("->", {"type": "connection_init"})
        ack = ws.receive_json();                                          show("<-", ack)
        assert ack["type"] == "connection_ack"

        sub = {"id": "1", "type": "subscribe", "payload": {"query": 'subscription { messages(room: "go") { room text } }'}}
        ws.send_json(sub);                                                show("->", sub)

        # the server needs a moment to register the subscriber; poll a plain HTTP query for it
        for _ in range(100):
            if client.post("/graphql", json={"query": "{ subscriberCount }"}).json()["data"]["subscriberCount"] == 1:
                break
        print("  subscribers registered on the server:", len(broker.subscribers))

        for room, text in [("go", "hello gophers"), ("python", "not for us"), ("go", "second message")]:
            client.post("/graphql", json={"query": "mutation($r:String!,$t:String!){ send(room:$r, text:$t){ text } }",
                                          "variables": {"r": room, "t": text}})
            print(f"  (someone sent {text!r} to room {room!r})")

        got = []
        for _ in range(2):                                               # expect exactly the two "go" messages
            m = ws.receive_json();                                        show("<-", m)
            got.append(m["payload"]["data"]["messages"]["text"])
        assert got == ["hello gophers", "second message"], got            # the "python" room event was filtered out

        ws.send_json({"id": "1", "type": "complete"});                    show("->", {"id": "1", "type": "complete"})

    for _ in range(100):                                                  # after disconnect the generator is cancelled
        if not broker.subscribers:
            break
        client.post("/graphql", json={"query": "{ subscriberCount }"})
    print("  subscribers after disconnect:", len(broker.subscribers))
    assert not broker.subscribers, "leak: a dead client is still subscribed"


if __name__ == "__main__":
    demo_protocol()
    print("OK")
