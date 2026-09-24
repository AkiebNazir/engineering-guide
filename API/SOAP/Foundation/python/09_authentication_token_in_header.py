"""
FOUNDATION LEVEL 09 - Authentication: proving who you are, inside the envelope
==================================================================================
Middleware (level 08) is the mechanism; authentication is the first thing
everyone puts in it. Authentication answers exactly ONE question: "do we
recognize this caller at all?" It says NOTHING about what they may do - that is
level 10, authorization, and keeping the two apart is the whole point.

WHERE THE CREDENTIAL GOES. A REST API sends `Authorization: Bearer xyz`, an
HTTP header. SOAP can do that too, but the SOAP-native answer is a security
element in <soap:Header>, because (level 07) the envelope survives hops and can
be signed. The real standard is WS-Security's UsernameToken:

    <soap:Header>
      <wsse:Security>
        <wsse:UsernameToken>
          <wsse:Username>alice</wsse:Username>
          <wsse:Password Type="...#PasswordText">s3cret</wsse:Password>
        </wsse:UsernameToken>
      </wsse:Security>
    </soap:Header>

This level uses the same SHAPE with a simple opaque token, so the lesson is the
check and not the ceremony. ../../labs/python/04_ws_security_username_token.py
does the real WS-Security version with digests, nonces and timestamps.

There is no "401" here: a SOAP service answers with a Fault (level 05). The
401-equivalent is faultcode soap:Client plus a <detail> element that names the
problem, so the caller can tell "I am not logged in" from "you typo'd a field".

You will learn
  * reading a credential out of <soap:Header> before the Body is parsed at all
  * authentication as middleware: it can short-circuit the chain entirely
  * the Fault that means "who even are you" - the 401 of the SOAP world
  * attaching the identified caller to the request so operations (and level
    10's role check) never re-verify the token
  * why the credential belongs in the envelope, not only in an HTTP header

Run it   python 09_authentication_token_in_header.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
# The real WS-Security namespace, so the header element you see here is the one
# you will meet in the wild.
WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("wsse", WSSE)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "wsse": WSSE, "t": TNS}

# A stand-in for "who is allowed in". A real service verifies a signed SAML
# assertion or looks the token up in a store instead of this dict.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}


@dataclass
class Request:
    """The request as it travels down the chain. `caller` starts empty and is
    filled in BY the authentication middleware - never by the caller."""
    raw: bytes
    envelope: ET.Element
    caller: dict | None = None


Dispatcher = Callable[[Request], tuple[int, bytes]]


def build_envelope(body_child: ET.Element, header_children: list[ET.Element] | None = None) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    header = ET.SubElement(envelope, f"{{{SOAP}}}Header")
    for child in header_children or []:
        header.append(child)
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def fault_envelope(code: str, message: str, detail_name: str | None = None) -> bytes:
    fault = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    if detail_name:
        detail = ET.SubElement(fault, "detail")
        ET.SubElement(detail, f"{{{TNS}}}{detail_name}")
    return build_envelope(fault)


def security_header(token: str) -> ET.Element:
    """The client side: a WS-Security-shaped header carrying one token."""
    security = ET.Element(f"{{{WSSE}}}Security")
    username_token = ET.SubElement(security, f"{{{WSSE}}}UsernameToken")
    ET.SubElement(username_token, f"{{{WSSE}}}Username").text = "the-token-holder"
    ET.SubElement(username_token, f"{{{WSSE}}}Password").text = token
    return security


def with_authentication(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        token = request.envelope.findtext(
            "soap:Header/wsse:Security/wsse:UsernameToken/wsse:Password", namespaces=NS)

        if token is None:
            # The 401 of SOAP. HTTP status stays 500 (level 06) - the FAULT
            # carries the meaning, and <detail> names it for machines.
            return 500, fault_envelope("soap:Client", "no credentials in the SOAP header",
                                       "Unauthenticated")

        caller = TOKENS.get(token)
        if caller is None:
            # Same fault, deliberately the same vague faultstring: telling an
            # attacker which half of the credential was wrong is a gift.
            return 500, fault_envelope("soap:Client", "unknown or expired token",
                                       "Unauthenticated")

        request.caller = caller          # everything downstream now knows who this is
        print(f"  [auth] recognized {caller['user']} (role={caller['role']})")
        return next_dispatch(request)
    return wrapped


def dispatch(request: Request) -> tuple[int, bytes]:
    operation = request.envelope.find("soap:Body", NS)[0]
    local = operation.tag.split("}")[-1]

    if local == "WhoAmI":
        # No token checking here at all - by the time an operation runs, the
        # caller is a known fact. That separation is what middleware buys you.
        response = ET.Element(f"{{{TNS}}}WhoAmIResponse")
        ET.SubElement(response, f"{{{TNS}}}user").text = request.caller["user"]
        ET.SubElement(response, f"{{{TNS}}}role").text = request.caller["role"]
        return 200, build_envelope(response)

    return 500, fault_envelope("soap:Client", f"unknown operation {local}")


pipeline: Dispatcher = with_authentication(dispatch)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            envelope = ET.fromstring(raw)
        except ET.ParseError:
            status, out = 500, fault_envelope("soap:Client", "malformed XML")
        else:
            status, out = pipeline(Request(raw=raw, envelope=envelope))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def call(url: str, operation: str, token: str | None = None) -> tuple[int, ET.Element]:
    headers = [security_header(token)] if token is not None else []
    raw = build_envelope(ET.Element(f"{{{TNS}}}{operation}"), headers)
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def detail_of(envelope: ET.Element) -> str | None:
    detail = envelope.find("soap:Body/soap:Fault/detail", NS)
    return detail[0].tag.split("}")[-1] if detail is not None and len(detail) else None


def demo(url: str) -> None:
    print("== 1. no credentials at all ==")
    status, envelope = call(url, "WhoAmI")
    print(f"  WhoAmI (no header)     -> {status} "
          f"{envelope.findtext('soap:Body/soap:Fault/faultcode', namespaces=NS)} <{detail_of(envelope)}>")
    assert status == 500 and detail_of(envelope) == "Unauthenticated"

    print("\n== 2. a token nobody has ever issued ==")
    status, envelope = call(url, "WhoAmI", token="hunter2")
    print(f"  WhoAmI (bad token)     -> {status} "
          f"{envelope.findtext('soap:Body/soap:Fault/faultstring', namespaces=NS)!r} <{detail_of(envelope)}>")
    assert status == 500 and detail_of(envelope) == "Unauthenticated"

    print("\n== 3. a real token ==")
    status, envelope = call(url, "WhoAmI", token="alice-token")
    user = envelope.findtext("soap:Body/t:WhoAmIResponse/t:user", namespaces=NS)
    role = envelope.findtext("soap:Body/t:WhoAmIResponse/t:role", namespaces=NS)
    print(f"  WhoAmI (alice-token)   -> {status} user={user} role={role}")
    assert (status, user, role) == (200, "alice", "admin")

    status, envelope = call(url, "WhoAmI", token="bob-token")
    user = envelope.findtext("soap:Body/t:WhoAmIResponse/t:user", namespaces=NS)
    role = envelope.findtext("soap:Body/t:WhoAmIResponse/t:role", namespaces=NS)
    print(f"  WhoAmI (bob-token)     -> {status} user={user} role={role}")
    assert (status, user, role) == (200, "bob", "viewer")
    print("  -> bob got in. Whether bob may DO anything is level 10's question.")

    print("\n== 4. what the authenticated request actually looked like ==")
    print("  " + build_envelope(ET.Element(f"{{{TNS}}}WhoAmI"),
                                [security_header("alice-token")]).decode().replace("><", ">\n  <"))

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
