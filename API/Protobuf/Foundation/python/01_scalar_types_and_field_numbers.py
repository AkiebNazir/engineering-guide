"""
FOUNDATION LEVEL 01 - Scalar types, and why field NUMBERS are the real names
=============================================================================
Level 00 had one field numbered 1 and never explained the number. This level
is about that number, because it is the single most important idea in the
format: the wire carries field NUMBERS, never field names.

That has a consequence people find surprising the first time: you can RENAME
a field freely and every byte ever encoded still decodes correctly. The name
is a label for programmers; it is compiled away. The number is the contract.
The mirror image is also true, and is the subject of level 06: changing a
field's NUMBER breaks everything, silently.

You will learn
  * the scalar types you will actually use: string, int32/int64, bool, double, bytes
  * that `= 1` is a permanent field number, not a value, index or ordering
  * PROOF: bytes encoded from a schema calling field 1 `title` decode perfectly
    under a schema calling field 1 `name` - because the name never travelled
  * why field numbers 1-15 are worth guarding: their tag costs one byte, 16+ cost two
  * that numbers need not be contiguous or in order - only unique and stable

Run it   python 01_scalar_types_and_field_numbers.py
"""
import l01_v1_pb2 as v1  # field 1 is called `title`
import l01_v2_pb2 as v2  # field 1 is called `name`  - SAME number

if __name__ == "__main__":
    print("== 1. the scalar types you will actually use ==")
    book = v1.Book(
        title="The Go Programming Language",
        year=2015,                      # int32  - whole numbers, varint-encoded
        in_print=True,                  # bool   - one byte: 0 or 1
        price=39.99,                    # double - always 8 fixed bytes
        copies_sold=1_250_000,          # int64  - same as int32, just a wider range
        cover_thumbnail=b"\x89PNG\r\n", # bytes  - arbitrary binary, no encoding applied
    )
    for field, value in [("title", book.title), ("year", book.year), ("in_print", book.in_print),
                         ("price", book.price), ("copies_sold", book.copies_sold),
                         ("cover_thumbnail", book.cover_thumbnail)]:
        print(f"  {field:<16} = {value!r}")

    encoded = book.SerializeToString()
    print(f"\n  encoded: {len(encoded)} bytes")
    print(f"  hex    : {encoded.hex()}")
    # The strings are visible in the hex because a protobuf string is just its
    # UTF-8 bytes, stored verbatim. Everything AROUND them is the structure.
    assert b"The Go Programming Language" in encoded
    print('  the string bytes are stored verbatim - but "title" is not in there at all:')
    assert b"title" not in encoded, "field names are never encoded"
    print(f'    b"title" in encoded -> {b"title" in encoded}')

    print("\n== 2. THE PROOF: rename the field, keep the number ==")
    # l01_v2.proto is a byte-for-byte copy of l01_v1.proto with ONE edit:
    #     string title = 1;   ->   string name = 1;
    # Nothing else changed. Now parse v1's bytes with v2's schema.
    reread = v2.Book()
    reread.ParseFromString(encoded)
    print(f"  encoded with v1 (field 1 = `title`) : {book.title!r}")
    print(f"  decoded with v2 (field 1 = `name`)  : {reread.name!r}")
    assert reread.name == book.title == "The Go Programming Language"
    assert reread.year == 2015 and reread.price == 39.99 and reread.in_print is True

    # And the reverse direction, for completeness: v2's bytes under v1's schema.
    back = v1.Book()
    back.ParseFromString(reread.SerializeToString())
    assert back.title == "The Go Programming Language"
    print("  and back again, v2 -> v1: still correct")
    print("  => renaming a field is a SAFE, invisible change. The name is for you,")
    print("     not for the wire. (Renaming it in every codebase that reads it is")
    print("     still work - it is just not a DATA-compatibility problem.)")

    # The real reason this works: encoding the same value under both schemas
    # produces literally the same bytes. The schemas are wire-identical.
    assert reread.SerializeToString() == encoded
    print(f"  re-encoded under v2 == original v1 bytes: {reread.SerializeToString() == encoded}")

    print("\n== 3. why 1-15 are precious ==")
    # A field's tag byte packs the number and the wire type together:
    #     tag = (field_number << 3) | wire_type
    # Three bits go to the wire type, so numbers 1-15 fit in the remaining
    # four bits of a single byte. Number 16 needs a second byte, forever.
    for number in (1, 15, 16, 2047):
        tag = number << 3  # wire_type 0, just to size the tag
        size = 1 if tag < 0x80 else (2 if tag < 0x4000 else 3)
        print(f"  field number {number:>4} -> tag value {tag:>6} -> {size} tag byte(s)")
    print("  => put your hottest, most-repeated fields in 1-15. In a message sent")
    print("     a billion times a day, one byte per field per message is real money.")

    print("\n== 4. numbers need not be tidy ==")
    # Only two rules: unique within the message, and never changed once shipped.
    # Gaps and out-of-order declarations are completely normal in mature schemas,
    # usually because fields were deleted (see level 06's `reserved`).
    sparse = v1.Book(title="Sparse", copies_sold=5)  # sets fields 1 and 5, skips 2/3/4
    print(f"  only fields 1 and 5 set -> {len(sparse.SerializeToString())} bytes "
          f"({sparse.SerializeToString().hex()})")
    print("  unset fields cost ZERO bytes. Nothing is reserved or padded for them.")
    assert len(sparse.SerializeToString()) < len(encoded)

    print("\nOK")
