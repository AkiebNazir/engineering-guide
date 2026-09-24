"""
FOUNDATION LEVEL 06 - HTTP status codes in a SOAP world
===========================================================
SOAP rides HTTP, so every response still has a status code - but SOAP uses
almost none of them. REST spends its error vocabulary on status codes (400,
401, 403, 404, 409, 422, ...). SOAP spends it inside <soap:Fault> and leaves
HTTP with essentially two codes:

    HTTP 200  +  <Body><XxxResponse>   it worked
    HTTP 500  +  <Body><soap:Fault>    it did not (SOAP 1.1, ANY fault)

That is the whole convention, and it surprises everyone: a 500 from a SOAP
service usually means "you sent a bad account number", not "the server is on
fire". SOAP 1.2 softened it - a sender fault SHOULD be HTTP 400 - so real
clients must treat "4xx or 5xx" as "read the body, there is a Fault in it".

THE FULL PICTURE (what comes from where)
  200 + response body   success                        SOAP decides
  500 + Fault body      any fault, SOAP 1.1            SOAP decides
  400 + Fault body      sender fault, SOAP 1.2         SOAP decides
  404                   wrong URL                      the HTTP layer
  405                   GET on a SOAP endpoint         the HTTP layer
  415                   wrong Content-Type             the HTTP layer
  401/403               an HTTP-level auth proxy       the HTTP layer
  -> rule of thumb: if the response HAS an envelope, the envelope is the truth.
     If it does not, the request never reached the SOAP code at all.

You will learn
  * why a well-formed SOAP service returns 500 for a client's own mistake
  * the 1.1 (always 500) vs 1.2 (400 for sender faults) difference
  * which codes come from HTTP itself and never carry an envelope
  * that a SOAP client must always read the BODY of an error response
  * why SOAP does not need 404/409/422: the Fault's detail says it instead

Run it   python 06_http_status_codes_in_soap.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
SOAP12 = "http://www.w3.org/2003/05/soap-envelope"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("env", SOAP12)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "env": SOAP12, "t": TNS}

SOAP_CONTENT_TYPES = ("text/xml", "application/soap+xml")


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def build_fault(code: str, message: str) -> ET.Element:
    fault = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    return fault


def build_soap12_fault(message: str) -> bytes:
    """SOAP 1.2 renamed everything AND changed the recommended status code.

    Same idea, different spelling: Code/Value/Reason/Text instead of
    faultcode/faultstring, namespaced children, and Sender/Receiver instead of
    Client/Server. Shown here only so the 400-vs-500 difference is concrete.
    """
    envelope = ET.Element(f"{{{SOAP12}}}Envelope")
    fault = ET.SubElement(ET.SubElement(envelope, f"{{{SOAP12}}}Body"), f"{{{SOAP12}}}Fault")
    code = ET.SubElement(fault, f"{{{SOAP12}}}Code")
    ET.SubElement(code, f"{{{SOAP12}}}Value").text = "env:Sender"
    reason = ET.SubElement(fault, f"{{{SOAP12}}}Reason")
    ET.SubElement(reason, f"{{{SOAP12}}}Text").text = message
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def dispatch(raw: bytes) -> tuple[int, bytes]:
    operation = ET.fromstring(raw).find("soap:Body", NS)[0]
    local = operation.tag.split("}")[-1]

    if local == "Ping":
        response = ET.Element(f"{{{TNS}}}PingResponse")
        ET.SubElement(response, f"{{{TNS}}}message").text = "Pong"
        return 200, build_envelope(response)          # success: a plain 200

    if local == "BadRequest":
        # The CLIENT is at fault, and SOAP 1.1 still says HTTP 500. This is the
        # line that makes SOAP 500s so misleading in dashboards.
        return 500, build_envelope(build_fault("soap:Client", "you sent something wrong"))

    if local == "BadRequest12":
        return 400, build_soap12_fault("you sent something wrong")   # the 1.2 way

    if local == "Explode":
        # We really did break. SAME status code as the client's mistake above;
        # only <faultcode> tells the two apart. That is why level 12 retries on
        # soap:Server and never on soap:Client.
        return 500, build_envelope(build_fault("soap:Server", "database unavailable"))

    return 500, build_envelope(build_fault("soap:Client", f"unknown operation {local}"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # A SOAP endpoint takes POST only. A GET never reaches the SOAP code, so
        # there is no envelope to send back - this is pure HTTP.
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.end_headers()

    def do_POST(self):
        if self.path != "/soap":
            self.send_response(404)     # pure HTTP: wrong address
            self.end_headers()
            return

        content_type = self.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type not in SOAP_CONTENT_TYPES:
            self.send_response(415)     # pure HTTP: "I do not speak that format"
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        status, out = dispatch(self.rfile.read(length))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def post(url: str, operation: str, content_type: str = "text/xml; charset=utf-8") -> tuple[int, bytes]:
    raw = build_envelope(ET.Element(f"{{{TNS}}}{operation}"))
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def has_envelope(raw: bytes) -> bool:
    """The rule that makes a SOAP client robust: is there an envelope at all?"""
    try:
        return ET.fromstring(raw).tag.endswith("Envelope")
    except ET.ParseError:
        return False


def fault_code(raw: bytes) -> str | None:
    envelope = ET.fromstring(raw)
    fault11 = envelope.find("soap:Body/soap:Fault/faultcode", NS)
    if fault11 is not None:
        return fault11.text
    return envelope.findtext("env:Body/env:Fault/env:Code/env:Value", namespaces=NS)


def demo(base: str) -> None:
    url = f"{base}/soap"

    print("== 1. codes the SOAP layer chooses (every one carries an envelope) ==")
    for label, operation, expected_status, expected_code in [
        ("success", "Ping", 200, None),
        ("client's fault (1.1)", "BadRequest", 500, "soap:Client"),
        ("client's fault (1.2)", "BadRequest12", 400, "env:Sender"),
        ("server's fault", "Explode", 500, "soap:Server"),
        ("unknown operation", "Nope", 500, "soap:Client"),
    ]:
        status, raw = post(url, operation)
        code = fault_code(raw) if status != 200 else None
        print(f"  {label:<21} -> HTTP {status}  envelope={has_envelope(raw)}  faultcode={code}")
        assert status == expected_status and code == expected_code and has_envelope(raw)

    print("\n== 2. codes the HTTP layer chooses (NO envelope: never reached SOAP) ==")
    status, raw = post(url, "Ping", content_type="application/json")
    print(f"  wrong Content-Type    -> HTTP {status}  envelope={has_envelope(raw)}")
    assert status == 415 and not has_envelope(raw)

    status, raw = post(f"{base}/wrong-url", "Ping")
    print(f"  wrong URL             -> HTTP {status}  envelope={has_envelope(raw)}")
    assert status == 404 and not has_envelope(raw)

    try:
        urllib.request.urlopen(url)   # a GET, not a POST
        raise AssertionError("expected 405")
    except urllib.error.HTTPError as e:
        print(f"  GET instead of POST   -> HTTP {e.code}  Allow: {e.headers.get('Allow')}")
        assert e.code == 405

    print("\n== 3. the takeaway a client must implement ==")
    print("  1) never trust the status code alone - 500 usually means YOUR mistake")
    print("  2) if the body parses as an Envelope, the Fault inside it is the real error")
    print("  3) if it does not, the request never got past HTTP (bad URL/verb/content type)")
    print("  4) retry on soap:Server / env:Receiver only - see level 12")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
