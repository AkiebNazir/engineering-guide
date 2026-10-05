"""
LAB 02 (basic) - A SOAP service with a generated WSDL: operations, types, validation and faults with detail
===========================================================================================================
You will learn
  * SOAP is CONTRACT-FIRST. The WSDL (Web Services Description Language) document describes the whole
    service in machine-readable XML, and tools generate clients from it. Its five parts:

        <types>     the XML Schema of every message         (what the data looks like)
        <message>   named request / response payloads        (which types travel)
        <portType>  the operations                            (the abstract interface: "what")
        <binding>   SOAP + HTTP + document/literal details    (the concrete protocol: "how")
        <service>   the endpoint URL                          (the address: "where")

  * DOCUMENT/LITERAL WRAPPED - the style every modern service uses: the Body has ONE element named
    after the operation, whose children are the parameters.
  * how a server DISPATCHES: look at the first child of <soap:Body> (or the SOAPAction header)
  * validating input against the contract: missing / extra / badly typed elements => a Client fault
  * fault design: faultcode says WHO is at fault  (Client = you sent something wrong, Server = we broke)
    and <detail> carries a machine-readable business error (InsufficientFunds) clients can catch
  * serving the WSDL at  ?wsdl  so clients (and Lab 03's zeep) can generate themselves from it

Needs   nothing (standard library only)
Run it  python 02_soap_server_and_wsdl.py
Serve   python 02_soap_server_and_wsdl.py --serve      (WSDL at http://localhost:8080/bank?wsdl)
"""
import sys
import threading
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from xml.sax.saxutils import escape

SOAP, TNS = "http://schemas.xmlsoap.org/soap/envelope/", "http://bank.example.com/ws"
XSD, WSDL, WSDL_SOAP = "http://www.w3.org/2001/XMLSchema", "http://schemas.xmlsoap.org/wsdl/", "http://schemas.xmlsoap.org/wsdl/soap/"
NS = {"soap": SOAP, "t": TNS}


# ----------------------------------------------------------------- the contract ----
@dataclass
class Operation:
    name: str
    inputs: list[tuple[str, str]]          # (element name, xsd type)
    outputs: list[tuple[str, str]]
    handler: Callable[..., dict]


class BusinessFault(Exception):
    """An expected failure the CLIENT should be able to catch by name."""

    def __init__(self, code: str, message: str, detail_name: str, detail: dict[str, str]):
        super().__init__(message)
        self.code, self.message, self.detail_name, self.detail = code, message, detail_name, detail


BALANCES = {"ACC-1001": Decimal("1042.50"), "ACC-2002": Decimal("87.10")}
_tx = iter(range(1, 10 ** 6))


def get_balance(accountId: str) -> dict:
    if accountId not in BALANCES:
        raise BusinessFault("soap:Client", f"No such account: {accountId}", "AccountNotFound", {"accountId": accountId})
    return {"balance": str(BALANCES[accountId]), "currency": "EUR"}


def transfer(fromAccount: str, toAccount: str, amount: Decimal) -> dict:
    for a in (fromAccount, toAccount):
        if a not in BALANCES:
            raise BusinessFault("soap:Client", f"No such account: {a}", "AccountNotFound", {"accountId": a})
    if amount <= 0:
        raise BusinessFault("soap:Client", "Amount must be positive", "InvalidAmount", {"amount": str(amount)})
    if BALANCES[fromAccount] < amount:
        raise BusinessFault("soap:Client", "Insufficient funds", "InsufficientFunds",
                            {"available": str(BALANCES[fromAccount]), "requested": str(amount)})
    BALANCES[fromAccount] -= amount
    BALANCES[toAccount] += amount
    return {"transactionId": f"TX-{next(_tx):06d}", "status": "COMPLETED"}


OPERATIONS = {op.name: op for op in [
    Operation("GetBalance", [("accountId", "string")], [("balance", "decimal"), ("currency", "string")], get_balance),
    Operation("Transfer", [("fromAccount", "string"), ("toAccount", "string"), ("amount", "decimal")],
              [("transactionId", "string"), ("status", "string")], transfer),
]}


# ------------------------------------------------------------- WSDL generation ----
def build_wsdl(location: str) -> str:
    elements = "".join(
        f'<xsd:element name="{op.name}"><xsd:complexType><xsd:sequence>'
        + "".join(f'<xsd:element name="{n}" type="xsd:{t}"/>' for n, t in op.inputs)
        + f'</xsd:sequence></xsd:complexType></xsd:element>'
        f'<xsd:element name="{op.name}Response"><xsd:complexType><xsd:sequence>'
        + "".join(f'<xsd:element name="{n}" type="xsd:{t}"/>' for n, t in op.outputs)
        + '</xsd:sequence></xsd:complexType></xsd:element>' for op in OPERATIONS.values())
    messages = "".join(f'<message name="{op.name}Input"><part name="parameters" element="tns:{op.name}"/></message>'
                       f'<message name="{op.name}Output"><part name="parameters" element="tns:{op.name}Response"/></message>'
                       for op in OPERATIONS.values())
    port_ops = "".join(f'<operation name="{op.name}"><input message="tns:{op.name}Input"/><output message="tns:{op.name}Output"/></operation>'
                       for op in OPERATIONS.values())
    bind_ops = "".join(f'<operation name="{op.name}"><soap:operation soapAction="{TNS}/{op.name}"/>'
                       f'<input><soap:body use="literal"/></input><output><soap:body use="literal"/></output></operation>'
                       for op in OPERATIONS.values())
    return f'''<?xml version="1.0" encoding="utf-8"?>
<definitions name="BankService" targetNamespace="{TNS}" xmlns="{WSDL}" xmlns:soap="{WSDL_SOAP}"
             xmlns:xsd="{XSD}" xmlns:tns="{TNS}">
  <types><xsd:schema targetNamespace="{TNS}" elementFormDefault="qualified">{elements}</xsd:schema></types>
  {messages}
  <portType name="BankPortType">{port_ops}</portType>
  <binding name="BankBinding" type="tns:BankPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>{bind_ops}
  </binding>
  <service name="BankService"><port name="BankPort" binding="tns:BankBinding"><soap:address location="{location}"/></port></service>
</definitions>'''


# ------------------------------------------------------------------- the server ----
XSD_PARSERS = {"string": str, "decimal": Decimal}


def envelope(inner: str) -> bytes:
    return (f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="{SOAP}"><soap:Body>{inner}</soap:Body></soap:Envelope>').encode()


def fault(code: str, message: str, detail: str = "") -> bytes:
    return envelope(f"<soap:Fault><faultcode>{code}</faultcode><faultstring>{escape(message)}</faultstring>"
                    + (f"<detail>{detail}</detail>" if detail else "") + "</soap:Fault>")


def dispatch(body: bytes) -> tuple[int, bytes]:
    """Parse the request, validate it against the contract, run the operation, build the response."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return 400, fault("soap:Client", "Malformed XML")
    soap_body = root.find("soap:Body", NS)
    if root.tag != f"{{{SOAP}}}Envelope" or soap_body is None or len(soap_body) != 1:
        return 400, fault("soap:Client", "Expected an Envelope with exactly one Body element")
    request = soap_body[0]
    ns, _, local = request.tag[1:].partition("}")
    op = OPERATIONS.get(local) if ns == TNS else None
    if op is None:
        return 500, fault("soap:Client", f"Unknown operation {request.tag}")

    args: dict[str, object] = {}
    for name, xsd_type in op.inputs:
        el = request.find(f"t:{name}", NS)
        if el is None or el.text is None:
            return 500, fault("soap:Client", f"Missing required element {name}")
        try:
            args[name] = XSD_PARSERS[xsd_type](el.text.strip())
        except InvalidOperation:
            return 500, fault("soap:Client", f"Element {name} must be a valid {xsd_type}")
    unexpected = {c.tag for c in request} - {f"{{{TNS}}}{n}" for n, _ in op.inputs}
    if unexpected:
        return 500, fault("soap:Client", f"Unexpected element(s): {sorted(unexpected)}")      # strict, like the schema

    try:
        result = op.handler(**args)
    except BusinessFault as e:
        detail = f'<t:{e.detail_name} xmlns:t="{TNS}">' + "".join(f"<t:{k}>{escape(v)}</t:{k}>" for k, v in e.detail.items()) + f"</t:{e.detail_name}>"
        return 500, fault(e.code, e.message, detail)                     # SOAP 1.1: faults use HTTP 500
    except Exception:
        return 500, fault("soap:Server", "Internal error")               # never leak stack traces
    out = "".join(f"<{k}>{escape(v)}</{k}>" for k, v in result.items())
    return 200, envelope(f'<{op.name}Response xmlns="{TNS}">{out}</{op.name}Response>')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("?wsdl") or self.path.endswith("?WSDL"):
            data = build_wsdl(f"http://{self.headers['Host']}/bank").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/xml; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 1_000_000:
            return self.send_error(413)
        status, data = dispatch(self.rfile.read(length))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def start(port: int = 0) -> HTTPServer:
    srv = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# --------------------------------------------------------------------- the demo ----
def post(url: str, xml: str) -> tuple[int, ET.Element]:
    import urllib.error
    req = urllib.request.Request(url, data=xml.encode(), headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req)
        return r.status, ET.fromstring(r.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def call(url, op, **params):
    inner = "".join(f"<{k}>{escape(str(v))}</{k}>" for k, v in params.items())
    return post(url, f'<soap:Envelope xmlns:soap="{SOAP}"><soap:Body><{op} xmlns="{TNS}">{inner}</{op}></soap:Body></soap:Envelope>')


if __name__ == "__main__":
    if "--serve" in sys.argv:
        srv = HTTPServer(("127.0.0.1", 8080), Handler)
        print("SOAP bank on http://localhost:8080/bank   WSDL: http://localhost:8080/bank?wsdl")
        srv.serve_forever()

    srv = start()
    url = f"http://127.0.0.1:{srv.server_port}/bank"

    print("== 1. the WSDL the server publishes (abridged) ==")
    wsdl = urllib.request.urlopen(url + "?wsdl").read().decode()
    root = ET.fromstring(wsdl)
    W = {"w": WSDL, "x": XSD, "s": WSDL_SOAP}
    print("  <types>    elements :", [e.get("name") for e in root.findall(".//x:schema/x:element", W)])
    print("  <message>  names    :", [m.get("name") for m in root.findall("w:message", W)])
    print("  <portType> ops      :", [o.get("name") for o in root.findall("w:portType/w:operation", W)])
    b = root.find("w:binding/s:binding", W)
    print(f"  <binding>  style={b.get('style')}, use=literal, soapAction per operation:",
          [o.find("s:operation", W).get("soapAction") for o in root.findall("w:binding/w:operation", W)])
    print("  <service>  address  :", root.find("w:service/w:port/s:address", W).get("location"))

    print("\n== 2. successful calls ==")
    status, resp = call(url, "GetBalance", accountId="ACC-1001")
    print("  GetBalance ->", status, {c.tag.split('}')[1]: c.text for c in resp.find("soap:Body", NS)[0]})
    assert status == 200
    status, resp = call(url, "Transfer", fromAccount="ACC-1001", toAccount="ACC-2002", amount="100.25")
    out = {c.tag.split('}')[1]: c.text for c in resp.find("soap:Body", NS)[0]}
    print("  Transfer   ->", status, out)
    assert status == 200 and out["status"] == "COMPLETED"
    assert BALANCES["ACC-1001"] == Decimal("942.25") and BALANCES["ACC-2002"] == Decimal("187.35")

    print("\n== 3. validation faults (the contract is enforced) ==")
    cases = [
        ("unknown operation", lambda: call(url, "DeleteEverything")),
        ("missing element", lambda: post(url, f'<soap:Envelope xmlns:soap="{SOAP}"><soap:Body><GetBalance xmlns="{TNS}"/></soap:Body></soap:Envelope>')),
        ("wrong type (amount=abc)", lambda: call(url, "Transfer", fromAccount="ACC-1001", toAccount="ACC-2002", amount="abc")),
        ("extra element", lambda: post(url, f'<soap:Envelope xmlns:soap="{SOAP}"><soap:Body><GetBalance xmlns="{TNS}"><accountId>ACC-1001</accountId><x>1</x></GetBalance></soap:Body></soap:Envelope>')),
    ]
    for label, thunk in cases:
        status, resp = thunk()
        f = resp.find("soap:Body/soap:Fault", NS)
        print(f"  {label:<26} -> HTTP {status}  {f.findtext('faultcode')}: {f.findtext('faultstring')[:60]}")
        assert status in (400, 500) and f.findtext("faultcode") == "soap:Client"

    print("\n== 4. business faults carry machine-readable <detail> ==")
    status, resp = call(url, "Transfer", fromAccount="ACC-2002", toAccount="ACC-1001", amount="5000")
    f = resp.find("soap:Body/soap:Fault", NS)
    d = f.find("detail")[0]
    print("  Transfer 5000 ->", f.findtext("faultstring"), "| detail:", d.tag.split("}")[1], {c.tag.split("}")[1]: c.text for c in d})
    assert d.tag == f"{{{TNS}}}InsufficientFunds"
    print("  a client can catch <InsufficientFunds> by NAME and show 'you have 187.35, you asked for 5000'")

    print("\n== 5. Client vs Server faults ==")
    from unittest import mock
    with mock.patch.dict(OPERATIONS["GetBalance"].__dict__, {"handler": lambda accountId: 1 / 0}):
        status, resp = call(url, "GetBalance", accountId="ACC-1001")
    f = resp.find("soap:Body/soap:Fault", NS)
    print(f"  a bug in the handler -> {f.findtext('faultcode')}: {f.findtext('faultstring')!r} (no stack trace leaked)")
    assert f.findtext("faultcode") == "soap:Server" and "ZeroDivision" not in ET.tostring(resp, encoding="unicode")
    print("  Client = 'you asked wrongly, do not retry as is'; Server = 'we failed, retrying may help'")
    print("\nOK")
    srv.shutdown()
