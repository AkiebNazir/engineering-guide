"""
LAB 01 (basic) - SOAP without any SOAP library: build an envelope, POST it, read the response and the Fault
===========================================================================================================
SOAP looks intimidating; on the wire it is just XML inside an HTTP POST.
You will learn
  * the anatomy of a SOAP 1.1 message:

        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">   <- namespaces matter!
          <soap:Header> ... optional: security, correlation ids, routing ... </soap:Header>
          <soap:Body>
            <GetBalance xmlns="http://bank.example.com/ws">        <- ONE element: the operation
              <accountId>ACC-1001</accountId>
            </GetBalance>
          </soap:Body>
        </soap:Envelope>

  * the HTTP side: POST, Content-Type: text/xml; charset=utf-8, and a SOAPAction header
  * XML NAMESPACES: <a:x> and <b:x> are different elements. Parsing without namespaces is the #1 SOAP bug.
  * a FAULT: SOAP 1.1 reports errors as <soap:Fault> inside a normal envelope, with HTTP status 500
  * parsing with ElementTree, namespace-aware, and turning a Fault into a Python exception
  * why XML text must be ESCAPED (never build XML with f-strings from user input: injection!)

Needs   nothing (standard library only)
Run it  python 01_envelope_and_fault_by_hand.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from xml.sax.saxutils import escape

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
BANK_NS = "http://bank.example.com/ws"
NS = {"soap": SOAP_NS, "b": BANK_NS}
ET.register_namespace("soap", SOAP_NS)

ACCOUNTS = {"ACC-1001": "1042.50", "ACC-2002": "87.10"}


# ============================================================ a tiny SOAP server ==
class BankHandler(BaseHTTPRequestHandler):
    """Just enough server to talk to. Lab 02 builds a proper one."""

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        print(f"  [server] received SOAPAction={self.headers.get('SOAPAction')} Content-Type={self.headers['Content-Type']}")
        try:
            request = ET.fromstring(body)
            op = request.find("soap:Body/b:GetBalance", NS)
            if op is None:
                return self.fault(400, "soap:Client", "Unknown operation")
            account = (op.findtext("b:accountId", namespaces=NS) or "").strip()
            if account not in ACCOUNTS:
                return self.fault(500, "soap:Client", f"No such account: {account}")
            self.reply(200, f'<GetBalanceResponse xmlns="{BANK_NS}"><balance>{ACCOUNTS[account]}</balance>'
                            f'<currency>EUR</currency></GetBalanceResponse>')
        except ET.ParseError:
            self.fault(400, "soap:Client", "Malformed XML")

    def reply(self, status, inner):
        envelope = f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="{SOAP_NS}"><soap:Body>{inner}</soap:Body></soap:Envelope>'
        data = envelope.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def fault(self, status, code, message):
        self.reply(status, f"<soap:Fault><faultcode>{code}</faultcode><faultstring>{escape(message)}</faultstring></soap:Fault>")

    def log_message(self, *a):
        pass


# ================================================================ the client ======
class SoapFault(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


def build_envelope(operation: str, params: dict[str, str]) -> bytes:
    # ESCAPE every value. f-string concatenation of raw input is XML injection.
    inner = "".join(f"<{k}>{escape(v)}</{k}>" for k, v in params.items())
    return (f'<?xml version="1.0" encoding="utf-8"?>'
            f'<soap:Envelope xmlns:soap="{SOAP_NS}"><soap:Body>'
            f'<{operation} xmlns="{BANK_NS}">{inner}</{operation}>'
            f'</soap:Body></soap:Envelope>').encode()


def call(url: str, operation: str, params: dict[str, str]) -> ET.Element:
    req = urllib.request.Request(url, data=build_envelope(operation, params), headers={
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": f'"{BANK_NS}/{operation}"',            # quotes are part of the SOAP 1.1 convention
    })
    try:
        raw = urllib.request.urlopen(req, timeout=5).read()
    except urllib.error.HTTPError as e:
        raw = e.read()                                        # faults arrive with HTTP 500 but a valid envelope body
    root = ET.fromstring(raw)
    fault = root.find("soap:Body/soap:Fault", NS)
    if fault is not None:
        raise SoapFault(fault.findtext("faultcode"), fault.findtext("faultstring"))
    return root.find("soap:Body", NS)[0]                      # the response element


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 0), BankHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/bank"

    print("== 1. the request on the wire ==")
    request_xml = build_envelope("GetBalance", {"accountId": "ACC-1001"})
    import xml.dom.minidom
    print(xml.dom.minidom.parseString(request_xml).toprettyxml(indent="  ").replace('<?xml version="1.0" ?>\n', ""))
    print("  ... POST with headers: Content-Type: text/xml; charset=utf-8   SOAPAction: \"http://bank.example.com/ws/GetBalance\"")

    print("\n== 2. a successful call ==")
    resp = call(url, "GetBalance", {"accountId": "ACC-1001"})
    balance = resp.findtext("b:balance", namespaces=NS)
    print("  response element:", resp.tag)
    print("  balance:", balance, resp.findtext("b:currency", namespaces=NS))
    assert balance == "1042.50"

    print("\n== 3. the SAME element name in the WRONG namespace is a different element ==")
    wrong = ET.fromstring(f'<GetBalanceResponse xmlns="http://evil.example.com"><balance>1</balance></GetBalanceResponse>')
    print("  find('b:balance') in the wrong namespace ->", wrong.find("b:balance", NS))
    print("  find('balance') without a namespace      ->", wrong.find("balance"), "(also None: the tag is '{ns}balance')")
    assert wrong.find("b:balance", NS) is None and wrong.find("balance") is None
    print("  => always search with the namespace, or you will 'randomly' find nothing.")

    print("\n== 4. a SOAP Fault becomes an exception ==")
    for label, account in [("unknown account", "ACC-9999"), ("XML injection attempt", "</accountId><evil/>")]:
        try:
            call(url, "GetBalance", {"accountId": account})
        except SoapFault as e:
            print(f"  {label:<22} -> SoapFault({e.code!r}, {e.message[:50]!r})")
            assert e.code == "soap:Client"
    print("  (the injection attempt was escaped to &lt;/accountId&gt;..., so it stayed DATA and was just an unknown account)")

    print("\n== 5. what escaping does ==")
    print("  escape('</accountId><evil/>') ->", escape("</accountId><evil/>"))
    print("\nOK")
    server.shutdown()
