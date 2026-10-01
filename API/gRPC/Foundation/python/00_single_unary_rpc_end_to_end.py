"""
FOUNDATION LEVEL 00 (start here) - A basic gRPC endpoint, explained end to end
==================================================================================
If someone says "build me a basic gRPC endpoint", THIS is what they mean: one
`.proto` file describing one function, generated code, a server that implements
that function, and a client that calls it. Nothing about streaming, metadata, or
interceptors yet - just enough to see the whole call happen once.

THE MENTAL MODEL (read this before the code)
  gRPC is REST's request/response idea with ONE big swap. In REST you agree on a
  convention - "GET /ping returns text, POST /orders takes this JSON shape" - and
  both sides hand-write code that hopes the other side kept the bargain. In gRPC
  you write that agreement down in a machine-readable file (`../proto/ping.proto`)
  and a compiler (`protoc`) GENERATES the client and server types from it. So:

    REST                              gRPC
    ------------------------------    ------------------------------------------
    URL + verb picks the operation    the method name picks it: /Greeter/Ping
    JSON body, parsed at runtime      protobuf bytes, typed at compile time
    docs/OpenAPI describe the shape   the .proto file IS the shape, enforced
    HTTP/1.1 text, one req per conn   HTTP/2 binary, many calls multiplexed
    404/400/500                       status codes: NOT_FOUND/INVALID_ARGUMENT...

  What is IDENTICAL: a server listens on a port; a client opens a connection,
  sends one message, gets one message back. Everything in levels 01-12 is one
  more piece bolted onto that loop.

You will learn
  * the four-step gRPC recipe: write .proto -> run the generator -> implement the
    Servicer -> call the Stub (there is no step where you parse anything by hand)
  * what the generated `ping_pb2` / `ping_pb2_grpc` modules actually give you:
    message classes, a `GreeterServicer` base class, and a `GreeterStub` client
  * that a unary RPC reads exactly like a local function call - `stub.Ping(req)` -
    even though a real network round trip happens inside it
  * what a CHANNEL is: one long-lived HTTP/2 connection you create once and reuse
  * that calling an RPC the server never implemented is a normal, handled outcome
    (status UNIMPLEMENTED), not a crash - gRPC's equivalent of REST's 404

Run it        python 00_single_unary_rpc_end_to_end.py
Keep serving  python 00_single_unary_rpc_end_to_end.py --serve   (listens on 127.0.0.1:50051)
"""
import sys
from concurrent import futures

import grpc

# These two modules are GENERATED - you never edit them. `../generate.sh` made
# them from ../proto/ping.proto. Level 13 shows what is inside them.
#   ping_pb2      -> the message classes (PingRequest, PongResponse)
#   ping_pb2_grpc -> the service plumbing (GreeterServicer, GreeterStub)
import ping_pb2 as pb
import ping_pb2_grpc as rpc


class GreeterServicer(rpc.GreeterServicer):
    """THE SERVER. Subclassing the generated GreeterServicer is how you promise
    "I implement the Greeter service". One method per `rpc` line in the .proto,
    named exactly as the .proto named it."""

    def Ping(self, request: pb.PingRequest, context: grpc.ServicerContext) -> pb.PongResponse:
        # `request` is already a fully parsed, typed PingRequest object. gRPC read
        # the bytes off the socket and decoded them for you before calling this -
        # there is no "parse the body" step, and no way to get a field name wrong
        # without the error showing up right here in your own code.
        print(f"  [server] Ping arrived with name={request.name!r}")

        # `context` is the per-call handle: deadlines, metadata (level 07),
        # and status codes (level 06) all live on it. Unused at this level.
        return pb.PongResponse(message=f"pong, {request.name}")


def start_server(port: int = 0) -> tuple[grpc.Server, int]:
    # A gRPC server is a thread pool plus a registry of services. Handlers run
    # concurrently on that pool, so one slow call does not block the others.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    # The generated `add_..._to_server` helper is what wires the method name
    # "/foundation.ping.v1.Greeter/Ping" to our Python method above.
    rpc.add_GreeterServicer_to_server(GreeterServicer(), server)

    # port 0 = "operating system, hand me any free port", so this demo never
    # collides with something already listening on your machine.
    bound = server.add_insecure_port(f"127.0.0.1:{port}")  # insecure = plaintext; use TLS in production
    server.start()
    return server, bound


def demo(port: int) -> None:
    # THE CLIENT. A channel is a managed HTTP/2 connection to one target. Create
    # it ONCE and reuse it for every call - it is not per-request like a socket.
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.GreeterStub(channel)  # the generated typed client

        # This one line is the whole request/response loop: serialise the
        # request, send HEADERS + DATA over HTTP/2, wait, read DATA + TRAILERS,
        # deserialise the response. It looks like a function call on purpose.
        response = stub.Ping(pb.PingRequest(name="world"), timeout=2)  # ALWAYS pass a timeout

        print(f"request  : /foundation.ping.v1.Greeter/Ping  name='world'")
        print(f"response : message={response.message!r}")
        assert response.message == "pong, world"

        # Ask for a method this server does not implement. gRPC answers with the
        # status UNIMPLEMENTED - the direct analogue of REST's 404, and just as
        # normal an outcome. We fake it by calling a made-up path by hand.
        unknown = channel.unary_unary(
            "/foundation.ping.v1.Greeter/DoesNotExist",
            request_serializer=pb.PingRequest.SerializeToString,
            response_deserializer=pb.PongResponse.FromString,
        )
        try:
            unknown(pb.PingRequest(name="world"), timeout=2)
            raise AssertionError("expected UNIMPLEMENTED, got a success instead")
        except grpc.RpcError as e:
            print(f"request  : /foundation.ping.v1.Greeter/DoesNotExist")
            print(f"response : {e.code().name}   (a method this server never agreed to answer - not a crash)")
            assert e.code() == grpc.StatusCode.UNIMPLEMENTED

    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        server, port = start_server(50051)
        print(f"listening on 127.0.0.1:{port}  (gRPC is binary - curl will not help; use grpcurl or level 00's client)")
        server.wait_for_termination()

    server, port = start_server()
    demo(port)
    server.stop(0).wait()
