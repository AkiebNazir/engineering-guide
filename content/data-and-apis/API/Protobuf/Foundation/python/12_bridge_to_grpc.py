"""
FOUNDATION LEVEL 12 - The bridge to gRPC (short, on purpose)
=============================================================
You have now learned the whole of protobuf as a data format. gRPC is a
different thing that USES it, and this level exists only to show you the
seam between them clearly, so you can walk into ../../../gRPC/Foundation
knowing exactly which half you already understand.

The seam is narrow. ../proto/l12_bridge.proto adds one construct you have not
seen - a `service` block - and nothing else:

    service EchoService {
      rpc Echo(EchoRequest) returns (EchoResponse);
    }

EchoRequest and EchoResponse are ordinary messages, identical in kind to
every message in levels 00-11. gRPC does not extend, wrap or subclass them.
It transports them.

You will learn
  * that gRPC request/response types are just the messages you already know
  * that the generated MESSAGE code contains no networking whatsoever, and
    that the `service` block adds nothing to it - a separate plugin handles that
  * the one wire detail gRPC adds: a 5-byte length prefix per message, which
    is level 09's framing problem solved once, properly
  * exactly what lives in ../../../gRPC/Foundation and is NOT re-taught here

Run it   python 12_bridge_to_grpc.py
"""
import struct

import l12_bridge_pb2 as pb

if __name__ == "__main__":
    print("== 1. the request and response are ordinary messages ==")
    request = pb.EchoRequest(text="hello, gRPC")
    response = pb.EchoResponse(text=request.text, length=len(request.text))
    print(f"  EchoRequest  -> {request.SerializeToString().hex()}")
    print(f"  EchoResponse -> {response.SerializeToString().hex()}")
    # Same API as level 00. Nothing here is gRPC-specific.
    round_tripped = pb.EchoRequest()
    round_tripped.ParseFromString(request.SerializeToString())
    assert round_tripped == request
    print("  built, encoded and decoded with the exact API from level 00.")

    print("\n== 2. the generated message code knows nothing about networking ==")
    # The `service` block in the .proto produced no message-level code at all.
    # Message codegen and service codegen are separate plugins:
    #   protoc --python_out     / protoc-gen-go        -> messages    (this folder)
    #   grpcio-tools --grpc_out / protoc-gen-go-grpc   -> service stubs (gRPC folder)
    names = sorted(n for n in dir(pb) if not n.startswith("_"))
    print(f"  l12_bridge_pb2 exports: {names}")
    assert "EchoRequest" in names and "EchoResponse" in names
    # No stub, no client, no server, no channel - because no gRPC plugin ran.
    for absent in ("EchoServiceStub", "EchoServiceServicer", "add_EchoServiceServicer_to_server"):
        assert not hasattr(pb, absent), f"{absent} would come from the gRPC plugin"
    print("  no stub, no servicer, no channel. The service block contributed")
    print("  nothing to this module - it is waiting for the gRPC plugin to read it.")

    print("\n== 3. the one wire detail gRPC adds ==")
    # Level 09 showed that protobuf messages are not self-delimiting and that
    # a stream of them needs framing. gRPC's answer is fixed and simple: every
    # message on the wire is preceded by 5 bytes.
    payload = request.SerializeToString()
    frame = struct.pack(">BI", 0, len(payload)) + payload
    #                     ^  ^
    #                     |  +-- 4-byte BIG-ENDIAN length
    #                     +----- 1 byte: 0 = not compressed, 1 = compressed
    print(f"  protobuf message : {len(payload)} bytes  {payload.hex()}")
    print(f"  gRPC frame       : {len(frame)} bytes  {frame.hex()}")
    print("                      ^^        ^^^^^^^^")
    print("                      |         +-- length 0x0000000d = 13, big-endian")
    print("                      +-- compression flag")

    # Unframing is the mirror image, and proves the payload is untouched.
    flag, size = struct.unpack(">BI", frame[:5])
    body = frame[5:5 + size]
    assert (flag, size) == (0, len(payload))
    assert body == payload, "gRPC carries the protobuf bytes verbatim"
    unframed = pb.EchoRequest()
    unframed.ParseFromString(body)
    assert unframed == request
    print("  the framed payload is byte-for-byte the protobuf message you encoded.")
    print("  gRPC then puts these frames in HTTP/2 DATA frames. That is the entire")
    print("  relationship: protobuf decides what a message IS, gRPC moves it.")

    print("\n== 4. what you already know, and what is next ==")
    print("  ALREADY YOURS (levels 00-11), unchanged inside gRPC:")
    print("    message definitions, field numbers, scalars, nested, repeated,")
    print("    presence/optional, enums, oneof, schema evolution, codegen, interop")
    print("  THE gRPC LAYER - see ../../../gRPC/Foundation, not re-taught here:")
    for item in ("unary, server-streaming, client-streaming and bidirectional RPCs",
                 "channels, stubs and generated server skeletons",
                 "status codes, error details and deadlines",
                 "interceptors (gRPC's middleware), metadata and auth",
                 "HTTP/2 multiplexing, keepalive and load balancing"):
        print(f"    - {item}")
    print("  Every one of those moves MESSAGES around. None of them changes what")
    print("  a message is. You already finished that part.")

    print("\nOK")
