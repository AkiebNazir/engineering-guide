"""
FOUNDATION LEVEL 10 - Authorization: what this caller is allowed to do
==========================================================================
Level 09 answered "who are you?". This answers the completely different
question "may you do THIS?". Mixing the two is the classic security bug, and in
SOAP it has a very concrete form: both answers are faultcode soap:Client, so if
you do not distinguish them in <detail>, a caller cannot tell "log in again"
from "stop asking, you will never be allowed".

    AUTHENTICATION failed -> <Unauthenticated/>   the 401 of SOAP: try again with a credential
    AUTHORIZATION  failed -> <Forbidden/>         the 403 of SOAP: your credential is fine and the answer is still no

Authorization is per-OPERATION, which is where SOAP's single-endpoint design
actually helps: the whole access-control policy is one table next to the
operation table, and one middleware enforces it for every operation at once.

You will learn
  * a second middleware, layered on top of level 09's, reading the identity it
    attached rather than re-checking the token
  * a per-operation role table - the smallest honest access-control policy
  * the Fault that means "we know exactly who you are, still no"
  * why <Forbidden/> must be distinguishable from <Unauthenticated/> by a
    machine, not just by an English sentence
  * that the same caller can be allowed one operation and refused the next

Run it   python 10_authorization_role_based_access.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("wsse", WSSE)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "wsse": WSSE, "t": TNS}

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

# THE POLICY, in one readable place. One SOAP endpoint serves every operation,
# so this table IS the service's access-control surface - easy to review, easy
# to audit, and impossible to forget to apply (the middleware does it).
REQUIRED_ROLES = {
    "ListDocuments": {"viewer", "admin"},   # anyone recognized
    "DeleteDocument": {"admin"},            # admins only
}

DOCUMENTS = {"DOC-1": "quarterly report", "DOC-2": "org chart"}


@dataclass
class Request:
    envelope: ET.Element
    operation: str
    caller: dict | None = None


Dispatcher = Callable[[Request], tuple[int, bytes]]


def build_envelope(body_child: ET.Element, header_children: list[ET.Element] | None = None) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    header = ET.SubElement(envelope, f"{{{SOAP}}}Header")
    for child in header_children or []:
        header.append(child)
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def fault_envelope(code: str, message: str, detail_name: str | None = None, **detail: str) -> bytes:
    fault = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    if detail_name:
        named = ET.SubElement(ET.SubElement(fault, "detail"), f"{{{TNS}}}{detail_name}")
        for key, value in detail.items():
            ET.SubElement(named, f"{{{TNS}}}{key}").text = value
    return build_envelope(fault)


def security_header(token: str) -> ET.Element:
    security = ET.Element(f"{{{WSSE}}}Security")
    token_element = ET.SubElement(security, f"{{{WSSE}}}UsernameToken")
    ET.SubElement(token_element, f"{{{WSSE}}}Password").text = token
    return security


# ---- level 09, unchanged: who is this? ----
def with_authentication(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        token = request.envelope.findtext(
            "soap:Header/wsse:Security/wsse:UsernameToken/wsse:Password", namespaces=NS)
        caller = TOKENS.get(token) if token else None
        if caller is None:
            return 500, fault_envelope("soap:Client", "missing or invalid credentials",
                                       "Unauthenticated")
        request.caller = caller
        return next_dispatch(request)
    return wrapped


# ---- NEW: may this caller run THIS operation? ----
def with_authorization(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        # Note what this does NOT do: it never looks at the token again. The
        # identity is already established; re-deriving it here is how the two
        # checks drift apart and a hole opens up.
        allowed = REQUIRED_ROLES.get(request.operation)
        if allowed is None:
            return 500, fault_envelope("soap:Client", f"unknown operation {request.operation}")

        if request.caller["role"] not in allowed:
            print(f"  [authz] {request.caller['user']} (role={request.caller['role']}) "
                  f"refused {request.operation}, needs one of {sorted(allowed)}")
            # The 403 of SOAP. The caller is authenticated - retrying with the
            # same credential will fail forever, and <Forbidden/> says so.
            return 500, fault_envelope(
                "soap:Client",
                f"role '{request.caller['role']}' may not call {request.operation}",
                "Forbidden", requiredRole=",".join(sorted(allowed)))

        return next_dispatch(request)
    return wrapped


def dispatch(request: Request) -> tuple[int, bytes]:
    if request.operation == "ListDocuments":
        response = ET.Element(f"{{{TNS}}}ListDocumentsResponse")
        documents = ET.SubElement(response, f"{{{TNS}}}documents")
        for doc_id, title in DOCUMENTS.items():
            document = ET.SubElement(documents, f"{{{TNS}}}document")
            document.set("id", doc_id)
            document.text = title
        return 200, build_envelope(response)

    if request.operation == "DeleteDocument":
        doc_id = request.envelope.findtext("soap:Body/t:DeleteDocument/t:id", namespaces=NS)
        DOCUMENTS.pop(doc_id, None)   # idempotent: deleting twice is not an error
        response = ET.Element(f"{{{TNS}}}DeleteDocumentResponse")
        ET.SubElement(response, f"{{{TNS}}}remaining").text = str(len(DOCUMENTS))
        return 200, build_envelope(response)

    return 500, fault_envelope("soap:Client", "unreachable")


# Order is the lesson: identify FIRST, then decide. Authorization cannot run
# before authentication, because it reads the identity that step attached.
pipeline: Dispatcher = with_authentication(with_authorization(dispatch))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            envelope = ET.fromstring(raw)
            operation = envelope.find("soap:Body", NS)[0].tag.split("}")[-1]
        except Exception:
            status, out = 500, fault_envelope("soap:Client", "malformed SOAP request")
        else:
            status, out = pipeline(Request(envelope=envelope, operation=operation))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def call(url: str, operation: str, token: str | None = None, **params: str) -> tuple[int, ET.Element]:
    element = ET.Element(f"{{{TNS}}}{operation}")
    for name, value in params.items():
        ET.SubElement(element, f"{{{TNS}}}{name}").text = value
    headers = [security_header(token)] if token else []
    request = urllib.request.Request(url, data=build_envelope(element, headers),
                                     headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def detail_of(envelope: ET.Element) -> str | None:
    detail = envelope.find("soap:Body/soap:Fault/detail", NS)
    return detail[0].tag.split("}")[-1] if detail is not None and len(detail) else None


def demo(url: str) -> None:
    print("== 1. no credentials: authentication stops it, authorization never runs ==")
    status, envelope = call(url, "ListDocuments")
    print(f"  ListDocuments (anonymous)  -> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "Unauthenticated"

    print("\n== 2. bob (viewer) may read ==")
    status, envelope = call(url, "ListDocuments", token="bob-token")
    titles = [d.text for d in envelope.findall("soap:Body/t:ListDocumentsResponse/t:documents/t:document", NS)]
    print(f"  ListDocuments (bob)        -> {status} {titles}")
    assert status == 200 and len(titles) == 2

    print("\n== 3. bob (viewer) may NOT delete - the whole point of this level ==")
    status, envelope = call(url, "DeleteDocument", token="bob-token", id="DOC-1")
    message = envelope.findtext("soap:Body/soap:Fault/faultstring", namespaces=NS)
    print(f"  DeleteDocument (bob)       -> {status} <{detail_of(envelope)}> {message!r}")
    assert detail_of(envelope) == "Forbidden"
    assert "DOC-1" in DOCUMENTS, "the refused call must not have changed anything"

    print("\n== 4. alice (admin) may delete ==")
    status, envelope = call(url, "DeleteDocument", token="alice-token", id="DOC-1")
    remaining = envelope.findtext("soap:Body/t:DeleteDocumentResponse/t:remaining", namespaces=NS)
    print(f"  DeleteDocument (alice)     -> {status} remaining={remaining}")
    assert (status, remaining) == (200, "1")

    print("\n== 5. the two faults a client MUST tell apart ==")
    _, anonymous = call(url, "ListDocuments")
    _, refused = call(url, "DeleteDocument", token="bob-token", id="DOC-2")
    same_code = (anonymous.findtext("soap:Body/soap:Fault/faultcode", namespaces=NS)
                 == refused.findtext("soap:Body/soap:Fault/faultcode", namespaces=NS))
    print(f"  identical faultcode? {same_code}   -> so <detail> is the ONLY reliable signal")
    print(f"    <{detail_of(anonymous)}> means: get a credential and retry")
    print(f"    <{detail_of(refused)}>      means: retrying changes nothing, ask an admin")
    assert same_code and detail_of(anonymous) != detail_of(refused)

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
