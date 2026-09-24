"""
FOUNDATION LEVEL 08 - Middleware, which gRPC calls INTERCEPTORS
===================================================================
Levels 00-07 put everything a call needed inside one handler method. An
INTERCEPTOR is gRPC's name for middleware: an object that wraps every RPC and
gets to run code before and/or after the real handler, without touching the
handler's code at all. Logging, panic recovery, authentication (level 09),
authorization (level 10), tracing, and rate limiting are all just interceptors.

"Interceptor" is the real, named mechanism - not a vague framework concept. Do
not go looking for "gRPC middleware" in the docs; the word is interceptor.

    grpc.server(pool, interceptors=[outer, inner])
                                     ^^^^^ runs first, returns last

THE PYTHON SHAPE, AND WHY IT IS ODD
  You subclass `grpc.ServerInterceptor` and implement ONE method:

      intercept_service(self, continuation, handler_call_details) -> handler

  You are NOT handed the request. You are handed `continuation`, which returns
  the next HANDLER in the chain, and you return a handler of your own that
  wraps it. So an interceptor is a function that transforms a handler into
  another handler - the same idea as REST's `with_logging(next_handler)`,
  just one level more indirect because it happens once per method, not once
  per call. (Go's interceptor signature is much more direct - see main.go.)

You will learn
  * an interceptor wraps the handler, so it sees the request on the way IN and
    the response or exception on the way OUT
  * chaining: the list order is outside-in, so the first interceptor in the list
    wraps the second, which wraps the third, which wraps your handler
  * ORDER MATTERS, and this file proves it: recovery placed INSIDE logging means
    the log line still happens on a crash; swap them and the log line vanishes
  * recovering from a crash in ONE handler so the server stays up and that one
    call becomes a clean INTERNAL status instead of a mystery
  * `handler_call_details.method` is the full method path
    ("/foundation.interceptor.v1.Work/Do") - how an interceptor knows which RPC
    it is wrapping, which is what levels 09-10 use to protect some RPCs and not
    others

Run it   python 08_middleware_interceptors_logging_and_recovery.py
"""
import time
from concurrent import futures

import grpc

import interceptor_pb2 as pb
import interceptor_pb2_grpc as rpc

CALL_LOG: list[str] = []


# ---- the "real" application logic, with zero knowledge of logging/recovery ----
class WorkServicer(rpc.WorkServicer):
    def Do(self, request: pb.DoRequest, context: grpc.ServicerContext) -> pb.DoResponse:
        if request.task == "boom":
            raise RuntimeError("simulated bug in a handler")  # on purpose, to prove recovery works
        return pb.DoResponse(result=f"did {request.task}")


def _wrap(handler, new_unary):
    """Rebuild a unary-unary RpcMethodHandler around a new function, keeping the
    original serializers. Every Python server interceptor needs this boilerplate."""
    return grpc.unary_unary_rpc_method_handler(
        new_unary,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )


# ---- interceptor #1: logs the method, outcome, and how long it took ----
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method          # e.g. "/foundation.interceptor.v1.Work/Do"
        handler = continuation(handler_call_details)  # the NEXT thing in the chain
        if handler is None or handler.unary_unary is None:
            return handler

        def logged(request, context):
            start = time.perf_counter()
            try:
                response = handler.unary_unary(request, context)
                outcome = "OK"
                return response
            except Exception:
                # We do NOT swallow it here - logging's job is to log. Recovery
                # is a separate interceptor with a separate job.
                outcome = "EXCEPTION"
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                line = f"{method} -> {outcome} ({elapsed_ms:.2f}ms)"
                CALL_LOG.append(line)
                print(f"  [log] {line}")

        return _wrap(handler, logged)


# ---- interceptor #2: turns ANY escaped exception into a clean INTERNAL status ----
class RecoveryInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def recovered(request, context):
            try:
                return handler.unary_unary(request, context)
            except Exception as exc:
                # grpcio implements context.abort() by raising a BARE Exception
                # after recording the status on the call. "type is exactly
                # Exception" therefore means "the handler deliberately chose a
                # status" (level 06) and must pass straight through; anything
                # else is a real bug. Level 11 relies on this same distinction.
                if type(exc) is Exception:
                    raise
                print(f"  [recovery] caught {exc!r} - server stays up, this ONE call becomes INTERNAL")
                # Without this, an escaped exception still becomes a status, but
                # UNKNOWN with the traceback leaked in the details - which tells
                # the caller nothing useful and tells an attacker too much.
                context.abort(grpc.StatusCode.INTERNAL, "internal error")

        return _wrap(handler, recovered)


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.WorkStub(channel)

        res = stub.Do(pb.DoRequest(task="ok"), timeout=2)
        print(f"Do(task='ok')    -> {res.result!r}")
        assert res.result == "did ok"

        try:
            stub.Do(pb.DoRequest(task="boom"), timeout=2)
            raise AssertionError("expected INTERNAL")
        except grpc.RpcError as e:
            print(f"Do(task='boom')  -> {e.code().name} {e.details()!r}   (the handler raised; recovery cleaned it up)")
            assert e.code() == grpc.StatusCode.INTERNAL
            # The traceback did NOT leak to the caller.
            assert "simulated bug" not in (e.details() or "")

        # The crash above must NOT have taken the server down for anyone else.
        res = stub.Do(pb.DoRequest(task="again"), timeout=2)
        print(f"Do(task='again') -> {res.result!r}   (server is still alive after the crash)")
        assert res.result == "did again"

    # ORDER PROOF. Logging is OUTSIDE recovery, so it observed all three calls -
    # including the one that raised. Swap the interceptors list below and the
    # "boom" call's log line disappears, because recovery would convert the
    # exception into an abort before logging ever saw a problem.
    print(f"\nwhat the logging interceptor recorded ({len(CALL_LOG)} calls):")
    for line in CALL_LOG:
        print(f"  {line}")
    assert len(CALL_LOG) == 3
    assert CALL_LOG[1].endswith(")") and "EXCEPTION" in CALL_LOG[1], \
        "logging must be OUTSIDE recovery to see the crash"
    print("  -> logging saw the EXCEPTION because it wraps recovery, not the reverse")

    print("OK")


if __name__ == "__main__":
    # Outside-in: LoggingInterceptor wraps RecoveryInterceptor wraps the handler.
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[LoggingInterceptor(), RecoveryInterceptor()],
    )
    rpc.add_WorkServicer_to_server(WorkServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
