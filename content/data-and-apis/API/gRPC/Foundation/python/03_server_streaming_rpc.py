"""
FOUNDATION LEVEL 03 - Server streaming: one request, many responses
=======================================================================
Levels 00-02 were unary: one message each way. Adding the word `stream` to the
RETURN type in the .proto changes the shape of both the server method and the
client call - and nothing else. This is gRPC's first genuinely new capability
over plain REST, where you would reach for polling, pagination, chunked
transfer encoding, or Server-Sent Events to get the same effect.

    rpc Countdown(CountdownRequest) returns (stream Tick);
                                            ^^^^^^ this one word

WHAT CHANGES IN THE CODE
  server: the method becomes a GENERATOR - every `yield` is one message on the
          wire, sent immediately, not collected into a list first
  client: the call returns an ITERATOR - every `for` step is one message
          arriving, not the whole batch

You will learn
  * `yield` on the server = "send this one now and keep the call open"
  * the client starts processing message 1 while the server is still producing
    message 5 - that is the point, and it is why this is not just "return a list"
  * the call ends when the server's generator returns; only THEN does the client
    receive the status (OK or an error), as HTTP/2 trailers
  * memory: a stream of a million rows never exists in RAM all at once on either
    side, unlike a single response containing a million-element repeated field
  * a client that stops iterating early CANCELS the call - the server's context
    reports it so the generator can stop working (`context.is_active()`)

Run it   python 03_server_streaming_rpc.py
"""
import time
from concurrent import futures

import grpc

import ticker_pb2 as pb
import ticker_pb2_grpc as rpc


class TickerServicer(rpc.TickerServicer):
    def Countdown(self, request: pb.CountdownRequest, context: grpc.ServicerContext):
        """A generator, not a function that returns. Each `yield` puts one Tick
        on the wire right away; the call stays open until this returns."""
        for value in range(request.start, 0, -1):
            # A client that hung up (or timed out) makes this False. Checking it
            # is how you avoid computing 10,000 more rows nobody will read.
            if not context.is_active():
                print(f"  [server] client went away at value={value}, stopping early")
                return
            print(f"  [server] yielding value={value}")
            yield pb.Tick(value=value, last=(value == 1))
            time.sleep(0.01)  # stand-in for real work per item


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.TickerStub(channel)

        # The call returns IMMEDIATELY with an iterator; nothing has been
        # received yet. The server is producing while we are consuming.
        stream = stub.Countdown(pb.CountdownRequest(start=4), timeout=2)
        print("client got an iterator back - the server is still working")

        received = []
        for tick in stream:  # each step = one message arriving off the wire
            print(f"  [client] received value={tick.value} last={tick.last}")
            received.append(tick.value)

        # The `for` loop ended because the server's generator returned, which is
        # what sends the final status. Reading it is how you know it ended
        # cleanly rather than erroring mid-stream.
        print(f"stream finished with status {stream.code().name}")
        assert received == [4, 3, 2, 1]
        assert stream.code() == grpc.StatusCode.OK

        # --- stopping early cancels the call ---
        print("\nnow abandoning a stream after one message:")
        stream = stub.Countdown(pb.CountdownRequest(start=100), timeout=2)
        first = next(iter(stream))
        assert first.value == 100
        stream.cancel()  # or simply `break` out of the loop / let it be garbage collected
        time.sleep(0.05)  # give the server a moment to notice
        try:
            next(iter(stream))
            raise AssertionError("expected CANCELLED after cancel()")
        except grpc.RpcError as e:
            print(f"  [client] further reads -> {e.code().name}")
            assert e.code() == grpc.StatusCode.CANCELLED

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_TickerServicer_to_server(TickerServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
