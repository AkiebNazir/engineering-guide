"""
LAB 04 (advanced) - Deadlines, cancellation propagation and retries
====================================================================
You will learn
  * a DEADLINE is an absolute time budget for the WHOLE call; a timeout is how you set it
  * NEVER call without one: a hung backend would hold your threads forever
  * deadlines CASCADE:   client(0.5s) -> gateway -> backend(needs 1s)
        the gateway passes its REMAINING time downstream (context.time_remaining()),
        so nobody keeps working after the original caller has given up
  * the server can see the budget shrinking (time_remaining) and the cancellation (is_active / callbacks)
  * RETRIES: transparent, declarative retries via a client service config
        - only for statuses that are safe to retry (UNAVAILABLE), never INVALID_ARGUMENT
        - exponential backoff between attempts, a cap on attempts
        - ONLY for idempotent calls: a retried `CreateOrder` could run twice!
  * wait_for_ready: queue the call while the channel connects instead of failing instantly

    caller --0.5s--> [gateway] --remaining ~0.49s--> [backend: sleeps 1s]
                          |                                |
                 DEADLINE_EXCEEDED  <----------------------+ cancelled (stops working)

Needs   pip install grpcio grpcio-tools protobuf   (stubs: shop_pb2*.py made by ../generate.sh)
Run it  python 04_deadlines_retries_cascading.py
"""
import json
import threading
import time
from concurrent import futures

import grpc

import shop_pb2 as pb
import shop_pb2_grpc as rpc


# --------------------------------------------------------------- backend ----
class Backend(rpc.CatalogServicer):
    def __init__(self):
        self.calls = 0
        self.saw_cancel = threading.Event()
        self.work_seconds = 1.0
        self.fail_first = 0                                   # first N calls fail with UNAVAILABLE

    def GetProduct(self, request, context):
        self.calls += 1
        if self.calls <= self.fail_first:
            context.abort(grpc.StatusCode.UNAVAILABLE, f"overloaded (call #{self.calls})")
        context.add_callback(lambda: None)
        deadline = time.monotonic() + self.work_seconds
        while time.monotonic() < deadline:                    # "work" in small steps, checking the caller
            if not context.is_active():
                self.saw_cancel.set()                         # caller gave up => stop wasting CPU
                return pb.Product()
            time.sleep(0.02)
        return pb.Product(id=request.id, name="from-backend")


# --------------------------------------------------------------- gateway ----
class Gateway(rpc.CatalogServicer):
    def __init__(self, backend_stub):
        self.backend = backend_stub
        self.budget_seen: float | None = None

    def GetProduct(self, request, context):
        remaining = context.time_remaining()                  # seconds left of the CALLER's deadline
        self.budget_seen = remaining
        try:
            # Propagate: give the backend ONLY the time that is left (minus a little for our own work).
            return self.backend.GetProduct(request, timeout=max(0.001, remaining - 0.01))
        except grpc.RpcError as e:
            context.abort(e.code(), f"backend: {e.details()}")


def serve(servicer):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    rpc.add_CatalogServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    return server, port


if __name__ == "__main__":
    backend = Backend()
    backend_server, backend_port = serve(backend)
    backend_channel = grpc.insecure_channel(f"127.0.0.1:{backend_port}")
    gateway = Gateway(rpc.CatalogStub(backend_channel))
    gateway_server, gateway_port = serve(gateway)
    channel = grpc.insecure_channel(f"127.0.0.1:{gateway_port}")
    stub = rpc.CatalogStub(channel)

    print("== 1. deadline exceeded ==")
    t = time.perf_counter()
    try:
        stub.GetProduct(pb.GetProductRequest(id=1), timeout=0.5)
    except grpc.RpcError as e:
        took = time.perf_counter() - t
        print(f"  caller waited {took:.2f}s and got {e.code().name}")
        assert e.code() == grpc.StatusCode.DEADLINE_EXCEEDED and took < 0.8
    print(f"  gateway saw a remaining budget of {gateway.budget_seen:.2f}s and passed it downstream")
    assert 0.3 < gateway.budget_seen <= 0.55

    print("\n== 2. the backend noticed the caller left and STOPPED working ==")
    assert backend.saw_cancel.wait(timeout=1.0), "backend kept working on a call nobody is waiting for"
    print("  backend saw cancellation: True (no wasted work after the deadline)")

    print("\n== 3. same call with enough time ==")
    backend.work_seconds = 0.1
    p = stub.GetProduct(pb.GetProductRequest(id=1), timeout=2)
    print("  ->", p.name)
    assert p.name == "from-backend"

    print("\n== 4. retries: a flaky backend that fails the first 2 calls with UNAVAILABLE ==")
    service_config = json.dumps({"methodConfig": [{
        "name": [{"service": "shop.v1.Catalog", "method": "GetProduct"}],     # only this (idempotent) method
        "retryPolicy": {"maxAttempts": 4, "initialBackoff": "0.05s", "maxBackoff": "0.5s",
                        "backoffMultiplier": 2, "retryableStatusCodes": ["UNAVAILABLE"]}}]})
    retry_channel = grpc.insecure_channel(f"127.0.0.1:{backend_port}", options=[
        ("grpc.enable_retries", 1), ("grpc.service_config", service_config)])
    retry_stub = rpc.CatalogStub(retry_channel)

    backend.calls, backend.fail_first = 0, 2
    p = retry_stub.GetProduct(pb.GetProductRequest(id=7), timeout=3)
    print(f"  client made ONE call; the backend saw {backend.calls} attempts; result: {p.name}")
    assert backend.calls == 3 and p.name == "from-backend"

    backend.calls, backend.fail_first = 0, 10                                  # never recovers
    try:
        retry_stub.GetProduct(pb.GetProductRequest(id=7), timeout=3)
    except grpc.RpcError as e:
        print(f"  permanently failing backend: gave up after {backend.calls} attempts with {e.code().name}")
        assert backend.calls == 4 and e.code() == grpc.StatusCode.UNAVAILABLE
    print("  (maxAttempts=4 caps it; without backoff a retry storm would hammer an already-sick server)")

    print("\n== 5. errors that must NOT be retried ==")
    class Strict(rpc.CatalogServicer):
        calls = 0
        def GetProduct(self, request, context):
            Strict.calls += 1
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "bad id")
    strict_server, strict_port = serve(Strict())
    ch = grpc.insecure_channel(f"127.0.0.1:{strict_port}", options=[("grpc.enable_retries", 1), ("grpc.service_config", service_config)])
    try:
        rpc.CatalogStub(ch).GetProduct(pb.GetProductRequest(id=1), timeout=2)
    except grpc.RpcError as e:
        print(f"  INVALID_ARGUMENT was attempted {Strict.calls} time(s): same request would fail the same way")
        assert Strict.calls == 1

    print("\n== 6. wait_for_ready: queue the call while the channel connects ==")
    backend.work_seconds = 0.0
    backend_server.stop(0).wait()
    dead = rpc.CatalogStub(grpc.insecure_channel(f"127.0.0.1:{backend_port}"))
    try:
        dead.GetProduct(pb.GetProductRequest(id=1), timeout=1)
    except grpc.RpcError as e:
        print("  default (fail fast)     ->", e.code().name)
    revived = {}
    def restart():
        time.sleep(0.5)
        s = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        rpc.add_CatalogServicer_to_server(Backend(), s)
        s.add_insecure_port(f"127.0.0.1:{backend_port}")
        s.start()
        revived["server"] = s
    threading.Thread(target=restart).start()
    p = dead.GetProduct(pb.GetProductRequest(id=1), timeout=5, wait_for_ready=True)
    print("  wait_for_ready=True     -> succeeded once the server came back:", p.name or "(empty)")

    for s in (gateway_server, strict_server, revived["server"]):
        s.stop(0)
    print("\nOK")
