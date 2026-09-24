"""
FOUNDATION LEVEL 02 - Nested messages: a message inside a message
==================================================================
So far every field has been a scalar. This level adds the other kind: a field
whose type is another MESSAGE. That is how protobuf builds structure, and it
is the same mechanism all the way down - there is no special "object" type,
just messages containing messages.

The one genuinely new behaviour is PRESENCE. A scalar string has no way to
say "absent" (level 04 explains why), but a message field always does:
`Person` with no `home` at all is a different, detectable state from `Person`
with a `home` whose every field happens to be empty.

You will learn
  * how to declare and set a message-typed field
  * that a nested message is encoded length-delimited: exactly like a string,
    but the "text" inside is itself a little protobuf message
  * HasField() on a message field - real presence, absent vs present-but-empty
  * the Python quirk that decides when a sub-message springs into existence:
    READING one does not create it, WRITING through one does
  * that nesting costs only a tag + a length byte, so deep structure is cheap

Run it   python 02_nested_messages.py
"""
import l02_nested_pb2 as pb

if __name__ == "__main__":
    print("== 1. building a nested value ==")
    # Two equivalent styles. Nested-constructor form is the clearest:
    ada = pb.Person(name="Ada", home=pb.Address(street="12 Dean St", city="Oslo", country_code="NO"))
    # ...and mutating form, which is what you use when filling a message gradually:
    grace = pb.Person(name="Grace")
    grace.home.street = "1 Navy Yard"   # writing THROUGH `home` creates it
    grace.home.city = "Arlington"
    grace.home.country_code = "US"

    print(f"  ada.home.city   = {ada.home.city!r}")
    print(f"  grace.home.city = {grace.home.city!r}")
    assert ada.home.city == "Oslo" and grace.home.city == "Arlington"

    print("\n== 2. how nesting looks on the wire ==")
    data = ada.SerializeToString()
    print(f"  {len(data)} bytes: {data.hex()}")
    # Field 2 (`home`) has tag byte 0x12 = (2 << 3) | 2, i.e. "field 2,
    # length-delimited". The very next byte is the LENGTH of the whole encoded
    # Address, and then the Address's own fields follow, using their OWN field
    # numbers 1/2/3 - restarting from 1 inside the nested scope.
    inner = ada.home.SerializeToString()
    print(f"  the Address alone encodes to {len(inner)} bytes: {inner.hex()}")
    assert bytes([0x12, len(inner)]) + inner in data, "parent embeds child verbatim after a length"
    print(f"  and the parent contains exactly  12 {len(inner):02x} <those {len(inner)} bytes>")
    print("  => a nested message is encoded like a string whose contents happen")
    print("     to be another message. That single rule is all of protobuf's")
    print("     structure; there is nothing else to learn about nesting.")
    print(f"  total overhead for wrapping the Address: {len(data) - len(inner) - len(b'Ada') - 2} bytes"
          " (one tag + one length)")

    print("\n== 3. presence: absent vs present-but-empty ==")
    # Same name in both, so the ONLY difference in the byte counts below is
    # the address field itself.
    nobody = pb.Person(name="Blank")                       # no home at all
    homeless = pb.Person(name="Blank", home=pb.Address())  # a home, entirely empty
    print(f"  no home field set     : HasField('home') -> {nobody.HasField('home')}, "
          f"{len(nobody.SerializeToString())} bytes")
    print(f"  home set to Address() : HasField('home') -> {homeless.HasField('home')}, "
          f"{len(homeless.SerializeToString())} bytes")
    assert not nobody.HasField("home")
    assert homeless.HasField("home")
    # The two are genuinely different bytes: the empty Address still emits its
    # own tag and a length of zero, which is what makes it detectable.
    assert nobody.SerializeToString() != homeless.SerializeToString()
    assert len(homeless.SerializeToString()) == len(nobody.SerializeToString()) + 2
    print("  the empty one costs 2 extra bytes (12 00 = 'field 2, length 0'):")
    print(f"    absent : {nobody.SerializeToString().hex()}")
    print(f"    empty  : {homeless.SerializeToString().hex()}")
    print("  => this matters for real APIs: 'the user cleared their address' and")
    print("     'the user did not mention their address' are different intents,")
    print("     and a message field can carry that difference. A string cannot.")

    print("\n== 4. the read-vs-write quirk ==")
    # A common source of confusion. Python creates the sub-message lazily, and
    # only a WRITE counts. This keeps `if p.HasField('home')` honest even after
    # code has read through the field defensively.
    p = pb.Person(name="Lazy")
    print(f"  fresh                  : HasField('home') -> {p.HasField('home')}")
    _ = p.home.city                  # a READ: returns "" and creates nothing
    print(f"  after reading home.city: HasField('home') -> {p.HasField('home')}")
    assert not p.HasField("home")
    p.home.city = "Bergen"           # a WRITE: creates it
    print(f"  after writing home.city: HasField('home') -> {p.HasField('home')}")
    assert p.HasField("home")
    # ClearField removes it again, back to genuinely absent.
    p.ClearField("home")
    assert not p.HasField("home")
    print("  ClearField('home') -> absent again")

    print("\n== 5. round trip ==")
    back = pb.Person()
    back.ParseFromString(data)
    assert back == ada, "nested values survive encode/decode exactly"
    assert back.home.country_code == "NO"
    print(f"  decoded: name={back.name!r} city={back.home.city!r} cc={back.home.country_code!r}")

    print("\nOK")
