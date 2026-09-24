"""
FOUNDATION LEVEL 01 - The .proto file IS the contract
=========================================================
Level 00 treated `ping.proto` as a magic incantation. This level treats it as
what it is: the single source of truth that both sides are generated from.
`../proto/contract.proto` is level 00's proto after exactly two edits - one new
FIELD on an existing message, one new RPC on the existing service - and this
file shows what each edit bought you.

THE WORKFLOW, AND IT IS NOT OPTIONAL
  1. edit the .proto
  2. run ../generate.sh  (protoc rewrites the generated modules)
  3. THEN write code against the new generated types
  Doing it in any other order means writing code that cannot compile yet. In
  REST you would just start sending a new JSON key and hope; here the contract
  moves first, on purpose. That is the entire trade: less freedom, no drift.

You will learn
  * field NUMBERS (`= 1`, `= 2`) are the wire identity, not field names - renaming
    a field is safe, renumbering or reusing a number is a breaking change
  * adding a field is backward compatible: an old client that never sets it sends
    nothing, and the server reads the proto3 zero value ("" / 0 / false)
  * adding an RPC is backward compatible too: old clients simply never call it
  * an empty request message (`message VersionRequest {}`) is normal and correct -
    every RPC takes exactly one message so the contract can grow later
  * `HasField` does not exist for plain proto3 scalars: "absent" and "zero" are
    the same thing on the wire, which is why `optional` exists when you need
    to tell them apart

Run it   python 01_the_proto_contract.py
"""
from concurrent import futures

import grpc

import contract_pb2 as pb
import contract_pb2_grpc as rpc

VERSION = "1.1.0"


class GreeterServicer(rpc.GreeterServicer):
    def Ping(self, request: pb.PingRequest, context: grpc.ServicerContext) -> pb.PongResponse:
        # `times` is the field EDIT #1 added. A client generated from the old
        # proto cannot set it, so we read 0 - and 0 has to mean "not specified".
        # This "zero means absent" ambiguity is the price of proto3 scalars.
        times = request.times if request.times > 0 else 1
        return pb.PongResponse(message=" ".join(["pong"] * times), count=times)

    def Version(self, request: pb.VersionRequest, context: grpc.ServicerContext) -> pb.VersionResponse:
        # `Version` is the RPC EDIT #2 added. Before regenerating, this method
        # name meant nothing to gRPC; after regenerating, the generated
        # GreeterServicer base class has a stub for it and gRPC routes to it.
        return pb.VersionResponse(version=VERSION)


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.GreeterStub(channel)

        # --- the old call, unchanged. Adding things did not break it. ---
        res = stub.Ping(pb.PingRequest(name="world"), timeout=2)
        print(f"Ping(name='world')            -> message={res.message!r} count={res.count}")
        assert (res.message, res.count) == ("pong", 1)

        # --- the same RPC, now using the field that edit #1 added ---
        res = stub.Ping(pb.PingRequest(name="world", times=3), timeout=2)
        print(f"Ping(name='world', times=3)   -> message={res.message!r} count={res.count}")
        assert (res.message, res.count) == ("pong pong pong", 3)

        # --- the RPC that edit #2 added ---
        res = stub.Version(pb.VersionRequest(), timeout=2)
        print(f"Version()                     -> version={res.version!r}")
        assert res.version == VERSION

    # --- what the contract itself says, read back out of the generated code ---
    # The descriptor is the .proto, parsed, carried inside the generated module.
    # This is why gRPC can never drift from its docs: the docs are the input.
    print("\nthe contract, read back out of the generated code:")
    for message in (pb.PingRequest, pb.PongResponse):
        fields = ", ".join(f"{f.name}={f.number}" for f in message.DESCRIPTOR.fields)
        print(f"  message {message.DESCRIPTOR.name:<14} fields: {fields}")
    methods = ", ".join(m.name for m in pb.DESCRIPTOR.services_by_name["Greeter"].methods)
    print(f"  service Greeter        rpcs:   {methods}")

    # Field numbers are the wire identity. Assert them, because changing one is
    # a silent, data-corrupting break that no compiler will catch for you.
    assert [f.number for f in pb.PingRequest.DESCRIPTOR.fields] == [1, 2]
    assert [m.name for m in pb.DESCRIPTOR.services_by_name["Greeter"].methods] == ["Ping", "Version"]

    # Proof of the proto3 rule above: an unset scalar is indistinguishable from
    # an explicit zero, because a zero-valued field is simply not written at all.
    assert pb.PingRequest(name="x").SerializeToString() == pb.PingRequest(name="x", times=0).SerializeToString()
    print("\nPingRequest(times unset) and PingRequest(times=0) serialise identically")
    print("  -> in proto3, 'absent' and 'zero' are the same bytes for a plain scalar")

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
