"""
LAB 01 (basic) - Receiving a webhook safely: verify the signature before you trust anything
============================================================================================
You will learn
  * a webhook endpoint is a PUBLIC URL: anyone on the internet can POST to it and claim to be Stripe
  * the fix: the provider signs each request with a secret you share (HMAC-SHA256 of the body);
    you recompute it and compare. Only someone with the secret can produce a valid signature.
  * three details that decide whether your check is actually secure:
      1. sign/verify the RAW BYTES of the body - NOT a re-serialised JSON object
         (json.loads -> json.dumps changes spacing and key order, so the signature no longer matches!)
      2. compare with hmac.compare_digest (constant time) - never `==` (timing side channel)
      3. verify FIRST, parse and act SECOND; on failure return 401 and do no work
  * respond 2xx quickly. The provider treats anything else as "not delivered" and retries.

    provider                                         you
       |-- POST /webhook  X-Signature: <hmac>  ------>|  verify(raw_body, secret, header)
       |                  {"type":"payment.succeeded"} |  ok?  -> 200      bad? -> 401
       |<-------------------------- 200 --------------|

Run it  python 01_receiver_hmac_verification.py            (self-contained demo)
Serve   python 01_receiver_hmac_verification.py --serve    (listens on :8080; POST with curl)
"""
import hashlib
import hmac
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = b"whsec_dev_secret_change_me"          # per-endpoint secret shared with the provider; load from env/vault
MAX_BODY = 1_000_000                             # never read an unbounded body


def sign(secret: bytes, body: bytes) -> str:
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def verify(secret: bytes, body: bytes, header: str) -> bool:
    expected = sign(secret, body)
    return hmac.compare_digest(expected, header or "")       # constant-time comparison


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            return self.reply(413, "body too large")
        raw = self.rfile.read(length)                         # RAW bytes: exactly what was signed

        if not verify(SECRET, raw, self.headers.get("X-Signature", "")):
            return self.reply(401, "invalid signature")       # reject BEFORE parsing or acting

        try:
            event = json.loads(raw)                           # only now is it safe to interpret
        except json.JSONDecodeError:
            return self.reply(400, "invalid JSON")
        EVENTS.append(event)                                  # ...do the (fast) work: enqueue it
        self.reply(200, "ok")

    def reply(self, status: int, text: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode())

    def log_message(self, *a):
        pass


EVENTS: list[dict] = []


def post(url: str, body: bytes, signature: str | None) -> int:
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Signature"] = signature
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        return urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        return e.code


def demo(url: str):
    body = json.dumps({"id": "evt_1", "type": "payment.succeeded", "amount": 4999}).encode()

    print("== 1. a valid signed request ==")
    sig = sign(SECRET, body)
    print("  signature:", sig[:24] + "...")
    status = post(url, body, sig)
    print("  ->", status, "| events accepted:", len(EVENTS))
    assert status == 200 and len(EVENTS) == 1

    print("\n== 2. attackers ==")
    cases = {
        "no signature header": (body, None),
        "random signature": (body, "0" * 64),
        "signature of a DIFFERENT body": (body, sign(SECRET, b'{"id":"evt_1","type":"payment.succeeded","amount":1}')),
        "tampered amount, old signature": (body.replace(b"4999", b"1"), sig),
        "right body, wrong secret": (body, sign(b"whsec_guess", body)),
    }
    for label, (b, s) in cases.items():
        st = post(url, b, s)
        print(f"  {label:<34} -> {st}")
        assert st == 401
    assert len(EVENTS) == 1, "no forged event may be accepted"

    print("\n== 3. why RAW bytes matter: re-serialising breaks the signature ==")
    pretty = json.dumps(json.loads(body), indent=2).encode()           # same data, different bytes
    print("  same JSON, re-formatted   ->", post(url, pretty, sig), "(rejected: bytes differ from what was signed)")
    print("  Frameworks that hand you a parsed dict (request.json()) can silently hide the raw body:")
    print("  always capture request.body()/rfile bytes BEFORE parsing when verifying signatures.")
    assert post(url, pretty, sig) == 401

    print("\n== 4. limits ==")
    try:
        outcome = post(url, b"x" * 1_500_000, sig)
    except (urllib.error.URLError, ConnectionError):
        outcome = "connection closed"                 # the server answered 413 and hung up without reading the body
    print("  1.5 MB body               ->", outcome, "(the server refused to read it: bounded before reading)")
    assert outcome in (413, "connection closed")
    print("\nOK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("webhook receiver on http://localhost:8080  (secret:", SECRET.decode() + ")")
        ThreadingHTTPServer(("127.0.0.1", 8080), Receiver).serve_forever()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{srv.server_port}/webhook")
    srv.shutdown()
