"""
FOUNDATION BONUS - What is a SOAP call, really? (optional, read after level 00)
==================================================================================
Every level so far used http.server and xml.etree and never asked what those
do underneath. This file answers that: a SOAP call is a string of text sent
over a TCP socket. Nothing more. It proves it by building the HTTP request AND
the SOAP envelope by hand, as string concatenation, sending them over a bare
socket, and picking the answer apart with str.find - no http.server, no
ElementTree, no XML library of any kind.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is all that XML machinery actually doing for me?" once you are
curious - and to make one specific point: SOAP's reputation for heaviness comes
from the TOOLING (WSDL generators, WS-* stacks), not from the wire format,
which is this small.

WHY YOU MUST NOT DO THIS FOR REAL: the parsing below is `str.find`. It breaks
the moment the server uses a different namespace prefix, adds whitespace,
escapes a character as &amp;, or splits the response across two TCP reads. That
fragility is exactly what a real XML parser exists to absorb.

You will learn
  * the complete bytes of a SOAP call: HTTP request line, headers, blank line,
    then an XML envelope as the body
  * that Content-Length is mandatory - it is the only thing telling the other
    side where the body ends
  * the SOAPAction header, and why it exists at the HTTP level at all
  * that "SOAP" is a convention about the body's shape, not a transport
  * exactly why string-matching XML is a bug waiting to happen

Run it   python 13_bonus_raw_envelope_over_tcp.py
"""
import socket
import threading

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"

# ---- the request envelope, typed out by hand, exactly as it goes on the wire ----
REQUEST_ENVELOPE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    f'<soap:Envelope xmlns:soap="{SOAP}">'
    "<soap:Header/>"
    f'<soap:Body><t:Ping xmlns:t="{TNS}"><t:who>raw socket</t:who></t:Ping></soap:Body>'
    "</soap:Envelope>"
)

RESPONSE_ENVELOPE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    f'<soap:Envelope xmlns:soap="{SOAP}">'
    f'<soap:Body><t:PingResponse xmlns:t="{TNS}"><t:message>Pong</t:message></t:PingResponse></soap:Body>'
    "</soap:Envelope>"
)


def build_http_request(host_header: str, body: str) -> bytes:
    """Four parts, and that is the entire HTTP protocol for our purposes:
    a request line, some headers (one per line), a BLANK line, then the body.
    Every line ends with \\r\\n - carriage return AND line feed, not just \\n.
    """
    return (
        "POST /soap HTTP/1.1\r\n"
        f"Host: {host_header}\r\n"
        "Content-Type: text/xml; charset=utf-8\r\n"
        # SOAPAction is SOAP 1.1's one concession to the HTTP layer: it lets a
        # proxy or firewall route on the operation without parsing any XML.
        f'SOAPAction: "{TNS}/Ping"\r\n'
        f"Content-Length: {len(body.encode())}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{body}"
    ).encode()


def build_http_response(body: str) -> bytes:
    """A response has the same four parts, with a status line at the top."""
    return (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/xml; charset=utf-8\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{body}"
    ).encode()


def serve_one_connection(listener: socket.socket) -> None:
    """The whole server: accept one connection, read the request, write bytes."""
    connection, _ = listener.accept()
    with connection:
        # Read until we have the header block, then keep reading until we have
        # Content-Length bytes of body. Doing this correctly is most of what
        # http.server was quietly handling for us in every other level.
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = connection.recv(4096)
            if not chunk:
                return
            data += chunk

        header_block, _, body = data.partition(b"\r\n\r\n")
        headers = header_block.decode().split("\r\n")
        content_length = next(
            (int(h.split(":", 1)[1]) for h in headers if h.lower().startswith("content-length")), 0)
        while len(body) < content_length:
            body += connection.recv(4096)

        print("---- raw bytes the server received ----")
        print(data.decode())

        # "Dispatch", string-matching style. This is the fragile part, on purpose.
        if "Ping" in body.decode():
            connection.sendall(build_http_response(RESPONSE_ENVELOPE))
        else:
            connection.sendall(build_http_response("<unknown/>"))


def main() -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))   # port 0 = "OS, give me any free port"
    listener.listen(1)
    host, port = listener.getsockname()
    threading.Thread(target=serve_one_connection, args=(listener,), daemon=True).start()

    # ---- now play the CLIENT, with nothing but a socket ----
    client = socket.create_connection((host, port))
    client.sendall(build_http_request(f"{host}:{port}", REQUEST_ENVELOPE))

    received = b""
    while True:
        chunk = client.recv(4096)     # "Connection: close" means recv returns b"" at the end
        if not chunk:
            break
        received += chunk
    client.close()
    listener.close()

    text = received.decode()
    print("---- raw bytes the client received ----")
    print(text)

    status_line, _, rest = text.partition("\r\n")
    header_block, _, body = rest.partition("\r\n\r\n")

    # ---- "parsing" XML with str.find, to show why nobody should ----
    start = body.find("<t:message>") + len("<t:message>")
    message = body[start:body.find("</t:message>")]

    print("---- what we extracted ----")
    print(f"status line : {status_line}")
    print(f"body length : {len(body.encode())} bytes")
    print(f"<t:message> : {message!r}")

    assert status_line == "HTTP/1.1 200 OK"
    assert f"Content-Length: {len(RESPONSE_ENVELOPE.encode())}" in header_block
    assert body == RESPONSE_ENVELOPE
    assert message == "Pong"

    # The point, stated once: the same document with a different prefix is the
    # SAME document (level 04) - and our string matching would miss it entirely.
    equivalent = (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<soap:Envelope xmlns:soap="{SOAP}">'
        f'<soap:Body><ns1:PingResponse xmlns:ns1="{TNS}">'
        "<ns1:message>Pong</ns1:message></ns1:PingResponse></soap:Body>"
        "</soap:Envelope>"
    )
    assert "<t:message>" not in equivalent
    assert equivalent.find("<t:message>") == -1
    print("\nthe same response with 'ns1:' instead of 't:' is an IDENTICAL document,")
    print("and find('<t:message>') would return -1 on it. That is why levels 00-12")
    print("used a real XML parser, and why you should too.")

    print("OK")


if __name__ == "__main__":
    main()
