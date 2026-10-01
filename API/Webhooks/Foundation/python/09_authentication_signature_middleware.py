"""
FOUNDATION LEVEL 09 - Authentication: the signature check, as middleware
============================================================================
This IS level 04's check. Same secret, same HMAC-SHA256 over the raw body, same
hmac.compare_digest. Nothing about the cryptography changes here. What changes
is WHERE it lives: level 04 wrote the check inline at the top of the handler,
and this level lifts it out into middleware (level 08's mechanism) that runs
before dispatch ever happens.

That move is the whole lesson, and it is not cosmetic:
  * the check cannot be forgotten on a new event type - there is one door
  * handlers stop containing security code, so they get simple and testable
  * a rejection short-circuits: dispatch is never called, so an unauthenticated
    delivery costs you one hash and nothing else

Authentication answers exactly ONE question: "is this delivery really from the
sender we share a secret with?" It says nothing about what that sender is
allowed to trigger - that is level 10, authorization, and it is deliberately a
separate concept. For webhooks the identity is the SENDER, not a user: there is
no login, no session, no bearer token you chose. The signature is the identity.

You will learn
  * how to turn an inline check into middleware, and why one door beats ten
  * 401 Unauthorized means "we do not recognize you" - never confuse it with
    403 (level 10), which means "we know you and the answer is still no"
  * middleware needs the RAW body, so read the body ONCE, at the edge, and pass
    those exact bytes down the chain (re-reading or re-encoding breaks the hash)
  * attaching the verified sender onto the delivery, so nothing downstream
    re-checks the signature

Run it   python 09_authentication_signature_middleware.py
"""
import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

SECRET = b"whsec_shared_with_the_provider"
MAX_BODY = 1_000_000

dispatch_calls: list[str] = []


@dataclass
class Delivery:
    raw_body: bytes                 # the exact bytes, read once at the edge
    signature: str
    sender: str | None = None       # filled in BY the middleware, never by the caller


@dataclass
class Res:
    status: int
    body: bytes
    headers: dict = field(default_factory=dict)


Handler = Callable[[Delivery], Res]


def sign(secret: bytes, raw_body: bytes) -> str:
    return hmac.new(secret, raw_body, hashlib.sha256).hexdigest()


def with_authentication(next_handler: Handler) -> Handler:
    """Level 04's four lines, now guarding every event type at once."""
    def wrapped(delivery: Delivery) -> Res:
        if not delivery.signature:
            return Res(401, json.dumps({"error": "missing signature header"}).encode())
        if not hmac.compare_digest(sign(SECRET, delivery.raw_body), delivery.signature):
            return Res(401, json.dumps({"error": "invalid signature"}).encode())
        delivery.sender = "payments-provider"   # who we now know this is
        return next_handler(delivery)           # only reached by verified deliveries
    return wrapped


def dispatch(delivery: Delivery) -> Res:
    # No security code in here at all - and no way to reach this line without
    # having passed the middleware above.
    event = json.loads(delivery.raw_body)
    dispatch_calls.append(event["id"])
    return Res(200, json.dumps({"accepted": event["id"], "from": delivery.sender}).encode())


pipeline: Handler = with_authentication(dispatch)


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        raw = self.rfile.read(length)   # read ONCE, hand the same bytes down
        res = pipeline(Delivery(raw_body=raw, signature=self.headers.get("X-Webhook-Signature", "")))
        self.send_response(res.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(res.body)))
        self.end_headers()
        self.wfile.write(res.body)

    def log_message(self, *args):
        pass


def deliver(base: str, raw: bytes, signature: str | None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Webhook-Signature"] = signature
    request = urllib.request.Request(f"{base}/webhook", data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    raw = b'{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}'

    status, body = deliver(base, raw, None)
    print(f"no signature        -> {status} {body}")
    assert status == 401

    status, body = deliver(base, raw, sign(b"whsec_wrong", raw))
    print(f"wrong secret        -> {status} {body}")
    assert status == 401

    status, body = deliver(base, raw, "not-even-hex")
    print(f"garbage signature   -> {status} {body}")
    assert status == 401

    status, body = deliver(base, raw, sign(SECRET, raw))
    print(f"correctly signed    -> {status} {body}   (and only now is the sender known)")
    assert status == 200 and body["from"] == "payments-provider"

    # The short-circuit, proved: three rejected deliveries never reached dispatch.
    print(f"dispatch was called for: {dispatch_calls}")
    assert dispatch_calls == ["evt_1"]
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), HttpHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
