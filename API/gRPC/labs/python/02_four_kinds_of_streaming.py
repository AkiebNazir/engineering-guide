"""
LAB 02 (basic) - The four RPC shapes: unary, server stream, client stream, bidirectional
=========================================================================================
You will learn
  * how each shape looks in Python - the trick is simply "generator in, generator out":

        unary            reply   = stub.Method(request)
        server stream    for r in stub.Method(request):            server does:  yield reply, yield reply ...
        client stream    reply   = stub.Method(iter_of_requests)    server does:  for req in request_iterator
        bidi stream      for r in stub.Method(iter_of_requests)     server does:  for req in it: yield reply

  * when to pick which:
        server stream  -> results too big for one message, live feeds, progress ("list 1M rows")
        client stream  -> uploads, telemetry batches ("send 10k metrics, get ONE summary")
        bidi           -> chat, multiplayer, anything conversational
  * a stream is ONE call on ONE HTTP/2 stream: cheap to keep open, ordered, with back-pressure
  * how to stop a stream from the client (cancel) and what the server sees

Needs   pip install grpcio grpcio-tools protobuf   (stubs: shop_pb2*.py made by ../generate.sh)
Run it  python 02_four_kinds_of_streaming.py
"""
import queue
import threading
import time
from concurrent import futures

import grpc

import shop_pb2 as pb
import shop_pb2_grpc as rpc

CATALOG = [pb.Product(id=i, name=name, price_cents=100 * i, stock=i)
           for i, name in enumerate(["Keyboard", "Kettle", "Keycap", "Mouse", "Monitor", "Kickstand"], start=1)]


class CatalogServicer(rpc.CatalogServicer):
    # 2. SERVER STREAMING: a generator. Each `yield` becomes one message on the wire.
    def ListProducts(self, request, context):
        sent = 0
        for p in CATALOG:
            if not context.is_active():                       # the client cancelled / left: stop working!
                print("  [server] client went away after", sent, "items")
                return
            if p.name.startswith(request.name_prefix):
                yield p
                sent += 1
                if request.limit and sent >= request.limit:
                    return
                time.sleep(0.01)                               # pretend each row costs something

    # 3. CLIENT STREAMING: the request is an ITERATOR of messages; return ONE reply at the end.
    def UploadMetrics(self, request_iterator, context):
        count, total = 0, 0.0
        for metric in request_iterator:                        # blocks until the next message arrives
            count += 1
            total += metric.value
        return pb.UploadSummary(count=count, sum=total, avg=total / count if count else 0)

    # 4. BIDIRECTIONAL: read requests and yield replies independently.
    def Chat(self, request_iterator, context):
        for msg in request_iterator:
            yield pb.ChatMessage(**{"from": "bot", "text": f"echo: {msg.text.upper()}"})


def start_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    rpc.add_CatalogServicer_to_server(CatalogServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    return server, port


if __name__ == "__main__":
    server, port = start_server()
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.CatalogStub(channel)

        print("== server streaming: one request, many responses ==")
        names = [p.name for p in stub.ListProducts(pb.ListProductsRequest(name_prefix="K"), timeout=5)]
        print("  products starting with K:", names)
        assert names == ["Keyboard", "Kettle", "Keycap", "Kickstand"]

        print("\n== client streaming: many requests, ONE response ==")
        def metrics():                                          # any iterable works: a generator streams lazily
            for i in range(1, 1001):
                yield pb.Metric(name="latency_ms", value=float(i))
        summary = stub.UploadMetrics(metrics(), timeout=5)
        print(f"  sent 1000 metrics -> count={summary.count} sum={summary.sum:.0f} avg={summary.avg:.1f}")
        assert (summary.count, summary.sum) == (1000, 500500.0)

        print("\n== bidirectional: a live conversation ==")
        outbox: queue.Queue = queue.Queue()                     # the client feeds this whenever it wants
        def outgoing():
            while True:
                item = outbox.get()
                if item is None:                                # sentinel: half-close our side
                    return
                yield item
        replies = stub.Chat(outgoing(), timeout=5)
        for text in ["hello", "how are you", "bye"]:
            outbox.put(pb.ChatMessage(**{"from": "me", "text": text}))
            reply = next(replies)                               # ping-pong; could also send 3 then read 3
            print(f"  me: {text:<12} bot: {reply.text}")
            assert reply.text == f"echo: {text.upper()}"
        outbox.put(None)
        assert list(replies) == []                              # server finishes after we close our side

        print("\n== cancelling a server stream from the client ==")
        stream = stub.ListProducts(pb.ListProductsRequest(), timeout=5)
        first = next(stream)
        stream.cancel()                                         # tells the server via RST_STREAM
        try:
            next(stream)
        except grpc.RpcError as e:
            print(f"  got {first.name}, then cancelled -> client sees {e.code().name}")
            assert e.code() == grpc.StatusCode.CANCELLED
        time.sleep(0.2)                                         # give the server a moment to print its message

    server.stop(0)
    print("\nOK")
