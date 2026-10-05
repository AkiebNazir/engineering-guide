"""
LAB 01 (basic) - What a WebSocket really is: the handshake, then an echo server
================================================================================
You will learn
  * a WebSocket is an HTTP request that ASKS TO SWITCH PROTOCOL, and after the server says
    "101 Switching Protocols" the same TCP connection carries WebSocket FRAMES instead of HTTP
  * the handshake, shown with a RAW socket - no library - so nothing is hidden:

        GET /chat HTTP/1.1                                HTTP/1.1 101 Switching Protocols
        Upgrade: websocket                                Upgrade: websocket
        Connection: Upgrade                               Connection: Upgrade
        Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==      Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
        Sec-WebSocket-Version: 13

    Accept = base64( sha1( Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11" ) )  - proves the server understood
  * what a frame looks like:  FIN+opcode | MASK+length | (mask key) | payload
    (client->server frames are ALWAYS masked; server->client frames are not)
  * an echo server and client with the `websockets` library: text vs binary messages,
    ordered delivery, and a clean close with a status code

Needs   pip install websockets
Run it  python 01_handshake_echo_and_frames.py
"""
import asyncio
import base64
import hashlib
import struct

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"          # fixed by RFC 6455


def accept_key(client_key: str) -> str:
    return base64.b64encode(hashlib.sha1((client_key + GUID).encode()).digest()).decode()


def frame(payload: bytes, opcode: int = 0x1, mask_key: bytes | None = None) -> bytes:
    """Build one WebSocket frame by hand."""
    header = bytes([0x80 | opcode])                                     # FIN=1 + opcode
    mask_bit = 0x80 if mask_key else 0
    n = len(payload)
    if n < 126:
        header += bytes([mask_bit | n])
    elif n < 65536:
        header += bytes([mask_bit | 126]) + struct.pack("!H", n)
    else:
        header += bytes([mask_bit | 127]) + struct.pack("!Q", n)
    if mask_key:
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        header += mask_key
    return header + payload


async def echo(websocket):
    async for message in websocket:                                     # yields str (text) or bytes (binary)
        kind = "text" if isinstance(message, str) else "binary"
        await websocket.send(message if kind == "binary" else f"echo: {message}")


async def main():
    async with serve(echo, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]

        print("== 1. the handshake, by hand, over a raw TCP socket ==")
        assert accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="      # the RFC 6455 example
        key = base64.b64encode(b"sixteen-byte-key").decode()
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write((f"GET /chat HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\n"
                      f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = (await reader.readuntil(b"\r\n\r\n")).decode()
        for line in head.strip().splitlines():
            print("  <-", line)
        assert head.startswith("HTTP/1.1 101") and f"Sec-WebSocket-Accept: {accept_key(key)}" in head
        print("  the server's Accept matches what we computed ourselves: sha1(key + GUID), base64")

        print("\n== 2. now the connection speaks frames: send one masked text frame by hand ==")
        mask = b"\x37\xfa\x21\x3d"
        wire = frame(b"Hello", opcode=0x1, mask_key=mask)
        print("  our frame :", wire.hex(" "), "   (0x81=FIN+text, 0x85=MASKED+len 5, 4 mask bytes, 5 masked bytes)")
        assert wire.hex(" ") == "81 85 37 fa 21 3d 7f 9f 4d 51 58"        # the RFC 6455 example
        writer.write(wire)
        reply = await reader.readexactly(2 + len("echo: Hello"))
        print("  reply     :", reply.hex(" "), "->", reply[2:].decode())
        print("  server frames carry NO mask: the 2nd byte is 0x%02x (mask bit clear, length %d)" % (reply[1], reply[1] & 0x7F))
        assert reply[0] == 0x81 and reply[1] == 11 and reply[2:] == b"echo: Hello"
        writer.write(frame(struct.pack("!H", 1000), opcode=0x8, mask_key=mask))                  # Close, code 1000
        await writer.drain()
        writer.close()

        print("\n== 3. the same thing with the library ==")
        async with connect(f"ws://127.0.0.1:{port}/chat") as ws:
            await ws.send("hi")                                        # str -> TEXT frame
            print("  text   :", await ws.recv())
            await ws.send(b"\x00\x01\x02\xff")                         # bytes -> BINARY frame
            print("  binary :", await ws.recv())
            for i in range(3):
                await ws.send(f"msg {i}")
            print("  ordered:", [await ws.recv() for _ in range(3)])   # WebSocket preserves order (it is TCP)
            pong_waiter = await ws.ping()                              # control frame; library answers pings for you
            latency = await pong_waiter
            print(f"  ping   : pong received in {latency * 1000:.1f} ms")
            await ws.close(code=1000, reason="done")
        print("  closed with:", ws.close_code, ws.close_reason)
        assert ws.close_code == 1000

        print("\n== 4. what the server sees when the client leaves ==")
        async with connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send("x")
            await ws.recv()
        try:
            await ws.recv()
        except ConnectionClosedOK as e:
            print("  reading from a closed connection raises", type(e).__name__, f"(code {e.rcvd.code if e.rcvd else None})")
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
