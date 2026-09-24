"""
FOUNDATION LEVEL 01 - Messages, not bytes: text frames, binary frames, boundaries
=====================================================================================
Level 00 sent strings and got strings back without ever asking what actually
travelled. This level asks. A WebSocket does NOT give you a byte stream like a
raw TCP socket does - it gives you discrete MESSAGES, each carried in one or
more frames, and the library hands you each message whole or not at all.

That single property is why WebSockets are pleasant to program against: you
never have to invent your own "where does this message end?" rule (length
prefixes, newline delimiters), the way you must with a bare socket.

You will learn
  * a message has a TYPE decided by its frame opcode: text (0x1) or binary (0x2)
  * in Python that type is simply the type you get back: str for text, bytes
    for binary - send str, receive str; send bytes, receive bytes
  * MESSAGE boundaries are preserved: two sends are two receives, always,
    never merged and never split (a raw TCP socket guarantees neither)
  * a big message may be split into several FRAMES on the wire, yet still
    arrives as ONE message - frames are transport detail, messages are the API
  * ordering is guaranteed, because underneath it is still one TCP connection

Run it   python 01_message_framing_text_and_binary.py
"""
import asyncio

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve


async def inspect_handler(websocket):
    """Reports back what KIND of message it received, and how big it was."""
    async for message in websocket:
        if isinstance(message, str):
            # A text frame's payload is required by RFC 6455 to be valid UTF-8,
            # which is exactly why the library can safely decode it to str.
            await websocket.send(f"text:{len(message)}:{message[:20]}")
        else:
            # A binary frame is arbitrary bytes - no encoding rules at all.
            await websocket.send(f"binary:{len(message)}")


async def demo(port: int) -> None:
    async with connect(f"ws://127.0.0.1:{port}") as ws:
        print("== 1. text vs binary: the frame opcode decides the Python type ==")
        await ws.send("hello")                    # str  -> TEXT frame   (opcode 0x1)
        print("  sent str    'hello'        -> server saw", await ws.recv())
        await ws.send(b"\x00\x01\x02\xff")        # bytes -> BINARY frame (opcode 0x2)
        print("  sent bytes  b'\\x00\\x01\\x02\\xff' -> server saw", await ws.recv())

        print("\n== 2. boundaries: two sends are two receives, never one blurred blob ==")
        await ws.send("aaaa")
        await ws.send("bb")
        first, second = await ws.recv(), await ws.recv()
        print(f"  sent 'aaaa' then 'bb'  -> {first!r} then {second!r}")
        # On a bare TCP socket these could have arrived as the 6 bytes "aaaabb"
        # in a single read, and you would have had no way to tell where the
        # first one ended. WebSockets removes that entire class of bug.
        assert first == "text:4:aaaa" and second == "text:2:bb"

        print("\n== 3. one MESSAGE can be many FRAMES, and still arrives whole ==")
        # Passing an iterable tells the library to send a FRAGMENTED message:
        # frame 1 (fin=0) "Hel", frame 2 (fin=0) "lo ", frame 3 (fin=1) "world".
        # The receiver never sees the seams - it gets one 11-character message.
        await ws.send(["Hel", "lo ", "world"])
        reassembled = await ws.recv()
        print(f"  sent 3 fragments        -> server saw {reassembled}"
              "   (one message, reassembled for it)")
        assert reassembled == "text:11:Hello world"

        # Same idea at size: 200 KB goes out in whatever frames the library and
        # the OS choose, and comes back as exactly one 200000-byte message.
        big = b"x" * 200_000
        await ws.send(big)
        got = await ws.recv()
        print(f"  sent 200000 binary bytes -> server saw {got}")
        assert got == "binary:200000"

        print("\n== 4. ordering is guaranteed (it is still one TCP connection) ==")
        for i in range(5):
            await ws.send(f"m{i}")
        replies = [await ws.recv() for _ in range(5)]
        print("  ", replies)
        assert replies == [f"text:2:m{i}" for i in range(5)]

        await ws.close(code=1000)
    print("\nOK")


async def main() -> None:
    async with serve(inspect_handler, "127.0.0.1", 0) as server:
        await demo(server.sockets[0].getsockname()[1])


if __name__ == "__main__":
    asyncio.run(main())
