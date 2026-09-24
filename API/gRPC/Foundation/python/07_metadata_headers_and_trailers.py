"""
FOUNDATION LEVEL 07 - Metadata: gRPC's headers
==================================================
Everything so far travelled inside the protobuf messages, which are governed by
the .proto contract. METADATA is the other channel: untyped key/value string
pairs that ride ALONGSIDE the messages, in both directions. It is literally
HTTP/2 headers, and it is exactly what HTTP headers are for in REST.

WHAT GOES IN METADATA, AND WHAT DOES NOT
  metadata (cross-cutting, about the CALL)   messages (the DATA of the call)
  ----------------------------------------   -------------------------------
  authorization / api keys (levels 09-10)    the order being placed
  x-request-id for tracing                   the user's name
  user-agent, accept-encoding                the search filters
  grpc-timeout (set for you by `timeout=`)   anything a client legitimately
  the grpc-status trailer itself               needs to see in the contract

  Rule of thumb: if changing it would change the ANSWER, it is a message field.
  If it is about plumbing - who, when, trace, retry - it is metadata. Notice
  ../proto/metaecho.proto has no request_id field anywhere.

THREE PLACES METADATA APPEARS (this is the bit people miss)
  1. REQUEST metadata  - client -> server, sent before the request message
  2. INITIAL metadata  - server -> client, sent BEFORE the response message
  3. TRAILING metadata - server -> client, sent AFTER it, with the status

  Trailers are the interesting one: HTTP/1.1 cannot really do them, so REST has
  no equivalent. They let a server report something it only learns at the END of
  a call - rows scanned, cache hit, time spent - even mid-stream.

You will learn
  * metadata keys are always lower-cased, and a key may legally repeat
  * values are strings; a `-bin` suffixed key carries raw bytes instead
  * `stub.Method.with_call(...)` is how blocking Python gets at the call object
    and therefore at the initial/trailing metadata
  * `context.invocation_metadata()`, `send_initial_metadata()` and
    `set_trailing_metadata()` are the three server-side halves
  * never put a secret in metadata over an insecure channel - it is plaintext
    (this is exactly why levels 09-10 say "use TLS in production")

Run it   python 07_metadata_headers_and_trailers.py
"""
import time
from concurrent import futures

import grpc

import metaecho_pb2 as pb
import metaecho_pb2_grpc as rpc


class MetaEchoServicer(rpc.MetaEchoServicer):
    def Echo(self, request: pb.EchoRequest, context: grpc.ServicerContext) -> pb.EchoResponse:
        # 1. READ request metadata. It is a tuple of (key, value) pairs, because
        #    a key may repeat - dict() keeps only the last of any duplicates.
        incoming = context.invocation_metadata()
        print("  [server] request metadata the client sent:")
        for key, value in incoming:
            print(f"             {key} = {value!r}")

        md = dict(incoming)
        request_id = md.get("x-request-id", "none")

        # gRPC itself adds metadata you never set. `grpc-timeout` is how the
        # client's `timeout=` reaches the server, so the server knows the
        # deadline too and can give up at the same moment (level 12).
        assert "user-agent" in md

        # 2. SEND initial metadata - goes out BEFORE the response message. Once
        #    sent it cannot be changed, so this is for things known up front.
        context.send_initial_metadata((("x-served-by", "metaecho-1"),))

        started = time.perf_counter()
        text = request.text.upper()
        elapsed_us = int((time.perf_counter() - started) * 1_000_000)

        # 3. SET trailing metadata - goes out AFTER the response, with the
        #    status. This is why it can carry something only knowable at the end.
        tenants = [v for k, v in incoming if k == "x-tenant"]  # a key may repeat
        context.set_trailing_metadata((
            ("x-request-id", request_id),                 # echo the caller's trace id back
            ("x-handler-micros", str(elapsed_us)),        # not knowable before the work was done
            ("x-tenants-seen", str(len(tenants))),        # proof duplicate keys survive the trip
        ))
        return pb.EchoResponse(text=text, saw_request_id=request_id)


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.MetaEchoStub(channel)

        # `with_call` returns (response, call). The plain `stub.Echo(...)` form
        # returns only the response and throws the metadata away.
        response, call = stub.Echo.with_call(
            pb.EchoRequest(text="hello"),
            timeout=2,
            metadata=(
                ("x-request-id", "req-42"),
                ("x-tenant", "acme"),
                ("x-tenant", "acme-eu"),  # legal: keys may repeat
            ),
        )

        print(f"\nresponse message      : text={response.text!r}")
        print(f"initial  metadata     : {dict(call.initial_metadata())}")
        print(f"trailing metadata     : {dict(call.trailing_metadata())}")
        print(f"final status          : {call.code().name}")

        assert response.text == "HELLO"
        # The server knew our trace id even though NO message field carried it.
        assert response.saw_request_id == "req-42"
        assert dict(call.initial_metadata())["x-served-by"] == "metaecho-1"
        assert dict(call.trailing_metadata())["x-request-id"] == "req-42"
        assert "x-handler-micros" in dict(call.trailing_metadata())
        assert call.code() == grpc.StatusCode.OK

        # We sent x-tenant TWICE. The server received both, because metadata is
        # a list of pairs, not a dict - which is why dict(md) is lossy and
        # md.get(key) style helpers exist on the Go side.
        print(f"\nx-tenant was sent twice; the server counted "
              f"{dict(call.trailing_metadata())['x-tenants-seen']} values")
        assert dict(call.trailing_metadata())["x-tenants-seen"] == "2"

        # --- sending no metadata at all is also fine ---
        response, call = stub.Echo.with_call(pb.EchoRequest(text="bare"), timeout=2)
        print(f"\ncalling with no metadata: saw_request_id={response.saw_request_id!r}")
        assert response.saw_request_id == "none"

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_MetaEchoServicer_to_server(MetaEchoServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
