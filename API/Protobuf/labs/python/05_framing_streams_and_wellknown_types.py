"""
LAB 05 (advanced) - Message framing for files/sockets, and the well-known types
===============================================================================
You will learn
  * PROBLEM: a serialised protobuf has NO length or end marker. Two messages glued together are
    ambiguous - you cannot tell where one ends. Files, TCP, Kafka-style logs need FRAMING.
  * The standard fix: length-delimited records   [varint length][message bytes] [varint length][message] ...
    (the same shape gRPC, Java's writeDelimitedTo and Go's protodelim use)
  * reading from a stream that hands you data in arbitrary chunks (TCP reality) without losing sync
  * detecting truncation and corruption instead of crashing or returning garbage
  * merging messages: concatenating two serialisations of the SAME message type == merging them
  * the well-known types: Timestamp, Duration, Any (payload of any type), FieldMask (partial updates)

    file:  | len=16 | User#1 (16 bytes) | len=20 | User#2 (20 bytes) | ...

Needs   pip install protobuf     (generated code: demo_pb2.py, made by ../generate.sh)
Run it  python 05_framing_streams_and_wellknown_types.py
"""
import io
import os
import tempfile
from datetime import datetime, timedelta, timezone

from google.protobuf import any_pb2, duration_pb2, field_mask_pb2
from google.protobuf.internal import decoder, encoder
from google.protobuf.message import DecodeError
from google.protobuf.timestamp_pb2 import Timestamp

import demo_pb2 as pb


# ----------------------------------------------------------------- framing --
# NOTE: Python's protobuf package has no PUBLIC delimited API, so we use two small internal helpers
# (encoder._VarintBytes / decoder._DecodeVarint32). Go (protodelim) and Java (writeDelimitedTo) do.
def write_delimited(out, msg) -> int:
    body = msg.SerializeToString()
    header = encoder._VarintBytes(len(body))
    out.write(header + body)
    return len(header) + len(body)


class DelimitedReader:
    """Incremental reader: feed() arbitrary chunks, iterate complete messages."""

    def __init__(self, msg_type, max_size: int = 1 << 20):
        self.msg_type, self.max_size, self.buf = msg_type, max_size, b""

    def feed(self, chunk: bytes):
        self.buf += chunk
        while self.buf:
            try:
                size, pos = decoder._DecodeVarint32(self.buf, 0)
            except (IndexError, DecodeError):
                return                                   # length prefix itself is incomplete: wait for more bytes
            if size > self.max_size:
                raise DecodeError(f"frame of {size} bytes exceeds limit {self.max_size} - corrupt stream or attack")
            if len(self.buf) < pos + size:
                return                                   # message body incomplete: wait for more bytes
            msg = self.msg_type.FromString(self.buf[pos:pos + size])
            self.buf = self.buf[pos + size:]
            yield msg


if __name__ == "__main__":
    users = [pb.User(id=i, name=f"user-{i}", tags=["t"] * (i % 3)) for i in range(1, 6)]

    print("== 1. WHY framing: glued messages are ambiguous ==")
    glued = b"".join(u.SerializeToString() for u in users[:2])
    parsed = pb.User.FromString(glued)          # protobuf 'merges' concatenated messages (see section 4)
    print("  parsing 2 concatenated users gives ONE user:", parsed.id, parsed.name, "(the second overwrote the first)")
    assert parsed.id == 2

    print("\n== 2. length-delimited file ==")
    path = os.path.join(tempfile.mkdtemp(), "users.pbstream")
    with open(path, "wb") as f:
        sizes = [write_delimited(f, u) for u in users]
    print("  wrote", len(users), "records, bytes each:", sizes, "-> file size", os.path.getsize(path))
    with open(path, "rb") as f:
        back = list(DelimitedReader(pb.User).feed(f.read()))
    assert back == users
    print("  read back:", [u.name for u in back])

    print("\n== 3. a TCP-like stream: data arrives in awkward chunks ==")
    blob = open(path, "rb").read()
    reader, got = DelimitedReader(pb.User), []
    for i in range(0, len(blob), 7):                 # 7-byte chunks split lengths AND bodies mid-way
        got += list(reader.feed(blob[i:i + 7]))
    print("  fed in 7-byte chunks ->", [u.id for u in got])
    assert got == users and reader.buf == b""

    print("\n== 4. truncation and corruption are DETECTED ==")
    r = DelimitedReader(pb.User)
    out = list(r.feed(blob[:-3]))                    # cut the last record short
    print(f"  truncated file: {len(out)} complete records delivered, {len(r.buf)} dangling bytes -> caller decides (retry / error)")
    assert len(out) == 4 and r.buf
    try:
        list(DelimitedReader(pb.User, max_size=100).feed(b"\xff\xff\xff\x7f" + b"x" * 10))
    except DecodeError as e:
        print("  absurd length prefix rejected:", str(e)[:60], "...")
    else:
        raise AssertionError("must refuse huge frames (memory exhaustion attack)")

    print("\n== 5. concatenation == merge (a feature, when you know about it) ==")
    base = pb.User(id=1, name="Ana", tags=["a"]).SerializeToString()
    patch = pb.User(name="Ana Maria", tags=["b"]).SerializeToString()
    merged = pb.User.FromString(base + patch)
    print("  base + patch ->", merged.id, merged.name, list(merged.tags), "(scalars: last wins; repeated: appended)")
    assert (merged.id, merged.name, list(merged.tags)) == (1, "Ana Maria", ["a", "b"])

    print("\n== 6. Timestamp / Duration ==")
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 9, 21, 10, 30, tzinfo=timezone.utc))
    print("  Timestamp:", ts.ToJsonString(), f"(seconds={ts.seconds}, nanos={ts.nanos}) -> {ts.ToDatetime(tzinfo=timezone.utc).isoformat()}")
    dur = duration_pb2.Duration()
    dur.FromTimedelta(timedelta(minutes=5, milliseconds=250))
    print("  Duration :", dur.ToJsonString(), f"(seconds={dur.seconds}, nanos={dur.nanos})")
    assert ts.ToJsonString() == "2026-09-21T10:30:00Z" and dur.ToJsonString() == "300.250s"

    print("\n== 7. Any: carry a message whose type you do not know at compile time ==")
    event = pb.Event(id="evt-1", ttl=dur)
    event.payload.Pack(pb.User(id=42, name="Zed"))
    print("  type_url:", event.payload.type_url)
    wire = event.SerializeToString()
    received = pb.Event.FromString(wire)
    if received.payload.Is(pb.User.DESCRIPTOR):
        inner = pb.User()
        received.payload.Unpack(inner)
        print("  unpacked:", inner.id, inner.name)
        assert inner.name == "Zed"
    assert not received.payload.Is(pb.Address.DESCRIPTOR)

    print("\n== 8. FieldMask: partial updates without null-vs-unset confusion ==")
    stored = pb.User(id=1, name="Ana", email="ana@old.io", role=pb.ROLE_USER)
    patch_msg = pb.UserPatch(user=pb.User(name="Ana M.", email=""),                 # email="" is a REAL value here
                             update_mask=field_mask_pb2.FieldMask(paths=["name", "email"]))
    for path_ in patch_msg.update_mask.paths:
        setattr(stored, path_, getattr(patch_msg.user, path_))                      # only masked fields are touched
    print("  mask", list(patch_msg.update_mask.paths), "->", stored.name, "|", repr(stored.email), "| role untouched:", pb.Role.Name(stored.role))
    assert stored.name == "Ana M." and stored.email == "" and stored.role == pb.ROLE_USER
    print("  (without the mask, the server cannot tell 'clear my email' from 'I did not send email')")
    print("\nOK")
