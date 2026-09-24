"""
FOUNDATION LEVEL 04 - Signature verification: proving the delivery is real
=============================================================================
Your webhook URL is public. There is no login page in front of it, no session,
no API key you got to choose - anyone who learns the URL can POST
`{"type":"invoice.paid","id":"evt_1"}` and claim to be your payment provider.

The fix is a shared secret that never travels on the wire. When the provider
signs up your endpoint, both sides store the same random string. For every
delivery the sender computes HMAC-SHA256(secret, raw_body) and puts it in a
header; you recompute the same thing and compare. Only someone holding the
secret can produce a matching value, so a match proves BOTH "this came from
them" and "nobody edited the body in flight".

Three details decide whether the check is actually secure:
  1. sign the RAW BODY BYTES - not a re-serialized dict. json.loads followed by
     json.dumps changes spacing and key order, and the signature stops matching.
  2. compare with hmac.compare_digest (constant time), never `==`, which leaks
     how many leading characters were right via how long it took to say no.
  3. verify FIRST, parse and act SECOND. An invalid delivery must cause zero
     work and zero logging of its contents.

You will learn
  * what an HMAC is, in one line: a keyed hash - same body + same key = same
    digest, and you cannot produce it without the key (level 13 builds one by hand)
  * why 401 and not 400: this is an identity failure, not a malformed payload
  * why the raw bytes matter, demonstrated with a re-serialized body that fails
  * that a signature says nothing about WHEN - replay protection needs a
    timestamp too (level 07)

Run it   python 04_signature_verification_hmac.py
"""
import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# In production this comes from the provider's dashboard and lives in a secret
# store / env var - never in the source tree like this.
SECRET = b"whsec_shared_with_the_provider"
SIGNATURE_HEADER = "X-Webhook-Signature"
MAX_BODY = 1_000_000

processed: list[str] = []


def sign(secret: bytes, raw_body: bytes) -> str:
    """The whole scheme. A keyed hash of the exact bytes, as lowercase hex."""
    return hmac.new(secret, raw_body, hashlib.sha256).hexdigest()


def verify(secret: bytes, raw_body: bytes, provided: str) -> bool:
    expected = sign(secret, raw_body)
    # compare_digest takes the same amount of time whether the first character
    # differs or only the last one does.
    return hmac.compare_digest(expected, provided)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        raw = self.rfile.read(length)  # keep the RAW bytes; do not parse yet

        provided = self.headers.get(SIGNATURE_HEADER, "")
        if not provided:
            self.reply(401, {"error": "missing signature"})
            return
        if not verify(SECRET, raw, provided):
            # No parsing, no logging of the body, no work. Just: no.
            print("  [receiver] signature mismatch -> 401, nothing was parsed or processed")
            self.reply(401, {"error": "invalid signature"})
            return

        event = json.loads(raw)  # only NOW is it safe to look inside
        processed.append(event["id"])
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


def deliver(base: str, raw: bytes, signature: str | None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers[SIGNATURE_HEADER] = signature
    request = urllib.request.Request(f"{base}/webhook", data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    raw = b'{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}'

    status, body = deliver(base, raw, sign(SECRET, raw))
    print(f"correctly signed        -> {status} {body}")
    assert status == 200

    status, body = deliver(base, raw, None)
    print(f"no signature header     -> {status} {body}")
    assert status == 401

    status, body = deliver(base, raw, sign(b"whsec_attacker_guess", raw))
    print(f"signed with wrong secret-> {status} {body}   (an impostor who knows the URL but not the secret)")
    assert status == 401

    # Same signature, body edited in flight: the amount is now 50000.
    tampered = raw.replace(b"500", b"50000")
    status, body = deliver(base, tampered, sign(SECRET, raw))
    print(f"body tampered in flight -> {status} {body}   (signature covers the bytes, so editing them breaks it)")
    assert status == 401

    # The classic self-inflicted bug: re-serializing the JSON before signing.
    # Identical MEANING, different BYTES (spaces after the separators).
    reserialized = json.dumps(json.loads(raw)).encode()
    assert reserialized != raw
    status, body = deliver(base, reserialized, sign(SECRET, raw))
    print(f"body re-serialized      -> {status} {body}   (same JSON, different bytes: sign/verify RAW)")
    assert status == 401

    print(f"events actually processed: {processed}")
    assert processed == ["evt_1"]
    print("OK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
