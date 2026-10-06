"""
FOUNDATION LEVEL 10 - Cross-language interop: the headline feature
===================================================================
This is why protobuf exists. Everything else in this folder - the schema, the
field numbers, the evolution rules - is machinery in service of one claim:

    bytes encoded by ANY language decode correctly in EVERY other language,
    with no adapter, no negotiation and no shared runtime.

Both sides here were compiled from the same ../proto/l10_interop.proto. They
share NOTHING else: not a library, not a process, not an interpreter. Go has
no idea Python exists.

The demo works in two independent ways, so it proves the claim even if you
only ever run one of the two files:

  1. Each file carries BOTH languages' bytes as hex constants below. Python
     asserts it re-produces PY_ENCODED_HEX and asserts it can decode
     GO_ENCODED_HEX. The Go file has the identical pair of constants and
     makes the mirror-image assertions. Neither file can pass unless the two
     languages really do agree byte-for-byte.
  2. Each file also WRITES its own bytes to a shared temp directory and, if
     the other language's file is already there, decodes it live. Run this
     file and then the Go one (in either order) to see that half light up.

You will learn
  * that a .proto is the only contract needed between two languages
  * PROOF: Python decodes Go-encoded bytes, field for field
  * PROOF: Python's own encoding matches the byte sequence Go produces
  * that non-ASCII text survives, because a protobuf string is defined as UTF-8
  * why this makes protobuf the default for polyglot systems, and what the
    corresponding obligation is (the .proto must be shared, not copy-pasted)

Run it   python 10_cross_language_interop.py
Then     go run ./Protobuf/Foundation/golang/10_cross_language_interop
"""
import os
import pathlib
import tempfile

import l10_interop_pb2 as pb

# ---------------------------------------------------------------------------
# The two byte sequences, written down as constants in BOTH language files.
# These are not computed here - they are checked in, so this file makes a
# falsifiable claim about what the other language produces.
# ---------------------------------------------------------------------------
PY_LANGUAGE, PY_TEXT = "en", "hello from the other language"
PY_ENCODED_HEX = "0a02656e121d68656c6c6f2066726f6d20746865206f74686572206c616e67756167651801"

# Note the non-ASCII characters: a protobuf `string` is defined as UTF-8, so
# Go writes the same bytes Python would for the same characters.
GO_LANGUAGE, GO_TEXT = "no", "hei fra det andre spraaket, med å og ø"
GO_ENCODED_HEX = ("0a026e6f1228686569206672612064657420616e6472652073707261616b65742c"
                  "206d656420c3a5206f6720c3b81801")

SCHEMA_VERSION = 1

# Both languages agree on this one path, and nothing else.
SHARED_DIR = pathlib.Path(tempfile.gettempdir()) / "protobuf_foundation_interop"
PY_FILE, GO_FILE = "from_python.pb", "from_go.pb"

if __name__ == "__main__":
    print("== 1. Python encodes a Greeting ==")
    mine = pb.Greeting(language=PY_LANGUAGE, text=PY_TEXT, schema_version=SCHEMA_VERSION)
    encoded = mine.SerializeToString()
    print(f"  {mine.language!r} / {mine.text!r}")
    print(f"  {len(encoded)} bytes: {encoded.hex()}")
    # Claim 1: these are exactly the bytes the Go file also asserts it produces.
    assert encoded.hex() == PY_ENCODED_HEX, "Python's encoding drifted from the shared constant"
    print("  matches PY_ENCODED_HEX, the constant the Go file also carries.")

    print("\n== 2. THE PROOF: Python decodes bytes that Go produced ==")
    # These bytes were produced by protoc-gen-go-generated Go code. Nothing in
    # this process has ever seen Go, and no conversion step is involved.
    from_go = pb.Greeting()
    from_go.ParseFromString(bytes.fromhex(GO_ENCODED_HEX))
    print(f"  raw bytes from Go : {GO_ENCODED_HEX[:48]}...")
    print(f"  language          : {from_go.language!r}")
    print(f"  text              : {from_go.text!r}")
    print(f"  schema_version    : {from_go.schema_version}")
    assert from_go.language == GO_LANGUAGE
    assert from_go.text == GO_TEXT
    assert from_go.schema_version == SCHEMA_VERSION
    print("  every field, exactly as Go set it. No adapter, no shared runtime.")

    print("\n== 3. UTF-8 is part of the contract ==")
    # `string` in a .proto means "UTF-8 bytes". That is why the two languages
    # agree on non-ASCII text without anyone configuring an encoding.
    special = [ch for ch in from_go.text if ord(ch) > 127]
    print(f"  non-ASCII characters recovered: {special}")
    print(f"  'å' occupies {len('å'.encode())} bytes on the wire (c3 a5), "
          f"'o' occupies {len('o'.encode())}")
    assert special == ["å", "ø"]
    assert "c3a5" in GO_ENCODED_HEX, "the UTF-8 bytes for a-ring are right there in the wire data"
    print("  a `bytes` field, by contrast, is arbitrary binary with NO encoding")
    print("  promised - use `string` for text and `bytes` for everything else.")

    print("\n== 4. and the reverse direction ==")
    # Re-encoding what Go sent gives Go's bytes back unchanged, which means the
    # round trip through Python is lossless in both directions.
    assert from_go.SerializeToString().hex() == GO_ENCODED_HEX
    print("  re-encoding Go's message in Python reproduces Go's bytes exactly")
    print("  -> the two implementations are not merely compatible, they are")
    print("     byte-for-byte deterministic for this message.")

    print("\n== 5. live exchange through a shared file ==")
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    (SHARED_DIR / PY_FILE).write_bytes(encoded)
    print(f"  wrote my bytes to {SHARED_DIR / PY_FILE}")

    go_path = SHARED_DIR / GO_FILE
    if go_path.exists():
        live = pb.Greeting()
        live.ParseFromString(go_path.read_bytes())
        print(f"  found {GO_FILE} from a real Go run and decoded it live:")
        print(f"    language={live.language!r} text={live.text!r} version={live.schema_version}")
        assert live.language and live.schema_version == SCHEMA_VERSION
        print("  that file was written by a Go process, on its own, at another time.")
    else:
        print(f"  {GO_FILE} is not there yet - run the Go level to create it:")
        print("      go run ./Protobuf/Foundation/golang/10_cross_language_interop")
        print("  then re-run this file to see it decoded live. (The hex constants")
        print("  above already prove the point; this is the hands-on version.)")

    print("\n== 6. the obligation that comes with this ==")
    print("  Interop is guaranteed by the SCHEMA, so the schema has to be shared")
    print("  for real - one file, one source of truth, vendored or pulled from a")
    print("  registry. Two hand-maintained copies of the same .proto in two repos")
    print("  is the failure mode: they drift, level 06's rules get broken on one")
    print("  side only, and the bytes stop meaning the same thing. Keeping that")
    print("  from happening is exactly what buf's registry and `buf breaking`")
    print("  (level 08) are for.")
    print(f"  (files exchanged under {SHARED_DIR}{os.sep})")

    print("\nOK")
