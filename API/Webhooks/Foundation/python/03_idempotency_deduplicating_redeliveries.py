"""
FOUNDATION LEVEL 03 - Idempotency: the same event WILL arrive twice
=======================================================================
This is the defining webhook problem. Not a rare edge case, not bad luck: every
serious sender promises AT-LEAST-ONCE delivery, which is a polite way of saying
"we will sometimes send you the same event more than once, on purpose".

It happens because the sender cannot tell these two situations apart:
    you never got the event                     -> must retry
    you got it, processed it, and your 200 was   -> must NOT retry (but it will)
    lost / timed out / arrived after 10s
Faced with silence, the only safe thing a sender can do is retry. So the only
safe thing YOU can do is make a repeat delivery harmless.

The fix is one idea: every event carries a stable `id` that is the SAME across
redeliveries. Remember the ids you have finished, and short-circuit the rest.
"Only process it once" is your job, not the sender's.

You will learn
  * at-least-once delivery, and why exactly-once delivery does not exist
  * dedupe on the EVENT id (stable across retries), never on the delivery id
    (new for every attempt - see level 07)
  * a duplicate must still answer 200: it IS delivered, you already have it
  * the check-and-mark must be ATOMIC (a lock here, a UNIQUE constraint in a
    real database - see ../../labs/python/04_idempotent_async_receiver.py)
  * that this is why level 05's fast ACK matters: slow handlers cause the very
    timeouts that produce the duplicates

Run it   python 03_idempotency_deduplicating_redeliveries.py
"""
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1_000_000

seen_lock = threading.Lock()
seen_ids: set[str] = set()      # in a real receiver: a table with UNIQUE(event_id)
side_effects: list[str] = []    # the thing that must happen exactly once


def claim(event_id: str) -> bool:
    """True if THIS call is the first to claim the id. Check-and-insert happen
    under one lock: two concurrent redeliveries cannot both win."""
    with seen_lock:
        if event_id in seen_ids:
            return False
        seen_ids.add(event_id)
        return True


def process(event: dict) -> None:
    # Pretend this charges a card / ships a box / sends an email - something you
    # would very much like not to do twice.
    side_effects.append(f"emailed receipt for {event['data']['order_id']}")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        event = json.loads(self.rfile.read(length))

        if not claim(event["id"]):
            print(f"  [receiver] id={event['id']} seen before -> skipping the work, still answering 200")
            self.reply(200, {"status": "duplicate", "id": event["id"]})
            return

        process(event)
        print(f"  [receiver] id={event['id']} is new -> processed")
        self.reply(200, {"status": "processed", "id": event["id"]})

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
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read())


def demo(base: str) -> None:
    event = {"type": "order.paid", "id": "evt_7", "data": {"order_id": "A-1"}}

    status, body = deliver(base, event)
    print(f"delivery 1 of evt_7 -> {status} {body}")
    assert body["status"] == "processed"

    # The sender's retry: byte-for-byte the same event, because from its point
    # of view the first attempt might never have landed.
    status, body = deliver(base, event)
    print(f"delivery 2 of evt_7 -> {status} {body}   (same id: accepted, but NOT processed again)")
    assert status == 200 and body["status"] == "duplicate"

    status, body = deliver(base, {"type": "order.paid", "id": "evt_8", "data": {"order_id": "A-2"}})
    print(f"delivery 1 of evt_8 -> {status} {body}")
    assert body["status"] == "processed"

    # Now the hard case: 12 redeliveries of one event, all at the same instant.
    burst = {"type": "order.paid", "id": "evt_9", "data": {"order_id": "A-3"}}
    threads = [threading.Thread(target=deliver, args=(base, burst)) for _ in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"3 distinct events, 15 deliveries -> side effects: {side_effects}")
    assert side_effects == [
        "emailed receipt for A-1",
        "emailed receipt for A-2",
        "emailed receipt for A-3",
    ], side_effects
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
