"""
LAB 03 (advanced) - Evolving a schema without breaking anyone (the golden rules, proven)
========================================================================================
Two services, deployed at DIFFERENT times, exchange Customer messages.
Old code and new code will meet in production. Protobuf is designed for that - IF you follow the rules.

You will learn (and watch fail when broken)
  RULE 1  adding a field is always safe         -> old readers skip it; new readers see the default
  RULE 2  unknown fields are PRESERVED           -> a proxy running old code does not destroy new data
  RULE 3  renaming a field is safe               -> names are not on the wire, only numbers
  RULE 4  NEVER change a field number/meaning    -> silent data corruption
  RULE 5  NEVER reuse a deleted number           -> `reserved 3;` makes protoc refuse it
  RULE 6  handle the default: 0/""/false may mean "old writer never set it"

  v1 (proto/evo_v1.proto): id=1 name=2 phone=3
  v2 (proto/evo_v2.proto): id=1 name=2 email=4 phones=5      reserved 3
  bad(proto/evo_bad.proto): id=1 name=2 nickname=3           <- REUSED tag 3

Needs   pip install protobuf     (generated code: evo_*_pb2.py, made by ../generate.sh)
Run it  python 03_schema_evolution.py
"""
import evo_bad_pb2 as bad
import evo_v1_pb2 as v1
import evo_v2_pb2 as v2

if __name__ == "__main__":
    print("== RULE 1: new writer -> OLD reader (email/phones are unknown to v1) ==")
    new_msg = v2.Customer(id=7, name="Ana", email="ana@x.io", phones=["+47 1", "+47 2"]).SerializeToString()
    old_view = v1.Customer.FromString(new_msg)
    print("  v1 reader sees: id=%d name=%r phone=%r   (no crash; new fields skipped)" % (old_view.id, old_view.name, old_view.phone))
    assert (old_view.id, old_view.name, old_view.phone) == (7, "Ana", "")

    print("\n== RULE 1b: old writer -> NEW reader (new fields take their defaults) ==")
    old_msg = v1.Customer(id=8, name="Ben", phone="+47 999").SerializeToString()
    new_view = v2.Customer.FromString(old_msg)
    print("  v2 reader sees: id=%d name=%r email=%r phones=%r" % (new_view.id, new_view.name, new_view.email, list(new_view.phones)))
    assert new_view.email == "" and list(new_view.phones) == []
    print("  RULE 6: email == \"\" means 'not provided by an old writer' - code must tolerate it.")

    print("\n== RULE 2: unknown fields survive a round trip through OLD code ==")
    #   service A (v2) --> proxy (still v1!) --> service B (v2)
    passed_through = v1.Customer.FromString(new_msg).SerializeToString()   # the proxy parses and re-serialises
    final = v2.Customer.FromString(passed_through)
    print("  after the v1 proxy, v2 still has email=%r phones=%r" % (final.email, list(final.phones)))
    assert final.email == "ana@x.io" and list(final.phones) == ["+47 1", "+47 2"]
    print("  (protobuf keeps unrecognised fields as 'unknown fields'; JSON-based proxies usually drop them)")

    print("\n== RULE 3: a rename is invisible on the wire ==")
    a = v1.Customer(id=1, name="x", phone="+1").SerializeToString()
    print("  bytes of a v1 Customer:", a.hex(" "))
    assert b"phone" not in a and b"name" not in a
    print("  the words 'phone' / 'name' appear nowhere: only numbers travel. Renaming `phone` to")
    print("  `phone_number` (same number, same type) leaves every stored byte valid. What DOES break:")
    print("  generated-code call sites, and JSON payloads (JSON uses the names).")

    print("\n== RULE 4/5: reusing tag 3 with a NEW meaning corrupts data SILENTLY ==")
    stored_last_year = v1.Customer(id=9, name="Cy", phone="+47 555 0100").SerializeToString()
    corrupted = bad.Customer.FromString(stored_last_year)       # new code reads OLD stored data
    print("  data written as phone='+47 555 0100' is read by new code as nickname=%r" % corrupted.nickname)
    assert corrupted.nickname == "+47 555 0100"
    print("  no error, no warning: a phone number is now displayed as a nickname.")
    print("  Same wire type => the parser cannot know. That is why v2 says `reserved 3;`")

    print("\n== RULE 4b: changing the TYPE of an existing number ==")
    #   int32 id=1 -> string id=1 : wire type changes from varint to length-delimited
    as_string_id = bytes([0x0A, 0x01, 0x37])            # field 1, LEN, "7"  (what a `string id = 1` writer sends)
    r = v1.Customer.FromString(as_string_id)
    print("  a reader expecting varint field 1 got LEN data -> id=%d (silently ignored, kept as unknown)" % r.id)
    assert r.id == 0

    print("\n== the compiler enforces reserved ==")
    import subprocess, sys, tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, "oops.proto").write_text(
            'syntax = "proto3";\nmessage Customer {\n  reserved 3;\n  string nickname = 3;\n}\n')
        r = subprocess.run([sys.executable, "-m", "grpc_tools.protoc", f"-I{d}", f"--python_out={d}", f"{d}/oops.proto"],
                           capture_output=True, text=True)
        print("  protoc exit code:", r.returncode)
        print("  protoc says     :", r.stderr.strip().splitlines()[0][:100])
        assert r.returncode != 0 and "reserved" in r.stderr

    print("\nCHECKLIST for every schema change")
    for line in ["adding a field with a NEW number ............... safe",
                 "removing a field: `reserved` its number+name ... safe",
                 "renaming a field ............................... safe on the wire (breaks JSON + generated code)",
                 "int32 <-> int64 <-> uint32 <-> bool ............ compatible-ish (truncation!); avoid",
                 "changing a number, or reusing one .............. NEVER",
                 "changing scalar <-> message, or repeated <-> scalar .. NEVER (repeated packed <-> unpacked is OK)"]:
        print("  -", line)
    print("\nOK")
