"""
LAB 02 (basic) - Working with generated messages: defaults, presence, oneof, maps, enums
=========================================================================================
You will learn
  * proto3 has NO null: an unset string is "", an unset int is 0, an unset enum is its 0 value
  * "was it set?" (PRESENCE):
        plain scalar   -> cannot tell 0 from unset
        optional       -> HasField() works
        message field  -> HasField() works (absent vs present-but-empty)
  * oneof: setting one member clears the others  - the schema itself prevents impossible states
  * repeated / map fields behave like list / dict
  * enums: unknown numbers survive a round trip (forward compatibility)
  * copying (CopyFrom / MergeFrom) and comparison, JSON and text formats for debugging

Needs   pip install protobuf     (generated code: demo_pb2.py, made by ../generate.sh)
Run it  python 02_messages_and_field_types.py
"""
from google.protobuf import json_format, text_format
from google.protobuf.timestamp_pb2 import Timestamp

import demo_pb2 as pb

if __name__ == "__main__":
    print("== 1. defaults: no null in proto3 ==")
    u = pb.User()
    print("  name=%r id=%r role=%s active=%r tags=%r attrs=%r" % (u.name, u.id, pb.Role.Name(u.role), u.active, list(u.tags), dict(u.attrs)))
    assert (u.name, u.id, u.active, u.role) == ("", 0, False, pb.ROLE_UNSPECIFIED)

    print("\n== 2. presence: can you tell 'zero' from 'not sent'? ==")
    u = pb.User(age=0)
    print("  optional int32 age=0 : HasField('age') ->", u.HasField("age"), "  (tracked)")
    u2 = pb.User(id=0)
    print("  plain int64 id=0     : serialised size ->", u2.ByteSize(), "bytes (0 and unset look IDENTICAL on the wire)")
    assert u.HasField("age") and u2.ByteSize() == 0
    try:
        u2.HasField("id")
    except ValueError as e:
        print("  HasField('id') raises:", str(e)[:60], "...")
    print("  nested message: HasField('address') before/after touching it:", end=" ")
    a = pb.User()
    before = a.HasField("address")
    a.address.city                      # READING does not create it
    mid = a.HasField("address")
    a.address.city = "Oslo"             # WRITING does
    print(before, mid, a.HasField("address"))
    assert (before, mid, a.HasField("address")) == (False, False, True)

    print("\n== 3. oneof: only one member at a time ==")
    u = pb.User(phone="+47 555")
    print("  which:", u.WhichOneof("contact"), "->", u.phone)
    u.slack = "@ana"                    # setting slack CLEARS phone
    print("  which:", u.WhichOneof("contact"), "-> phone is now", repr(u.phone))
    assert u.WhichOneof("contact") == "slack" and u.phone == ""
    u.ClearField("contact")
    assert u.WhichOneof("contact") is None

    print("\n== 4. repeated and map fields ==")
    u = pb.User(tags=["admin"], attrs={"team": "core"})
    u.tags.append("beta")
    u.tags.extend(["eu", "vip"])
    u.attrs["region"] = "eu-west"
    print("  tags :", list(u.tags))
    print("  attrs:", dict(u.attrs))
    u.address.street = "Main St"
    u.address.city = "Oslo"
    del u.tags[0]
    assert list(u.tags) == ["beta", "eu", "vip"]

    print("\n== 5. enums and unknown values ==")
    print("  Role.Name(2) =", pb.Role.Name(2), "; Role.Value('ROLE_USER') =", pb.Role.Value("ROLE_USER"))
    newer = pb.User(id=1).SerializeToString() + bytes([0x20, 0x07])   # role = 7: a value this schema does not know
    u = pb.User.FromString(newer)
    print("  role=7 (not in our enum) survives parsing:", u.role, "-> re-serialised unchanged:", u.SerializeToString() == newer)
    assert u.role == 7 and u.SerializeToString() == newer
    print("  => never `switch` on an enum without a default branch: new values WILL arrive.")

    print("\n== 6. strict typing ==")
    for label, thunk in [("name = 5", lambda: setattr(pb.User(), "name", 5)),
                         ("id = 'x'", lambda: setattr(pb.User(), "id", "x")),
                         ("unknown field", lambda: pb.User(nmae="typo"))]:
        try:
            thunk()
        except (TypeError, ValueError) as e:
            print(f"  {label:<14} -> {type(e).__name__}")
        else:
            raise AssertionError(label)

    print("\n== 7. copy, merge, compare ==")
    a = pb.User(id=1, name="Ana", tags=["x"])
    b = pb.User()
    b.CopyFrom(a)                        # deep copy
    b.name = "Changed"
    print("  a.name after editing the copy:", a.name)
    assert a.name == "Ana" and a != b
    b.MergeFrom(pb.User(name="Merged", tags=["y"]))   # scalars overwrite, repeated APPEND
    print("  merge -> name:", b.name, " tags:", list(b.tags))
    assert list(b.tags) == ["x", "y"] and b.name == "Merged"
    assert pb.User(id=1) == pb.User(id=1)

    print("\n== 8. debugging formats ==")
    ts = Timestamp()
    ts.FromJsonString("2026-09-21T10:30:00Z")
    u = pb.User(id=150, name="Ana", role=pb.ROLE_ADMIN, created_at=ts, tags=["a", "b"], attrs={"k": "v"})
    print("  text format:\n" + "\n".join("    " + line for line in text_format.MessageToString(u).splitlines()))
    js = json_format.MessageToJson(u, indent=None)
    print("  JSON:", js)
    assert '"id": "150"' in js, "int64 becomes a JSON STRING (JavaScript cannot hold 64-bit ints)"
    assert json_format.Parse(js, pb.User()) == u
    print("  (canonical JSON: lowerCamelCase names, int64 as strings, enum names, Timestamp as RFC 3339)")
    print("\nOK")
