"""
LAB 03 (advanced) - Server interceptors: authentication, logging, rate limiting, error shielding
================================================================================================
You will learn
  * interceptors are gRPC's MIDDLEWARE: code that wraps every call before it reaches your servicer
  * an interceptor sees the method name and the metadata (headers) - perfect for cross-cutting concerns
  * a chain, outermost first:

        request -> [Logging] -> [Auth] -> [RateLimit] -> servicer method
                    times it     token?    tokens left?

  * authentication via metadata:   authorization: Bearer <token>   ->  UNAUTHENTICATED if wrong
  * per-client rate limiting (token bucket) -> RESOURCE_EXHAUSTED  (gRPC's version of HTTP 429)
  * failing fast: an interceptor can reject WITHOUT ever calling your business code
  * CLIENT interceptors: attach the token to every outgoing call in one place

Needs   pip install grpcio grpcio-tools protobuf   (stubs: shop_pb2*.py made by ../generate.sh)
Run it  python 03_interceptors_auth_logging_ratelimit.py
"""
import threading
import time
from concurrent import futures

import grpc

import shop_pb2 as pb
import shop_pb2_grpc as rpc

TOKENS = {"tok-alice": "alice", "tok-bob": "bob"}                     # token -> user
PRODUCT = pb.Product(id=1, name="Keyboard", price_cents=4999, stock=3)


# --------------------------------------------------------------- helpers ----
def deny(code: grpc.StatusCode, message: str) -> grpc.RpcMethodHandler:
    """A handler that immediately fails the call. Returning it means the servicer never runs."""
    def handler(request, context):
        context.abort(code, message)
    return grpc.unary_unary_rpc_method_handler(handler)


def wrap_unary(handler: grpc.RpcMethodHandler, wrapper) -> grpc.RpcMethodHandler:
    """Rebuild a unary-unary handler with `wrapper(request, context, original_fn)` around it."""
    return grpc.unary_unary_rpc_method_handler(
        lambda request, context: wrapper(request, context, handler.unary_unary),
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer)


# ----------------------------------------------------------- interceptors ---
class LoggingInterceptor(grpc.ServerInterceptor):
    def __init__(self, log: list):
        self.log = log

    def intercept_service(self, continuation, details):
        handler = continuation(details)
        if handler is None or handler.unary_unary is None:
            return handler
        def timed(request, context, original):
            start = time.perf_counter()
            try:
                return original(request, context)
            finally:                                              # runs on success AND on abort
                code = context.code() or grpc.StatusCode.OK
                self.log.append(f"{details.method} -> {code.name} in {(time.perf_counter() - start) * 1000:.1f}ms")
        return wrap_unary(handler, timed)


class AuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, details):
        md = dict(details.invocation_metadata)
        token = md.get("authorization", "").removeprefix("Bearer ")
        user = TOKENS.get(token)
        if user is None:
            return deny(grpc.StatusCode.UNAUTHENTICATED, "missing or invalid token")
        handler = continuation(details)
        def with_user(request, context, original):
            context.set_trailing_metadata((("x-user", user),))   # hand the identity on (or use contextvars)
            return original(request, context)
        return wrap_unary(handler, with_user) if handler and handler.unary_unary else handler


class RateLimitInterceptor(grpc.ServerInterceptor):
    """Token bucket per token: `capacity` burst, refilled at `rate`/second."""

    def __init__(self, rate: float, capacity: int):
        self.rate, self.capacity, self.lock = rate, capacity, threading.Lock()
        self.buckets: dict[str, tuple[float, float]] = {}       # key -> (tokens, last_time)

    def intercept_service(self, continuation, details):
        key = dict(details.invocation_metadata).get("authorization", "anonymous")
        with self.lock:
            tokens, last = self.buckets.get(key, (float(self.capacity), time.monotonic()))
            now = time.monotonic()
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            allowed = tokens >= 1
            self.buckets[key] = (tokens - 1 if allowed else tokens, now)
        if not allowed:
            return deny(grpc.StatusCode.RESOURCE_EXHAUSTED, "rate limit exceeded, retry later")
        return continuation(details)


class ShieldInterceptor(grpc.ServerInterceptor):
    """Turn unexpected exceptions into INTERNAL without leaking details to the client."""

    def intercept_service(self, continuation, details):
        handler = continuation(details)
        if handler is None or handler.unary_unary is None:
            return handler
        def shielded(request, context, original):
            try:
                return original(request, context)
            except Exception as exc:                              # abort() itself raises a special exception; re-raise it
                if context.code() is not None:
                    raise
                print(f"  [server log] unexpected error: {exc!r}")
                context.abort(grpc.StatusCode.INTERNAL, "internal error")
        return wrap_unary(handler, shielded)


# -------------------------------------------------------- the business code --
class CatalogServicer(rpc.CatalogServicer):
    def GetProduct(self, request, context):
        if request.id == 666:
            raise RuntimeError("psycopg2.OperationalError: could not connect to 10.0.3.7")
        return PRODUCT


# ------------------------------------------------------ client interceptor ---
class TokenClientInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, token: str):
        self.token = token

    def intercept_unary_unary(self, continuation, details, request):
        md = list(details.metadata or []) + [("authorization", f"Bearer {self.token}")]
        new = details._replace(metadata=md)
        return continuation(new, request)


def main():
    log: list[str] = []
    # ORDER MATTERS: the first interceptor in the list is the OUTERMOST.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), interceptors=[
        LoggingInterceptor(log), AuthInterceptor(), RateLimitInterceptor(rate=5, capacity=3), ShieldInterceptor()])
    rpc.add_CatalogServicer_to_server(CatalogServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()

    def call(token=None, req_id=1):
        with grpc.insecure_channel(f"127.0.0.1:{port}") as ch:
            if token:
                ch = grpc.intercept_channel(ch, TokenClientInterceptor(token))    # token added in ONE place
            try:
                return "OK " + rpc.CatalogStub(ch).GetProduct(pb.GetProductRequest(id=req_id), timeout=2).name
            except grpc.RpcError as e:
                return e.code().name

    print("== authentication ==")
    r = call(None);        print("  no token        ->", r);  assert r == "UNAUTHENTICATED"
    r = call("tok-mallory"); print("  wrong token     ->", r); assert r == "UNAUTHENTICATED"
    r = call("tok-alice"); print("  alice           ->", r);  assert r == "OK Keyboard"

    print("\n== rate limiting: capacity 3, refill 5/s ==")
    results = [call("tok-bob") for _ in range(5)]
    print("  bob x5 quickly  ->", results)
    assert results.count("RESOURCE_EXHAUSTED") >= 2 and results[0].startswith("OK")
    print("  alice unaffected->", call("tok-alice"), "(limits are per client)")
    time.sleep(0.5)
    print("  bob after 0.5s  ->", call("tok-bob"), "(tokens refilled)")

    print("\n== error shielding ==")
    r = call("tok-alice", req_id=666)
    print("  client sees     ->", r, "(the SQL host name stayed in the server log)")
    assert r == "INTERNAL"

    print("\n== the log written by the outermost interceptor ==")
    for line in log[:6]:
        print("  ", line)
    assert any("UNAUTHENTICATED" in l for l in log) and any("RESOURCE_EXHAUSTED" in l for l in log)
    server.stop(0)
    print("\nOK")


if __name__ == "__main__":
    main()
