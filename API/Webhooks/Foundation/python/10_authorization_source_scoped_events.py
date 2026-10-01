"""
FOUNDATION LEVEL 10 - Authorization: each source may only send its own events
================================================================================
Authentication (level 09) proved a delivery was signed by SOMEONE we share a
secret with. Authorization is a different question: is THIS sender allowed to
trigger THIS event type?

It matters as soon as you integrate more than one system - and everyone does.
Your receiver ends up with a billing provider, a support desk, a CI system, all
POSTing to you. Give them one shared secret and you have built a privilege
escalation: the support desk's secret (or a leaked support integration) can now
fabricate `refund.created` and move money. Fix it with two rules:

    every source gets its OWN secret          -> a leak is contained to one source
    every source gets its OWN allowed types   -> a valid signature is not a blank cheque

So `billing` may send `refund.created`; `support`, correctly signed with its own
real secret, may not - and that is a 403, not a 401. The difference is the whole
level: 401 means "I do not know you", 403 means "I know exactly who you are and
the answer is still no".

You will learn
  * per-source secrets, selected by the source in the URL, checked with that
    source's key only (never "try every secret until one matches")
  * an allow-list of event types per source - authorization data, not code
  * 403 Forbidden vs 401 Unauthorized, on the same endpoint, same day
  * the order that this forces: identify -> authenticate -> authorize -> dispatch
  * why a 403 is a permanent answer: the sender must NOT retry it (level 06)

Run it   python 10_authorization_source_scoped_events.py
"""
import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1_000_000

# One registration record per source: its own secret, its own scope. In a real
# receiver this is a database table you can edit without deploying code.
SOURCES = {
    "billing": {
        "secret": b"whsec_billing_only",
        "allowed_types": {"invoice.paid", "refund.created"},
    },
    "support": {
        "secret": b"whsec_support_only",
        "allowed_types": {"ticket.created", "ticket.closed"},
    },
}

processed: list[str] = []


def sign(secret: bytes, raw_body: bytes) -> str:
    return hmac.new(secret, raw_body, hashlib.sha256).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # ---- 1. IDENTIFY: which registration is this delivery claiming to be? ----
        if not self.path.startswith("/webhook/"):
            self.reply(404, {"error": "not found"})
            return
        source_name = self.path.removeprefix("/webhook/")
        source = SOURCES.get(source_name)

        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        raw = self.rfile.read(length)

        if source is None:
            # An unregistered source is an identity failure, not a scope failure.
            self.reply(401, {"error": "unknown webhook source"})
            return

        # ---- 2. AUTHENTICATE: with THIS source's secret, and only that one ----
        signature = self.headers.get("X-Webhook-Signature", "")
        if not signature or not hmac.compare_digest(sign(source["secret"], raw), signature):
            self.reply(401, {"error": f"invalid signature for source {source_name!r}"})
            return

        event = json.loads(raw)

        # ---- 3. AUTHORIZE: is this type inside the source's registered scope? ----
        if event["type"] not in source["allowed_types"]:
            print(f"  [receiver] {source_name} is genuine but not scoped for {event['type']} -> 403")
            self.reply(403, {
                "error": f"source {source_name!r} may not send {event['type']!r}",
                "allowed": sorted(source["allowed_types"]),
            })
            return

        # ---- 4. DISPATCH: everything above passed ----
        processed.append(f"{source_name}:{event['type']}")
        self.reply(200, {"accepted": event["id"], "source": source_name})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def deliver(base: str, source: str, event: dict, sign_with: bytes | None):
    raw = json.dumps(event).encode()
    headers = {"Content-Type": "application/json"}
    if sign_with is not None:
        headers["X-Webhook-Signature"] = sign(sign_with, raw)
    request = urllib.request.Request(f"{base}/webhook/{source}", data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    refund = {"type": "refund.created", "id": "evt_1", "data": {"amount": 500}}
    ticket = {"type": "ticket.created", "id": "evt_2", "data": {"subject": "help"}}

    status, body = deliver(base, "billing", refund, SOURCES["billing"]["secret"])
    print(f"billing -> refund.created (own secret)  -> {status} {body}")
    assert status == 200

    status, body = deliver(base, "support", ticket, SOURCES["support"]["secret"])
    print(f"support -> ticket.created (own secret)  -> {status} {body}")
    assert status == 200

    # The point of the level: a perfectly valid, correctly signed delivery from
    # a source that has no business creating refunds.
    status, body = deliver(base, "support", refund, SOURCES["support"]["secret"])
    print(f"support -> refund.created (own secret)  -> {status} {body}")
    assert status == 403

    # Signed with the WRONG source's secret: never gets as far as scope.
    status, body = deliver(base, "billing", refund, SOURCES["support"]["secret"])
    print(f"billing -> refund.created (support key) -> {status} {body}   (per-source secrets do not interchange)")
    assert status == 401

    status, body = deliver(base, "ci-system", ticket, SOURCES["support"]["secret"])
    print(f"ci-system (never registered)            -> {status} {body}")
    assert status == 401

    print(f"processed: {processed}")
    assert processed == ["billing:refund.created", "support:ticket.created"]
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
