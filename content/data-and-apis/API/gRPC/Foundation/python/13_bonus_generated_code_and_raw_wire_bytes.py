"""
FOUNDATION BONUS - What protoc actually generated (optional, read after level 00)
=====================================================================================
Level 00 ran `../generate.sh`, imported `ping_pb2`, and never asked what was in
it. This file answers that in two steps: first what the generator PRODUCED for
`PingRequest`, then what that produces ON THE WIRE - decoded by hand, with no
protobuf library involved at all.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is protoc actually doing for me?" once you are curious.

WHERE THE FULL WALKTHROUGH LIVES
  This is the SAME exercise as `../../Protobuf/Foundation`'s own bonus level.
  That folder is about the message/wire format as its whole subject - varints,
  ZigZag, wire types, length-delimited fields, packed repeated fields, unknown
  field preservation - and it walks the bytes properly. Go there for the full
  byte-by-byte treatment. This file stays shallow on purpose: just enough to
  prove the bytes are not magic, in the context of the RPC you already ran.
  Everything ELSE in this Foundation folder is about the RPC layer - services,
  interceptors, streaming, status codes - which protobuf itself knows nothing
  about.

You will learn
  * a generated Python message class is thin: the real work is a DESCRIPTOR
    built from a serialized copy of the .proto, plus a C++ implementation
  * what a generated service stub contains: one multi-callable per RPC, keyed by
    the full method path, with a serializer and deserializer bolted on
  * the whole protobuf encoding rule for a string field, in one line:
    tag byte = (field_number << 3) | wire_type, then a length, then the bytes
  * why the encoding is so small: field NAMES are never transmitted, only numbers
  * that gRPC frames each message with 1 compression byte + 4 length bytes
    before handing it to HTTP/2

Run it   python 13_bonus_generated_code_and_raw_wire_bytes.py
"""
import ping_pb2 as pb
import ping_pb2_grpc as rpc

# ---------------------------------------------------------------------------
# PART 1 - what the generator produced for level 00's PingRequest
# ---------------------------------------------------------------------------
print("PART 1: the generated class")
print("=" * 60)

# In Python, `class PingRequest` is generated but almost empty. All the real
# information lives in a DESCRIPTOR, which protoc built by embedding a
# serialized copy of ping.proto into ping_pb2.py as a byte string.
descriptor = pb.PingRequest.DESCRIPTOR
print(f"class            : {pb.PingRequest.__module__}.{pb.PingRequest.__name__}")
print(f"full proto name  : {descriptor.full_name}")
print(f"defined in       : {descriptor.file.name}  (package {descriptor.file.package})")
print(f"fields           :")
for field in descriptor.fields:
    # field.type is the protobuf type enum; 9 == TYPE_STRING. The descriptor is
    # the .proto, parsed - nothing here was hand-written by protoc as Python.
    print(f"  {field.name!r:<10} number={field.number} type={field.type} "
          f"(TYPE_STRING={field.TYPE_STRING}) default={field.default_value!r}")

assert descriptor.full_name == "foundation.ping.v1.PingRequest"
assert [f.name for f in descriptor.fields] == ["name"]
assert descriptor.fields[0].number == 1

# The equivalent in Go is a real struct with real tags, which is why the Go
# version of this file can print the struct definition directly:
print("""
what protoc-gen-go emitted for the same message (see ../golang/pb/pingpb/ping.pb.go):

    type PingRequest struct {
        state         protoimpl.MessageState
        sizeCache     protoimpl.SizeCache
        unknownFields protoimpl.UnknownFields

        Name string `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
    }                            ^^^^^ ^                       ^^^^ the wire rules,
                                 wire  field number            as a struct tag
""")

# And the SERVICE half: the stub is a thin dictionary of callables, one per RPC,
# each carrying the full wire path and the two functions that convert
# messages <-> bytes. There is no cleverness here at all.
print("the generated GreeterStub, taken apart:")


class _FakeChannel:
    """Stands in for a real channel so we can see what the stub asks it for."""

    def unary_unary(self, method, request_serializer=None, response_deserializer=None, **kwargs):
        print(f"  method path          : {method}")
        print(f"  request_serializer   : {request_serializer.__qualname__}")
        print(f"  response_deserializer: {response_deserializer.__qualname__}")
        return "<multicallable>"


stub = rpc.GreeterStub(_FakeChannel())
assert stub.Ping == "<multicallable>"

# ---------------------------------------------------------------------------
# PART 2 - the bytes, decoded by hand
# ---------------------------------------------------------------------------
print("\nPART 2: decoding PingRequest(name='world') with no protobuf library")
print("=" * 60)

message = pb.PingRequest(name="world")
raw = message.SerializeToString()
print(f"SerializeToString() -> {raw!r}   ({len(raw)} bytes)")
assert raw == b"\x0a\x05world"


def decode_by_hand(data: bytes) -> dict[int, bytes]:
    """A deliberately tiny protobuf reader. Handles exactly the two wire types
    this message needs. `../../Protobuf/Foundation` does this properly."""
    fields: dict[int, bytes] = {}
    i = 0
    while i < len(data):
        # 1. The TAG is a varint packing two things together:
        #       field_number = tag >> 3
        #       wire_type    = tag & 0b111
        tag = data[i]
        i += 1
        field_number, wire_type = tag >> 3, tag & 0b111
        print(f"  byte 0x{tag:02x} = 0b{tag:08b} -> field_number={field_number} wire_type={wire_type}")

        if wire_type == 2:  # 2 = length-delimited: string, bytes, or a nested message
            length = data[i]  # a varint too; single byte for anything under 128
            i += 1
            value = data[i:i + length]
            i += length
            print(f"    length-delimited, {length} bytes -> {value!r}")
            fields[field_number] = value
        elif wire_type == 0:  # 0 = varint: int32/int64/bool/enum
            shift, value = 0, 0
            while True:
                byte = data[i]
                i += 1
                value |= (byte & 0x7F) << shift  # 7 payload bits per byte...
                if not byte & 0x80:              # ...top bit means "one more byte follows"
                    break
                shift += 7
            print(f"    varint -> {value}")
            fields[field_number] = value
        else:
            raise NotImplementedError(f"wire type {wire_type} - see ../../Protobuf/Foundation")
    return fields


decoded = decode_by_hand(raw)
print(f"\nby hand : field 1 = {decoded[1]!r}  ->  {decoded[1].decode()!r}")
print(f"protobuf: name    = {message.name!r}")
assert decoded[1].decode() == message.name == "world"

# THE POINT: the string "name" appears nowhere in those 7 bytes. Only the NUMBER
# 1 does. That is why renaming a field is free and renumbering one is fatal
# (level 01), and it is most of why protobuf is so much smaller than JSON.
json_equivalent = b'{"name":"world"}'
print(f"\nprotobuf: {len(raw)} bytes  {raw!r}")
print(f"JSON    : {len(json_equivalent)} bytes {json_equivalent!r}")
print("  the field NAME is never transmitted - only field number 1")
assert len(raw) < len(json_equivalent)

# One more layer: gRPC does not put those 7 bytes straight onto HTTP/2. It
# prefixes every message with a 5-byte frame header so the receiver knows where
# each message ends within the stream (essential for levels 03-05, where many
# messages share one call).
framed = bytes([0]) + len(raw).to_bytes(4, "big") + raw
print(f"\non the wire, gRPC frames it: {framed!r}")
print(f"  byte 0      = 0    -> not compressed")
print(f"  bytes 1-4   = {len(raw)}    -> message length, big-endian uint32")
print(f"  bytes 5-{4 + len(raw)}   -> the {len(raw)} protobuf bytes decoded above")
assert len(framed) == 5 + len(raw)

print("\nfor varints, ZigZag, packed repeated fields, nested messages and")
print("unknown-field preservation, read ../../Protobuf/Foundation - that folder")
print("is the wire format's full walkthrough, and this was only its first page.")
print("\nOK")
