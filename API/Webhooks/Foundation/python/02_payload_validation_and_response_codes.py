"""
FOUNDATION LEVEL 02 - Validating the payload, and choosing the right status code
===================================================================================
Levels 00-01 trusted the body: `json.loads` on whatever arrived, then
`event["type"]` without looking. A webhook URL is PUBLIC - anything on the
internet can POST garbage to it, and even the real sender ships bugs. An
unhandled exception here is not just a 500: it is a 500 the sender will retry,
again and again, forever.

The one rule for a receiver: never leave the sender hanging. Answer fast, and be
unambiguous about accepted vs rejected. The status code is the ONLY thing the
sender understands (level 06 shows exactly what it does with each one).

You will learn
  * bound the body first (Content-Length is a claim, not a guarantee) -> 413
  * malformed JSON and a missing envelope field are BAD REQUESTS -> 400, because
    no amount of retrying will ever make that same bytes-on-the-wire valid
  * an event you cannot handle YET (your database is down) is the opposite:
    -> 500, please retry me, this is my fault and it is temporary
  * why you should never answer 302/301/401-by-accident: senders treat anything
    that is not 2xx as "not delivered"
  * validate the ENVELOPE (type, id) and the per-type `data` separately

Run it   python 02_payload_validation_and_response_codes.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 10_000  # deliberately small so the demo can trip it


def validate(raw: bytes) -> tuple[dict | None, str]:
    """Returns (event, "") when usable, or (None, reason). Pure function: no
    network, no exceptions escaping - easy to unit test on its own."""
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"body is not valid JSON: {exc.msg}"
    if not isinstance(event, dict):
        return None, "body must be a JSON object"
    for field in ("type", "id"):
        if not isinstance(event.get(field), str) or not event[field]:
            return None, f"envelope field {field!r} must be a non-empty string"
    if not isinstance(event.get("data", {}), dict):
        return None, "envelope field 'data' must be an object"
    return event, ""


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.reply(404, {"error": "not found"})
            return

        declared = int(self.headers.get("Content-Length") or 0)
        if declared > MAX_BODY:
            # 413 tells the sender "permanently too big" - retrying the same
            # payload cannot help. Read nothing; do not let a caller make us
            # allocate 2GB just by claiming it in a header.
            self.reply(413, {"error": f"payload larger than {MAX_BODY} bytes"})
            return

        raw = self.rfile.read(declared)
        event, reason = validate(raw)
        if event is None:
            # 400 = "this delivery is permanently unusable, do not retry it".
            self.reply(400, {"error": reason})
            return

        if event["type"] == "order.created" and event["data"].get("order_id") is None:
            # Envelope was fine, the per-type payload was not. Still a 400.
            self.reply(400, {"error": "order.created requires data.order_id"})
            return

        if event["type"] == "order.exploded":
            # A stand-in for "my database is down right now". This is OUR
            # problem and it is temporary, so we ask to be retried: 500.
            self.reply(500, {"error": "temporarily unable to process, please retry"})
            return

        self.reply(200, {"accepted": event["id"]})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def deliver(base: str, raw: bytes):
    request = urllib.request.Request(
        f"{base}/webhook", data=raw, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    cases = [
        ("valid event", b'{"type":"order.created","id":"evt_1","data":{"order_id":"A-1"}}', 200),
        ("not JSON at all", b"<html>oops</html>", 400),
        ("JSON, but not an object", b'["order.created"]', 400),
        ("envelope missing id", b'{"type":"order.created","data":{}}', 400),
        ("per-type data missing", b'{"type":"order.created","id":"evt_2","data":{}}', 400),
        ("oversized body", b'{"type":"order.created","id":"evt_3","data":{"pad":"' + b"x" * MAX_BODY + b'"}}', 413),
        ("our side is broken", b'{"type":"order.exploded","id":"evt_4","data":{}}', 500),
    ]
    for label, raw, expected in cases:
        status, body = deliver(base, raw)
        meaning = {200: "accepted", 400: "never retry", 413: "never retry", 500: "please retry"}[status]
        print(f"{label:<24} -> {status} ({meaning}) {body}")
        assert status == expected, f"{label}: wanted {expected}, got {status}"

    # The crucial property: not one of those answered slowly, hung, or crashed
    # the server. The next delivery still works.
    status, _ = deliver(base, b'{"type":"order.created","id":"evt_9","data":{"order_id":"A-9"}}')
    assert status == 200
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
