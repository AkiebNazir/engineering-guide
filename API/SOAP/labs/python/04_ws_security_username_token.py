"""
LAB 04 (advanced) - WS-Security: UsernameToken with PasswordDigest, nonce and timestamp
========================================================================================
Enterprise SOAP services rarely rely on HTTP-level auth alone. WS-Security puts credentials INSIDE
the message (in <soap:Header>), so security travels with the message through intermediaries.

You will learn
  * the UsernameToken profile - what is in the header:

        <wsse:Security>
          <wsse:UsernameToken>
            <wsse:Username>alice</wsse:Username>
            <wsse:Password Type="...#PasswordDigest">Base64( SHA1( Nonce + Created + Password ) )</wsse:Password>
            <wsse:Nonce>Base64 random bytes</wsse:Nonce>          <- makes every message unique
            <wsu:Created>2026-09-21T10:30:00Z</wsu:Created>        <- when it was made
          </wsse:UsernameToken>
        </wsse:Security>

  * the PASSWORD DIGEST: the password itself is never sent, but the server must know it (or an equivalent)
    to recompute the digest.
  * the two defences that make a digest useful:
      - FRESHNESS: reject `Created` older/newer than a window (5 min) => a captured message expires
      - NONCE cache: reject a nonce already seen inside that window => a captured message cannot be replayed
  * INTEROP: our server verifies messages produced by zeep's UsernameToken(use_digest=True)
  * failing properly with a WS-Security fault (wsse:FailedAuthentication) that reveals nothing
    about WHY (wrong user vs wrong password vs stale)
  * honest limits: SHA-1 + shared secret is LEGACY. Prefer TLS + X.509 certificates / SAML / OAuth
    where you have the choice - but you will meet UsernameToken constantly in banks and ERPs.

Reuses the server from lab 02.

Needs   pip install zeep
Run it  python 04_ws_security_username_token.py
"""
import base64
import hashlib
import hmac
import importlib.util
import logging
import pathlib
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer

import zeep
import zeep.exceptions
from zeep.plugins import HistoryPlugin
from zeep.wsse.username import UsernameToken

logging.getLogger("zeep").setLevel(logging.ERROR)
spec = importlib.util.spec_from_file_location("lab02", pathlib.Path(__file__).with_name("02_soap_server_and_wsdl.py"))
lab02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab02)

WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
DIGEST_TYPE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest"
NS = {"soap": lab02.SOAP, "wsse": WSSE, "wsu": WSU}

USERS = {"alice": "s3cret-alice", "bob": "s3cret-bob"}     # digest auth needs the plaintext-equivalent on the server
WINDOW = timedelta(minutes=5)
seen_nonces: dict[str, datetime] = {}                      # production: Redis with TTL = WINDOW
nonce_lock = threading.Lock()


class AuthFailure(Exception):
    pass


def compute_digest(nonce: bytes, created: str, password: str) -> str:
    return base64.b64encode(hashlib.sha1(nonce + created.encode() + password.encode()).digest()).decode()


def authenticate(envelope: ET.Element, now: datetime) -> str:
    token = envelope.find("soap:Header/wsse:Security/wsse:UsernameToken", NS)
    if token is None:
        raise AuthFailure("no security header")
    username = token.findtext("wsse:Username", namespaces=NS)
    pw_el = token.find("wsse:Password", NS)
    nonce_b64 = token.findtext("wsse:Nonce", namespaces=NS)
    created = token.findtext("wsu:Created", namespaces=NS)
    if not (username and pw_el is not None and nonce_b64 and created):
        raise AuthFailure("incomplete UsernameToken")
    if pw_el.get("Type") != DIGEST_TYPE:
        raise AuthFailure("PasswordText is not accepted; PasswordDigest required")     # policy: never accept plaintext

    try:
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        nonce = base64.b64decode(nonce_b64)
    except ValueError:
        raise AuthFailure("malformed token")
    if abs(now - created_at) > WINDOW:
        raise AuthFailure("token expired")                                            # freshness

    password = USERS.get(username)
    expected = compute_digest(nonce, created, password or "dummy")                   # same work whether or not the user exists
    if password is None or not hmac.compare_digest(expected, (pw_el.text or "").strip()):
        raise AuthFailure("bad credentials")

    with nonce_lock:                                                                  # replay protection
        for n, t in list(seen_nonces.items()):
            if now - t > WINDOW:
                del seen_nonces[n]                                                    # expired entries can go
        if nonce_b64 in seen_nonces:
            raise AuthFailure("nonce reuse")
        seen_nonces[nonce_b64] = now
    return username


def secure_dispatch(body: bytes) -> tuple[int, bytes]:
    try:
        env = ET.fromstring(body)
    except ET.ParseError:
        return 400, lab02.fault("soap:Client", "Malformed XML")
    try:
        user = authenticate(env, datetime.now(timezone.utc))
    except AuthFailure as e:
        print(f"  [server log] auth rejected: {e}")                                  # the REASON goes to the log ...
        return 500, lab02.fault("wsse:FailedAuthentication", "The security token could not be authenticated")   # ... not the client
    print(f"  [server log] authenticated as {user}")
    return lab02.dispatch(body)


class SecureHandler(lab02.Handler):
    def do_POST(self):
        status, data = secure_dispatch(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def build_request(username: str, password: str, created: datetime, nonce: bytes | None = None) -> bytes:
    """Hand-built secured request (for the attack demos)."""
    nonce = nonce or __import__("os").urandom(16)
    created_s = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f'<soap:Envelope xmlns:soap="{lab02.SOAP}" xmlns:wsse="{WSSE}" xmlns:wsu="{WSU}">'
            f'<soap:Header><wsse:Security><wsse:UsernameToken><wsse:Username>{username}</wsse:Username>'
            f'<wsse:Password Type="{DIGEST_TYPE}">{compute_digest(nonce, created_s, password)}</wsse:Password>'
            f'<wsse:Nonce>{base64.b64encode(nonce).decode()}</wsse:Nonce><wsu:Created>{created_s}</wsu:Created>'
            f'</wsse:UsernameToken></wsse:Security></soap:Header>'
            f'<soap:Body><GetBalance xmlns="{lab02.TNS}"><accountId>ACC-1001</accountId></GetBalance></soap:Body></soap:Envelope>').encode()


def raw_post(url: str, body: bytes) -> str:
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "text/xml"})
    try:
        raw = urllib.request.urlopen(req).read()
    except urllib.error.HTTPError as e:
        raw = e.read()
    root = ET.fromstring(raw)
    f = root.find("soap:Body/soap:Fault", NS)
    return f"FAULT {f.findtext('faultcode')}: {f.findtext('faultstring')}" if f is not None else "OK " + (root.findtext(".//{%s}balance" % lab02.TNS) or "")


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 0), SecureHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/bank"
    now = datetime.now(timezone.utc)

    print("== 1. no credentials ==")
    r = raw_post(url, f'<soap:Envelope xmlns:soap="{lab02.SOAP}"><soap:Body><GetBalance xmlns="{lab02.TNS}"><accountId>ACC-1001</accountId></GetBalance></soap:Body></soap:Envelope>'.encode())
    print("  ->", r)
    assert r.startswith("FAULT wsse:FailedAuthentication")

    print("\n== 2. a real client: zeep with UsernameToken(use_digest=True) ==")
    history = HistoryPlugin()
    client = zeep.Client(f"{url}?wsdl", plugins=[history], wsse=UsernameToken("alice", "s3cret-alice", use_digest=True))
    result = client.service.GetBalance(accountId="ACC-1001")
    print("  GetBalance ->", result.balance, "(zeep's digest verified by OUR server: interoperable)")
    assert str(result.balance) == "1042.50"
    from lxml import etree
    header = history.last_sent["envelope"].find("{%s}Header" % lab02.SOAP)
    print(etree.tostring(header, pretty_print=True).decode())
    sent = etree.tostring(history.last_sent["envelope"]).decode()
    assert "s3cret-alice" not in sent
    print("  the password does not appear anywhere in the message: True")

    print("== 3. attacks ==")
    print("  wrong password        ->", raw_post(url, build_request("alice", "wrong-password", now)))
    print("  unknown user          ->", raw_post(url, build_request("mallory", "whatever", now)))
    print("  (both answers are IDENTICAL: an attacker cannot tell whether the user exists)")
    good = build_request("bob", "s3cret-bob", now)
    print("  valid message         ->", raw_post(url, good))
    print("  SAME bytes replayed   ->", raw_post(url, good))
    print("  1 hour old token      ->", raw_post(url, build_request("alice", "s3cret-alice", now - timedelta(hours=1))))
    print("  token from the future ->", raw_post(url, build_request("alice", "s3cret-alice", now + timedelta(hours=1))))
    assert raw_post(url, good).startswith("FAULT")

    print("\n== 4. why the nonce cache and the timestamp window need each other ==")
    print("  the window alone lets an attacker replay a message for 5 minutes;")
    print("  the nonce cache alone would grow forever - entries only need to live as long as the window.")
    print(f"  nonces currently remembered: {len(seen_nonces)} (each expires after {int(WINDOW.total_seconds())}s)")
    print("\n== 5. honest limits ==")
    for line in ["SHA-1 is deprecated; the digest scheme also forces the server to hold a plaintext-equivalent secret.",
                 "Without TLS the BODY is readable and modifiable. UsernameToken authenticates, it does not sign the body.",
                 "Stronger options in WS-Security: X.509 BinarySecurityToken + XML Signature over Body and Timestamp,",
                 "SAML assertions for federation. Always run SOAP over TLS."]:
        print("  -", line)
    print("\nOK")
    srv.shutdown()
