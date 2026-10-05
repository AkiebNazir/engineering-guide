"""
LAB 04 (advanced) - Measuring Protobuf against JSON (do not trust claims, measure)
==================================================================================
You will learn
  * how to benchmark serialisation honestly: same data, many iterations, best-of-N, warm-up
  * SIZE: raw, and after gzip (gzip narrows the gap a lot - know this before claiming "10x smaller")
  * SPEED: encode, decode, and decode-then-touch-one-field
  * WHEN Protobuf wins big and when it barely matters:
        - many small numeric fields / repeated numbers  -> big win (varints, packing, no field names)
        - one long text field                            -> almost no win (text is text)
  * the hidden cost of JSON: int64 -> string, bytes -> base64 (+33%), floats as text

Needs   pip install protobuf     (generated code: demo_pb2.py, made by ../generate.sh)
Run it  python 04_size_speed_vs_json.py      (takes a few seconds)
"""
import base64
import gzip
import json
import random
import time

import demo_pb2 as pb

random.seed(7)


def make_users(n: int, long_text: bool = False) -> list[pb.User]:
    users = []
    for i in range(n):
        u = pb.User(id=1_000_000 + i, name=f"user-{i}", email=f"user{i}@example.com", role=pb.ROLE_USER,
                    tags=["alpha", "beta"], active=bool(i % 2), rating=random.random() * 5,
                    scores=[random.randint(0, 100) for _ in range(20)],
                    avatar=random.randbytes(64))
        u.address.city, u.address.zip = "Oslo", "0150"
        if long_text:
            u.attrs["bio"] = " ".join(random.choice(["lorem", "ipsum", "dolor", "sit", "amet"]) for _ in range(400))
        users.append(u)
    return users


def to_json_dict(u: pb.User) -> dict:
    """What a typical REST/JSON API would send for the same user."""
    return {"id": u.id, "name": u.name, "email": u.email, "role": pb.Role.Name(u.role), "tags": list(u.tags),
            "active": u.active, "rating": u.rating, "scores": list(u.scores),
            "avatar": base64.b64encode(u.avatar).decode(),                   # JSON cannot carry raw bytes
            "address": {"city": u.address.city, "zip": u.address.zip},
            "attrs": dict(u.attrs)}


def best_of(fn, repeat=5) -> float:
    fn()                                                                     # warm-up
    times = []
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return min(times)


def compare(title: str, users: list[pb.User]):
    dicts = [to_json_dict(u) for u in users]
    proto_blobs = [u.SerializeToString() for u in users]
    json_blobs = [json.dumps(d).encode() for d in dicts]

    p_raw, j_raw = sum(map(len, proto_blobs)), sum(map(len, json_blobs))
    p_gz, j_gz = len(gzip.compress(b"".join(proto_blobs))), len(gzip.compress(b"".join(json_blobs)))

    enc_p = best_of(lambda: [u.SerializeToString() for u in users])
    enc_j = best_of(lambda: [json.dumps(d) for d in dicts])
    dec_p = best_of(lambda: [pb.User.FromString(b) for b in proto_blobs])
    dec_j = best_of(lambda: [json.loads(b) for b in json_blobs])

    print(f"\n### {title}  ({len(users)} users)")
    print(f"  {'':<22}{'JSON':>12}{'Protobuf':>12}{'ratio':>9}")
    print(f"  {'size (bytes/user)':<22}{j_raw / len(users):>12,.0f}{p_raw / len(users):>12,.0f}{j_raw / p_raw:>8.1f}x")
    print(f"  {'size after gzip':<22}{j_gz / len(users):>12,.0f}{p_gz / len(users):>12,.0f}{j_gz / p_gz:>8.1f}x")
    print(f"  {'encode (ms)':<22}{enc_j * 1000:>12.1f}{enc_p * 1000:>12.1f}{enc_j / enc_p:>8.1f}x")
    print(f"  {'decode (ms)':<22}{dec_j * 1000:>12.1f}{dec_p * 1000:>12.1f}{dec_j / dec_p:>8.1f}x")
    return j_raw / p_raw, j_gz / p_gz


if __name__ == "__main__":
    print("Note: the Python protobuf package uses a C/upb backend; a pure-Python fallback would be far slower.")
    from google.protobuf.internal import api_implementation
    print("protobuf backend:", api_implementation.Type())

    raw1, gz1 = compare("structured data: many small numbers and short strings", make_users(2000))
    raw2, gz2 = compare("text-heavy data: one 400-word field per user", make_users(300, long_text=True))

    print("\nWhat to conclude")
    print(f"  * structured data : {raw1:.1f}x smaller raw, but only {gz1:.1f}x after gzip")
    print(f"  * text-heavy data : {raw2:.1f}x raw, {gz2:.1f}x after gzip - text dominates, the format barely matters")
    print("  * speed: the C-backed protobuf codec is many times faster than json here, and the ratio holds even for text.")
    print("    Treat exact ratios as rough: results move with backend, message shape and machine (run it twice).")
    print("  * the real win is often the CONTRACT (typed schema, safe evolution), not the bytes.")
    assert raw1 > 1.5, "protobuf should be clearly smaller on structured data"
    assert raw1 > raw2, "the advantage shrinks when the payload is mostly text"
    assert gz1 < raw1, "gzip narrows the gap"
    print("\nOK")
