"""
FOUNDATION LEVEL 00 (start here) - A basic SOAP endpoint, explained end to end
=================================================================================
If someone says "build me a basic SOAP endpoint", THIS is what they mean: one
HTTP server, one URL that accepts POSTs, one operation. A client posts an XML
document called an ENVELOPE; the server reads which operation was asked for,
does the work, and posts back another envelope. Nothing about WSDL, namespaces,
faults or security yet - just enough to watch the whole loop happen once.

THE MENTAL MODEL (read this before the code)
  SOAP is "XML instead of JSON, riding the same plain HTTP you already know".
  There is no magic transport. It is still:
      POST /soap HTTP/1.1  +  a body of bytes  ->  200 OK  +  a body of bytes
  The only differences from a REST call are:
    - the body is always an XML <Envelope>, never bare JSON
    - the URL does NOT say what you want: ONE url serves every operation, and
      the operation name is the first element INSIDE the envelope's <Body>
      (so the server DISPATCHES on XML content, not on the path or the verb)
  Level 13 proves the "plain HTTP" claim by typing a whole envelope over a
  bare TCP socket with no libraries at all.

You will learn
  * the anatomy of a SOAP envelope at a glance: Envelope > Body > <OperationName>
  * that one SOAP endpoint = one URL + one HTTP verb (POST), always
  * how a server dispatches: look at the name of the first child of <Body>
  * that a SOAP response is just another envelope, whose Body holds
    <OperationName>Response
  * that SOAP still obeys plain HTTP rules underneath - a wrong URL is a
    plain old 404, nothing SOAP-ish about it

Run it        python 00_single_operation_and_how_it_works.py
Keep serving  python 00_single_operation_and_how_it_works.py --serve   (curl hint is printed on start)
"""
import sys
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Two namespaces, and you cannot avoid them even at level 00 (level 04 explains
# WHY they exist). Read them as "vocabularies":
#   SOAP = the envelope vocabulary, identical for every SOAP service on earth
#   TNS  = OUR service's own vocabulary ("target namespace"), our operations
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"

# ElementTree writes tags as "{namespace}local". register_namespace only makes
# the OUTPUT prettier ("soap:Envelope" instead of "ns0:Envelope") - it changes
# no meaning at all.
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)

NS = {"soap": SOAP, "t": TNS}  # the prefix->namespace map ET's find() needs


def build_envelope(body_child: ET.Element) -> bytes:
    """Wrap one operation element in Envelope > Body. This is THE whole trick."""
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP}}}Body")
    body.append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def dispatch(raw: bytes) -> bytes:
    """The SOAP part of a SOAP server, in ten lines.

    Parse the envelope, find the ONE element inside <Body>, and switch on its
    name. That element's name IS the operation - there is no route table.
    """
    envelope = ET.fromstring(raw)
    body = envelope.find("soap:Body", NS)
    operation = body[0]  # the first (and here only) child of Body

    # operation.tag is the fully qualified name, e.g.
    # "{http://foundation.example.com/soap}Ping" - namespace AND local name.
    if operation.tag == f"{{{TNS}}}Ping":
        # By convention the answer to <Ping> is named <PingResponse>. Nothing
        # enforces that here; a WSDL (see ../../labs) would.
        response = ET.Element(f"{{{TNS}}}PingResponse")
        ET.SubElement(response, f"{{{TNS}}}message").text = "Pong"
        return build_envelope(response)

    # Unknown operation. The GROWN-UP answer is a <soap:Fault> (level 05); for
    # now we keep level 00 honest and tiny by refusing to invent one.
    raise ValueError(f"this endpoint has no operation named {operation.tag}")


class Handler(BaseHTTPRequestHandler):
    # Note there is no do_GET at all: a SOAP endpoint answers POST, and only
    # POST, because every request carries an XML document as its body.
    def do_POST(self):
        if self.path != "/soap":
            self.send_response(404)  # plain HTTP rules still apply, see level 06
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        out = dispatch(self.rfile.read(length))

        self.send_response(200)
        # "text/xml" is the SOAP 1.1 content type (1.2 uses application/soap+xml).
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass  # keep the demo output clean


def demo(base: str) -> None:
    # THE CLIENT. curl, a Java app, or zeep (level 12) all do exactly this:
    # build an envelope, POST it, parse the envelope that comes back.
    request_xml = build_envelope(ET.Element(f"{{{TNS}}}Ping"))
    print("---- request body we POST ----")
    print(request_xml.decode())

    http_request = urllib.request.Request(
        f"{base}/soap",
        data=request_xml,
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    with urllib.request.urlopen(http_request) as response:
        status, raw = response.status, response.read()

    print("---- response body we got back ----")
    print(raw.decode())

    envelope = ET.fromstring(raw)
    # Walk down the same three steps on the way out: Envelope > Body > operation.
    message = envelope.find("soap:Body/t:PingResponse/t:message", NS)

    print(f"HTTP status      : {status}   (SOAP success is a boring 200, see level 06)")
    print(f"parsed <message> : {message.text!r}")
    assert status == 200
    assert message is not None and message.text == "Pong"

    # Same server, wrong URL: SOAP adds nothing here. It is plain HTTP.
    bad = urllib.request.Request(f"{base}/nope", data=request_xml,
                                 headers={"Content-Type": "text/xml"})
    try:
        urllib.request.urlopen(bad)
        raise AssertionError("expected a 404")
    except urllib.error.HTTPError as e:
        print(f"POST /nope       : {e.code}   (a wrong URL is a normal HTTP 404, not a SOAP concept)")
        assert e.code == 404

    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/soap - try:\n")
        print("  curl -s -X POST localhost:8080/soap -H 'Content-Type: text/xml' -d \\\n"
              f"    '<soap:Envelope xmlns:soap=\"{SOAP}\"><soap:Body>"
              f"<Ping xmlns=\"{TNS}\"/></soap:Body></soap:Envelope>'\n")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

    # port 0 = "operating system, hand me any free port", so this demo never
    # collides with anything already listening on your machine.
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
