"""
LAB 05 (advanced) - SOAP 1.1 vs 1.2, header processing rules (mustUnderstand), and version-tolerant code
========================================================================================================
Real integrations meet BOTH versions: 1.1 (2000) is still everywhere, 1.2 (2003, a W3C standard) is
what newer services and the WS-* stack use. You will see the exact differences in bytes, then build a
server that speaks both and a client that reads both.

                          SOAP 1.1                               SOAP 1.2
    Envelope namespace    .../soap/envelope/                     .../2003/05/soap-envelope
    HTTP Content-Type     text/xml; charset=utf-8                application/soap+xml; charset=utf-8; action="..."
    Action                separate SOAPAction HTTP header        `action` parameter of the Content-Type
    Fault structure       faultcode / faultstring / detail       Code>Value / Reason>Text / Detail
    Fault codes           Client, Server, VersionMismatch,       Sender, Receiver, VersionMismatch,
                          MustUnderstand                         MustUnderstand, DataEncodingUnknown
    HTTP status of fault  500 always                             400 for Sender faults, 500 for Receiver

You will learn
  * the HEADER PROCESSING MODEL - a core SOAP idea that REST does not have:
        a header block marked  mustUnderstand="1"  MUST be processed, or the receiver MUST fault.
        (Without it, an unknown header is silently ignored - which is right for optional extras but
        dangerous for things like security or transaction context.)
  * VersionMismatch: what to do when the envelope namespace is not one you speak
  * a server that detects the version from the envelope and answers IN THE SAME VERSION
  * a client-side fault parser that understands both shapes

Needs   nothing (standard library only)
Run it  python 05_soap_1_1_vs_1_2_and_mustunderstand.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from xml.sax.saxutils import escape

TNS = "http://bank.example.com/ws"
V11, V12 = "http://schemas.xmlsoap.org/soap/envelope/", "http://www.w3.org/2003/05/soap-envelope"
XML_NS = "http://www.w3.org/XML/1998/namespace"
UNDERSTOOD_HEADERS = {f"{{{TNS}}}CorrelationId"}                  # header blocks THIS service knows how to process


# --------------------------------------------------------------------- server ---
def envelope(version: str, inner: str, header: str = "") -> bytes:
    hdr = f"<soap:Header>{header}</soap:Header>" if header else ""
    return f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="{version}">{hdr}<soap:Body>{inner}</soap:Body></soap:Envelope>'.encode()


def make_fault(version: str, kind: str, message: str) -> tuple[int, bytes]:
    """kind: 'sender' | 'receiver' | 'mustunderstand' | 'versionmismatch'"""
    if version == V11:
        code = {"sender": "soap:Client", "receiver": "soap:Server", "mustunderstand": "soap:MustUnderstand", "versionmismatch": "soap:VersionMismatch"}[kind]
        return 500, envelope(V11, f"<soap:Fault><faultcode>{code}</faultcode><faultstring>{escape(message)}</faultstring></soap:Fault>")
    code = {"sender": "soap:Sender", "receiver": "soap:Receiver", "mustunderstand": "soap:MustUnderstand", "versionmismatch": "soap:VersionMismatch"}[kind]
    status = 400 if kind == "sender" else 500                   # 1.2 lets HTTP say who is at fault
    return status, envelope(V12, f'<soap:Fault><soap:Code><soap:Value>{code}</soap:Value></soap:Code>'
                                 f'<soap:Reason><soap:Text xml:lang="en">{escape(message)}</soap:Text></soap:Reason></soap:Fault>')


def handle(body: bytes) -> tuple[int, str, bytes]:
    """Returns (http status, content type, body)."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        s, b = make_fault(V11, "sender", "Malformed XML")
        return s, "text/xml; charset=utf-8", b
    ns = root.tag[1:].split("}")[0] if root.tag.startswith("{") else ""
    if root.tag not in (f"{{{V11}}}Envelope", f"{{{V12}}}Envelope"):
        # per spec: answer with a VersionMismatch fault, in SOAP 1.2 format, listing the versions we support
        s, b = make_fault(V12, "versionmismatch", f"Unsupported envelope namespace {ns!r}; supported: 1.1, 1.2")
        return s, "application/soap+xml; charset=utf-8", b
    version = ns
    ctype = "text/xml; charset=utf-8" if version == V11 else "application/soap+xml; charset=utf-8"
    must = f"{{{version}}}mustUnderstand"

    # ---- the header processing model ------------------------------------------------
    header = root.find(f"{{{version}}}Header")
    for block in (list(header) if header is not None else []):
        mandatory = block.get(must) in ("1", "true")
        if mandatory and block.tag not in UNDERSTOOD_HEADERS:
            s, b = make_fault(version, "mustunderstand", f"Mandatory header {block.tag} was not understood")
            return s, ctype, b
        # optional + unknown => ignore silently.  known => process it (here: echo the correlation id back)
    correlation = header.findtext(f"{{{TNS}}}CorrelationId") if header is not None else None

    op = root.find(f"{{{version}}}Body/{{{TNS}}}GetBalance")
    if op is None:
        s, b = make_fault(version, "sender", "Unknown operation")
        return s, ctype, b
    account = op.findtext(f"{{{TNS}}}accountId")
    if account != "ACC-1001":
        s, b = make_fault(version, "sender", f"No such account: {account}")
        return s, ctype, b
    reply_header = f'<c:CorrelationId xmlns:c="{TNS}">{escape(correlation)}</c:CorrelationId>' if correlation else ""
    return 200, ctype, envelope(version, f'<GetBalanceResponse xmlns="{TNS}"><balance>1042.50</balance></GetBalanceResponse>', reply_header)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        status, ctype, data = handle(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


# --------------------------------------------------------------------- client ---
def request_xml(version: str, account: str, header_blocks: str = "") -> bytes:
    hdr = f"<soap:Header>{header_blocks}</soap:Header>" if header_blocks else ""
    return (f'<soap:Envelope xmlns:soap="{version}">{hdr}<soap:Body><GetBalance xmlns="{TNS}">'
            f'<accountId>{escape(account)}</accountId></GetBalance></soap:Body></soap:Envelope>').encode()


def post(url: str, version: str, body: bytes) -> tuple[int, str, bytes]:
    if version == V11:
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f'"{TNS}/GetBalance"'}
    else:
        headers = {"Content-Type": f'application/soap+xml; charset=utf-8; action="{TNS}/GetBalance"'}        # no SOAPAction header!
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers))
        return r.status, r.headers["Content-Type"], r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers["Content-Type"], e.read()


def parse_fault(raw: bytes) -> tuple[str, str] | None:
    """Understands BOTH fault shapes. Returns (normalised kind, message) or None if it is not a fault."""
    root = ET.fromstring(raw)
    f11 = root.find(f"{{{V11}}}Body/{{{V11}}}Fault")
    if f11 is not None:
        code = (f11.findtext("faultcode") or "").split(":")[-1]
        return {"Client": "sender", "Server": "receiver"}.get(code, code.lower()), f11.findtext("faultstring") or ""
    f12 = root.find(f"{{{V12}}}Body/{{{V12}}}Fault")
    if f12 is not None:
        code = (f12.findtext(f"{{{V12}}}Code/{{{V12}}}Value") or "").split(":")[-1]
        return {"Sender": "sender", "Receiver": "receiver"}.get(code, code.lower()), f12.findtext(f"{{{V12}}}Reason/{{{V12}}}Text") or ""
    return None


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/bank"

    print("== 1. the same call in both versions ==")
    for name, v in (("SOAP 1.1", V11), ("SOAP 1.2", V12)):
        st, ct, raw = post(url, v, request_xml(v, "ACC-1001"))
        print(f"  {name}: HTTP {st}, response Content-Type: {ct}")
        print(f"          envelope ns: {ET.fromstring(raw).tag.split('}')[0][1:]}")
        assert st == 200 and ct.startswith("text/xml" if v == V11 else "application/soap+xml")
    print("  1.1 sends the action in a SOAPAction HTTP header; 1.2 moves it into the Content-Type `action=` parameter.")

    print("\n== 2. the same FAULT in both versions ==")
    for name, v in (("SOAP 1.1", V11), ("SOAP 1.2", V12)):
        st, ct, raw = post(url, v, request_xml(v, "ACC-0000"))
        kind, msg = parse_fault(raw)
        print(f"  {name}: HTTP {st}  ->  normalised by our parser: ({kind}, {msg!r})")
        assert kind == "sender" and st == (500 if v == V11 else 400)
    print("  1.1: always HTTP 500 and faultcode 'Client'.   1.2: HTTP 400 for the sender's mistake, code 'Sender'.")
    print("  Raw 1.2 fault body:")
    print("   ", post(url, V12, request_xml(V12, "ACC-0000"))[2].decode().split("<soap:Body>")[1].split("</soap:Body>")[0])

    print("\n== 3. mustUnderstand: the header processing model ==")
    scenarios = [
        ("known header, mandatory", f'<c:CorrelationId xmlns:c="{TNS}" soap:mustUnderstand="1">req-42</c:CorrelationId>', 200),
        ("UNKNOWN header, optional", f'<x:Audit xmlns:x="urn:acme:audit">trace</x:Audit>', 200),
        ("UNKNOWN header, MANDATORY", f'<x:Transaction xmlns:x="urn:acme:tx" soap:mustUnderstand="1">tx-9</x:Transaction>', 500),
    ]
    for label, block, expected in scenarios:
        for name, v in (("1.1", V11), ("1.2", V12)):
            body = request_xml(v, "ACC-1001", block)
            st, ct, raw = post(url, v, body)
            fault = parse_fault(raw)
            print(f"  {label:<26} SOAP {name} -> HTTP {st} {'FAULT ' + str(fault) if fault else 'ok'}")
            assert st == expected
    print("  => a mandatory header nobody understands must FAIL the message, never be skipped.")
    print("     (Security, transactions and reliable-messaging context use this so they cannot be silently ignored.)")
    st, ct, raw = post(url, V11, request_xml(V11, "ACC-1001", f'<c:CorrelationId xmlns:c="{TNS}">req-42</c:CorrelationId>'))
    echoed = ET.fromstring(raw).findtext(f"{{{V11}}}Header/{{{TNS}}}CorrelationId")
    print("  correlation id echoed back in the RESPONSE header:", echoed)
    assert echoed == "req-42"

    print("\n== 4. VersionMismatch: an envelope namespace nobody speaks ==")
    st, ct, raw = post(url, V11, request_xml("http://example.com/soap/9.9", "ACC-1001"))
    print("  HTTP", st, parse_fault(raw), "| answered in SOAP 1.2 format, as the spec requires")
    assert parse_fault(raw)[0] == "versionmismatch"

    print("\nFault mapping cheat sheet (useful when a REST gateway sits in front of SOAP - Go lab 5)")
    for row in [("Client / Sender", "your input is wrong", "400 or 422", "do NOT retry as is"),
                ("Server / Receiver", "their system failed", "502 / 503", "retry idempotent calls with backoff"),
                ("MustUnderstand", "a mandatory header was ignored", "400", "fix the client's headers"),
                ("VersionMismatch", "wrong envelope version", "400", "use 1.1 or 1.2"),
                ("(no response / timeout)", "network or overload", "504", "retry idempotent calls")]:
        print(f"  {row[0]:<24} {row[1]:<32} {row[2]:<11} {row[3]}")
    print("\nOK")
    srv.shutdown()
