"""
FOUNDATION LEVEL 12 - Being the sender: signing and delivering a webhook
============================================================================
Levels 00-11 were all RECEIVER code. Now switch chairs. Every provider whose
webhooks you consume runs the code in this file, and you will write it too the
first time your own service needs to notify customers.

This is the mirror of every other API type's "being a client" level, but with a
twist that is unique to webhooks: nobody asked you for this request. There is no
user waiting, no response to render. You are calling into someone else's server,
unprompted, and you are entirely responsible for making sure the event
eventually lands - which means the retry loop is not optional, it IS the feature.

The sender's contract, in the order this file does it:
    1. serialize the event ONCE and keep those exact bytes
    2. sign timestamp + bytes, put delivery id / timestamp / signature in headers
    3. POST with a short timeout - a slow receiver must not block your queue
    4. read the status code and decide: done / retry later / give up (level 06)
    5. back off exponentially between attempts, honouring Retry-After
    6. keep the EVENT id stable across attempts so the receiver can dedupe,
       and give each ATTEMPT a fresh delivery id so logs stay untangled

You will learn
  * serialize once, sign the same bytes you send (re-serializing breaks the HMAC)
  * exponential backoff, and why a fixed 1s retry is how you DDoS a recovering
    receiver with your whole queue at once
  * giving up: a 4xx goes to a dead-letter queue, not back on the retry loop
  * that "at-least-once" is a SENDER-side decision, and duplicates are its
    unavoidable price (level 03 is the receiver paying it)

Run it   python 12_being_a_sender.py
"""
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = b"whsec_shared_with_the_receiver"
TIMEOUT = 0.5          # never let one slow receiver hold a sender thread hostage
MAX_ATTEMPTS = 4
BASE_BACKOFF = 0.05    # tiny so the demo is quick; real senders use seconds -> hours

dead_letter: list[dict] = []
attempts_seen: dict[str, int] = {"/flaky": 0, "/bad-payload": 0, "/good": 0}


# ---------------------------------------------------------------------------
# THE SENDER
# ---------------------------------------------------------------------------
def sign(secret: bytes, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret, timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()


def attempt_delivery(url: str, raw: bytes, event_id: str, attempt: int):
    """One HTTP attempt. Returns (status, retry_after) - status None means the
    receiver never answered, which is NOT the same as answering 'no'."""
    timestamp = str(int(time.time()))
    headers = {
        "Content-Type": "application/json",
        # New per ATTEMPT - so the receiver's logs can tell attempts apart...
        "X-Webhook-Delivery": f"dlv_{event_id}_{attempt}",
        "X-Webhook-Timestamp": timestamp,
        # ...re-signed per attempt, because the timestamp is inside the signature.
        "X-Webhook-Signature": sign(SECRET, timestamp, raw),
    }
    request = urllib.request.Request(url, data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.headers.get("Retry-After")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Retry-After")
    except (urllib.error.URLError, TimeoutError):
        return None, None


def send_event(url: str, event: dict) -> tuple[bool, int]:
    """Deliver one event, with retries. Returns (delivered, attempts_used)."""
    raw = json.dumps(event).encode()          # serialize ONCE; these are the signed bytes

    for attempt in range(1, MAX_ATTEMPTS + 1):
        status, retry_after = attempt_delivery(url, raw, event["id"], attempt)

        if status is not None and 200 <= status < 300:
            print(f"  [sender] attempt {attempt}: {status} - delivered, stopping")
            return True, attempt

        permanent = status is not None and 400 <= status < 500 and status not in (408, 429)
        if permanent:
            # The receiver told us this payload will never work. Retrying it is
            # pure waste; a human needs to look at it.
            print(f"  [sender] attempt {attempt}: {status} - permanent rejection, dead-lettering")
            dead_letter.append({"event": event, "status": status})
            return False, attempt

        if attempt == MAX_ATTEMPTS:
            print(f"  [sender] attempt {attempt}: {status} - out of attempts, dead-lettering for now")
            dead_letter.append({"event": event, "status": status})
            return False, attempt

        # Exponential backoff: 1x, 2x, 4x... so a struggling receiver gets more
        # room each time, not the same hammering. Retry-After overrides us.
        wait = float(retry_after) if retry_after else BASE_BACKOFF * (2 ** (attempt - 1))
        reason = "Retry-After" if retry_after else "backoff"
        print(f"  [sender] attempt {attempt}: {status} - retrying in {wait:.3f}s ({reason})")
        time.sleep(wait)

    return False, MAX_ATTEMPTS


# ---------------------------------------------------------------------------
# A RECEIVER to deliver to, so the sender has something to fight with.
# ---------------------------------------------------------------------------
class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        attempts_seen[self.path] = attempts_seen.get(self.path, 0) + 1
        n = attempts_seen[self.path]

        timestamp = self.headers.get("X-Webhook-Timestamp", "")
        if not hmac.compare_digest(sign(SECRET, timestamp, raw), self.headers.get("X-Webhook-Signature", "")):
            self.reply(401, {"error": "invalid signature"})   # the sender got the signing wrong
            return

        if self.path == "/good":
            self.reply(202, {"status": "queued"})
        elif self.path == "/flaky":
            # Down for the first two attempts, then recovers - the single most
            # common real situation, and exactly what backoff exists for.
            if n <= 2:
                self.reply(503, {"error": "still starting up"})
            else:
                self.reply(202, {"status": "queued"})
        elif self.path == "/bad-payload":
            self.reply(400, {"error": "data.amount must be an integer"})
        else:
            self.reply(404, {"error": "no endpoint registered"})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def demo(base: str) -> None:
    event = {"type": "invoice.paid", "id": "evt_1", "data": {"amount": 500}}

    print("delivering to a healthy receiver:")
    delivered, used = send_event(f"{base}/good", event)
    assert delivered and used == 1

    print("delivering to a receiver that is down, then recovers:")
    delivered, used = send_event(f"{base}/flaky", event)
    print(f"  -> delivered={delivered} after {used} attempts, receiver saw {attempts_seen['/flaky']}")
    assert delivered and used == 3 and attempts_seen["/flaky"] == 3

    print("delivering a payload the receiver permanently rejects:")
    delivered, used = send_event(f"{base}/bad-payload", event)
    print(f"  -> delivered={delivered} after {used} attempt (no retries: 400 is final)")
    assert not delivered and used == 1 and attempts_seen["/bad-payload"] == 1

    print("delivering to an endpoint that does not exist:")
    delivered, used = send_event(f"{base}/gone", event)
    assert not delivered and used == 1          # 404 is a 4xx: permanent

    print(f"dead letter queue holds {len(dead_letter)} event(s): "
          f"{[(d['event']['id'], d['status']) for d in dead_letter]}")
    assert len(dead_letter) == 2
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
