"""
FOUNDATION LEVEL 08 - Middleware: code that wraps every operation
=====================================================================
Levels 00-07 put everything an operation needed inside the dispatcher itself.
Middleware is a WRAPPER: a function that takes a dispatcher and returns a new
dispatcher which runs code before and/or after calling the original - without
touching the original's code at all.

In SOAP this pattern is even more valuable than in REST, because a SOAP
dispatcher is the ONE choke point for every operation in the service (one URL,
remember). Logging, authentication (level 09), authorization (level 10),
schema validation and tracing all get bolted on here, once, for fifty
operations at a time. Real stacks call these "handler chains" (Java JAX-WS) or
"plugins" (Python's zeep, on the client side).

The SOAP-specific twist: a crash inside an operation must come back out as a
<soap:Fault> with faultcode soap:Server. A dead connection or an HTML stack
trace page breaks every SOAP client in existence - they parse XML, and only XML.

You will learn
  * a middleware has the SAME shape as a dispatcher: bytes in, (status, bytes) out
  * chaining: wrapping a wrapper in a wrapper, in a chosen order
  * ORDER matters: logging OUTSIDE recovery still logs a crashed call;
    logging INSIDE it would never run
  * turning an unexpected Python exception into a clean soap:Server fault -
    the difference between "our service is broken" and "our service is down"
  * that one crashed operation must not take down the whole server

Run it   python 08_middleware_logging_and_recovery.py
"""
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "t": TNS}

# A dispatcher: raw request bytes -> (http status, raw response bytes).
Dispatcher = Callable[[bytes], tuple[int, bytes]]
Middleware = Callable[[Dispatcher], Dispatcher]

LOG: list[str] = []  # so the demo can assert on what the logger actually saw


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def fault_envelope(code: str, message: str) -> bytes:
    fault = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    return build_envelope(fault)


def operation_name(raw: bytes) -> str:
    """Peek at the operation name WITHOUT running it - what logging needs.

    A SOAP access log that only records "POST /soap 200" is useless: every
    request looks identical. The operation name lives in the XML, so the
    logging middleware has to crack the envelope open itself.
    """
    try:
        return ET.fromstring(raw).find("soap:Body", NS)[0].tag.split("}")[-1]
    except Exception:
        return "<unparseable>"


# ---- the "real" service logic, with zero knowledge of logging or recovery ----
def dispatch(raw: bytes) -> tuple[int, bytes]:
    operation = ET.fromstring(raw).find("soap:Body", NS)[0]
    local = operation.tag.split("}")[-1]

    if local == "Ping":
        response = ET.Element(f"{{{TNS}}}PingResponse")
        ET.SubElement(response, f"{{{TNS}}}message").text = "Pong"
        return 200, build_envelope(response)

    if local == "Boom":
        # A BUG, on purpose: an unhandled exception in the middle of an
        # operation, the way a real one would come from a null field or a
        # dropped database connection.
        raise RuntimeError("simulated bug: division by zero in pricing")

    return 500, fault_envelope("soap:Client", f"unknown operation {local}")


# ---- middleware #1: which operation, what outcome, how long ----
def with_logging(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(raw: bytes) -> tuple[int, bytes]:
        name = operation_name(raw)
        started = time.perf_counter()
        status, out = next_dispatch(raw)
        elapsed_ms = (time.perf_counter() - started) * 1000

        # Log the FAULTCODE, not just the status: level 06 showed that HTTP 500
        # alone cannot tell "your fault" from "our fault".
        code = ET.fromstring(out).findtext("soap:Body/soap:Fault/faultcode", namespaces=NS)
        line = f"{name} -> HTTP {status}{' ' + code if code else ''} ({elapsed_ms:.2f}ms)"
        LOG.append(line)
        print(f"  [log] {line}")
        return status, out
    return wrapped


# ---- middleware #2: any exception becomes a well-formed soap:Server fault ----
def with_recovery(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(raw: bytes) -> tuple[int, bytes]:
        try:
            return next_dispatch(raw)
        except Exception as exc:
            print(f"  [recovery] caught {exc!r} - one call becomes a Fault, the server stays up")
            # Deliberately generic text: never leak a stack trace or an
            # internal table name to a caller.
            return 500, fault_envelope("soap:Server", "internal error")
    return wrapped


# Built once, outside in. Logging is OUTSIDE recovery, so a crashed operation
# still produces a log line (recovery converts the crash into a real response
# before logging ever sees it). Swap the two and /Boom vanishes from the log -
# the single most common mistake in a handler chain.
pipeline: Dispatcher = with_logging(with_recovery(dispatch))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        status, out = pipeline(self.rfile.read(length))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def call(url: str, operation: str) -> tuple[int, ET.Element]:
    raw = build_envelope(ET.Element(f"{{{TNS}}}{operation}"))
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def demo(url: str) -> None:
    print("== 1. a normal call passes through both wrappers ==")
    status, envelope = call(url, "Ping")
    print(f"  Ping -> {status} {envelope.findtext('soap:Body/t:PingResponse/t:message', namespaces=NS)!r}")
    assert status == 200

    print("\n== 2. an operation that crashes ==")
    status, envelope = call(url, "Boom")
    code = envelope.findtext("soap:Body/soap:Fault/faultcode", namespaces=NS)
    message = envelope.findtext("soap:Body/soap:Fault/faultstring", namespaces=NS)
    print(f"  Boom -> {status} {code} {message!r}   (a Fault a client can parse, not a dead socket)")
    assert status == 500 and code == "soap:Server" and message == "internal error"
    assert "RuntimeError" not in ET.tostring(envelope, encoding="unicode"), "never leak internals"

    print("\n== 3. the server survived that crash ==")
    status, _ = call(url, "Ping")
    print(f"  Ping -> {status}   (still alive, still serving everyone else)")
    assert status == 200

    print("\n== 4. what the logging middleware recorded ==")
    for line in LOG:
        print(f"  {line}")
    assert len(LOG) == 3
    assert LOG[0].startswith("Ping -> HTTP 200")
    # THE POINT: the crashed call IS in the log, because logging wraps recovery.
    assert LOG[1].startswith("Boom -> HTTP 500 soap:Server")
    print("  -> the crash is in the log because logging wraps recovery, not the other way round")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
