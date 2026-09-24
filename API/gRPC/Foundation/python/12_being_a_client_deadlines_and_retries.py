"""
FOUNDATION LEVEL 12 - Every service you write is also somebody's client
===========================================================================
Levels 00-11 were all SERVER code. But you spend at least as much real-world
time writing CLIENTS: code that calls someone else's service. This level flips
the lens - a small server plays "someone else's flaky service", and the
interesting code is the client calling it.

TWO THINGS EVERY gRPC CLIENT MUST DO
  1. SET A DEADLINE. Every single call. gRPC has no default timeout, so a call
     without one can hang until the process dies. `timeout=2` becomes the
     `grpc-timeout` metadata (level 07), which means the SERVER knows the
     deadline too and stops working the moment it passes - unlike REST, where a
     client timeout leaves the server churning on work nobody will read.
  2. RETRY ONLY THE RETRYABLE. The status code (level 06) tells you which:
     UNAVAILABLE and RESOURCE_EXHAUSTED are transient, INVALID_ARGUMENT and
     NOT_FOUND will be exactly as wrong next time.

You will learn
  * exponential backoff: wait longer after each failure, so a struggling server
    is not hammered harder while it is already struggling
  * why the retry decision is a switch on `e.code()`, never on a message string
  * DEADLINE_EXCEEDED is the client's own clock firing, and it is the one status
    where "safe to retry" depends on whether the call is idempotent - the server
    may well have completed the work before you gave up
  * deadlines are ABSOLUTE and propagate: if you have 2s left and you call a
    downstream service, it must finish within that same 2s, not get a fresh 2s
  * gRPC also has a built-in, config-driven retry policy (a JSON service config)
    for exactly this - hand-rolling it once first makes that config readable

Run it   python 12_being_a_client_deadlines_and_retries.py
"""
import time
from concurrent import futures

import grpc

import flaky_pb2 as pb
import flaky_pb2_grpc as rpc

ATTEMPTS = {"count": 0}


class FlakyServicer(rpc.FlakyServicer):
    """Fails the first 2 Fetch calls with UNAVAILABLE, then succeeds. Simulates a
    real service warming up or briefly overloaded - not actually broken."""

    def Fetch(self, request: pb.FetchRequest, context: grpc.ServicerContext) -> pb.FetchResponse:
        ATTEMPTS["count"] += 1
        if ATTEMPTS["count"] <= 2:
            context.abort(grpc.StatusCode.UNAVAILABLE, "warming up, try again")
        return pb.FetchResponse(status="ready", attempt=ATTEMPTS["count"])

    def Slow(self, request: pb.SlowRequest, context: grpc.ServicerContext) -> pb.SlowResponse:
        # The server can SEE the client's deadline, because `timeout=` travelled
        # as grpc-timeout metadata. A well-behaved server checks it instead of
        # doing work whose result can never be delivered.
        remaining = context.time_remaining()
        print(f"  [server] the client gave me {remaining:.2f}s; this work needs 1.0s")
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if not context.is_active():
                print("  [server] deadline passed, abandoning the work")
                return pb.SlowResponse(status="abandoned")
            time.sleep(0.02)
        return pb.SlowResponse(status="finished")


# Only these two mean "the same request might work if you ask again".
RETRYABLE = {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.RESOURCE_EXHAUSTED}


def fetch_with_retries(stub, max_attempts: int = 5) -> pb.FetchResponse:
    for attempt in range(1, max_attempts + 1):
        try:
            # A deadline on EVERY call, including every retry. Note each retry
            # gets its own 1s here; a stricter client would budget one overall
            # deadline across all attempts so the total is bounded.
            return stub.Fetch(pb.FetchRequest(), timeout=1)
        except grpc.RpcError as e:
            if e.code() not in RETRYABLE or attempt == max_attempts:
                # Not retryable, or out of attempts: give up honestly and let
                # the caller see the real status.
                raise
            wait = 0.05 * (2 ** (attempt - 1))  # exponential backoff: 0.05s, 0.1s, 0.2s, ...
            print(f"  attempt {attempt} got {e.code().name}, backing off {wait:.2f}s before retrying")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.FlakyStub(channel)

        print("== retrying a transient UNAVAILABLE with exponential backoff ==")
        res = fetch_with_retries(stub)
        print(f"final result -> status={res.status!r} on server attempt {res.attempt}")
        assert res.status == "ready"
        assert ATTEMPTS["count"] == 3, "expected exactly 2 failures then 1 success"

        print("\n== a deadline the server cannot meet ==")
        started = time.perf_counter()
        try:
            stub.Slow(pb.SlowRequest(), timeout=0.3)  # the work needs 1.0s
            raise AssertionError("expected DEADLINE_EXCEEDED")
        except grpc.RpcError as e:
            elapsed = time.perf_counter() - started
            print(f"  client gave up after {elapsed:.2f}s -> {e.code().name}")
            assert e.code() == grpc.StatusCode.DEADLINE_EXCEEDED
            # The client's own clock fired at ~0.3s; it did NOT wait 1.0s.
            assert elapsed < 0.9

        # The server's handler thread for that abandoned call is STILL RUNNING
        # right now - it only notices at its next is_active() check. Waiting
        # here just keeps this demo's output in order; it is also a real lesson:
        # a client giving up does not instantly free the server's resources.
        time.sleep(0.9)

        print("\n== the same call with a deadline that fits ==")
        res = stub.Slow(pb.SlowRequest(), timeout=3)
        print(f"  -> status={res.status!r}")
        assert res.status == "finished"

        print("\n== never retry a non-retryable status ==")
        # Calling a method that does not exist is UNIMPLEMENTED - permanent.
        # A retry loop that ignored the code would burn 5 attempts to learn this.
        missing = channel.unary_unary(
            "/foundation.flaky.v1.Flaky/Nope",
            request_serializer=pb.FetchRequest.SerializeToString,
            response_deserializer=pb.FetchResponse.FromString,
        )
        before = ATTEMPTS["count"]
        try:
            missing(pb.FetchRequest(), timeout=1)
            raise AssertionError("expected UNIMPLEMENTED")
        except grpc.RpcError as e:
            print(f"  -> {e.code().name} is permanent; retrying it would waste everyone's time")
            assert e.code() == grpc.StatusCode.UNIMPLEMENTED
            assert e.code() not in RETRYABLE
        assert ATTEMPTS["count"] == before

    print("\nOK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_FlakyServicer_to_server(FlakyServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
