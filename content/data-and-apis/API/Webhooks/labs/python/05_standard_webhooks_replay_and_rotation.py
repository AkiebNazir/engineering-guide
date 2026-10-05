"""
LAB 05 (advanced) - The Standard Webhooks scheme: replay protection and zero-downtime secret rotation
=====================================================================================================
Every provider invented its own signature format (Stripe, GitHub, Slack, ...). The open
"Standard Webhooks" spec (standardwebhooks.com) captures the best practices in one scheme:

    headers:   webhook-id:        msg_p5jXN8AQM9LWM0D4loKWxJek        <- unique per message (dedupe key)
               webhook-timestamp: 1614265330                            <- unix seconds
               webhook-signature: v1,g0hM9Ss...=  v1,Rk2p...=          <- one or MORE space-separated signatures
    signed:    HMAC-SHA256( secret , f"{id}.{timestamp}.{raw_body}" ) then base64
    secret:    "whsec_" + base64(key bytes)

You will learn
  * checking your implementation against the spec's OFFICIAL TEST VECTOR (a known-answer test)
  * REPLAY PROTECTION: a captured valid request must not work an hour later
        - the timestamp is signed, so an attacker cannot refresh it
        - the receiver rejects timestamps outside a tolerance window (5 min), in BOTH directions
        - plus dedupe on webhook-id inside the window
  * SECRET ROTATION without downtime: the sender signs with the OLD and the NEW secret at once and
    sends both signatures; a receiver accepts if ANY matches. Roll out the new secret whenever,
    then retire the old one.
        sender:   webhook-signature: v1,<sig with old>  v1,<sig with new>
        receiver: knows [old] -> ok      later knows [new] -> ok      knows [old, new] -> ok
  * timing-safe comparison, and rejecting unknown signature versions

Run it  python 05_standard_webhooks_replay_and_rotation.py
"""
import base64
import hashlib
import hmac
import time

TOLERANCE = 300                                   # seconds: reject anything older/newer than 5 minutes


class VerificationError(Exception):
    pass


def secret_bytes(secret: str) -> bytes:
    return base64.b64decode(secret.removeprefix("whsec_"))


def sign(secret: str, msg_id: str, timestamp: int, body: bytes) -> str:
    content = f"{msg_id}.{timestamp}.".encode() + body
    return base64.b64encode(hmac.new(secret_bytes(secret), content, hashlib.sha256).digest()).decode()


def make_headers(secrets: list[str], msg_id: str, timestamp: int, body: bytes) -> dict:
    """SENDER side. More than one secret => more than one signature (rotation window)."""
    sigs = " ".join(f"v1,{sign(s, msg_id, timestamp, body)}" for s in secrets)
    return {"webhook-id": msg_id, "webhook-timestamp": str(timestamp), "webhook-signature": sigs}


seen_ids: dict[str, int] = {}                      # id -> timestamp. In production: Redis with TTL = TOLERANCE


def verify(secrets: list[str], headers: dict, body: bytes, now: float | None = None) -> None:
    """RECEIVER side. Raises VerificationError; returns None on success."""
    now = now if now is not None else time.time()
    try:
        msg_id, ts_raw, sig_header = headers["webhook-id"], headers["webhook-timestamp"], headers["webhook-signature"]
        ts = int(ts_raw)
    except (KeyError, ValueError):
        raise VerificationError("missing or malformed webhook headers")

    if abs(now - ts) > TOLERANCE:                  # too old (replay) OR too far in the future (clock trick)
        raise VerificationError(f"timestamp outside tolerance ({now - ts:+.0f}s)")

    candidates = []
    for part in sig_header.split(" "):
        version, _, sig = part.partition(",")
        if version == "v1":                        # ignore versions we do not understand (forward compatibility)
            candidates.append(sig)
    if not candidates:
        raise VerificationError("no supported signature version")

    ok = False
    for secret in secrets:                         # receiver secrets: [current] or [current, previous] during rotation
        expected = sign(secret, msg_id, ts, body)
        for sig in candidates:
            ok |= hmac.compare_digest(expected, sig)      # constant time; |= avoids short-circuit timing differences
    if not ok:
        raise VerificationError("no signature matched")

    if msg_id in seen_ids:                         # idempotency: same id inside the window is a duplicate/replay
        raise VerificationError("duplicate webhook-id")
    seen_ids[msg_id] = ts


def attempt(label: str, fn, expect_ok: bool):
    try:
        fn()
        outcome = "ACCEPTED"
        assert expect_ok, f"{label}: should have been rejected"
    except VerificationError as e:
        outcome = f"rejected ({e})"
        assert not expect_ok, f"{label}: should have been accepted, got {e}"
    print(f"  {label:<52} {outcome}")


if __name__ == "__main__":
    print("== 1. known-answer test: the OFFICIAL Standard Webhooks vector ==")
    vec_secret = "whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw"
    vec_body = b'{"test": 2432232314}'
    got = sign(vec_secret, "msg_p5jXN8AQM9LWM0D4loKWxJek", 1614265330, vec_body)
    print("  expected: g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=")
    print("  computed:", got)
    assert got == "g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE="
    print("  -> our implementation is interoperable with every Standard Webhooks library")

    OLD = "whsec_" + base64.b64encode(b"old-secret-old-secret-old-secret!").decode()
    NEW = "whsec_" + base64.b64encode(b"new-secret-new-secret-new-secret!").decode()
    body = b'{"type":"invoice.paid","data":{"id":"in_1"}}'
    now = 1_800_000_000

    print("\n== 2. replay protection ==")
    h = make_headers([OLD], "msg_1", now, body)
    attempt("fresh request", lambda: verify([OLD], h, body, now=now + 2), True)
    attempt("EXACT same request again (duplicate id)", lambda: verify([OLD], h, body, now=now + 3), False)
    h2 = make_headers([OLD], "msg_2", now, body)
    attempt("captured request replayed 1 hour later", lambda: verify([OLD], h2, body, now=now + 3600), False)
    h3 = make_headers([OLD], "msg_3", now + 3600, body)
    attempt("timestamp in the FUTURE (clock skew / trick)", lambda: verify([OLD], h3, body, now=now), False)
    forged = dict(h2, **{"webhook-timestamp": str(now + 3600), "webhook-id": "msg_4"})
    attempt("attacker refreshes the timestamp header", lambda: verify([OLD], forged, body, now=now + 3600), False)
    print("  (the timestamp is inside the signed content, so editing it invalidates the signature)")

    print("\n== 3. tampering ==")
    h5 = make_headers([OLD], "msg_5", now, body)
    attempt("body modified in transit", lambda: verify([OLD], h5, body.replace(b"in_1", b"in_9"), now=now), False)
    attempt("unsupported signature version only", lambda: verify([OLD], dict(h5, **{"webhook-signature": "v2,abc"}), body, now=now), False)
    attempt("missing headers", lambda: verify([OLD], {}, body, now=now), False)

    print("\n== 4. zero-downtime secret rotation ==")
    print("  phase 1: sender signs with OLD only, receiver knows OLD")
    attempt("OLD -> [OLD]", lambda: verify([OLD], make_headers([OLD], "rot_1", now, body), body, now=now), True)
    print("  phase 2: sender starts signing with BOTH; receivers (not yet updated) still know only OLD")
    both = make_headers([OLD, NEW], "rot_2", now, body)
    print("    header:", both["webhook-signature"][:50] + "...  (two v1 signatures)")
    attempt("OLD+NEW signatures -> receiver knows [OLD]", lambda: verify([OLD], both, body, now=now), True)
    print("  phase 3: customers roll out the new secret (during the overlap they may hold [NEW, OLD])")
    both2 = make_headers([OLD, NEW], "rot_3", now, body)
    attempt("OLD+NEW signatures -> receiver knows [NEW]", lambda: verify([NEW], both2, body, now=now), True)
    attempt("OLD+NEW signatures -> receiver knows [NEW, OLD]", lambda: verify([NEW, OLD], make_headers([OLD, NEW], "rot_4", now, body), body, now=now), True)
    print("  phase 4: sender stops signing with OLD; receivers that already switched to NEW keep working")
    attempt("NEW only -> receiver knows [NEW]", lambda: verify([NEW], make_headers([NEW], "rot_5", now, body), body, now=now), True)
    attempt("NEW only -> receiver STILL on [OLD] (forgot to update)", lambda: verify([OLD], make_headers([NEW], "rot_6", now, body), body, now=now), False)
    print("  => no request was ever rejected because of the rotation itself; a receiver that never updated fails loudly")
    print("\nOK")
