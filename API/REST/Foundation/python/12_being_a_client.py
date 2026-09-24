"""
FOUNDATION LEVEL 12 - Every API you will ever use is also just a client
============================================================================
Levels 00-09 were all SERVER code. But you spend at least as much real-world
time writing CLIENTS: code that calls someone else's API. This level flips the
lens: a small server plays "someone else's API", and the interesting code is
the client calling it - handling timeouts, non-2xx responses, and retrying a
transient failure. This is deliberately where Foundation stops and
../../labs/ (auth, rate limiting, retries, idempotency, pagination) picks up.

You will learn
  * a client must treat "connection refused / timeout" and "got a 500" as two
    DIFFERENT failure kinds - one means "maybe try again", the other might too,
    but for a different reason (the server told you something, it did not just vanish)
  * exponential backoff: wait longer after each failed attempt, so a struggling
    server is not hammered harder while it is already struggling
  * why you must NEVER blindly retry every failed request (retrying a non-
    idempotent POST can create the same order twice - covered properly in
    ../../labs/python/05_idempotency_and_cursor_pagination.py)

Run it   python 12_being_a_client.py
"""
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ATTEMPTS = {"count": 0}


class FlakyHandler(BaseHTTPRequestHandler):
    """Fails the first 2 calls to /flaky with 503, then succeeds. Simulates a
    real service warming up or briefly overloaded - not actually broken."""

    def do_GET(self):
        if self.path != "/flaky":
            self.send_response(404)
            self.end_headers()
            return
        ATTEMPTS["count"] += 1
        if ATTEMPTS["count"] <= 2:
            body = json.dumps({"error": "temporarily unavailable"}).encode()
            self.send_response(503)
            self.send_header("Retry-After", "0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = json.dumps({"status": "ready"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def get_with_retries(url: str, max_attempts: int = 5):
    """A GET is safe to retry: calling it twice never changes server state."""
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            # The server DID respond - only 5xx is worth retrying, 4xx never is
            # (a 400 will still be a 400 next time; the request itself is bad).
            if e.code < 500 or attempt == max_attempts:
                return e.code, json.loads(e.read())
            wait = 0.05 * (2 ** (attempt - 1))   # exponential backoff: 0.05s, 0.1s, 0.2s, ...
            print(f"  attempt {attempt} got {e.code}, backing off {wait:.2f}s before retrying")
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError) as e:
            # The server did not even answer - same backoff-and-retry idea applies.
            if attempt == max_attempts:
                raise
            time.sleep(0.05 * (2 ** (attempt - 1)))
    raise RuntimeError("unreachable")


def demo(base: str) -> None:
    status, body = get_with_retries(f"{base}/flaky")
    print(f"final result -> {status} {body}")
    assert status == 200 and body == {"status": "ready"}
    assert ATTEMPTS["count"] == 3, "expected exactly 2 failures then 1 success"
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), FlakyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
