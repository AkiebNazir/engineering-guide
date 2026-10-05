"""
LAB 01 (basic) - Your first gRPC service: a unary call, status codes and metadata
=================================================================================
You will learn
  * the gRPC recipe:   .proto  ->  generated stubs  ->  Servicer (server)  +  Stub (client)
  * a unary RPC looks like a local function call:   stub.GetProduct(GetProductRequest(id=1))
  * errors are NOT HTTP codes; they are gRPC status codes with a message:
        NOT_FOUND, INVALID_ARGUMENT, PERMISSION_DENIED, UNAUTHENTICATED, INTERNAL, UNAVAILABLE ...
    the client catches grpc.RpcError and reads .code() / .details()
  * METADATA = gRPC's headers: client sends request metadata, server replies with
    initial metadata (before the response) and trailing metadata (after it)
  * the channel: one long-lived HTTP/2 connection reused for every call (create it once!)

    client  --[HEADERS: /shop.v1.Catalog/GetProduct + metadata]-->  server
    client  --[DATA: 5-byte frame header + protobuf request]----->
    client  <--[HEADERS]--  <--[DATA: protobuf response]--  <--[TRAILERS: grpc-status: 0]--

Needs   pip install grpcio grpcio-tools protobuf   (stubs: shop_pb2*.py made by ../generate.sh)
Run it  python 01_unary_status_codes_metadata.py
"""
from concurrent import futures

import grpc

import shop_pb2 as pb
import shop_pb2_grpc as rpc

PRODUCTS = {1: pb.Product(id=1, name="Keyboard", price_cents=4999, stock=12),
            2: pb.Product(id=2, name="Mouse", price_cents=1999, stock=0)}


class CatalogServicer(rpc.CatalogServicer):
    def GetProduct(self, request: pb.GetProductRequest, context: grpc.ServicerContext) -> pb.Product:
        # request metadata (headers) sent by the client
        md = dict(context.invocation_metadata())
        request_id = md.get("x-request-id", "none")

        if request.id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id must be positive")   # raises: nothing below runs
        product = PRODUCTS.get(request.id)
        if product is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"product {request.id} does not exist")

        context.send_initial_metadata((("x-served-by", "catalog-1"),))      # sent BEFORE the response
        context.set_trailing_metadata((("x-request-id", request_id),))      # sent AFTER the response
        return product


def start_server() -> tuple[grpc.Server, int]:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_CatalogServicer_to_server(CatalogServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")          # port 0 = any free port; use TLS in production
    server.start()
    return server, port


if __name__ == "__main__":
    server, port = start_server()
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:      # create ONCE, reuse for every call
        stub = rpc.CatalogStub(channel)

        print("== a successful call ==")
        product = stub.GetProduct(pb.GetProductRequest(id=1), timeout=2)          # ALWAYS set a timeout
        print("  ->", product.name, f"${product.price_cents / 100:.2f}", "stock", product.stock)
        assert product.name == "Keyboard"

        print("\n== reading metadata: use with_call() to get the call object ==")
        product, call = stub.GetProduct.with_call(pb.GetProductRequest(id=2), timeout=2,
                                                  metadata=(("x-request-id", "req-42"),))
        print("  initial  metadata:", dict(call.initial_metadata()))
        print("  trailing metadata:", dict(call.trailing_metadata()))
        print("  status:", call.code())
        assert dict(call.trailing_metadata())["x-request-id"] == "req-42"
        assert call.code() == grpc.StatusCode.OK

        print("\n== errors: catch grpc.RpcError, switch on .code() ==")
        for label, req in [("unknown id", pb.GetProductRequest(id=99)), ("bad argument", pb.GetProductRequest(id=-5))]:
            try:
                stub.GetProduct(req, timeout=2)
            except grpc.RpcError as e:
                print(f"  {label:<13} -> {e.code().name:<16} {e.details()!r}")
                assert e.code() in (grpc.StatusCode.NOT_FOUND, grpc.StatusCode.INVALID_ARGUMENT)

        print("\n== the server is down: UNAVAILABLE (retryable) vs a logic error (not retryable) ==")
        server.stop(0).wait()
        try:
            stub.GetProduct(pb.GetProductRequest(id=1), timeout=1)
        except grpc.RpcError as e:
            print("  ->", e.code().name)
            assert e.code() == grpc.StatusCode.UNAVAILABLE

    print("\nstatus code cheat sheet")
    for code, meaning in [("INVALID_ARGUMENT", "client sent nonsense; never retry"),
                          ("NOT_FOUND", "resource does not exist; never retry"),
                          ("ALREADY_EXISTS", "creating something that exists"),
                          ("PERMISSION_DENIED", "authenticated but not allowed"),
                          ("UNAUTHENTICATED", "no/invalid credentials"),
                          ("RESOURCE_EXHAUSTED", "rate limited / quota; retry with backoff"),
                          ("FAILED_PRECONDITION", "system not in the required state"),
                          ("DEADLINE_EXCEEDED", "took too long; retry only if idempotent"),
                          ("UNAVAILABLE", "transient, server down/overloaded; safe to retry with backoff"),
                          ("INTERNAL", "server bug")]:
        print(f"  {code:<20} {meaning}")
    print("\nOK")
