"""
FOUNDATION LEVEL 07 - Delivery metadata: the headers around the event
=========================================================================
The body says WHAT happened. Three headers say things about THIS ATTEMPT to
tell you, and they are not interchangeable:

    X-Webhook-Delivery    a unique id for this ATTEMPT. A retry of the same
                          event gets a NEW delivery id. Log it, never dedupe on it.
    X-Webhook-Timestamp   when the sender signed the request (unix seconds)
    X-Webhook-Signature   level 04's HMAC - but now over "<timestamp>.<body>"

That last change is the point of this level. A signature over the body alone is
valid FOREVER: anyone who captures one legitimate delivery can replay those
exact bytes at you next year and the signature still verifies. Binding the
timestamp INTO the signed string, and then refusing anything outside a few
minutes, closes that window. The timestamp has to be signed, or an attacker
would just edit the header.

You will learn
  * event id vs delivery id: one is stable across retries (dedupe key), the
    other is unique per attempt (log/support key)
  * signing "<timestamp>.<raw_body>" instead of the raw body alone
  * a replay window: reject timestamps older (or newer) than the tolerance
  * why the clock check comes with the signature check, not after it
  * that this is exactly the scheme Stripe and the Standard Webhooks spec use
    (see ../../labs/python/05_standard_webhooks_replay_and_rotation.py)

Run it   python 07_delivery_metadata_headers.py
"""
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = b"whsec_shared_with_the_provider"
TOLERANCE = 300          # seconds: five minutes either side, like most providers
MAX_BODY = 1_000_000

processed: list[str] = []
delivery_log: list[str] = []


def signed_payload(timestamp: str, raw_body: bytes) -> bytes:
    """The exact bytes both sides hash. The separator matters as much as the
    parts: without it, timestamp "1" + body "23..." and "12" + "3..." would
    hash identically."""
    return timestamp.encode() + b"." + raw_body


def sign(secret: bytes, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret, signed_payload(timestamp, raw_body), hashlib.sha256).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        raw = self.rfile.read(length)

        delivery_id = self.headers.get("X-Webhook-Delivery", "")
        timestamp = self.headers.get("X-Webhook-Timestamp", "")
        signature = self.headers.get("X-Webhook-Signature", "")
        if not (delivery_id and timestamp and signature):
            self.reply(400, {"error": "missing delivery metadata headers"})
            return

        # 1. Verify the signature over timestamp + body. Until this passes, the
        #    timestamp header is just an attacker-supplied string.
        if not hmac.compare_digest(sign(SECRET, timestamp, raw), signature):
            self.reply(401, {"error": "invalid signature"})
            return

        # 2. Only now is the timestamp trustworthy - so now we can judge its age.
        try:
            age = abs(time.time() - int(timestamp))
        except ValueError:
            self.reply(400, {"error": "timestamp is not an integer"})
            return
        if age > TOLERANCE:
            # Correctly signed, but far too old (or from the future - a badly
            # skewed clock). A 400: retrying these same bytes will only get older.
            print(f"  [receiver] delivery={delivery_id} signature valid but {age:.0f}s old -> replay window closed")
            self.reply(400, {"error": f"timestamp outside the {TOLERANCE}s tolerance"})
            return

        event = json.loads(raw)
        # The delivery id is what you quote in a support ticket ("we never got
        # delivery 7f3a"); the EVENT id is what you dedupe on (level 03).
        delivery_log.append(f"{delivery_id} carried event {event['id']}")
        processed.append(event["id"])
        self.reply(200, {"accepted": event["id"], "delivery": delivery_id})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def deliver(base: str, raw: bytes, delivery_id: str, timestamp: int, signature: str | None = None):
    ts = str(timestamp)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Delivery": delivery_id,
        "X-Webhook-Timestamp": ts,
        "X-Webhook-Signature": signature if signature is not None else sign(SECRET, ts, raw),
    }
    request = urllib.request.Request(f"{base}/webhook", data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    raw = b'{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}'
    now = int(time.time())

    status, body = deliver(base, raw, "dlv_001", now)
    print(f"fresh, signed delivery      -> {status} {body}")
    assert status == 200

    # The retry of the SAME event: new delivery id, new timestamp, same event id.
    status, body = deliver(base, raw, "dlv_002", now)
    print(f"retry (new delivery id)     -> {status} {body}   (same event id inside - level 03 dedupes it)")
    assert status == 200 and body["delivery"] == "dlv_002"

    # A captured delivery replayed an hour later, signature perfectly intact.
    old = now - 3600
    status, body = deliver(base, raw, "dlv_003", old)
    print(f"replayed one hour later     -> {status} {body}")
    assert status == 400

    # An attacker who rewrites the timestamp header to look fresh: the
    # signature was computed over the OLD timestamp, so it no longer matches.
    status, body = deliver(base, raw, "dlv_004", now, signature=sign(SECRET, str(old), raw))
    print(f"timestamp header rewritten  -> {status} {body}   (the timestamp is inside the signature)")
    assert status == 401

    status, body = deliver(base, raw, "", now)
    print(f"no metadata headers at all  -> {status} {body}")
    assert status == 400

    print(f"delivery log: {delivery_log}")
    assert processed == ["evt_1", "evt_1"]   # two attempts of ONE event reached the handler
    assert len(delivery_log) == 2
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
