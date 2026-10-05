"""
FOUNDATION LEVEL 05 - The fast ACK: answer now, work later
==============================================================
Senders give you a few seconds - Stripe and GitHub give about 10, some give 5 -
and then they hang up and call the delivery failed. They do not know your
handler was still busy resizing a video; silence looks exactly like being down.

So a receiver that does its real work INSIDE the handler is not merely slow, it
is incorrect: the sender times out, retries, and now the same event is being
processed twice at once. That is the duplicate storm level 03 was defending
against - and the cheapest way to stop causing it is to stop being slow.

The pattern, in two lines of responsibility:
    handler:  validate -> store/enqueue (cheap, durable) -> 202, done
    worker:   pick it up in the background -> do the slow, failable part
Your 2xx means "I have accepted responsibility for this event", NOT "the work
is finished". Those are different promises, and only the first one is fast.

You will learn
  * how a sender-side timeout actually looks (and that it causes a retry, so
    the slow handler gets you duplicate WORK, not just a scary log line)
  * the enqueue-then-ACK split, with a background thread as the worker
  * 202 Accepted as the honest status code for "queued, not finished"
  * the durability catch: an in-memory queue loses events if the process dies,
    which is why real receivers enqueue into a database or broker first
    (see ../../labs/python/04_idempotent_async_receiver.py)

Run it   python 05_fast_ack_and_background_work.py
"""
import json
import queue
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SENDER_TIMEOUT = 0.25   # our pretend sender gives up after 250ms
SLOW_WORK = 0.60        # the real work takes longer than that

work_queue: queue.Queue = queue.Queue()
done_lock = threading.Lock()
slow_handler_runs: list[str] = []   # every time the SLOW endpoint did the work
worker_runs: list[str] = []         # every time the BACKGROUND worker did it


def do_the_slow_work(event_id: str, log: list[str]) -> None:
    time.sleep(SLOW_WORK)
    with done_lock:
        log.append(event_id)


def worker() -> None:
    while True:
        event = work_queue.get()
        do_the_slow_work(event["id"], worker_runs)
        work_queue.task_done()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        event = json.loads(self.rfile.read(length))

        if self.path == "/slow":
            # THE ANTI-PATTERN. The work happens before the response, so the
            # response cannot arrive before the work is finished.
            do_the_slow_work(event["id"], slow_handler_runs)
            self.reply(200, {"status": "finished the work inline"})
            return

        if self.path == "/fast-ack":
            # Cheap and durable only: hand it off, then answer immediately.
            work_queue.put(event)
            self.reply(202, {"status": "queued", "id": event["id"]})
            return

        self.reply(404, {"error": "not found"})

    def reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # This is what a sender timeout feels like from INSIDE the receiver:
            # you finally have an answer and there is nobody left to give it to.
            print("  [receiver] finished, but the sender already hung up - our 200 goes nowhere")

    def log_message(self, *args):
        pass


def deliver(base: str, path: str, event: dict):
    """A sender with a real timeout, like every provider has."""
    request = urllib.request.Request(
        base + path,
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=SENDER_TIMEOUT) as response:
            return response.status, (time.perf_counter() - started)
    except (urllib.error.URLError, TimeoutError):
        return None, (time.perf_counter() - started)  # None = "no answer in time"


def demo(base: str) -> None:
    event = {"type": "video.uploaded", "id": "evt_1", "data": {}}

    # --- the anti-pattern: the sender gives up, then retries ---
    status, elapsed = deliver(base, "/slow", event)
    print(f"POST /slow     -> timed out after {elapsed:.2f}s (no status at all: {status})")
    assert status is None
    status, _ = deliver(base, "/slow", event)  # the retry any sender would make
    print("POST /slow     -> timed out again; the work has now run TWICE for one event")
    assert status is None

    # --- the pattern: ACK first, work in the background ---
    status, elapsed = deliver(base, "/fast-ack", event)
    print(f"POST /fast-ack -> {status} in {elapsed:.3f}s   (202 = accepted, not finished)")
    assert status == 202
    assert elapsed < SENDER_TIMEOUT, "the ACK must be far faster than the sender's timeout"

    work_queue.join()  # let the background worker finish, purely so we can assert
    time.sleep(SLOW_WORK + 0.3)  # and let the two abandoned /slow calls finish too

    with done_lock:
        print(f"slow-handler runs: {len(slow_handler_runs)}   (one event, processed twice - duplicate work)")
        print(f"background worker runs: {len(worker_runs)}   (one event, processed once)")
        assert len(slow_handler_runs) == 2
        assert worker_runs == ["evt_1"]
    print("OK")


if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
