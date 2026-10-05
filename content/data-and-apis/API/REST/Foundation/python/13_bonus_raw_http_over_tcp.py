"""
FOUNDATION BONUS - What is an HTTP request, really? (optional, read after level 00)
=======================================================================================
Level 00 built a working endpoint using http.server and never asked what that
library does for you underneath. This file answers that: an HTTP server is a
program that reads bytes off a TCP socket, and those bytes happen to follow a
text format everyone agreed on. This proves it by building both the request
AND the response BY HAND - no `http.server`, no framework, nothing but the
raw `socket` module.

This is optional. Nothing in levels 01+ depends on it. It exists to answer
"but what is a framework actually doing for me?" once you're curious.

You will learn
  * a "web request" is plain ASCII text sent over a plain TCP connection
  * the exact wire format: request line, headers, a blank line, then an optional body
  * a response has the same shape: status line, headers, blank line, body
  * why every response needs Content-Length: it is the only way the client knows
    where the body ends (the connection itself does not signal that)

Run it   python 13_bonus_raw_http_over_tcp.py
"""
import socket
import threading

RESPONSE_BODY = b"hello from a hand-written HTTP response\n"


def handle_one_connection(conn: socket.socket) -> None:
    request = conn.recv(4096)  # whatever the client sent, as raw, undecoded bytes
    print("---- raw request bytes received by the server ----")
    print(request.decode())

    # We write every line of the response ourselves. Order matters: status line,
    # then headers (one per line, each ending \r\n), then a BLANK line, then the body.
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: " + str(len(RESPONSE_BODY)).encode() + b"\r\n"
        b"Connection: close\r\n"
        b"\r\n"
    ) + RESPONSE_BODY
    conn.sendall(response)
    conn.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))  # port 0 = "OS, pick me any free port"
    server.listen(1)
    host, port = server.getsockname()

    def accept_loop():
        conn, _addr = server.accept()
        handle_one_connection(conn)

    threading.Thread(target=accept_loop, daemon=True).start()

    # Now play the CLIENT: open our own TCP connection and type the request by hand.
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    request_text = (
        "GET / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client.sendall(request_text.encode())
    response_text = client.recv(4096).decode()
    client.close()
    server.close()

    print("---- raw response bytes received by the client ----")
    print(response_text)

    status_line = response_text.split("\r\n", 1)[0]
    header_block, _, body = response_text.partition("\r\n\r\n")
    expected_length = len(RESPONSE_BODY)

    assert status_line == "HTTP/1.1 200 OK"
    assert f"Content-Length: {expected_length}" in header_block
    assert body.encode() == RESPONSE_BODY
    print("OK")


if __name__ == "__main__":
    main()
