"""
FOUNDATION LEVEL 00 (start here) - A basic webhook receiver, explained end to end
====================================================================================
If someone says "build me a basic webhook receiver", THIS is what they mean: one
server, one URL that accepts POST, and a 200 answer. Nothing about signatures,
retries, or queues yet - just enough to see one delivery arrive and be accepted,
so every later level is "add one more piece" instead of "understand everything
at once".

THE MENTAL MODEL (read this before the code)
  A webhook is just you running a small REST server that someone else's system
  calls into, unprompted. You never initiate the connection - you have no idea
  when it will happen - you only have to be READY when it arrives:
    - you publish a URL once ("here is where to reach me")
    - their system POSTs a JSON event to it whenever something happens
    - you answer 200 as fast as you can, meaning "got it, it's mine now"
  That is the whole reversal: in a normal API (../../REST/Foundation) you are
  the client and they are the server. Here they are the client and YOU are the
  server. Everything difficult about webhooks follows from that one flip.

You will learn
  * that a webhook receiver is an ordinary HTTP endpoint - no new protocol
  * why it is POST (a delivery carries a body and changes your state)
  * the exact loop: raw body in -> 200 out, immediately
  * that answering 200 is a PROMISE ("I have it"), not just politeness - the
    sender deletes its copy or stops retrying based on that number
  * that a path nobody registered is a normal, handled 404, not a crash

Run it        python 00_single_receiver_endpoint_and_how_it_works.py
Keep serving  python 00_single_receiver_endpoint_and_how_it_works.py --serve
              (then: curl -i -X POST localhost:8080/webhook -d '{"type":"ping"}')
"""
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1_000_000  # never read an unbounded body off the network


class Handler(BaseHTTPRequestHandler):
    # do_POST runs exactly once per incoming delivery. By the time it starts,
    # the library has already read the request line and headers off the socket
    # and parsed them for you - the bonus level (13) shows the one thing a
    # webhook receiver must NOT let a library hide: the raw body bytes.
    def do_POST(self):
        # This server has agreed to answer exactly ONE path. Anything else is
        # "not found" - an expected outcome, not a bug in our code.
        if self.path != "/webhook":
            self.reply(404, {"error": "no webhook registered at that path"})
            return

        # The body is the event. Read exactly Content-Length bytes: the socket
        # itself gives no signal for "the body ended", the header does.
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        raw = self.rfile.read(length)

        # A real sender POSTs JSON. Later levels validate this properly (02)
        # and verify it really came from who it claims (04) - not yet.
        event = json.loads(raw)
        print(f"  [receiver] a delivery arrived, unprompted: {event}")

        # 200 is the entire point of the exercise. To the sender it means
        # "delivered, stop worrying about this event".
        self.reply(200, {"received": True})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)                            # step 1: the status line
        self.send_header("Content-Type", "application/json")  # step 2: headers...
        self.send_header("Content-Length", str(len(body)))    #         ...so the client knows where the body ends
        self.end_headers()                                    # step 3: the blank line that ends the headers
        self.wfile.write(body)                                # step 4: the body itself

    def log_message(self, *args):
        pass  # silence the default per-request console line, to keep the demo output clean


def post(base: str, path: str, payload: dict):
    """This function IS 'their system'. There is nothing special about a
    webhook sender - it is any program that can make an HTTP POST."""
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def demo(base: str) -> None:
    status, body = post(base, "/webhook", {"type": "order.created", "id": "evt_1"})
    print(f"POST /webhook -> {status} {body}")
    assert status == 200 and body == {"received": True}

    status, body = post(base, "/not-registered", {"type": "order.created"})
    print(f"POST /not-registered -> {status} {body}   (a path nobody registered - not a crash)")
    assert status == 404

    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/webhook")
        print("try: curl -i -X POST localhost:8080/webhook -d '{\"type\":\"ping\"}'")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

    # port 0 = "operating system, hand me any free port" - so this demo never
    # collides with something already listening on 8080 on your machine.
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
