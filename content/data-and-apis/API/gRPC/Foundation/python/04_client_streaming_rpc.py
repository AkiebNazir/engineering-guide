"""
FOUNDATION LEVEL 04 - Client streaming: many requests, one response
=======================================================================
Level 03 put `stream` on the response. This level puts it on the REQUEST, and
everything mirrors: the client sends as many messages as it likes over one open
call, and the server replies exactly once, at the end.

    rpc UploadReadings(stream Reading) returns (UploadSummary);
                       ^^^^^^ this side now

In REST you would either POST one giant array (and hold it all in memory on
both sides), or POST a thousand small requests (and pay a thousand round trips).
Client streaming is the third option: one call, a thousand messages, one answer.

WHAT CHANGES IN THE CODE
  client: you pass an ITERATOR of requests instead of a single request message
  server: your method receives an ITERATOR and `return`s one message, once

You will learn
  * the server method signature becomes `(request_iterator, context)` - note the
    plural: there is no single `request` to look at
  * the server can start folding numbers into a running total while the client is
    still sending, so neither side ever holds the whole batch
  * the single response is sent only after the client half-closes (its iterator
    is exhausted) - the server has no way to answer early without erroring
  * a natural fit for uploads, metrics, batch inserts and log shipping
  * the server can still fail the whole call with a status code (level 06) if one
    message in the middle of the stream is invalid

Run it   python 04_client_streaming_rpc.py
"""
from concurrent import futures

import grpc

import upload_pb2 as pb
import upload_pb2_grpc as rpc


class UploaderServicer(rpc.UploaderServicer):
    def UploadReadings(self, request_iterator, context: grpc.ServicerContext) -> pb.UploadSummary:
        # Note the parameter name: request_ITERATOR. Iterating it blocks until
        # the next message arrives, and ends when the client half-closes.
        count, total = 0, 0.0
        for reading in request_iterator:
            print(f"  [server] received sensor={reading.sensor!r} value={reading.value}")
            count += 1
            total += reading.value
            # Everything we need is in `count` and `total` - the readings
            # themselves are already garbage. That is the memory win.

        print(f"  [server] client half-closed after {count} messages, answering once")
        return pb.UploadSummary(count=count, sum=total, average=(total / count) if count else 0.0)


def readings():
    """The client's side of the stream. A generator, so the values are produced
    lazily - this could just as easily be a 10GB file read line by line."""
    for sensor, value in [("temp-a", 20.5), ("temp-a", 21.0), ("temp-b", 19.0), ("temp-b", 23.5)]:
        print(f"  [client] sending sensor={sensor!r} value={value}")
        yield pb.Reading(sensor=sensor, value=value)


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.UploaderStub(channel)

        # Pass the ITERATOR where a unary call would take one message. The call
        # blocks here until the server sends its single response.
        summary = stub.UploadReadings(readings(), timeout=2)
        print(f"\nsummary  : count={summary.count} sum={summary.sum} average={summary.average}")
        assert summary.count == 4
        assert abs(summary.sum - 84.0) < 1e-9
        assert abs(summary.average - 21.0) < 1e-9

        # --- sending nothing at all is legal: zero messages, then half-close ---
        summary = stub.UploadReadings(iter([]), timeout=2)
        print(f"empty    : count={summary.count} average={summary.average}   (an empty stream is valid)")
        assert summary.count == 0 and summary.average == 0.0

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_UploaderServicer_to_server(UploaderServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
