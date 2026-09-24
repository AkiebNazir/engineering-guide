"""
FOUNDATION LEVEL 08 - Middleware: code that wraps every delivery
====================================================================
Levels 00-07 put everything a delivery needed inside one handler. Middleware is
a WRAPPER: a function that takes a handler and returns a new handler that runs
code before and/or after calling the original - without touching the original
at all. Signature checks (09), source scoping (10), logging and recovery all
become one line each, applied to every event type at once.

For a receiver, recovery is not a nicety. A handler that raises has TWO bad
outcomes to avoid: the obvious one (this delivery dies with no answer, so the
sender times out and retries blind) and the sneaky one (some frameworks answer
200 by default on an unhandled error, and then the event is lost forever).
Recovery makes the failure explicit and correct: log it, answer 500, and let the
sender retry on purpose (level 06).

You will learn
  * a middleware has the SAME shape as a handler: delivery in, response out -
    it just also gets to call "the next thing" in between
  * chaining: wrapping a wrapper in a wrapper, in a chosen order
  * ORDER matters: logging placed OUTSIDE recovery still logs the crashed
    delivery and the 500 it became; placed INSIDE, it would never run at all
  * a webhook log line is worth designing: event type, event id, delivery id,
    outcome, duration - that is what you will search at 3am
  * one poisonous delivery must not affect the next one

Run it   python 08_middleware_logging_and_recovery.py
"""
import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

# A tiny stand-in for "the delivery" and "the response" - just enough fields to
# demonstrate the wrapping idea, independent of http.server's own classes.


@dataclass
class Delivery:
    delivery_id: str
    event_type: str
    event_id: str
    data: dict


@dataclass
class Res:
    status: int
    body: bytes
    headers: dict = field(default_factory=dict)


Handler = Callable[[Delivery], Res]
Middleware = Callable[[Handler], Handler]

log_lines: list[str] = []
refunds: list[str] = []


# ---- the "real" application logic, with zero knowledge of logging/recovery ----
def dispatch(delivery: Delivery) -> Res:
    if delivery.event_type == "refund.created":
        refunds.append(delivery.event_id)
        return Res(200, b'{"handled": true}')
    if delivery.event_type == "order.exploded":
        # A real bug: the payload is missing a field this handler assumed.
        raise KeyError(delivery.data["definitely_not_here"])
    return Res(200, b'{"handled": false, "reason": "unsubscribed event type"}')


# ---- middleware #1: the log line you will actually page through ----
def with_logging(next_handler: Handler) -> Handler:
    def wrapped(delivery: Delivery) -> Res:
        start = time.perf_counter()
        res = next_handler(delivery)
        elapsed_ms = (time.perf_counter() - start) * 1000
        line = (f"delivery={delivery.delivery_id} type={delivery.event_type} "
                f"event={delivery.event_id} status={res.status} ({elapsed_ms:.2f}ms)")
        log_lines.append(line)
        print(f"  [log] {line}")
        return res
    return wrapped


# ---- middleware #2: catches ANY exception from everything it wraps ----
def with_recovery(next_handler: Handler) -> Handler:
    def wrapped(delivery: Delivery) -> Res:
        try:
            return next_handler(delivery)
        except Exception as exc:
            print(f"  [recovery] caught {exc!r} - answering 500 so the sender retries, staying up")
            return Res(500, b'{"error": "internal error, please retry"}')
    return wrapped


# Built once, outside in: logging sees everything, including failures that
# recovery converts into a deliberate 500. Swap the order and the crashed
# delivery vanishes from your logs - the one line you most needed.
pipeline: Handler = with_logging(with_recovery(dispatch))


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        event = json.loads(self.rfile.read(length))
        res = pipeline(Delivery(
            delivery_id=self.headers.get("X-Webhook-Delivery", "?"),
            event_type=event.get("type", ""),
            event_id=event.get("id", ""),
            data=event.get("data", {}),
        ))
        self.send_response(res.status)
        self.send_header("Content-Type", "application/json")
        for k, v in res.headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(res.body)))
        self.end_headers()
        self.wfile.write(res.body)

    def log_message(self, *args):
        pass


def deliver(base: str, delivery_id: str, event: dict):
    request = urllib.request.Request(
        f"{base}/webhook",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json", "X-Webhook-Delivery": delivery_id},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    status, body = deliver(base, "dlv_1", {"type": "refund.created", "id": "evt_1", "data": {}})
    print(f"refund.created  -> {status} {body}")
    assert status == 200

    status, body = deliver(base, "dlv_2", {"type": "order.exploded", "id": "evt_2", "data": {}})
    print(f"order.exploded  -> {status} {body}   (the handler raised - recovery made it a deliberate 500)")
    assert status == 500

    # The crash above must not have taken the receiver down for the next sender.
    status, body = deliver(base, "dlv_3", {"type": "refund.created", "id": "evt_3", "data": {}})
    print(f"refund.created  -> {status} {body}   (receiver still alive after the crash)")
    assert status == 200

    assert refunds == ["evt_1", "evt_3"]
    assert len(log_lines) == 3, "every delivery must be logged, INCLUDING the one that crashed"
    assert "status=500" in log_lines[1]
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), HttpHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
