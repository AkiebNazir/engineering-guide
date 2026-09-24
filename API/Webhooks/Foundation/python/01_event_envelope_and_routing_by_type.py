"""
FOUNDATION LEVEL 01 - The event envelope, and routing by type
=================================================================
Level 00 accepted any JSON at one URL. Real senders deliver EVERY kind of event
to that same URL, wrapped in a small, boring, predictable envelope:

    {"type": "order.created", "id": "evt_1", "data": {...}}
     ^ what happened          ^ which        ^ the payload
                               delivery it is

So a webhook receiver does not route on the URL path the way a REST API does
(../../REST/Foundation level 01) - one path handles everything. It routes on the
`type` FIELD INSIDE the body. That is webhooks' routing equivalent.

You will learn
  * the envelope/payload split: the outer fields are metadata every event has,
    `data` is the part that differs per type
  * dispatch = a lookup table from event type -> handler function
  * why an UNKNOWN type must still be answered 200 and ignored: the sender will
    add new event types without asking you, and a non-2xx makes it retry
    forever for an event you were never going to care about
  * that dotted type names (`order.created`) are a convention, not a rule - they
    just make prefix matching and subscriptions readable

Run it   python 01_event_envelope_and_routing_by_type.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1_000_000

# What each handler actually did, so the demo can prove the right one ran.
EFFECTS: list[str] = []


# ---- one handler per event type. Each one only knows about its own `data`. ----
def on_order_created(event: dict) -> None:
    EFFECTS.append(f"reserved stock for order {event['data']['order_id']}")


def on_order_cancelled(event: dict) -> None:
    EFFECTS.append(f"released stock for order {event['data']['order_id']}")


# The dispatch table IS the router. Adding an event type means adding one line
# here - not a new URL, not a new endpoint.
HANDLERS = {
    "order.created": on_order_created,
    "order.cancelled": on_order_cancelled,
}


def dispatch(event: dict) -> dict:
    handler = HANDLERS.get(event["type"])
    if handler is None:
        # NOT an error. The sender is allowed to invent new event types at any
        # time; "I don't handle that one" is a successful, final outcome.
        return {"handled": False, "reason": "unsubscribed event type"}
    handler(event)
    return {"handled": True}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.reply(404, {"error": "not found"})
            return
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        event = json.loads(self.rfile.read(length))
        result = dispatch(event)
        print(f"  [receiver] type={event['type']:<16} id={event['id']:<7} -> {result}")
        # Both outcomes are 200: "this delivery is finished, never send it again".
        self.reply(200, result)

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def deliver(base: str, event: dict):
    request = urllib.request.Request(
        f"{base}/webhook",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    status, body = deliver(base, {"type": "order.created", "id": "evt_1", "data": {"order_id": "A-1"}})
    print(f"order.created   -> {status} {body}")
    assert status == 200 and body["handled"] is True

    status, body = deliver(base, {"type": "order.cancelled", "id": "evt_2", "data": {"order_id": "A-1"}})
    print(f"order.cancelled -> {status} {body}")
    assert status == 200 and body["handled"] is True

    status, body = deliver(base, {"type": "order.gift_wrapped", "id": "evt_3", "data": {}})
    print(f"order.gift_wrapped -> {status} {body}   (a type we never subscribed to: ACK it, ignore it)")
    assert status == 200 and body["handled"] is False

    print(f"effects in order: {EFFECTS}")
    assert EFFECTS == ["reserved stock for order A-1", "released stock for order A-1"]
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
