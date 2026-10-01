"""
FOUNDATION BONUS - What is a webhook signature, really? (optional, read last)
=================================================================================
Every level from 04 onwards called `hmac.new(secret, body, sha256).hexdigest()`
and trusted it. This file opens that box. There is no webhook-signing helper
here, no `hmac` module doing the interesting part - just sha256 and the
definition of HMAC, printed byte by byte, so you can see that a signature is
nothing more than "a keyed hash of the body".

    HMAC(K, m) = H( (K' XOR opad) || H( (K' XOR ipad) || m ) )

      H      sha256
      K'     the key, zero-padded to the hash's 64-byte block size
             (or, if the key is longer than a block, hashed down first)
      ipad   the byte 0x36 repeated 64 times
      opad   the byte 0x5c repeated 64 times
      ||     plain concatenation of bytes

That is the entire algorithm. Two hashes and two XORs. The nesting is not
decoration: hashing the key with the message ONCE (`sha256(key + body)`) is a
real, broken scheme - length-extension attacks let an attacker append to your
body and still produce a valid digest without ever knowing the key.

This is optional. Nothing in levels 00-12 depends on it. It exists to answer
"but what is `hmac.new` actually doing for me?" once you are curious.

You will learn
  * a "signature" is a hex string of 32 bytes: the output of one hash function
  * exactly which bytes get hashed, printed - the secret, the timestamp, the body
  * why HMAC nests two hashes instead of doing the obvious one
  * that our hand-rolled version is byte-identical to the stdlib's, which is
    the proof there was never any magic

Run it   python 13_bonus_hmac_by_hand.py
"""
import hashlib
import hmac  # imported ONLY to prove our version matches at the end

BLOCK_SIZE = 64        # sha256 processes 64-byte blocks - that is where 64 comes from
IPAD_BYTE = 0x36
OPAD_BYTE = 0x5C


def hmac_sha256_by_hand(key: bytes, message: bytes, verbose: bool = False) -> bytes:
    # STEP 1: normalise the key to exactly one block.
    if len(key) > BLOCK_SIZE:
        key = hashlib.sha256(key).digest()      # too long: hash it down to 32 bytes
    padded_key = key + b"\x00" * (BLOCK_SIZE - len(key))   # too short: zero-fill to 64

    # STEP 2: two different 64-byte masks, derived from the same key.
    inner_key = bytes(b ^ IPAD_BYTE for b in padded_key)
    outer_key = bytes(b ^ OPAD_BYTE for b in padded_key)

    # STEP 3: hash (inner_key || message), then hash (outer_key || that digest).
    inner_input = inner_key + message
    inner_digest = hashlib.sha256(inner_input).digest()
    outer_input = outer_key + inner_digest
    final = hashlib.sha256(outer_input).digest()

    if verbose:
        print(f"  key padded to {len(padded_key)} bytes : {padded_key.hex()}")
        print(f"  inner key (key XOR 0x36)     : {inner_key.hex()}")
        print(f"  outer key (key XOR 0x5c)     : {outer_key.hex()}")
        print(f"  inner input  ({len(inner_input):3d} bytes)   : {inner_key.hex()[:16]}... || {message!r}")
        print(f"  inner digest ( 32 bytes)     : {inner_digest.hex()}")
        print(f"  outer input  ({len(outer_input):3d} bytes)   : {outer_key.hex()[:16]}... || <inner digest>")
        print(f"  final digest ( 32 bytes)     : {final.hex()}")
    return final


def main() -> None:
    secret = b"whsec_shared_with_the_provider"
    timestamp = "1700000000"
    body = b'{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}'

    # This is the ONE string a webhook signature is computed over (level 07).
    # Nothing clever: the timestamp, a dot, and the raw body bytes.
    signed_payload = timestamp.encode() + b"." + body
    print("---- the exact bytes being hashed ----")
    print(f"  secret        : {secret!r}   ({len(secret)} bytes, never sent over the wire)")
    print(f"  signed payload: {signed_payload!r}   ({len(signed_payload)} bytes)")
    print()

    print("---- HMAC-SHA256, computed by hand from sha256 alone ----")
    by_hand = hmac_sha256_by_hand(secret, signed_payload, verbose=True)
    print()
    print(f"signature header value: {by_hand.hex()}")
    print()

    # The proof: the stdlib, which every level from 04 on used, agrees exactly.
    from_stdlib = hmac.new(secret, signed_payload, hashlib.sha256).digest()
    print(f"hand-rolled == hmac.new: {by_hand == from_stdlib}")
    assert by_hand == from_stdlib
    assert len(by_hand) == 32 and len(by_hand.hex()) == 64

    # Two properties worth seeing for yourself, both straight from "keyed hash":
    # 1. one different byte in the body changes the whole digest (avalanche)
    tampered = hmac_sha256_by_hand(secret, signed_payload.replace(b"500", b"501"))
    differing = sum(a != b for a, b in zip(by_hand, tampered))
    print(f"changing one digit of the amount changes {differing}/32 digest bytes")
    assert differing > 20

    # 2. without the secret you cannot produce the digest, even with the body
    guessed = hmac_sha256_by_hand(b"whsec_attacker_guess", signed_payload)
    assert guessed != by_hand

    # And the longer-than-a-block key path, which is easy to get wrong.
    long_key = b"k" * 100
    assert hmac_sha256_by_hand(long_key, signed_payload) == \
        hmac.new(long_key, signed_payload, hashlib.sha256).digest()

    # Finally: verification is just doing all of the above again and comparing.
    # Use compare_digest even here - constant time, always (level 04).
    assert hmac.compare_digest(hmac_sha256_by_hand(secret, signed_payload).hex(), by_hand.hex())
    print("OK")


if __name__ == "__main__":
    main()
