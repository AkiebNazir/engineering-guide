"""
FOUNDATION LEVEL 11 (CAPSTONE) - One realistic schema, used end to end
=======================================================================
Everything from levels 00-10, combined into one schema you could defend in a
design review. ../proto/l11_capstone.proto has nested messages (02), repeated
fields (03), an `optional` field for real presence (04), an enum (05), and a
documented evolution log with a `reserved` number (06).

This program and its Go twin both read and write the SAME file format, so the
pair of them is a complete, if tiny, polyglot system: a Python service writes
shipments, a Go service consumes them, and neither one knows the other's
language. That is the whole point of the folder, demonstrated once properly.

You will learn
  * how the pieces combine in a schema you would actually ship
  * why a top-level "file" message with a schema_version beats a bare list
  * doing real work with decoded data: filtering, grouping, summing
  * checking presence to tell "not delivered yet" from "delivered at time 0"
  * the size win over equivalent JSON, measured on realistic data
  * that the Go twin reads this exact file, and writes one this reads back

Run it   python 11_capstone_realistic_schema.py
Then     go run ./Protobuf/Foundation/golang/11_capstone_realistic_schema
"""
import json
import pathlib
import tempfile

import l11_capstone_pb2 as pb

SCHEMA_VERSION = 2   # matches the evolution log in ../proto/l11_capstone.proto

# Shared with the Go twin. Each language writes its own file and reads the
# other's if it is present.
SHARED_DIR = pathlib.Path(tempfile.gettempdir()) / "protobuf_foundation_capstone"
PY_FILE, GO_FILE = "shipments_from_python.pb", "shipments_from_go.pb"


def build_shipment_file() -> pb.ShipmentFile:
    """Build a realistic payload, exercising every construct in the schema."""
    doc = pb.ShipmentFile(schema_version=SCHEMA_VERSION)

    # A delivered shipment. `delivered_unix_millis` is set, so presence is on.
    first = doc.shipments.add(
        shipment_id="SHP-1001",
        carrier=pb.CARRIER_DHL,                                  # enum (level 05)
        destination=pb.Address(line1="12 Dean St", city="Oslo",   # nested (level 02)
                               country_code="NO"),
        delivered_unix_millis=1_700_000_000_000,                  # optional (level 04)
    )
    first.tags.extend(["priority", "signed-for"])                 # repeated scalar (03)
    first.items.add(sku="WIDGET-1", qty=2, unit_price_cents=1999)  # repeated message (03)
    first.items.add(sku="CABLE-3", qty=1, unit_price_cents=499)

    # An in-transit shipment. `delivered_unix_millis` is deliberately NOT set -
    # that absence is the data, and level 04 is why it survives the round trip.
    second = doc.shipments.add(
        shipment_id="SHP-1002",
        carrier=pb.CARRIER_POSTNORD,
        destination=pb.Address(line1="1 Storgata", city="Bergen", country_code="NO"),
    )
    second.tags.append("fragile")
    second.items.add(sku="WIDGET-1", qty=10, unit_price_cents=1999)

    # A third, with an enum value left unset, to show *_UNSPECIFIED in action.
    third = doc.shipments.add(
        shipment_id="SHP-1003",
        destination=pb.Address(line1="9 Karl Johans gate", city="Oslo", country_code="NO"),
    )
    third.items.add(sku="CABLE-3", qty=3, unit_price_cents=499)
    return doc


def as_plain_dict(doc: pb.ShipmentFile) -> dict:
    """The same data as nested dicts, purely to size the JSON comparison."""
    return {
        "schema_version": doc.schema_version,
        "shipments": [
            {
                "shipment_id": s.shipment_id,
                "carrier": pb.Carrier.Name(s.carrier),
                "destination": {"line1": s.destination.line1,
                                "city": s.destination.city,
                                "country_code": s.destination.country_code},
                "items": [{"sku": i.sku, "qty": i.qty,
                           "unit_price_cents": i.unit_price_cents} for i in s.items],
                "tags": list(s.tags),
                **({"delivered_unix_millis": s.delivered_unix_millis}
                   if s.HasField("delivered_unix_millis") else {}),
            }
            for s in doc.shipments
        ],
    }


if __name__ == "__main__":
    print("== 1. build the payload ==")
    doc = build_shipment_file()
    print(f"  schema_version = {doc.schema_version}, {len(doc.shipments)} shipments")
    for s in doc.shipments:
        delivered = (s.delivered_unix_millis if s.HasField("delivered_unix_millis")
                     else "not delivered")
        print(f"    {s.shipment_id}  {pb.Carrier.Name(s.carrier):<18} "
              f"{s.destination.city:<7} items={len(s.items)} delivered={delivered}")

    print("\n== 2. encode, and compare against JSON ==")
    encoded = doc.SerializeToString()
    as_json = json.dumps(as_plain_dict(doc), separators=(",", ":")).encode()
    print(f"  protobuf : {len(encoded):>4} bytes")
    print(f"  JSON     : {len(as_json):>4} bytes (compact, no whitespace)")
    saved = 100 - round(100 * len(encoded) / len(as_json))
    print(f"  -> {saved}% smaller. On realistic nested data the gap is much wider")
    print("     than level 00's single field, because every repeated element in")
    print("     JSON re-sends all of its key names as text.")
    assert len(encoded) < len(as_json)

    print("\n== 3. write it, then read it back as a separate step ==")
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    path = SHARED_DIR / PY_FILE
    path.write_bytes(encoded)                       # binary mode (level 09)
    reloaded = pb.ShipmentFile()
    reloaded.ParseFromString(path.read_bytes())
    print(f"  wrote and re-read {path.name} ({len(encoded)} bytes)")
    assert reloaded == doc, "the whole document round-trips exactly"
    print("  the reloaded document is equal to the original, field for field.")

    print("\n== 4. presence survived, and it matters ==")
    delivered_flags = [(s.shipment_id, s.HasField("delivered_unix_millis"))
                       for s in reloaded.shipments]
    for shipment_id, has in delivered_flags:
        print(f"    {shipment_id}: HasField('delivered_unix_millis') -> {has}")
    assert delivered_flags == [("SHP-1001", True), ("SHP-1002", False), ("SHP-1003", False)]
    print("  had this field been a plain int64, SHP-1002 would be indistinguishable")
    print("  from 'delivered at midnight on 1 January 1970' (level 04).")

    print("\n== 5. doing real work with the decoded data ==")
    # Ordinary application code. The decoded message is just an object.
    total_cents = sum(i.qty * i.unit_price_cents
                      for s in reloaded.shipments for i in s.items)
    print(f"  total value across all shipments : {total_cents / 100:.2f}")
    assert total_cents == 2 * 1999 + 499 + 10 * 1999 + 3 * 499

    by_carrier: dict[str, int] = {}
    for s in reloaded.shipments:
        by_carrier[pb.Carrier.Name(s.carrier)] = by_carrier.get(pb.Carrier.Name(s.carrier), 0) + 1
    print(f"  shipments per carrier            : {by_carrier}")
    assert by_carrier["CARRIER_UNSPECIFIED"] == 1, "SHP-1003 never had a carrier set"

    pending = [s.shipment_id for s in reloaded.shipments
               if not s.HasField("delivered_unix_millis")]
    print(f"  still in transit                 : {pending}")
    assert pending == ["SHP-1002", "SHP-1003"]

    widget_qty = sum(i.qty for s in reloaded.shipments for i in s.items if i.sku == "WIDGET-1")
    print(f"  total WIDGET-1 units             : {widget_qty}")
    assert widget_qty == 12

    print("\n== 6. the evolution log is part of the design ==")
    print("  ../proto/l11_capstone.proto records, in comments beside the fields:")
    print("    v1 : fields 1-5")
    print("    v2 : added optional delivered_unix_millis (6)")
    print("    v2 : deleted tracking_url (7) -> `reserved 7; reserved \"tracking_url\";`")
    print("  A v1 reader handed this file ignores field 6 and keeps it on re-encode")
    print("  (level 06). A v3 that needs a new field appends number 8 - never 7.")
    print(f"  The payload also states its own version ({reloaded.schema_version}), which costs")
    print("  2 bytes and tells a future reader which rules produced these bytes.")

    print("\n== 7. the Go twin reads this exact file ==")
    go_path = SHARED_DIR / GO_FILE
    if go_path.exists():
        from_go = pb.ShipmentFile()
        from_go.ParseFromString(go_path.read_bytes())
        print(f"  found {GO_FILE} written by a real Go run:")
        print(f"    schema_version={from_go.schema_version}, "
              f"{len(from_go.shipments)} shipments")
        for s in from_go.shipments:
            print(f"      {s.shipment_id}  {pb.Carrier.Name(s.carrier):<18} "
                  f"{s.destination.city} items={len(s.items)}")
        assert from_go.schema_version == SCHEMA_VERSION
        assert len(from_go.shipments) > 0
        # The real test of a shared format: Python understands Go's presence bits.
        go_pending = [s.shipment_id for s in from_go.shipments
                      if not s.HasField("delivered_unix_millis")]
        print(f"    in transit, per Python's reading of Go's bytes: {go_pending}")
        print("  a Go process wrote that file. Nothing was converted or negotiated.")
    else:
        print(f"  {GO_FILE} is not there yet. Run the Go twin:")
        print("      go run ./Protobuf/Foundation/golang/11_capstone_realistic_schema")
        print("  then re-run this file - it will decode Go's shipments above.")
        print(f"  (both languages exchange files under {SHARED_DIR})")

    print("\n== where this leaves you ==")
    print("  You can now design a protobuf schema, evolve it without breaking")
    print("  anyone, and move it between languages. Level 12 is the one-page")
    print("  bridge to gRPC; level 13 is the optional wire-format deep dive.")

    print("\nOK")
