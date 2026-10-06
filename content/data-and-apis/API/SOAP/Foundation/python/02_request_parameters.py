"""
FOUNDATION LEVEL 02 - Request parameters: how a caller passes arguments
==========================================================================
REST has three places to put an argument: the path, the query string, and the
body. SOAP has exactly ONE: child elements of the operation element inside the
Body. There is no `/orders/42`, no `?limit=10` - `<GetQuote>` simply carries
`<symbol>` and `<quantity>` inside it, and the URL never changes.

That single rule is why one SOAP endpoint can serve fifty operations from one
URL, and why the wire format stays readable: every argument is a named
element, never a positional one.

You will learn
  * "document/literal wrapped" - the universal shape: one wrapper element
    named after the operation, its children are the parameters
  * mapping XML child elements onto real Python arguments by name
  * that XML text is ALWAYS a string: every number, bool or date you receive
    has to be parsed, and that parse can fail
  * that element ORDER is part of the contract in XML (unlike JSON keys), even
    though a hand-written parser like ours does not care
  * how missing optional parameters differ from missing required ones

Run it   python 02_request_parameters.py
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

PRICES = {"ACME": 12.50, "GLOBEX": 340.00}


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def get_quote(symbol: str, quantity: int, currency: str) -> ET.Element:
    """The actual business logic - plain Python, no XML in sight.

    Keeping the operation a normal function with normal typed arguments is the
    whole reason the dispatcher below bothers to convert the XML first.
    """
    total = PRICES[symbol] * quantity
    response = ET.Element(f"{{{TNS}}}GetQuoteResponse")
    ET.SubElement(response, f"{{{TNS}}}total").text = f"{total:.2f}"
    ET.SubElement(response, f"{{{TNS}}}currency").text = currency
    return response


def dispatch(raw: bytes) -> tuple[int, bytes]:
    envelope = ET.fromstring(raw)
    operation = envelope.find("soap:Body", NS)[0]
    if operation.tag != f"{{{TNS}}}GetQuote":
        return 400, b"unknown operation"

    # ---- the parameter extraction step, element by element ----
    # findtext(None) distinguishes "the element was not sent at all" from
    # "it was sent empty" - a distinction JSON makes with null and SOAP makes
    # with element presence.
    symbol = operation.findtext("t:symbol", default=None, namespaces=NS)
    quantity_text = operation.findtext("t:quantity", default=None, namespaces=NS)

    # An OPTIONAL parameter: absent means "use the default", not "bad request".
    # In a real service the WSDL would say minOccurs="0" for exactly this.
    currency = operation.findtext("t:currency", default="EUR", namespaces=NS)

    if symbol is None or quantity_text is None:
        return 400, b"missing required parameter (symbol, quantity)"

    # XML carries TEXT. <quantity>3</quantity> is the string "3", and turning
    # it into an int is our job - and can fail on "three". Level 05 turns that
    # failure into a proper SOAP Fault instead of this blunt 400.
    try:
        quantity = int(quantity_text)
    except ValueError:
        return 400, b"quantity must be an integer"

    if symbol not in PRICES:
        return 400, b"unknown symbol"

    return 200, build_envelope(get_quote(symbol, quantity, currency))


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


def call_get_quote(url: str, **params: str) -> tuple[int, bytes]:
    """The client side of the same rule: one element per named parameter."""
    operation = ET.Element(f"{{{TNS}}}GetQuote")
    for name, value in params.items():
        ET.SubElement(operation, f"{{{TNS}}}{name}").text = str(value)
    return post(url, build_envelope(operation))


def demo(url: str) -> None:
    print("== 1. all parameters supplied ==")
    status, raw = post(url, build_envelope(ET.fromstring(
        f'<t:GetQuote xmlns:t="{TNS}">'
        "<t:symbol>ACME</t:symbol><t:quantity>4</t:quantity><t:currency>USD</t:currency>"
        "</t:GetQuote>")))
    envelope = ET.fromstring(raw)
    total = envelope.findtext("soap:Body/t:GetQuoteResponse/t:total", namespaces=NS)
    currency = envelope.findtext("soap:Body/t:GetQuoteResponse/t:currency", namespaces=NS)
    print(f"  GetQuote(ACME, 4, USD) -> {status} total={total} {currency}")
    assert (status, total, currency) == (200, "50.00", "USD")

    print("\n== 2. the OPTIONAL parameter left out entirely ==")
    status, raw = call_get_quote(url, symbol="GLOBEX", quantity="2")
    envelope = ET.fromstring(raw)
    currency = envelope.findtext("soap:Body/t:GetQuoteResponse/t:currency", namespaces=NS)
    print(f"  GetQuote(GLOBEX, 2)    -> {status} currency={currency}   (defaulted, not an error)")
    assert (status, currency) == (200, "EUR")

    print("\n== 3. a REQUIRED parameter left out ==")
    status, raw = call_get_quote(url, symbol="ACME")
    print(f"  GetQuote(ACME)         -> {status} {raw!r}")
    assert status == 400

    print("\n== 4. right element, wrong kind of text ==")
    status, raw = call_get_quote(url, symbol="ACME", quantity="three")
    print(f"  quantity='three'       -> {status} {raw!r}   (XML is text; parsing is YOUR job)")
    assert status == 400

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
