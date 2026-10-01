"""
FOUNDATION LEVEL 09 - Using generated code in a real program
=============================================================
Every level so far encoded and decoded in the same breath, in one process,
which is not what protobuf is for. This level is the smallest HONEST example:
two separate programs, started separately, sharing nothing but a file on disk
and ../proto/l09_batch.proto.

Deliberately there is NO gRPC, no service, no network. Protobuf is a
serialization format; the transport is your choice. A file is a transport,
and it is the one that makes the separation impossible to fake - the writer
has already exited by the time the reader starts.

The one genuinely new problem: protobuf messages are NOT self-delimiting.
An encoded message does not record its own length, and the parser reads until
the bytes run out. That is fine for ONE message in a file, but if you
concatenate two, they silently merge into one corrupt value. The fix is
length-prefix framing, which this level implements in six lines and which is
exactly what gRPC does for you on the wire.

You will learn
  * the real shape of a protobuf program: build -> SerializeToString -> write bytes
  * that the reader needs only the same .proto, not the same language or process
  * WHY a stream of messages needs framing, demonstrated by letting it corrupt
  * length-prefix framing: write varint length, then the message, repeat
  * always open these files in BINARY mode ("wb"/"rb") - this is not text
  * that a schema-version field in the payload is cheap and saves you later

Run it   python 09_generated_code_in_a_real_program.py
Or as two real programs, by hand:
         python 09_generated_code_in_a_real_program.py --write /tmp/batches.pb
         python 09_generated_code_in_a_real_program.py --read  /tmp/batches.pb
"""
import os
import subprocess
import sys
import tempfile

import l09_batch_pb2 as pb


# Framing needs a length prefix, and protobuf's own varint is the natural
# choice: small lengths cost one byte. These two helpers are the entire
# mechanism, written out rather than imported so nothing is hidden. Level 13
# explains the seven-bits-plus-continuation-bit trick in detail.
def put_varint(value: int) -> bytes:
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)   # low 7 bits, continuation bit set
        value >>= 7
    out.append(value)                       # final byte, continuation bit clear
    return bytes(out)


def get_varint(blob: bytes, position: int) -> tuple[int, int]:
    value, shift = 0, 0
    while True:
        byte = blob[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:                 # continuation bit clear -> last byte
            return value, position
        shift += 7

# The three batches program A writes and program B expects to read back.
BATCHES = [
    ("sensor-a", [(1700000000000, 21.5), (1700000060000, 21.7)]),
    ("sensor-b", [(1700000000000, 48.0)]),
    ("sensor-c", [(1700000000000, -3.25), (1700000060000, -3.5), (1700000120000, -3.75)]),
]


def write_batches(path: str) -> None:
    """PROGRAM A: build messages and write them to a file. Exits when done."""
    with open(path, "wb") as out:      # "wb" - BINARY. Text mode would corrupt this.
        for device_id, samples in BATCHES:
            batch = pb.SensorBatch(device_id=device_id)
            for unix_millis, value in samples:
                batch.samples.add(unix_millis=unix_millis, value=value)

            payload = batch.SerializeToString()
            # FRAMING: write the length as a varint, then the payload. The
            # reader can now tell where each message stops. Without this the
            # three messages below would merge into one on the way back in.
            out.write(put_varint(len(payload)))
            out.write(payload)
    print(f"  program A wrote {len(BATCHES)} batches -> {path} ({os.path.getsize(path)} bytes)")


def read_batches(path: str) -> list[pb.SensorBatch]:
    """PROGRAM B: read the file back. Knows only the .proto, not program A."""
    with open(path, "rb") as handle:
        blob = handle.read()

    out, position = [], 0
    while position < len(blob):
        size, position = get_varint(blob, position)
        batch = pb.SensorBatch()
        batch.ParseFromString(blob[position:position + size])
        position += size
        out.append(batch)
    return out


def demo() -> None:
    # A temp directory, so the two programs share nothing but this one path.
    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, "batches.pb")
        me = os.path.abspath(__file__)

        print("== 1. two genuinely separate processes ==")
        # Not a function call - a real subprocess. Program A runs to completion
        # and exits before program B is even started.
        wrote = subprocess.run([sys.executable, me, "--write", path],
                               check=True, capture_output=True, text=True)
        print(wrote.stdout.rstrip())
        read = subprocess.run([sys.executable, me, "--read", path],
                              check=True, capture_output=True, text=True)
        print(read.stdout.rstrip())
        assert "sensor-c" in read.stdout

        print("\n== 2. the reader reconstructed exactly what the writer built ==")
        batches = read_batches(path)
        assert len(batches) == len(BATCHES), "framing must recover every message"
        for batch, (device_id, samples) in zip(batches, BATCHES):
            assert batch.device_id == device_id
            assert [(s.unix_millis, s.value) for s in batch.samples] == samples
            print(f"  {batch.device_id}: {len(batch.samples)} samples, "
                  f"values {[s.value for s in batch.samples]}")
        print("  every field, in every message, in order. Nothing was lost or guessed.")

        print("\n== 3. WHY the framing was necessary ==")
        # Concatenate two messages with no length prefixes and read them back
        # as one. This does not raise - which is what makes it dangerous.
        one = pb.SensorBatch(device_id="first")
        one.samples.add(unix_millis=1, value=1.0)
        two = pb.SensorBatch(device_id="second")
        two.samples.add(unix_millis=2, value=2.0)
        glued = one.SerializeToString() + two.SerializeToString()

        merged = pb.SensorBatch()
        merged.ParseFromString(glued)     # no error!
        print(f"  wrote 'first' then 'second' with no length prefixes ({len(glued)} bytes)")
        print(f"  parsed back as ONE message: device_id={merged.device_id!r}, "
              f"{len(merged.samples)} samples")
        # The documented merge rules bite here: the last `device_id` wins
        # (it is a scalar) and the repeated `samples` are APPENDED together.
        assert merged.device_id == "second", "last scalar wins"
        assert len(merged.samples) == 2, "repeated fields concatenate"
        print("  the two messages MERGED: the second device_id overwrote the first,")
        print("  and both sample lists were appended into one. No exception, no")
        print("  warning, just a plausible-looking wrong answer.")
        print("  => a protobuf message does not know its own length. If you put")
        print("     more than one in a file, a socket or a log, YOU must frame them.")
        print("     (This is precisely the job gRPC's 5-byte prefix does - level 12.)")

        print("\n== 4. what this looks like in production ==")
        print("  The pattern above is the whole idea behind:")
        print("    - protobuf records in Kafka / Pub/Sub / SQS message bodies")
        print("    - a `bytes` column in Postgres or a value in Redis")
        print("    - on-disk formats and write-ahead logs")
        print("    - gRPC request/response bodies (level 12)")
        print("  In every one of them the code is the same two lines you saw:")
        print("    bytes_out = msg.SerializeToString()   /   msg.ParseFromString(bytes_in)")
        print("  Two cautions worth internalising now:")
        print("    * open files in binary mode; there is no text encoding here")
        print("    * ParseFromString on untrusted bytes can raise - catch")
        print("      DecodeError rather than letting it kill the process")

        # Show that last point rather than just asserting it.
        from google.protobuf.message import DecodeError
        try:
            pb.SensorBatch().ParseFromString(b"\xff\xff\xff\xff\xff")
            raise AssertionError("expected garbage to be rejected")
        except DecodeError as exc:
            print(f"  garbage in -> DecodeError: {str(exc)[:48]}... (an error, never a crash)")

    print("\nOK")


if __name__ == "__main__":
    # The two "program" entry points, so you can run them separately by hand.
    if "--write" in sys.argv:
        write_batches(sys.argv[sys.argv.index("--write") + 1])
        raise SystemExit(0)
    if "--read" in sys.argv:
        target = sys.argv[sys.argv.index("--read") + 1]
        for item in read_batches(target):
            print(f"  program B read {item.device_id} with {len(item.samples)} samples")
        raise SystemExit(0)
    demo()
