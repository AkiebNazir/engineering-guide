"""
FOUNDATION LEVEL 06 - Retry-aware responses: your status code is an instruction
==================================================================================
Level 02 picked status codes from the receiver's chair. This level sits in the
SENDER's chair and shows what those numbers actually do, because the sender has
no other channel: it cannot read your error message, it will not open your
dashboard. It reads one integer and decides your fate.

    2xx        done. Delete the delivery, stop, never send this event again.
    408, 429   slow down, then retry (429 usually with a Retry-After header)
    5xx        please retry me later - you said the problem is yours and temporary
    other 4xx  do NOT retry. You told me this payload will never work; retrying
               identical bytes cannot change your answer. Park it in a dead-letter
               queue and alert a human instead.

The consequences of getting this wrong are real and asymmetric:
  * returning 500 for a permanently bad payload = the sender retries for days,
    and a retry queue backs up behind an event that can never succeed
  * returning 200 for something you failed to handle = the event is GONE. The
    sender deletes it, nobody retries, and you have silently lost data.
When in doubt, 500 is the safer mistake - a duplicate (level 03 handles it) is
recoverable, a lost event is not.

You will learn
  * the sender-side decision function: status code in -> retry / stop / fail-fast out
  * why 2xx is a promise you must not make lightly
  * Retry-After, and a sender that honours it instead of its own backoff
  * that redirects (3xx) are not success: most senders do not follow them

Run it   python 06_retry_aware_status_codes.py
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------------------
# THE SENDER'S SIDE: the whole retry policy, as one pure function.
# ---------------------------------------------------------------------------
STOP = "stop"            # delivered, we are finished
RETRY = "retry"          # try again later, with backoff
DEAD_LETTER = "dead"     # permanently rejected: stop retrying, tell a human


def decide(status: int | None) -> str:
    if status is None:
        return RETRY                       # timeout / connection refused: no answer is not a "no"
    if 200 <= status < 300:
        return STOP
    if status in (408, 429):
        return RETRY                       # explicitly "later", not "never"
    if 500 <= status < 600:
        return RETRY                       # the receiver called it temporary
    if 300 <= status < 400:
        return DEAD_LETTER                 # a redirect is a misconfigured endpoint, not a delivery
    return DEAD_LETTER                     # every other 4xx: identical bytes will fail identically


# ---------------------------------------------------------------------------
# THE RECEIVER'S SIDE: one endpoint per answer, so we can see each decision.
# ---------------------------------------------------------------------------
ROUTES = {
    "/ok": (200, {"accepted": True}),
    "/queued": (202, {"queued": True}),
    "/malformed": (400, {"error": "data.amount is not a number - this will never parse"}),
    "/unknown-source": (401, {"error": "bad signature"}),
    "/too-many": (429, {"error": "slow down"}),
    "/database-down": (503, {"error": "temporarily unavailable"}),
    "/moved": (302, {"error": "we changed our URL and forgot to tell you"}),
}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        status, payload = ROUTES.get(self.path, (404, {"error": "not found"}))
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if status == 429:
            self.send_header("Retry-After", "2")   # seconds; the sender should obey this
        if status == 302:
            self.send_header("Location", "/ok")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class NoRedirects(urllib.request.HTTPRedirectHandler):
    """Most webhook senders do NOT follow redirects (a moved endpoint is a
    config change you must acknowledge, and following one could leak the
    signature to a third host). We turn urllib's auto-following off to match."""

    def redirect_request(self, *args):
        return None


opener = urllib.request.build_opener(NoRedirects)


def deliver(base: str, path: str):
    """Returns (status, retry_after_seconds_or_None)."""
    request = urllib.request.Request(
        base + path,
        data=b'{"type":"order.paid","id":"evt_1","data":{}}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(request) as response:
            return response.status, response.headers.get("Retry-After")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Retry-After")


def demo(base: str) -> None:
    expected = {
        "/ok": STOP,
        "/queued": STOP,
        "/malformed": DEAD_LETTER,
        "/unknown-source": DEAD_LETTER,
        "/too-many": RETRY,
        "/database-down": RETRY,
        "/moved": DEAD_LETTER,
    }
    for path, want in expected.items():
        status, retry_after = deliver(base, path)
        decision = decide(status)
        hint = f"  (Retry-After: {retry_after}s - wait that long, not your own guess)" if retry_after else ""
        print(f"POST {path:<17} -> {status} -> sender decides: {decision}{hint}")
        assert decision == want, f"{path}: wanted {want}, got {decision}"

    # No answer at all is a retry, not a failure: the event may well have been
    # processed, we simply never heard back (this is level 03's whole reason).
    print(f"POST (connection timed out) -> no status -> sender decides: {decide(None)}")
    assert decide(None) == RETRY

    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
