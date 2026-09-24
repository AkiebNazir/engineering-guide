"""
FOUNDATION LEVEL 05 - Bidirectional streaming: both sides stream at once
============================================================================
`stream` on BOTH sides. This is the fourth and last RPC shape, and it is not
"client streaming plus server streaming" - it is genuinely different, because
the two directions are INDEPENDENT. Neither side has to wait for the other.

    rpc Talk(stream ChatMessage) returns (stream ChatMessage);
             ^^^^^^                       ^^^^^^ both

The four shapes, complete:
  unary              one  -> one    levels 00-02
  server streaming   one  -> many   level 03
  client streaming   many -> one    level 04
  bidirectional      many -> many   this level

This is the closest gRPC gets to a WebSocket (see ../../WebSockets/Foundation),
with one advantage: every message is still a typed, contract-checked protobuf
message, not an untyped text frame you parse yourself.

You will learn
  * the server method is a GENERATOR that also ITERATES its input - both at once
  * "independent" means the server may send 5 messages before reading any, or
    read 5 before sending any; the pattern is yours to choose, not gRPC's
  * the simplest useful pattern is read-one/send-one (an echo or a request/reply
    conversation over a single long-lived call)
  * the call is over when BOTH directions close: the client half-closes, then the
    server's generator returns, which sends the final status
  * ordering is guaranteed WITHIN each direction, and there is no ordering
    relationship at all BETWEEN the two directions

Run it   python 05_bidirectional_streaming_rpc.py
"""
from concurrent import futures

import grpc

import chat_pb2 as pb
import chat_pb2_grpc as rpc


class ChatServicer(rpc.ChatServicer):
    def Talk(self, request_iterator, context: grpc.ServicerContext):
        """Iterates the incoming stream AND yields into the outgoing one. The
        two are separate HTTP/2 streams inside one call, so this generator is
        free to interleave reads and writes however it likes."""
        # First, one unsolicited message BEFORE reading anything. A unary or
        # client-streaming RPC could not do this - proof the directions are
        # independent rather than strictly alternating.
        print("  [server] sending a greeting before reading a single message")
        yield pb.ChatMessage(sender="server", text="welcome")

        for msg in request_iterator:
            print(f"  [server] read {msg.text!r} from {msg.sender!r}")
            if msg.text == "bye":
                # Answer and then stop reading: the server may end its side of
                # the conversation whenever it likes.
                yield pb.ChatMessage(sender="server", text="goodbye")
                return
            yield pb.ChatMessage(sender="server", text=f"you said {msg.text!r}")


def outgoing():
    for text in ["hello", "how are you", "bye"]:
        print(f"  [client] sending {text!r}")
        yield pb.ChatMessage(sender="client", text=text)


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.ChatStub(channel)

        # One call, two independent streams. The call returns an iterator
        # immediately while our `outgoing()` generator is consumed in the
        # background by grpcio's own thread.
        responses = stub.Talk(outgoing(), timeout=2)

        received = []
        for msg in responses:
            print(f"  [client] read {msg.text!r} from {msg.sender!r}")
            received.append(msg.text)

        print(f"\nserver sent {len(received)} messages: {received}")
        # "welcome" arrived before we sent anything, then one reply per message.
        assert received[0] == "welcome"
        assert received[-1] == "goodbye"
        assert "you said 'hello'" in received
        assert responses.code() == grpc.StatusCode.OK
        print(f"call finished with status {responses.code().name}")

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_ChatServicer_to_server(ChatServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
