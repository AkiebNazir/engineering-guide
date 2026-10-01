"""
FOUNDATION LEVEL 12 - Being the client: calling a SOAP service properly
===========================================================================
Levels 00-11 were all SERVER code. In real work you far more often CONSUME a
SOAP service than write one - SOAP is the protocol of other people's legacy
systems. So this level flips the lens: a small server plays "the vendor's
service" (a cut-down level 11, plus a deliberately flaky operation), and the
interesting code is the client calling it.

A CHOICE, EXPLAINED: this file keeps hand-rolling the envelope with urllib +
xml.etree instead of using `zeep`, the real Python SOAP client. Two reasons:
the retry/fault logic below is the actual lesson and zeep would hide it, and
every other file in Foundation is stdlib-only, so nothing here needs installing.
zeep's real value is generating everything from a WSDL and it gets a whole lab
of its own - ../../labs/python/03_zeep_client_from_wsdl.py. Use zeep at work;
read this to know what it is doing for you.

THE RULE THAT MATTERS: never retry blindly. Level 05 built the distinction, and
this is what it was for:
    soap:Client  -> your message is wrong. Retrying it unchanged will fail
                    identically, forever. Fix the message or give up.
    soap:Server  -> the service failed. A retry may well succeed.
    no envelope  -> you never reached the SOAP code at all (timeout, refused
                    connection, 404, 415). Retry only if it was transient.

You will learn
  * a reusable "call one operation" client function, and why it returns the
    Fault rather than raising a bare urllib error
  * turning a <soap:Fault> into a real Python exception carrying its detail
  * retry with EXPONENTIAL BACKOFF on soap:Server, and never on soap:Client
  * treating a timeout and a fault as two different failure kinds
  * why a retried CreateOrder can create two orders, and what to do about it

Run it   python 12_being_a_client.py
"""
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/orders"
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "t": TNS}

ATTEMPTS = {"GetStatus": 0, "Flaky": 0}


# ============================ "the vendor's service" =========================
# Deliberately thin - it exists only to give the client something to talk to.
def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def build_fault(code: str, message: str, detail_name: str | None = None, **detail: str) -> bytes:
    fault = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    if detail_name:
        named = ET.SubElement(ET.SubElement(fault, "detail"), f"{{{TNS}}}{detail_name}")
        for key, value in detail.items():
            ET.SubElement(named, f"{{{TNS}}}{key}").text = value
    return build_envelope(fault)


class VendorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        operation = ET.fromstring(self.rfile.read(length)).find("soap:Body", NS)[0]
        local = operation.tag.split("}")[-1]

        if local == "GetStatus":
            ATTEMPTS["GetStatus"] += 1
            response = ET.Element(f"{{{TNS}}}GetStatusResponse")
            ET.SubElement(response, f"{{{TNS}}}status").text = "UP"
            status, out = 200, build_envelope(response)

        elif local == "Flaky":
            # Fails twice with a SERVER fault, then works - a service restarting
            # or briefly overloaded, not actually broken.
            ATTEMPTS["Flaky"] += 1
            if ATTEMPTS["Flaky"] <= 2:
                status, out = 500, build_fault("soap:Server", "database connection pool exhausted")
            else:
                response = ET.Element(f"{{{TNS}}}FlakyResponse")
                ET.SubElement(response, f"{{{TNS}}}result").text = "finally"
                status, out = 200, build_envelope(response)

        elif local == "CreateOrder":
            status, out = 500, build_fault("soap:Client", "quantity must be at least 1",
                                           "InvalidValue", element="quantity")
        elif local == "Slow":
            time.sleep(1.5)                       # longer than the client's timeout
            status, out = 200, build_envelope(ET.Element(f"{{{TNS}}}SlowResponse"))
        else:
            status, out = 500, build_fault("soap:Client", f"unknown operation {local}")

        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


# ================================ THE CLIENT =================================
class SoapFault(Exception):
    """A <soap:Fault> as a Python exception, with the parts a caller needs to
    make a decision: the code (retry or not) and the detail (which error)."""

    def __init__(self, code: str, message: str, detail_name: str | None):
        super().__init__(f"{code}: {message}")
        self.code, self.message, self.detail_name = code, message, detail_name

    @property
    def retryable(self) -> bool:
        # THE decision, in one place. soap:Server / env:Receiver = the service
        # failed; anything else is our own message being wrong.
        return self.code.split(":")[-1] in ("Server", "Receiver")


def call_once(url: str, operation: str, timeout: float = 1.0, **params: str) -> ET.Element:
    """POST one operation and return the response element, or raise SoapFault.

    Note that a fault arrives as an HTTP 500 WITH a body (level 06), so the
    error branch must read that body - throwing the HTTPError away loses the
    entire error message.
    """
    element = ET.Element(f"{{{TNS}}}{operation}")
    for name, value in params.items():
        ET.SubElement(element, f"{{{TNS}}}{name}").text = str(value)

    request = urllib.request.Request(
        url, data=build_envelope(element),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            # Many servers dispatch on SOAPAction instead of the body element,
            # and some reject the request outright if it is missing.
            "SOAPAction": f'"{TNS}/{operation}"',
        })

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            envelope = ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        envelope = ET.fromstring(e.read())     # the fault is IN here

    fault = envelope.find("soap:Body/soap:Fault", NS)
    if fault is not None:
        detail = fault.find("detail", NS)
        raise SoapFault(
            fault.findtext("faultcode", default=""),
            fault.findtext("faultstring", default=""),
            detail[0].tag.split("}")[-1] if detail is not None and len(detail) else None)

    return envelope.find("soap:Body", NS)[0]


def call_with_retries(url: str, operation: str, max_attempts: int = 5, **params: str) -> ET.Element:
    """Retry only what is worth retrying, waiting longer each time."""
    for attempt in range(1, max_attempts + 1):
        try:
            return call_once(url, operation, **params)

        except SoapFault as fault:
            if not fault.retryable or attempt == max_attempts:
                raise                                   # soap:Client: give up immediately
            wait = 0.05 * 2 ** (attempt - 1)            # 0.05s, 0.1s, 0.2s, ...
            print(f"  attempt {attempt}: {fault.code} - retrying in {wait:.2f}s")
            time.sleep(wait)

        except (urllib.error.URLError, TimeoutError) as exc:
            # No envelope came back at all: a timeout or a refused connection.
            # Same backoff idea, but we know NOTHING about whether the server
            # already did the work - see the closing note about idempotency.
            if attempt == max_attempts:
                raise
            print(f"  attempt {attempt}: no response ({type(exc).__name__}) - backing off")
            time.sleep(0.05 * 2 ** (attempt - 1))

    raise RuntimeError("unreachable")


def demo(url: str) -> None:
    print("== 1. the happy path ==")
    response = call_with_retries(url, "GetStatus")
    print(f"  GetStatus -> <{response.tag.split('}')[-1]}> status="
          f"{response.findtext('t:status', namespaces=NS)}")
    assert response.findtext("t:status", namespaces=NS) == "UP"
    assert ATTEMPTS["GetStatus"] == 1, "a successful call must not be retried"

    print("\n== 2. a soap:Server fault IS worth retrying ==")
    response = call_with_retries(url, "Flaky")
    print(f"  Flaky -> {response.findtext('t:result', namespaces=NS)!r} "
          f"after {ATTEMPTS['Flaky']} attempts")
    assert response.findtext("t:result", namespaces=NS) == "finally"
    assert ATTEMPTS["Flaky"] == 3, "expected 2 failures then 1 success"

    print("\n== 3. a soap:Client fault is NOT - fail fast, do not hammer ==")
    before = time.perf_counter()
    try:
        call_with_retries(url, "CreateOrder", quantity="0")
        raise AssertionError("expected a fault")
    except SoapFault as fault:
        elapsed = time.perf_counter() - before
        print(f"  CreateOrder -> {fault.code} <{fault.detail_name}> {fault.message!r}")
        print(f"  gave up after {elapsed * 1000:.1f}ms with NO retries "
              "(the same message would fail the same way forever)")
        assert fault.detail_name == "InvalidValue" and not fault.retryable
        assert elapsed < 0.2

    print("\n== 4. no answer at all is a different failure kind ==")
    try:
        call_once(url, "Slow", timeout=0.2)
        raise AssertionError("expected a timeout")
    except (TimeoutError, urllib.error.URLError) as exc:
        print(f"  Slow (timeout 0.2s) -> {type(exc).__name__}   (no envelope: nothing to parse)")

    print("\n== 5. the warning that goes with every retry loop ==")
    print("  a retried CreateOrder can create the order TWICE: the first attempt")
    print("  may have succeeded and only the RESPONSE been lost. Fix it by sending")
    print("  a client-generated id (wsa:MessageID, level 07) the server remembers,")
    print("  so the second attempt returns the FIRST attempt's answer instead of")
    print("  doing the work again - see ../../labs/golang/03_client_timeouts_faults_retries.")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), VendorHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/orders")
    server.shutdown()
