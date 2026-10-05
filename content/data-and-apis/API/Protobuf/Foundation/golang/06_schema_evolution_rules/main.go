/*
FOUNDATION LEVEL 06 - Schema evolution: changing a schema without breaking anything
====================================================================================
This is the reason large systems choose protobuf. Two services, deployed
weeks apart, each built against a different version of the same .proto, have
to keep talking. Protobuf makes that work - but only if you follow three
rules, which this level proves one at a time.

  - RULE 1  Add fields with NEW numbers. Never change an existing field's number.
  - RULE 2  Never reuse a number that was ever used, even for a deleted field.
  - RULE 3  Mark deleted numbers and names `reserved` so the compiler enforces #2.

The payoff is BIDIRECTIONAL compatibility, and both directions matter:

  - backward: new code reads old bytes  (deploy a reader first - easy to believe)
  - forward:  old code reads new bytes  (a straggler reads new data - the hard one)

../../proto/l06_v1.proto is Order{id=1, sku=2, qty=3}; ../../proto/l06_v2.proto
is the same three, plus currency=4, plus `reserved 9`.

See also ../../../labs/proto/evo_v1.proto, evo_v2.proto and evo_bad.proto for
a second, larger worked example - evo_bad.proto is the renumbering disaster
that rule 2 exists to prevent.

You will learn
  - PROOF of backward compatibility: v2 code reading v1 bytes
  - PROOF of forward compatibility: v1 code reading v2 bytes, and why the
    unknown field is PRESERVED rather than discarded
  - why that preservation is what makes read-modify-write through an old
    service safe instead of silently destructive
  - what `reserved` does, and that it is a compile-time guard rail
  - the full list of safe vs breaking changes, for reference

Run it   go run ./Protobuf/Foundation/golang/06_schema_evolution_rules
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l06v1"
	"dsapractice/api/Protobuf/Foundation/golang/pb/l06v2"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func mustMarshal(m proto.Message) []byte {
	data, err := proto.Marshal(m)
	must(err == nil, "marshal")
	return data
}

func main() {
	fmt.Println("== 1. BACKWARD compatibility: new code reads old bytes ==")
	// An old producer, still on v1, emits an order. No `currency` exists yet.
	oldBytes := mustMarshal(&l06v1.Order{Id: 1001, Sku: "WIDGET-1", Qty: 7})
	fmt.Printf("  v1 wrote %d bytes: %x\n", len(oldBytes), oldBytes)

	upgraded := &l06v2.Order{}
	must(proto.Unmarshal(oldBytes, upgraded) == nil, "v2 parses v1 bytes")
	fmt.Printf("  v2 reads : id=%d sku=%q qty=%d currency=%q\n",
		upgraded.GetId(), upgraded.GetSku(), upgraded.GetQty(), upgraded.GetCurrency())
	must(upgraded.GetId() == 1001 && upgraded.GetSku() == "WIDGET-1" && upgraded.GetQty() == 7,
		"the v1 fields all decoded")
	// The field that did not exist yet simply reads as its default. That is
	// the ONLY thing that happens - no error, no warning, no special case.
	must(upgraded.GetCurrency() == "", "the new field reads as its default")
	fmt.Println("  the new field reads as its default (\"\"). No error, no special case.")
	fmt.Println("  => this is why adding a field is a non-event. Plan for the default")
	fmt.Println("     being indistinguishable from 'an old client sent this' (level 04).")

	fmt.Println("\n== 2. FORWARD compatibility: old code reads NEW bytes ==")
	// Now the producer is upgraded and starts sending `currency`.
	newBytes := mustMarshal(&l06v2.Order{Id: 1002, Sku: "WIDGET-2", Qty: 3, Currency: "NOK"})
	fmt.Printf("  v2 wrote %d bytes: %x\n", len(newBytes), newBytes)
	fmt.Println("    ...ending in 22 03 4e4f4b = 'field 4, 3 bytes, NOK' - tag 4 is a")
	fmt.Println("    number v1 has never heard of.")

	straggler := &l06v1.Order{}
	must(proto.Unmarshal(newBytes, straggler) == nil, "v1 parses v2 bytes without error")
	fmt.Printf("  v1 reads : id=%d sku=%q qty=%d\n",
		straggler.GetId(), straggler.GetSku(), straggler.GetQty())
	must(straggler.GetId() == 1002 && straggler.GetSku() == "WIDGET-2" && straggler.GetQty() == 3,
		"the shared fields all decoded")
	fmt.Println("  the v1 struct has no Currency field at all and does not care.")
	fmt.Println("  It could only skip tag 4 because every field on the wire carries its")
	fmt.Println("  own wire type in the tag - so a parser can always tell how many bytes")
	fmt.Println("  to jump, even for a field it knows nothing about. (See level 13.)")

	fmt.Println("\n== 3. the unknown field is PRESERVED, not discarded ==")
	// This is the subtle, important part. v1 kept tag 4 in the message's
	// unknown-fields store. Re-marshalling puts it back, byte for byte.
	fmt.Printf("  v1 stashed %d bytes it did not understand: %x\n",
		len(straggler.ProtoReflect().GetUnknown()), straggler.ProtoReflect().GetUnknown())
	reforwarded := mustMarshal(straggler)
	fmt.Printf("  v1 re-serialises      : %x\n", reforwarded)
	must(bytes.Equal(reforwarded, newBytes), "nothing was lost passing through v1")
	fmt.Println("  IDENTICAL to what v2 sent. The currency survived a full trip through")
	fmt.Println("  a build that does not know the field exists.")
	final := &l06v2.Order{}
	must(proto.Unmarshal(reforwarded, final) == nil, "v2 re-reads it")
	must(final.GetCurrency() == "NOK", "the currency is intact")
	fmt.Printf("  v2 reads it back      : currency=%q\n", final.GetCurrency())
	fmt.Println("  => THIS is what makes an old proxy, gateway or read-modify-write")
	fmt.Println("     service safe. Without preservation, every straggler in the fleet")
	fmt.Println("     would quietly strip fields it did not understand.")

	// The honest caveat: preservation is about fields v1 does not KNOW. A
	// field v1 does know, it will happily overwrite - so read-modify-write is
	// safe for unknown fields, not for concurrent edits.
	edited := &l06v1.Order{}
	must(proto.Unmarshal(newBytes, edited) == nil, "v1 parses again")
	edited.Qty = 99
	after := &l06v2.Order{}
	must(proto.Unmarshal(mustMarshal(edited), after) == nil, "v2 reads the edit")
	must(after.GetQty() == 99 && after.GetCurrency() == "NOK", "edit applied, currency kept")
	fmt.Printf("  (v1 editing Qty->99 keeps currency: qty=%d currency=%q)\n",
		after.GetQty(), after.GetCurrency())

	fmt.Println("\n== 4. `reserved`: making rule 2 the compiler's problem ==")
	// l06_v2.proto contains:  reserved 9;  reserved "internal_note";
	// Field 9 was deleted in a past release. Somewhere out there, encoded
	// bytes with tag 9 still sit in a queue, a log or a database column. If a
	// future edit gave number 9 to a new `int32 discount`, those old bytes
	// would parse as a discount - wrong type, wrong meaning, no error anywhere.
	//
	// The reservation is recorded in the compiled descriptor, not just in a
	// comment, which is why tooling such as `buf breaking` can enforce it.
	desc := (&l06v2.Order{}).ProtoReflect().Descriptor()
	ranges := desc.ReservedRanges()
	names := desc.ReservedNames()
	fmt.Print("  compiled descriptor says: reserved numbers ")
	for i := 0; i < ranges.Len(); i++ {
		r := ranges.Get(i)
		fmt.Printf("[%d..%d] ", r[0], r[1]-1)
	}
	fmt.Print(", reserved names ")
	for i := 0; i < names.Len(); i++ {
		fmt.Printf("%q ", names.Get(i))
	}
	fmt.Println()
	must(ranges.Len() == 1 && ranges.Get(0)[0] == 9, "field 9 is reserved")
	must(names.Len() == 1 && names.Get(0) == "internal_note", "the name is reserved too")

	fmt.Println("  Now `protoc` REFUSES to compile any attempt to reuse either one:")
	fmt.Println("      int32 discount = 9;        -> error: field number 9 is reserved")
	fmt.Println("      string internal_note = 12; -> error: field name is reserved")
	fmt.Println("  The name is reserved too, so nobody accidentally revives the old")
	fmt.Println("  meaning under a new number and confuses every human reader.")

	// Demonstrate the danger concretely: a tag-9 varint from the deleted field
	// still parses fine today, as an unknown field.
	fromDeletedEra := append(append([]byte{}, newBytes...), byte(9<<3|0), 42)
	ancient := &l06v2.Order{}
	must(proto.Unmarshal(fromDeletedEra, ancient) == nil, "old tag-9 bytes still parse")
	must(ancient.GetCurrency() == "NOK", "and the known fields are unaffected")
	must(bytes.Equal(mustMarshal(ancient), fromDeletedEra), "they round-trip unchanged")
	fmt.Printf("  proof those bytes are still out there: appending a tag-9 varint parses\n")
	fmt.Printf("  cleanly today (%d bytes) and round-trips unchanged.\n", len(fromDeletedEra))
	fmt.Println("  If 9 were ever reused, THAT is the byte that would be misread.")

	fmt.Println("\n== 5. the reference list ==")
	safe := []string{
		"add a new field with a brand-new number",
		"rename a field (level 01 - the name never travels)",
		"delete a field, if you `reserved` its number and name",
		"add a new value to an enum (level 05)",
		"turn a plain scalar into `optional` (same bytes; changes the Go type)",
		"int32 <-> int64 <-> uint32 <-> uint64 <-> bool  (all varints; mind the range)",
		"add a brand-new message or enum type",
	}
	breaking := []string{
		"change a field's NUMBER                 - the field silently vanishes",
		"change a field's TYPE across wire kinds - varint vs length-delimited: garbage",
		"reuse a number from a deleted field     - old bytes decode as the wrong thing",
		"move a field into or out of a `oneof`   - changes the generated contract",
		"change a field from repeated to single  - or the reverse",
		"renumber anything to 'tidy up'          - see ../../../labs/proto/evo_bad.proto",
	}
	fmt.Println("  SAFE:")
	for _, item := range safe {
		fmt.Printf("    + %s\n", item)
	}
	fmt.Println("  BREAKING:")
	for _, item := range breaking {
		fmt.Printf("    - %s\n", item)
	}
	fmt.Println("\n  Note what makes the breaking list dangerous: almost none of it FAILS.")
	fmt.Println("  It decodes, returns defaults or nonsense, and ships. The only real")
	fmt.Println("  defences are `reserved` and an automated breaking-change check -")
	fmt.Println("  which is exactly what `buf breaking` does, in level 08.")

	fmt.Println("\nOK")
}
