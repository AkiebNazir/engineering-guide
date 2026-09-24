"""
FOUNDATION LEVEL 06 - Schema evolution: changing a schema without breaking anything
====================================================================================
This is the reason large systems choose protobuf. Two services, deployed
weeks apart, each built against a different version of the same .proto, have
to keep talking. Protobuf makes that work - but only if you follow three
rules, which this level proves one at a time.

  RULE 1  Add fields with NEW numbers. Never change an existing field's number.
  RULE 2  Never reuse a number that was ever used, even for a deleted field.
  RULE 3  Mark deleted numbers and names `reserved` so the compiler enforces #2.

The payoff is BIDIRECTIONAL compatibility, and both directions matter:
  * backward : new code reads old bytes    (deploy a reader first - easy to believe)
  * forward  : old code reads new bytes    (a straggler reads new data - the hard one)

    ../proto/l06_v1.proto : Order { id=1, sku=2, qty=3 }
    ../proto/l06_v2.proto : the same three, plus currency=4, plus `reserved 9`

See also ../../labs/proto/evo_v1.proto / evo_v2.proto / evo_bad.proto for a
second, larger worked example - evo_bad.proto is the renumbering disaster
that rule 2 exists to prevent.

You will learn
  * PROOF of backward compatibility: v2 code reading v1 bytes
  * PROOF of forward compatibility: v1 code reading v2 bytes, and why the
    unknown field is PRESERVED rather than discarded
  * why that preservation is what makes read-modify-write through an old
    service safe instead of silently destructive
  * what `reserved` does, and that it is a compile-time guard rail
  * the full list of safe vs breaking changes, for reference

Run it   python 06_schema_evolution_rules.py
"""
from google.protobuf import descriptor_pb2

import l06_v1_pb2 as v1
import l06_v2_pb2 as v2

if __name__ == "__main__":
    print("== 1. BACKWARD compatibility: new code reads old bytes ==")
    # An old producer, still on v1, emits an order. No `currency` exists yet.
    old_bytes = v1.Order(id=1001, sku="WIDGET-1", qty=7).SerializeToString()
    print(f"  v1 wrote {len(old_bytes)} bytes: {old_bytes.hex()}")

    upgraded = v2.Order()
    upgraded.ParseFromString(old_bytes)
    print(f"  v2 reads : id={upgraded.id} sku={upgraded.sku!r} qty={upgraded.qty} "
          f"currency={upgraded.currency!r}")
    assert (upgraded.id, upgraded.sku, upgraded.qty) == (1001, "WIDGET-1", 7)
    # The field that did not exist yet simply reads as its default. That is the
    # ONLY thing that happens - no error, no warning, no special case.
    assert upgraded.currency == ""
    print("  the new field reads as its default (''). No error, no special case.")
    print("  => this is why adding a field is a non-event. Plan for the default")
    print("     being indistinguishable from 'an old client sent this' (level 04).")

    print("\n== 2. FORWARD compatibility: old code reads NEW bytes ==")
    # Now the producer is upgraded and starts sending `currency`.
    new_bytes = v2.Order(id=1002, sku="WIDGET-2", qty=3, currency="NOK").SerializeToString()
    print(f"  v2 wrote {len(new_bytes)} bytes: {new_bytes.hex()}")
    print("    ...ending in 22 03 4e4f4b = 'field 4, 3 bytes, NOK' - tag 4 is a")
    print("    number v1 has never heard of.")

    straggler = v1.Order()
    straggler.ParseFromString(new_bytes)   # does not raise
    print(f"  v1 reads : id={straggler.id} sku={straggler.sku!r} qty={straggler.qty}")
    assert (straggler.id, straggler.sku, straggler.qty) == (1002, "WIDGET-2", 3)
    assert not hasattr(straggler, "currency"), "v1 has no such attribute at all"
    print("  v1 has no `currency` attribute and does not care. It skipped tag 4.")
    print("  It could only skip it because every field on the wire carries its own")
    print("  wire type in the tag - so a parser can always tell how many bytes to")
    print("  jump, even for a field it knows nothing about. (See level 13.)")

    print("\n== 3. the unknown field is PRESERVED, not discarded ==")
    # This is the subtle, important part. v1 kept tag 4 in an "unknown fields"
    # holding area. Re-serialising puts it back, byte for byte.
    reforwarded = straggler.SerializeToString()
    print(f"  v1 re-serialises      : {reforwarded.hex()}")
    assert reforwarded == new_bytes, "nothing was lost passing through v1"
    print("  IDENTICAL to what v2 sent. The currency survived a full trip through")
    print("  a build that does not know the field exists.")
    final = v2.Order()
    final.ParseFromString(reforwarded)
    assert final.currency == "NOK"
    print(f"  v2 reads it back      : currency={final.currency!r}")
    print("  => THIS is what makes an old proxy, gateway or read-modify-write")
    print("     service safe. Without preservation, every straggler in the fleet")
    print("     would quietly strip fields it did not understand.")

    # The honest caveat: preservation is about fields v1 does not KNOW. A field
    # v1 does know, it will happily overwrite - so read-modify-write is safe for
    # unknown fields, not for concurrent edits.
    edited = v1.Order()
    edited.ParseFromString(new_bytes)
    edited.qty = 99
    after = v2.Order()
    after.ParseFromString(edited.SerializeToString())
    assert after.qty == 99 and after.currency == "NOK"
    print(f"  (v1 editing qty->99 keeps currency: qty={after.qty} currency={after.currency!r})")

    print("\n== 4. `reserved`: making rule 2 the compiler's problem ==")
    # l06_v2.proto contains:  reserved 9;  reserved "internal_note";
    # Field 9 was deleted in a past release. Somewhere out there, encoded bytes
    # with tag 9 still sit in a queue, a log or a database column. If a future
    # edit gave number 9 to a new `int32 discount`, those old bytes would parse
    # as a discount - wrong type, wrong meaning, no error anywhere.
    # The reservation is not just a comment - it is recorded in the compiled
    # descriptor, which is why tooling (like `buf breaking`) can enforce it.
    fdp = descriptor_pb2.FileDescriptorProto()
    fdp.ParseFromString(v2.Order.DESCRIPTOR.file.serialized_pb)
    order_desc = next(m for m in fdp.message_type if m.name == "Order")
    ranges = [(r.start, r.end - 1) for r in order_desc.reserved_range]
    print(f"  compiled descriptor says: reserved numbers {ranges}, "
          f"reserved names {list(order_desc.reserved_name)}")
    assert ranges == [(9, 9)] and list(order_desc.reserved_name) == ["internal_note"]

    print("  ../proto/l06_v2.proto declares:")
    print("      reserved 9;")
    print('      reserved "internal_note";')
    print("  Now `protoc` REFUSES to compile any attempt to reuse either one:")
    print("      int32 discount = 9;        -> error: field number 9 is reserved")
    print('      string internal_note = 12; -> error: field name is reserved')
    print("  The name is reserved too, so nobody accidentally revives the old")
    print("  meaning under a new number and confuses every human reader.")

    # Demonstrate the danger concretely, without needing a broken schema: a
    # tag-9 varint from the deleted field still parses fine as an unknown field.
    from_deleted_era = new_bytes + bytes([9 << 3 | 0, 42])   # tag 9, varint 42
    ancient = v2.Order()
    ancient.ParseFromString(from_deleted_era)
    assert ancient.currency == "NOK"
    assert ancient.SerializeToString() == from_deleted_era
    print(f"  proof those bytes are still out there: appending a tag-9 varint parses")
    print(f"  cleanly today ({len(from_deleted_era)} bytes) and round-trips unchanged.")
    print("  If 9 were ever reused, THAT is the byte that would be misread.")

    print("\n== 5. the reference list ==")
    safe = [
        "add a new field with a brand-new number",
        "rename a field (level 01 - the name never travels)",
        "delete a field, if you `reserved` its number and name",
        "add a new value to an enum (level 05)",
        "turn a plain scalar into `optional` (gains presence, same bytes)",
        "int32 <-> int64 <-> uint32 <-> uint64 <-> bool  (all varints; mind the range)",
        "add a brand-new message or enum type",
    ]
    breaking = [
        "change a field's NUMBER                 - the field silently vanishes",
        "change a field's TYPE across wire kinds - varint vs length-delimited: garbage",
        "reuse a number from a deleted field     - old bytes decode as the wrong thing",
        "move a field into or out of a `oneof`   - changes the generated contract",
        "change a field from repeated to single  - or the reverse",
        "renumber anything to 'tidy up'          - see ../../labs/proto/evo_bad.proto",
    ]
    print("  SAFE:")
    for item in safe:
        print(f"    + {item}")
    print("  BREAKING:")
    for item in breaking:
        print(f"    - {item}")
    print("\n  Note what makes the breaking list dangerous: almost none of it FAILS.")
    print("  It decodes, returns defaults or nonsense, and ships. The only real")
    print("  defences are `reserved` and an automated breaking-change check -")
    print("  which is exactly what `buf breaking` does, in level 08.")

    print("\nOK")
