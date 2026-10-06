"""
LAB 02 (basic) - Being the SENDER: event design, signing with a timestamp, and delivering
=========================================================================================
Webhooks flip the usual roles: YOU are the client, your customer's server is the API.
You will learn
  * a good event envelope - every event carries:
        id          unique, stable across retries (receivers de-duplicate on it)
        type        "invoice.paid", "order.shipped" (dotted, past tense: something HAS happened)
        created     when it happened
        api_version which payload shape this is (so you can evolve it)
        data        the payload
  * FAT vs THIN payloads:  fat = full object inside (convenient, but stale and bigger, leaks more)
                           thin = ids only, receiver GETs the current state from your API (always fresh)
  * a timestamped signature:  sign( f"{timestamp}.{body}" )   sent as   t=<ts>,v1=<hmac>
    The timestamp is INSIDE the signed data, so a captured request cannot be replayed later.
  * headers receivers rely on:  Webhook-Id, Webhook-Timestamp, a User-Agent, Content-Type
  * delivery hygiene: short timeouts (5s), no unbounded redirects, record every attempt's outcome

    your system --event--> [ Sender: build -> serialise ONCE -> sign -> POST ] --> customer endpoint

Run it  python 02_sender_signed_events.py
"""
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# ======================================================== SENDER (your product) ==
def make_event(event_type: str, data: dict, api_version: str = "2026-01-01") -> dict:
    return {"id": f"evt_{uuid.uuid4().hex[:16]}", "type": event_type, "created": int(time.time()),
            "api_version": api_version, "data": data}


def sign(secret: str, timestamp: int, body: bytes) -> str:
    signed_payload = f"{timestamp}.".encode() + body               # timestamp is part of what is signed
    return hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()


@dataclass
class Delivery:
    event_id: str
    url: str
    status: int | None
    error: str | None
    duration_ms: float


@dataclass
class Sender:
    log: list[Delivery] = field(default_factory=list)

    def deliver(self, url: str, secret: str, event: dict) -> Delivery:
        # Serialise ONCE. The exact bytes we sign are the exact bytes we send.
        body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode()
        ts = int(time.time())
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Acme-Webhooks/1.0",
            "Webhook-Id": event["id"],
            "Webhook-Timestamp": str(ts),
            "Webhook-Signature": f"t={ts},v1={sign(secret, ts, body)}",
        }
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        start = time.perf_counter()
        status = error = None
        try:
            with urllib.request.urlopen(req, timeout=5) as r:               # always a timeout
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code                                                  # a response, just not a 2xx
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            error = str(getattr(e, "reason", e))                             # no response at all
        d = Delivery(event["id"], url, status, error, (time.perf_counter() - start) * 1000)
        self.log.append(d)
        return d

    @staticmethod
    def succeeded(d: Delivery) -> bool:
        return d.status is not None and 200 <= d.status < 300


# ===================================================== a customer endpoint ========
def make_customer_endpoint(secret: str, received: list):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            t, v1 = (p.split("=", 1)[1] for p in self.headers["Webhook-Signature"].split(","))
            ok = hmac.compare_digest(sign(secret, int(t), body), v1)
            received.append({"headers": dict(self.headers), "body": body, "valid": ok})
            self.send_response(200 if ok else 401)
            self.end_headers()

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    SECRET = "whsec_customer_42"
    received: list = []
    srv = make_customer_endpoint(SECRET, received)
    url = f"http://127.0.0.1:{srv.server_port}/hooks"
    sender = Sender()

    print("== 1. a FAT event ==")
    fat = make_event("invoice.paid", {"object": {"id": "in_9", "customer": "cus_7", "amount_paid": 4999, "currency": "usd",
                                                 "lines": [{"sku": "A1", "qty": 2}]}})
    d = sender.deliver(url, SECRET, fat)
    print(f"  {fat['type']} -> {d.status} in {d.duration_ms:.1f} ms")
    print("  what the customer's server received:")
    for h in ("Content-Type", "User-Agent", "Webhook-Id", "Webhook-Timestamp", "Webhook-Signature"):
        v = received[-1]["headers"][h]
        print(f"    {h}: {v[:60]}{'...' if len(v) > 60 else ''}")
    print("    body:", received[-1]["body"].decode()[:100] + "...")
    assert d.status == 200 and received[-1]["valid"]
    assert received[-1]["headers"]["Webhook-Id"] == fat["id"]

    print("\n== 2. a THIN event: ids only; the receiver fetches current state from your API ==")
    thin = make_event("invoice.paid", {"invoice_id": "in_9"})
    d = sender.deliver(url, SECRET, thin)
    print(f"  body is only {len(received[-1]['body'])} bytes; receiver would now call GET /v1/invoices/in_9")
    assert d.status == 200 and len(received[-1]["body"]) < len(json.dumps(fat))
    print("  fat: convenient, but the snapshot may be STALE by the time it is processed, and leaks more data")
    print("  thin: always fresh and safer, costs the receiver an API call (needs API auth + rate limits)")

    print("\n== 3. the signature covers the timestamp: a captured request cannot be replayed later ==")
    r = received[0]
    ts_old = int(r["headers"]["Webhook-Timestamp"])
    forged = sign(SECRET, ts_old + 3600, r["body"])
    print("  same body with a different timestamp needs a different signature:", forged != sign(SECRET, ts_old, r["body"]))
    assert forged != sign(SECRET, ts_old, r["body"])
    print("  a receiver that rejects timestamps older than 5 minutes therefore rejects any replay (lab 05)")

    print("\n== 4. what failure looks like to the sender ==")
    srv.shutdown()
    srv.server_close()
    d = sender.deliver(url, SECRET, make_event("order.shipped", {"order_id": "o_1"}))
    print(f"  endpoint down  -> status={d.status} error={d.error!r}   (no response at all: retry later)")
    assert d.status is None and d.error
    bad = make_customer_endpoint("a-different-secret", received)
    d = sender.deliver(f"http://127.0.0.1:{bad.server_port}/hooks", SECRET, make_event("order.shipped", {"order_id": "o_2"}))
    print(f"  wrong secret   -> status={d.status} (the receiver answered 401: a config problem, not transient)")
    assert d.status == 401 and not Sender.succeeded(d)
    bad.shutdown()

    print("\ndelivery log kept by the sender (this becomes the 'recent deliveries' page in your dashboard):")
    for x in sender.log:
        print(f"  {x.event_id}  status={x.status}  error={x.error}  {x.duration_ms:.0f}ms")
    print("\nOK")
