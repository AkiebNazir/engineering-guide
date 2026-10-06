"""
FOUNDATION LEVEL 08 - Two toolchains, one schema, identical bytes
==================================================================
Every level so far used `protoc`, the official compiler. In real teams you
will meet a second toolchain, `buf`, and the obvious worry is whether it
produces different, incompatible code. This level settles that by running
both over ../proto/l08_toolchains.proto and comparing what comes out.

The short answer: buf replaces the DRIVER, not the code generator. Look at
../buf.gen.yaml - it says `local: protoc-gen-go`, the exact same plugin
binary protoc invokes. So the generated Go is byte-identical, and the encoded
bytes are identical in both languages. buf's value is entirely in the
workflow around codegen:

  protoc                                    buf
  ------------------------------------      ------------------------------------
  every include path and input file on      the schema is declared once in
  the command line, every time              buf.yaml and checked in
  plugin flags memorised or buried in       plugin config declared in
  a Makefile                                buf.gen.yaml, reproducible in CI
  imports resolved from your filesystem     dependencies resolved and version-
  (vendor other people's protos by hand)    pinned from a registry
  no opinion on schema quality              `buf lint` enforces conventions
  no protection against rule 2 of           `buf breaking` diffs against the
  level 06                                  last release and FAILS the build

That last row is the one that makes teams switch: level 06 listed a pile of
changes that break compatibility silently, and `buf breaking` is how you stop
them at review time instead of discovering them in production.

You will learn
  * that both toolchains call the SAME codegen plugins, so neither owns the format
  * PROOF: buf-generated code, run in a separate process, produces byte-identical
    serialized output to protoc-generated code
  * the one place the two compilers genuinely differ, and why it cannot affect
    the binary encoding
  * what buf adds that protoc has no answer for: lint and breaking-change checks
  * that a .proto is a portable asset, not a protoc artefact

Run it   python 08_protoc_and_buf_same_bytes.py
"""
import pathlib
import subprocess
import sys

from google.protobuf import descriptor_pb2

# The protoc-generated module, exactly like every other level in this folder.
import l08_toolchains_pb2 as protoc_pb

# ../generate.sh wrote buf's output here. It is checked in, so this level runs
# even on a machine that has never had buf installed.
BUF_PY_DIR = pathlib.Path(__file__).resolve().parent.parent / "buf_out" / "python"

# The message both toolchains will be asked to encode.
NAME, VALUE, LABELS = "cpu.load", 0.75, ["host=a", "env=prod"]

# Written down here so this file states its claim up front rather than merely
# comparing two things it computed itself. Level 10 reuses this same trick
# across languages.
EXPECTED_HEX = "0a086370752e6c6f616411000000000000e83f1a06686f73743d611a08656e763d70726f64"


def encode_with_buf_generated_code() -> tuple[str, str]:
    """Run buf's generated module in a SEPARATE process and return (msg hex, descriptor hex).

    A separate process is not for show. Both modules describe a file called
    "l08_toolchains.proto", and protobuf keeps one global descriptor pool per
    process - importing both here would be a duplicate-registration error.
    Two processes, two pools, no conflict. (Go has the identical restriction,
    which is why the Go version of this level compares source files instead.)
    """
    program = (
        "import l08_toolchains_pb2 as pb\n"
        f"m = pb.Metric(name={NAME!r}, value={VALUE!r}, labels={LABELS!r})\n"
        "print(m.SerializeToString().hex())\n"
        "print(pb.DESCRIPTOR.serialized_pb.hex())\n"
    )
    # cwd puts buf's copy first on sys.path, so this child cannot see ours.
    result = subprocess.run(
        [sys.executable, "-c", program],
        cwd=BUF_PY_DIR, capture_output=True, text=True, check=True,
    )
    msg_hex, descriptor_hex = result.stdout.split()
    return msg_hex, descriptor_hex


def strip_json_names(serialized: bytes) -> bytes:
    """Return a descriptor with every explicit json_name removed.

    json_name is a DERIVED value: lowerCamelCase of the field name, used only
    by the JSON mapping. buf's compiler writes it out explicitly; protoc
    leaves it implicit. Clearing it on both sides shows the descriptors are
    otherwise the same file.
    """
    fdp = descriptor_pb2.FileDescriptorProto()
    fdp.ParseFromString(serialized)
    for message in fdp.message_type:
        for field in message.field:
            field.ClearField("json_name")
    return fdp.SerializeToString()


if __name__ == "__main__":
    print("== 1. encode with the protoc-generated code ==")
    metric = protoc_pb.Metric(name=NAME, value=VALUE, labels=LABELS)
    protoc_hex = metric.SerializeToString().hex()
    print(f"  Metric(name={NAME!r}, value={VALUE}, labels={LABELS})")
    print(f"  {len(metric.SerializeToString())} bytes: {protoc_hex}")
    assert protoc_hex == EXPECTED_HEX, "protoc output changed unexpectedly"

    if not BUF_PY_DIR.exists():
        # Graceful degradation: the lesson above still stands, we just cannot
        # demonstrate it on this machine.
        print("\n== 2. buf ==")
        print(f"  SKIPPED: {BUF_PY_DIR} is missing.")
        print("  Install buf and re-run ../generate.sh to enable this half:")
        print("      go install github.com/bufbuild/buf/cmd/buf@latest")
        print("\nOK")
        raise SystemExit(0)

    print("\n== 2. encode with the buf-generated code, in a separate process ==")
    buf_hex, buf_descriptor_hex = encode_with_buf_generated_code()
    print(f"  {len(bytes.fromhex(buf_hex))} bytes: {buf_hex}")

    print("\n== 3. THE PROOF ==")
    print(f"  protoc-generated code encoded : {protoc_hex}")
    print(f"  buf-generated code encoded    : {buf_hex}")
    assert buf_hex == protoc_hex == EXPECTED_HEX
    print("  BYTE-FOR-BYTE IDENTICAL.")
    print("  Neither toolchain owns the wire format. The .proto file does.")

    # Decoding across the boundary, for good measure: our protoc-generated
    # class reads what buf's class wrote, with no adapter of any kind.
    decoded = protoc_pb.Metric()
    decoded.ParseFromString(bytes.fromhex(buf_hex))
    assert decoded == metric
    print(f"  and our class decodes buf's bytes exactly: name={decoded.name!r} "
          f"value={decoded.value} labels={list(decoded.labels)}")

    print("\n== 4. where the two compilers DO differ (and why it is harmless) ==")
    ours = protoc_pb.DESCRIPTOR.serialized_pb
    theirs = bytes.fromhex(buf_descriptor_hex)
    print(f"  compiled descriptor size: protoc {len(ours)} bytes, buf {len(theirs)} bytes")
    if ours == theirs:
        print("  the descriptors are byte-identical on this machine.")
    else:
        print("  they differ - buf's compiler records the derived `json_name` for")
        print("  every field explicitly, where protoc leaves it implicit:")
        print(f"    protoc: ...\\x04name\\x18\\x01 \\x01(\\t...")
        print(f"    buf   : ...\\x04name\\x18\\x01 \\x01(\\tR\\x04name...   <- the R\\x04name")
        assert strip_json_names(ours) == strip_json_names(theirs), \
            "after clearing json_name the descriptors must match exactly"
        print("  with json_name cleared on both sides the descriptors match exactly.")
        print("  This CANNOT affect the binary encoding: json_name is consulted only")
        print("  by the JSON mapping, and its value here is the default anyway")
        print("  (lowerCamelCase of the field name). Section 3 already proved the")
        print("  binary bytes are identical - this is a descriptor-verbosity")
        print("  difference, not a compatibility one.")

    print("\n== 5. what buf adds that protoc cannot ==")
    print("  ../buf.yaml declares the schema once, so `buf generate` needs no flags:")
    print("      protoc -I proto --go_out=. --go_opt=module=... proto/*.proto")
    print("      buf generate")
    print("  and it unlocks two commands protoc has no equivalent for:")
    print("      buf lint      - enforce naming/structure conventions across the repo")
    print("      buf breaking  - diff this schema against the last released version")
    print("                      and FAIL if any change from level 06's breaking list")
    print("                      slipped in (renumbered field, changed type, reused tag)")
    print("  Try it:  cd .. && buf lint && buf breaking --against '.git#branch=main'")
    print("  That is the real reason to adopt buf. Not different bytes - the same")
    print("  bytes, with rule 2 of level 06 enforced by CI instead of by memory.")

    print("\nOK")
