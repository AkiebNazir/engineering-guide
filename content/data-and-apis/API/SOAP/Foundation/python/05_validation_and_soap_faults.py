"""
FOUNDATION LEVEL 05 - Validation and <soap:Fault>: SOAP's own error channel
===============================================================================
Levels 01-04 answered bad input with a bare HTTP 400 and a plain-text string.
No SOAP client on earth understands that. SOAP defines exactly ONE error shape,
and it lives inside the envelope like everything else:

    <soap:Body>
      <soap:Fault>
        <faultcode>soap:Client</faultcode>     WHO is to blame
        <faultstring>Amount must be > 0</faultstring>   human-readable why
        <faultactor>...</faultactor>           optional: which node failed
        <detail>                               optional: MACHINE-readable why
          <t:InvalidAmount><t:field>amount</t:field></t:InvalidAmount>
        </detail>
      </soap:Fault>
    </soap:Body>

The two faultcodes that matter: `soap:Client` means "your message was wrong,
do not retry it unchanged", `soap:Server` means "we failed, retrying might
work". That single distinction is what level 12's retry logic keys off.

WATCH OUT: the Fault's children (faultcode, faultstring, detail) are NOT
namespaced in SOAP 1.1 - `<faultcode>`, never `<soap:faultcode>`. The VALUE of
faultcode, though, is a namespaced QName (`soap:Client`). It is a genuine wart.

You will learn
  * the exact <soap:Fault> shape, and why a fault travels in the Body
  * soap:Client vs soap:Server, and the retry decision that hangs off it
  * <detail> with a named child element, so clients can branch on the error
    KIND instead of regex-matching an English sentence
  * validating input up front and converting every failure into one fault
  * that a fault is a normal, expected outcome - not a crash (level 08)

Run it   python 05_validation_and_soap_faults.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "t": TNS}

BALANCES = {"ACC-1": Decimal("500.00")}


class Fault(Exception):
    """A fault the service raises on purpose. Carrying it as an exception keeps
    the validation code readable: check, raise, and let one place format it."""

    def __init__(self, code: str, message: str, detail_name: str | None = None, **detail: str):
        super().__init__(message)
        self.code, self.message, self.detail_name, self.detail = code, message, detail_name, detail


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def build_fault(fault: Fault) -> ET.Element:
    element = ET.Element(f"{{{SOAP}}}Fault")
    # UNQUALIFIED children - this is not a typo, it is the SOAP 1.1 spec.
    ET.SubElement(element, "faultcode").text = fault.code       # value IS a QName
    ET.SubElement(element, "faultstring").text = fault.message  # for a human
    if fault.detail_name:
        detail = ET.SubElement(element, "detail")
        named = ET.SubElement(detail, f"{{{TNS}}}{fault.detail_name}")
        for key, value in fault.detail.items():
            ET.SubElement(named, f"{{{TNS}}}{key}").text = str(value)
    return element


def withdraw(account: str, amount_text: str | None) -> ET.Element:
    """Validate everything first, then act. Every rejection is one raise."""
    if account is None or amount_text is None:
        raise Fault("soap:Client", "accountId and amount are both required",
                    "MissingElement", element="accountId|amount")
    try:
        amount = Decimal(amount_text)
    except InvalidOperation:
        raise Fault("soap:Client", f"amount is not a number: {amount_text!r}",
                    "InvalidAmount", field="amount", got=amount_text)
    if amount <= 0:
        raise Fault("soap:Client", "amount must be greater than zero",
                    "InvalidAmount", field="amount", got=str(amount))
    if account not in BALANCES:
        raise Fault("soap:Client", f"no such account: {account}",
                    "AccountNotFound", accountId=account)
    if BALANCES[account] < amount:
        # A BUSINESS fault: the message was perfectly well formed, the request
        # is simply not allowed. Still soap:Client - do not retry unchanged.
        raise Fault("soap:Client", "insufficient funds", "InsufficientFunds",
                    available=str(BALANCES[account]), requested=str(amount))

    BALANCES[account] -= amount
    response = ET.Element(f"{{{TNS}}}WithdrawResponse")
    ET.SubElement(response, f"{{{TNS}}}balance").text = str(BALANCES[account])
    return response


def dispatch(raw: bytes) -> tuple[int, bytes]:
    try:
        try:
            envelope = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise Fault("soap:Client", f"malformed XML: {exc}")

        body = envelope.find("soap:Body", NS)
        if body is None or len(body) != 1:
            raise Fault("soap:Client", "expected exactly one element inside soap:Body")

        operation = body[0]
        if operation.tag != f"{{{TNS}}}Withdraw":
            raise Fault("soap:Client", f"unknown operation {operation.tag}")

        response = withdraw(
            operation.findtext("t:accountId", default=None, namespaces=NS),
            operation.findtext("t:amount", default=None, namespaces=NS),
        )
        return 200, build_envelope(response)

    except Fault as fault:
        # SOAP 1.1 convention: a fault rides an HTTP 500, even when the CLIENT
        # is at fault. Level 06 lays out that whole status-code story.
        return 500, build_envelope(build_fault(fault))


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
        # A fault arrives as a 500 WITH a body. Never ignore the body of an
        # error response in SOAP: the body is the error.
        return e.code, ET.fromstring(e.read())


def withdraw_call(url: str, **params) -> tuple[int, ET.Element]:
    operation = ET.Element(f"{{{TNS}}}Withdraw")
    for name, value in params.items():
        ET.SubElement(operation, f"{{{TNS}}}{name}").text = str(value)
    return post(url, build_envelope(operation))


def read_fault(envelope: ET.Element) -> tuple[str, str, str | None]:
    fault = envelope.find("soap:Body/soap:Fault", NS)
    detail = fault.find("detail", NS)
    detail_name = detail[0].tag.split("}")[-1] if detail is not None and len(detail) else None
    return fault.findtext("faultcode"), fault.findtext("faultstring"), detail_name


def demo(url: str) -> None:
    print("== 1. a valid call, for contrast ==")
    status, envelope = withdraw_call(url, accountId="ACC-1", amount="100.00")
    balance = envelope.findtext("soap:Body/t:WithdrawResponse/t:balance", namespaces=NS)
    print(f"  Withdraw(ACC-1, 100.00) -> HTTP {status}, balance={balance}")
    assert (status, balance) == (200, "400.00")

    print("\n== 2. the full raw fault, once, so the shape is concrete ==")
    status, envelope = withdraw_call(url, accountId="ACC-1", amount="-5")
    print(f"  HTTP {status}")
    print("  " + ET.tostring(envelope, encoding="unicode").replace("><", ">\n  <"))

    print("\n== 3. every validation failure, as a fault ==")
    cases = [
        ("negative amount", dict(accountId="ACC-1", amount="-5"), "InvalidAmount"),
        ("not a number", dict(accountId="ACC-1", amount="ten"), "InvalidAmount"),
        ("unknown account", dict(accountId="ACC-9", amount="5"), "AccountNotFound"),
        ("too poor", dict(accountId="ACC-1", amount="9999"), "InsufficientFunds"),
        ("missing element", dict(accountId="ACC-1"), "MissingElement"),
    ]
    for label, params, expected_detail in cases:
        status, envelope = withdraw_call(url, **params)
        code, message, detail_name = read_fault(envelope)
        print(f"  {label:<16} -> HTTP {status}  {code:<12} <{detail_name}>  {message!r}")
        assert status == 500 and code == "soap:Client" and detail_name == expected_detail

    print("\n== 4. why <detail> matters: branch on the KIND, not on the English ==")
    status, envelope = withdraw_call(url, accountId="ACC-1", amount="9999")
    detail = envelope.find("soap:Body/soap:Fault/detail", NS)[0]
    fields = {c.tag.split("}")[-1]: c.text for c in detail}
    print(f"  caught <{detail.tag.split('}')[-1]}> with {fields}")
    print("  -> a client can show 'you have 400.00, you asked for 9999' without parsing prose")
    assert fields == {"available": "400.00", "requested": "9999"}

    print("\n== 5. malformed XML is a fault too, not a stack trace ==")
    status, envelope = post(url, b"<soap:Envelope><not-closed>")
    code, message, _ = read_fault(envelope)
    print(f"  garbage in -> HTTP {status}  {code}  {message[:40]!r}...")
    assert status == 500 and code == "soap:Client"

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
