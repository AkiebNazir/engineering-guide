"""
FOUNDATION LEVEL 01 - Envelope anatomy: Header vs Body
==========================================================
Level 00 used only half the envelope. The full shape is fixed and tiny:

    <soap:Envelope>            the only legal root element
      <soap:Header>            OPTIONAL, at most one, MUST come first
        ...metadata...         who you are, trace ids, routing (levels 07-10)
      </soap:Header>
      <soap:Body>              REQUIRED, exactly one, MUST come last
        <TheOperation>...      the actual payload: what you are asking for
      </soap:Body>
    </soap:Envelope>

The split is the whole point of SOAP: BODY is the message for the final
recipient, HEADER is instructions for anyone handling the message along the
way (a gateway, a logger, an auth proxy). This level builds and parses both
explicitly, even though our Header is still empty - so that levels 07-10 are
"put something in the Header" rather than "learn a new concept".

You will learn
  * the four fixed parts of every SOAP message and their required order
  * Header is optional and Body is not - and how to reject a Body-less envelope
  * why metadata belongs in the Header, not as extra fields in the Body
  * that an EMPTY <soap:Header/> is perfectly legal and very common
  * how to read both halves of a message with one parse pass

Run it   python 01_envelope_header_and_body.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "t": TNS}


def build_envelope(body_child: ET.Element, header_children: list[ET.Element] | None = None) -> bytes:
    """Build a full envelope. Header FIRST, Body LAST - that order is required."""
    envelope = ET.Element(f"{{{SOAP}}}Envelope")

    # We always emit a Header element, even with nothing in it. That is legal,
    # it is what most real services do, and it leaves an obvious place for
    # level 07's routing headers and level 09's auth token to land.
    header = ET.SubElement(envelope, f"{{{SOAP}}}Header")
    for child in header_children or []:
        header.append(child)

    body = ET.SubElement(envelope, f"{{{SOAP}}}Body")
    body.append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def dispatch(raw: bytes) -> tuple[int, bytes]:
    envelope = ET.fromstring(raw)

    if envelope.tag != f"{{{SOAP}}}Envelope":
        return 400, b"not a SOAP envelope"

    # ---- read the HEADER half (metadata about the message) ----
    # .find() returns None for "absent", which is NOT an error: Header is optional.
    header = envelope.find("soap:Header", NS)
    header_children = list(header) if header is not None else []
    header_items = {child.tag.split("}")[-1]: (child.text or "") for child in header_children}
    print(f"  [server] header has {len(header_items)} element(s): {header_items or '{}'}")

    # ---- read the BODY half (the actual request) ----
    body = envelope.find("soap:Body", NS)
    if body is None or len(body) == 0:
        # Body is mandatory. A missing Body is a malformed message, and level 05
        # will upgrade this blunt 400 into a proper <soap:Fault>.
        return 400, b"envelope has no Body"

    operation = body[0]
    if operation.tag != f"{{{TNS}}}Echo":
        return 400, b"unknown operation"

    said = operation.findtext("t:text", default="", namespaces=NS)
    response = ET.Element(f"{{{TNS}}}EchoResponse")
    ET.SubElement(response, f"{{{TNS}}}text").text = said

    # The RESPONSE has the same two halves. Services commonly answer with a
    # header of their own - here a trace id, so the client can correlate logs.
    trace = ET.Element(f"{{{TNS}}}TraceId")
    trace.text = "trace-0001"
    return 200, build_envelope(response, [trace])


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


def post(url: str, raw: bytes) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def demo(url: str) -> None:
    echo = ET.Element(f"{{{TNS}}}Echo")
    ET.SubElement(echo, f"{{{TNS}}}text").text = "hello envelope"

    print("== 1. empty Header, one operation in the Body ==")
    status, raw = post(url, build_envelope(echo))
    envelope = ET.fromstring(raw)
    print(f"  -> {status}")
    print(f"  response Header : {[c.tag.split('}')[-1] for c in envelope.find('soap:Header', NS)]}")
    print(f"  response Body   : {envelope.find('soap:Body', NS)[0].tag}")
    assert status == 200
    assert envelope.findtext("soap:Body/t:EchoResponse/t:text", namespaces=NS) == "hello envelope"
    assert envelope.findtext("soap:Header/t:TraceId", namespaces=NS) == "trace-0001"

    print("\n== 2. a Header WITH metadata in it (a preview of levels 07-10) ==")
    caller = ET.Element(f"{{{TNS}}}CallerName")
    caller.text = "level-01-demo"
    status, raw = post(url, build_envelope(echo, [caller]))
    print(f"  -> {status}   (the Body was identical; only the metadata changed)")
    assert status == 200

    print("\n== 3. an envelope with NO Body is not a SOAP message at all ==")
    headless = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(headless, f"{{{SOAP}}}Header")
    status, raw = post(url, ET.tostring(headless))
    print(f"  -> {status} {raw!r}   (Header alone is meaningless: Body is mandatory)")
    assert status == 400

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
