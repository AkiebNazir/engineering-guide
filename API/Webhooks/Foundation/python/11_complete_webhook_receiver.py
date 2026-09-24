"""
FOUNDATION LEVEL 11 - Putting it all together: one complete webhook receiver
================================================================================
Nothing new here. Every idea from levels 00-10 - the envelope, routing by type,
validation, idempotency, signature verification, the replay window, the fast
ACK, retry-aware status codes, logging, recovery, and source-scoped
authorization - combined into one receiver, in the order a real one uses:

    log -> recover -> authenticate (signature + timestamp)
        -> validate -> authorize (source scope) -> dedupe -> enqueue -> 202
                                                                  |
                                             background worker does the slow part

That order is not arbitrary. Cheap and security-critical checks go first, so a
hostile or broken delivery is rejected before it costs you anything; the slow,
failable work goes last, off the request path entirely.

This is deliberately the same shape as ../../labs/python/04_idempotent_async_receiver.py
and ../../labs/python/05_standard_webhooks_replay_and_rotation.py: once this
feels easy, those labs (a SQLite inbox with a UNIQUE constraint, dead-letter
queues, secret rotation, SSRF-safe senders) are the very next step, not a jump.

You will learn
  * how ten small lessons compose into one real, secured, reliable receiver
  * that "a webhook receiver" is not one big new idea - it is these small ideas,
    layered in a deliberate order
  * which failures are the sender's to retry (5xx) and which are final (4xx)

Run it        python 11_complete_webhook_receiver.py
Keep serving  python 11_complete_webhook_receiver.py --serve   (POST to localhost:8080/webhook/billing)
"""
import hashlib
import hmac
import json
import queue
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 100_000
TOLERANCE = 300

# ---- level 10: one registration record per source ----
SOURCES = {
    "billing": {"secret": b"whsec_billing_only",
                "allowed_types": {"invoice.paid", "invoice.disputed", "refund.created"}},
    "support": {"secret": b"whsec_support_only", "allowed_types": {"ticket.created"}},
}

# ---- level 03: the dedupe store, and level 05: the work queue ----
state_lock = threading.Lock()
seen_ids: set[str] = set()
work_queue: queue.Queue = queue.Queue()
completed: list[str] = []          # what the worker actually finished
log_lines: list[str] = []


def sign(secret: bytes, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret, timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()


def worker() -> None:
    """Level 05: the slow, failable half of the job, off the request path."""
    while True:
        source_name, event = work_queue.get()
        time.sleep(0.05)                                   # pretend: charge, email, ship
        with state_lock:
            completed.append(f"{source_name}:{event['type']}:{event['id']}")
        work_queue.task_done()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        started = time.perf_counter()
        delivery_id = self.headers.get("X-Webhook-Delivery", "-")
        status, payload = self.handle_delivery()             # level 08: recovery lives inside
        line = f"delivery={delivery_id} status={status} ({(time.perf_counter() - started) * 1000:.1f}ms)"
        with state_lock:
            log_lines.append(line)
        print(f"  [log] {line}")
        self.reply(status, payload)

    def handle_delivery(self) -> tuple[int, dict]:
        try:
            return self.pipeline()
        except Exception as exc:                             # level 08: never leak a crash
            print(f"  [recovery] caught {exc!r}")
            return 500, {"error": "internal error, please retry"}

    def pipeline(self) -> tuple[int, dict]:
        # --- level 10 step 1: identify the source from its own endpoint URL ---
        if not self.path.startswith("/webhook/"):
            return 404, {"error": "not found"}
        source_name = self.path.removeprefix("/webhook/")
        source = SOURCES.get(source_name)

        declared = int(self.headers.get("Content-Length") or 0)
        if declared > MAX_BODY:                              # level 02
            return 413, {"error": "payload too large"}
        raw = self.rfile.read(declared)                      # read the RAW bytes once (level 04/09)

        if source is None:
            return 401, {"error": "unknown webhook source"}

        # --- level 09: authentication, with this source's secret only ---
        timestamp = self.headers.get("X-Webhook-Timestamp", "")
        signature = self.headers.get("X-Webhook-Signature", "")
        if not (timestamp and signature):
            return 401, {"error": "missing signature or timestamp"}
        if not hmac.compare_digest(sign(source["secret"], timestamp, raw), signature):
            return 401, {"error": "invalid signature"}

        # --- level 07: the replay window, now that the timestamp is trusted ---
        if not timestamp.isdigit() or abs(time.time() - int(timestamp)) > TOLERANCE:
            return 400, {"error": f"timestamp outside the {TOLERANCE}s tolerance"}

        # --- level 02: validation. Bad bytes are permanently bad -> 400 ---
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            return 400, {"error": "body is not valid JSON"}
        if not isinstance(event, dict) or not isinstance(event.get("type"), str) \
                or not isinstance(event.get("id"), str):
            return 400, {"error": "envelope needs string 'type' and 'id'"}

        # --- level 10 step 3: authorization. Genuine, but out of scope -> 403 ---
        if event["type"] not in source["allowed_types"]:
            return 403, {"error": f"source {source_name!r} may not send {event['type']!r}"}

        # --- level 01: route by type. Unknown-but-allowed types are ACKed ---
        if event["type"] == "invoice.disputed":
            # Stand-in for "my database is down": mine, temporary -> ask for a retry (level 06).
            return 500, {"error": "storage unavailable, please retry"}

        # --- level 03: idempotency. A redelivery is accepted, not reprocessed ---
        with state_lock:
            first_time = event["id"] not in seen_ids
            seen_ids.add(event["id"])
        if not first_time:
            return 202, {"status": "duplicate", "id": event["id"]}

        # --- level 05: the fast ACK. Queue it and answer; do not do the work here ---
        work_queue.put((source_name, event))
        return 202, {"status": "queued", "id": event["id"]}

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


# ---------------------------------------------------------------------------
# The demo below plays the SENDER (level 12 does that properly).
# ---------------------------------------------------------------------------
def deliver(base, source, raw: bytes, secret: bytes | None, timestamp: int | None = None, delivery="dlv"):
    headers = {"Content-Type": "application/json", "X-Webhook-Delivery": delivery}
    if secret is not None:
        ts = str(timestamp if timestamp is not None else int(time.time()))
        headers["X-Webhook-Timestamp"] = ts
        headers["X-Webhook-Signature"] = sign(secret, ts, raw)
    request = urllib.request.Request(f"{base}/webhook/{source}", data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    billing, support = SOURCES["billing"]["secret"], SOURCES["support"]["secret"]
    paid = b'{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}'

    checks = [
        ("unsigned delivery", lambda: deliver(base, "billing", paid, None), 401),
        ("signed with the wrong source's secret", lambda: deliver(base, "billing", paid, support), 401),
        ("stale timestamp (replayed later)",
         lambda: deliver(base, "billing", paid, billing, int(time.time()) - 3600), 400),
        ("malformed JSON", lambda: deliver(base, "billing", b"{not json", billing), 400),
        ("out-of-scope event type",
         lambda: deliver(base, "support", paid, support), 403),
        ("receiver temporarily broken",
         lambda: deliver(base, "billing", b'{"type":"invoice.disputed","id":"evt_2"}', billing), 500),
        ("valid delivery", lambda: deliver(base, "billing", paid, billing, delivery="dlv_a"), 202),
        ("the sender retries the SAME event",
         lambda: deliver(base, "billing", paid, billing, delivery="dlv_b"), 202),
        ("a different event", lambda: deliver(base, "support",
                                              b'{"type":"ticket.created","id":"evt_3"}', support), 202),
    ]
    for label, call, expected in checks:
        status, body = call()
        print(f"{label:<38} -> {status} {body}")
        assert status == expected, f"{label}: wanted {expected}, got {status}"

    work_queue.join()
    with state_lock:
        print(f"work actually completed: {completed}")
        assert completed == ["billing:invoice.paid:evt_1", "support:ticket.created:evt_3"], completed
        assert len(log_lines) == len(checks), "every delivery gets exactly one log line"
    print("OK")


if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/webhook/billing  (secret: whsec_billing_only)")
        print("a delivery needs X-Webhook-Timestamp and X-Webhook-Signature - see level 12 for a sender")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
