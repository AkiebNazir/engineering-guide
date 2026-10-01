"""
FOUNDATION LEVEL 07 - Custom SOAP headers: metadata inside the envelope
===========================================================================
Level 01 left <soap:Header> empty. This is what it is for: elements that are
ABOUT the message rather than part of the request. Routing, correlation ids,
transaction ids, session tokens, timestamps - all of it goes in the Header, in
your own namespace, as ordinary XML.

SOAP HEADER vs HTTP HEADER - the distinction that justifies all this XML:
  an HTTP header dies at the next hop. The envelope does not. If a message
  travels HTTP -> message queue -> another HTTP call, the SOAP Header rides
  along untouched, and it can be signed as part of the document (WS-Security
  does exactly that - see ../../labs/python/04_ws_security_username_token.py).
  That is the "SOAP is transport-independent" claim, made concrete.

The industry standardised the obvious headers as WS-Addressing:
  <wsa:MessageID>  this message's unique id
  <wsa:To>         the intended destination
  <wsa:Action>     which operation (so infrastructure can route WITHOUT
                   parsing the Body - the point of the exercise below)
  <wsa:RelatesTo>  "this is the reply to MessageID X"

You will learn
  * putting your own elements in <soap:Header>, in your own namespace
  * reading the Header BEFORE the Body - the dispatcher's real order of work
  * a WS-Addressing-style MessageID / Action / RelatesTo round trip
  * why headers survive hops and re-transports when HTTP headers do not
  * mustUnderstand="1": "reject the whole message if you don't know this
    header" - the one header attribute worth knowing (labs cover it properly)

Run it   python 07_custom_soap_headers.py
"""
import threading
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
WSA = "http://www.w3.org/2005/08/addressing"     # the real WS-Addressing namespace
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("wsa", WSA)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "wsa": WSA, "t": TNS}

# Headers this service knows how to honour. Anything else marked
# mustUnderstand="1" must be rejected outright.
UNDERSTOOD = {f"{{{WSA}}}MessageID", f"{{{WSA}}}To", f"{{{WSA}}}Action", f"{{{TNS}}}TraceId"}


class Fault(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def build_envelope(body_child: ET.Element, header_children: list[ET.Element]) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    header = ET.SubElement(envelope, f"{{{SOAP}}}Header")
    for child in header_children:
        header.append(child)
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def build_fault(fault: Fault) -> ET.Element:
    element = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(element, "faultcode").text = fault.code
    ET.SubElement(element, "faultstring").text = fault.message
    return element


def header_element(qname: str, text: str) -> ET.Element:
    element = ET.Element(qname)
    element.text = text
    return element


def dispatch(raw: bytes) -> tuple[int, bytes]:
    try:
        envelope = ET.fromstring(raw)
        header = envelope.find("soap:Header", NS)
        header_children = list(header) if header is not None else []

        # ---- STEP 1: the Header, before we look at the Body at all ----
        # This is the real reason infrastructure likes SOAP headers: a router,
        # a logger or an auth gateway (levels 09-10) can do its whole job here
        # and never parse the payload.
        message_id = envelope.findtext("soap:Header/wsa:MessageID", namespaces=NS)
        action = envelope.findtext("soap:Header/wsa:Action", namespaces=NS)
        trace_id = envelope.findtext("soap:Header/t:TraceId", default="-", namespaces=NS)

        if message_id is None:
            raise Fault("soap:Client", "wsa:MessageID header is required")

        # mustUnderstand="1" means "fail loudly rather than silently ignore me".
        # Note the ATTRIBUTE is namespaced: soap:mustUnderstand, not mustUnderstand.
        for child in header_children:
            must = child.get(f"{{{SOAP}}}mustUnderstand")
            if must in ("1", "true") and child.tag not in UNDERSTOOD:
                raise Fault("soap:MustUnderstand",
                            f"header {child.tag} is marked mustUnderstand but this service does not know it")

        print(f"  [server] header read first: action={action} trace={trace_id} id={message_id[:8]}...")

        # ---- STEP 2: only now, the Body ----
        operation = envelope.find("soap:Body", NS)[0]
        if operation.tag != f"{{{TNS}}}Reserve":
            raise Fault("soap:Client", f"unknown operation {operation.tag}")
        if action is not None and action != f"{TNS}/Reserve":
            # The Action header and the Body element must agree, or someone is
            # routing this message somewhere it does not belong.
            raise Fault("soap:Client", f"wsa:Action {action} does not match the Body element")

        response = ET.Element(f"{{{TNS}}}ReserveResponse")
        ET.SubElement(response, f"{{{TNS}}}reservationId").text = "RES-77"

        # ---- STEP 3: answer WITH headers of our own ----
        # RelatesTo is how the caller matches this reply to its request - vital
        # once replies can come back out of order (or over a queue).
        return 200, build_envelope(response, [
            header_element(f"{{{WSA}}}RelatesTo", message_id),
            header_element(f"{{{TNS}}}TraceId", trace_id),
        ])

    except Fault as fault:
        return 500, build_envelope(build_fault(fault), [])


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        status, out = dispatch(self.rfile.read(length))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def post(url: str, raw: bytes) -> tuple[int, ET.Element]:
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def reserve(url: str, headers: list[ET.Element]) -> tuple[int, ET.Element]:
    operation = ET.Element(f"{{{TNS}}}Reserve")
    ET.SubElement(operation, f"{{{TNS}}}seat").text = "12A"
    return post(url, build_envelope(operation, headers))


def demo(url: str) -> None:
    message_id = f"urn:uuid:{uuid.uuid4()}"

    print("== 1. a request whose Header carries WS-Addressing metadata ==")
    status, envelope = reserve(url, [
        header_element(f"{{{WSA}}}MessageID", message_id),
        header_element(f"{{{WSA}}}To", url),
        header_element(f"{{{WSA}}}Action", f"{TNS}/Reserve"),
        header_element(f"{{{TNS}}}TraceId", "trace-abc"),
    ])
    print("  " + ET.tostring(envelope, encoding="unicode").replace("><", ">\n  <"))
    relates = envelope.findtext("soap:Header/wsa:RelatesTo", namespaces=NS)
    print(f"  -> HTTP {status}, the reply's wsa:RelatesTo == our MessageID: {relates == message_id}")
    assert status == 200 and relates == message_id
    assert envelope.findtext("soap:Header/t:TraceId", namespaces=NS) == "trace-abc"
    assert envelope.findtext("soap:Body/t:ReserveResponse/t:reservationId", namespaces=NS) == "RES-77"

    print("\n== 2. a required header missing -> fault, Body never even parsed ==")
    status, envelope = reserve(url, [header_element(f"{{{WSA}}}To", url)])
    print(f"  -> HTTP {status} {envelope.findtext('soap:Body/soap:Fault/faultstring', namespaces=NS)!r}")
    assert status == 500

    print("\n== 3. Action disagreeing with the Body element -> fault ==")
    status, envelope = reserve(url, [
        header_element(f"{{{WSA}}}MessageID", message_id),
        header_element(f"{{{WSA}}}Action", f"{TNS}/CancelEverything"),
    ])
    print(f"  -> HTTP {status} {envelope.findtext('soap:Body/soap:Fault/faultstring', namespaces=NS)!r}")
    assert status == 500

    print("\n== 4. mustUnderstand=\"1\" on a header we do not know ==")
    exotic = header_element("{http://vendor.example.com}QuantumPriority", "high")
    exotic.set(f"{{{SOAP}}}mustUnderstand", "1")
    status, envelope = reserve(url, [header_element(f"{{{WSA}}}MessageID", message_id), exotic])
    code = envelope.findtext("soap:Body/soap:Fault/faultcode", namespaces=NS)
    print(f"  -> HTTP {status} {code}   (ignoring it silently would be the dangerous choice)")
    assert status == 500 and code == "soap:MustUnderstand"

    print("\n== 5. the SAME header WITHOUT mustUnderstand is ignored happily ==")
    optional = header_element("{http://vendor.example.com}QuantumPriority", "high")
    status, envelope = reserve(url, [header_element(f"{{{WSA}}}MessageID", message_id), optional])
    print(f"  -> HTTP {status}   (unknown-but-optional headers are skipped, by design)")
    assert status == 200

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
