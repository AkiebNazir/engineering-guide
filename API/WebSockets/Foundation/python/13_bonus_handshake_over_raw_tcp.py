"""
FOUNDATION BONUS - What does "upgrading a connection" actually mean? (optional, read last)
============================================================================================
Level 00 called `connect()` and `serve()` and never asked what happened. This
file answers it, with no WebSocket library on EITHER side - just a bare TCP
socket, hand-written bytes, and the rules from RFC 6455. Both the server and
the client here are built from scratch.

It exists to dissolve the word "upgrade". There is no magic: the client sends a
perfectly ordinary HTTP GET with a couple of extra headers, the server replies
`101 Switching Protocols`, and from the next byte onward both sides simply
agree to stop writing HTTP and start writing frames down the same socket. The
socket never changed. Only the convention did.

This is optional. Nothing in levels 00-12 depends on it. Read it when you are
curious what the library is doing for you.

You will learn
  - the exact handshake bytes: GET + Upgrade/Connection/Sec-WebSocket-Key,
    answered with 101 + Sec-WebSocket-Accept
  - what Sec-WebSocket-Accept proves: base64(sha1(key + a fixed GUID)), which a
    confused plain HTTP server could never produce by accident
  - the frame layout by hand: FIN+opcode, MASK+length, an optional 4-byte mask
    key, then the payload
  - the masking rule that trips everyone up: client->server frames MUST be
    masked (XOR with those 4 bytes), server->client frames MUST NOT be
  - that "text" and "binary" are literally just opcode 0x1 vs 0x2

Run it   python 13_bonus_handshake_over_raw_tcp.py
"""
import asyncio
import base64
import hashlib
import os
import struct

# Fixed by RFC 6455. It is not a secret and not a key - it is a constant chosen
# so that a server's answer can only come from software that meant to answer.
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OPCODE_TEXT = 0x1
OPCODE_CLOSE = 0x8


def accept_key(client_key: str) -> str:
    """The server's half of the handshake proof: sha1(key + GUID), base64'd."""
    digest = hashlib.sha1((client_key + GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def build_frame(payload: bytes, opcode: int, mask_key: bytes | None) -> bytes:
    """One WebSocket frame, byte by byte.

    byte 0 : FIN(1) RSV1-3(3) opcode(4)          -> 0x80 | opcode for a final frame
    byte 1 : MASK(1) payload-length(7)           -> 0x80 set only when masking
    then   : 2 or 8 extra length bytes if the length did not fit in 7 bits
    then   : the 4-byte mask key, if MASK was set
    then   : the payload (XOR'd with the mask key, if MASK was set)
    """
    header = bytes([0x80 | opcode])                 # FIN=1, no RSV bits, opcode

    n = len(payload)
    mask_bit = 0x80 if mask_key else 0x00
    if n < 126:
        header += bytes([mask_bit | n])             # the length fits in 7 bits
    elif n < 65536:
        header += bytes([mask_bit | 126]) + struct.pack("!H", n)   # 126 => 2 more bytes
    else:
        header += bytes([mask_bit | 127]) + struct.pack("!Q", n)   # 127 => 8 more bytes

    if mask_key:
        # Masking is NOT encryption - the key travels in the clear right here.
        # It exists so that a malicious page cannot make a browser emit bytes
        # that a dumb intermediate proxy would mistake for a real HTTP request.
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        header += mask_key

    return header + payload


def parse_frame(data: bytes) -> tuple[int, bytes]:
    """Read one frame back out of raw bytes. Returns (opcode, payload)."""
    opcode = data[0] & 0x0F
    masked = bool(data[1] & 0x80)
    length = data[1] & 0x7F
    offset = 2

    if length == 126:
        length = struct.unpack("!H", data[offset:offset + 2])[0]
        offset += 2
    elif length == 127:
        length = struct.unpack("!Q", data[offset:offset + 8])[0]
        offset += 8

    if masked:
        mask_key = data[offset:offset + 4]
        offset += 4
        raw = data[offset:offset + length]
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(raw))
    else:
        payload = data[offset:offset + length]

    return opcode, payload


async def raw_server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """A WebSocket server written entirely by hand."""
    # ---- phase 1: this is still ordinary HTTP. Read the request head. ----
    head = (await reader.readuntil(b"\r\n\r\n")).decode()
    print("---- the upgrade request, exactly as it arrives ----")
    print(head, end="")

    headers = {}
    for line in head.split("\r\n")[1:]:
        if ": " in line:
            name, value = line.split(": ", 1)
            headers[name.lower()] = value

    # A real server would also check the method, the version, and Origin.
    if headers.get("upgrade", "").lower() != "websocket":
        writer.write(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        return

    # ---- phase 2: say 101, and the socket's meaning changes ----
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key(headers['sec-websocket-key'])}\r\n"
        "\r\n"
    )
    print("---- the 101 response we write back ----")
    print(response, end="")
    writer.write(response.encode())
    await writer.drain()

    # ---- phase 3: no more HTTP. Frames only, on the very same socket. ----
    frame_head = await reader.readexactly(2)
    length = frame_head[1] & 0x7F
    masked = bool(frame_head[1] & 0x80)
    rest = await reader.readexactly(length + (4 if masked else 0))
    opcode, payload = parse_frame(frame_head + rest)
    print(f"---- one frame received ----\n  raw     : {(frame_head + rest).hex(' ')}")
    print(f"  opcode  : 0x{opcode:x} ({'text' if opcode == OPCODE_TEXT else 'other'})")
    print(f"  masked  : {masked} (required for client -> server)")
    print(f"  payload : {payload!r}")

    # Our reply carries NO mask - a server that masked would be non-compliant.
    reply = build_frame(b"echo: " + payload, OPCODE_TEXT, mask_key=None)
    print(f"---- our unmasked reply frame ----\n  raw     : {reply.hex(' ')}")
    writer.write(reply)

    # A close frame's payload is a 2-byte big-endian status code (1000 = normal).
    writer.write(build_frame(struct.pack("!H", 1000), OPCODE_CLOSE, mask_key=None))
    await writer.drain()
    writer.close()


async def raw_client(port: int) -> None:
    """A WebSocket client written entirely by hand."""
    reader, writer = await asyncio.open_connection("127.0.0.1", port)

    # The key is 16 random bytes, base64'd. It is a handshake nonce, not a
    # credential - it proves the peer speaks WebSocket, nothing about identity.
    key = base64.b64encode(os.urandom(16)).decode()
    request = (
        f"GET /ws HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    writer.write(request.encode())
    await writer.drain()

    head = (await reader.readuntil(b"\r\n\r\n")).decode()
    assert head.startswith("HTTP/1.1 101 "), head
    # Verify the server's proof OURSELVES, the way every real client does.
    expected = accept_key(key)
    assert f"Sec-WebSocket-Accept: {expected}" in head
    print(f"---- the client verifies the proof ----\n  we computed  : {expected}")
    print("  it matches the server's Sec-WebSocket-Accept, so this really is a\n"
          "  WebSocket server and not some HTTP server echoing our headers back")

    # Frames from a client MUST be masked. The mask key is fresh per frame.
    mask = os.urandom(4)
    writer.write(build_frame(b"hello", OPCODE_TEXT, mask_key=mask))
    await writer.drain()

    data = await reader.read(4096)
    opcode, payload = parse_frame(data)
    print(f"---- what came back ----\n  raw     : {data.hex(' ')}")
    print(f"  decoded : opcode 0x{opcode:x}, payload {payload!r}")
    assert opcode == OPCODE_TEXT
    assert payload == b"echo: hello"
    # The second byte's top bit is the MASK bit; on a server frame it is clear.
    assert data[1] & 0x80 == 0, "server frames must not be masked"

    # The close frame the server appended, right after the text frame.
    close_start = 2 + len(payload)
    close_opcode, close_payload = parse_frame(data[close_start:])
    code = struct.unpack("!H", close_payload)[0]
    print(f"  then    : opcode 0x{close_opcode:x} (close), status code {code}")
    assert close_opcode == OPCODE_CLOSE and code == 1000

    writer.close()


async def main() -> None:
    # A known-answer test straight out of RFC 6455 section 1.3: if our accept
    # computation is right, this exact key must produce this exact value.
    assert accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    print("RFC 6455's own example handshake verifies against our accept_key()\n")

    # And the RFC's example frame: a masked text frame carrying "Hello".
    rfc_frame = build_frame(b"Hello", OPCODE_TEXT, mask_key=bytes.fromhex("37fa213d"))
    assert rfc_frame.hex(" ") == "81 85 37 fa 21 3d 7f 9f 4d 51 58"
    print(f"RFC 6455's own example frame verifies too: {rfc_frame.hex(' ')}")
    print("  81 = FIN+text, 85 = MASKED + length 5, then 4 mask bytes, "
          "then 5 masked bytes\n")

    server = await asyncio.start_server(raw_server, "127.0.0.1", 0)
    async with server:
        port = server.sockets[0].getsockname()[1]
        await raw_client(port)

    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
