/*
FOUNDATION LEVEL 04 - Presence: the proto3 gotcha worth knowing before you ship
================================================================================
This is the level that saves you a production incident.

proto3 has no null. Every scalar field always has a value, and if that value
is the type's default (0, "", false) the encoder SKIPS it entirely to save
space. The consequence: for a plain int32, "I never set this" and "I
deliberately set this to zero" produce byte-for-byte IDENTICAL output. The
information that you meant zero is not compressed - it is destroyed.

That is fine for a counter. It is a disaster for a PATCH request ("set the
discount to 0%"), a boolean flag ("disable this"), or any field where zero is
a meaningful choice rather than an absence.

The fix is one keyword: mark the field `optional`. Go then generates a
POINTER (*int32) instead of a value, and nil is the honest "not set".

You will learn
  - the proto3 default for every scalar type, and that there is no null
  - PROOF: an unset plain int32 and an explicit 0 encode to the same bytes
  - what `optional` changes: a *int32 field, plus proto.Int32 to build one
  - that the nil-safe getter still returns 0, so GetX() is not a presence check
  - which field kinds already had presence all along (message, oneof, optional)
  - the practical rule for when to reach for `optional`

Run it   go run ./Protobuf/Foundation/golang/04_presence_and_defaults
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l04"
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
	fmt.Println("== 1. proto3 defaults: there is no null ==")
	blank := &l04.Reading{}
	fmt.Printf("  SensorId (string)   = %q\n", blank.GetSensorId())
	fmt.Printf("  Celsius  (int32 )   = %d\n", blank.GetCelsius())
	fmt.Printf("  Humidity (*int32)   = %d   <- optional, but the getter still says 0\n",
		blank.GetHumidity())
	must(blank.GetSensorId() == "" && blank.GetCelsius() == 0, "defaults")
	fmt.Println("  a fresh message is never 'empty' - it is fully populated with defaults.")
	fmt.Printf("  ...yet it encodes to %d bytes: defaults are not sent.\n", len(mustMarshal(blank)))
	must(len(mustMarshal(blank)) == 0, "an all-default message is zero bytes")

	fmt.Println("\n== 2. THE GOTCHA: unset vs explicit zero, on a PLAIN int32 ==")
	neverSet := &l04.Reading{SensorId: "s1"}
	setToZero := &l04.Reading{SensorId: "s1", Celsius: 0} // deliberately zero!
	a, b := mustMarshal(neverSet), mustMarshal(setToZero)
	fmt.Printf("  Reading{SensorId: \"s1\"}             -> %d bytes: %x\n", len(a), a)
	fmt.Printf("  Reading{SensorId: \"s1\", Celsius: 0} -> %d bytes: %x\n", len(b), b)
	must(bytes.Equal(a, b), "this is the whole point: they are indistinguishable")
	fmt.Println("  IDENTICAL. The `Celsius: 0` never made it onto the wire, so no reader")
	fmt.Println("  anywhere - in any language - can tell these two apart. Ever.")
	fmt.Println("  And in Go there is nothing to ask: Celsius is an int32, not a pointer,")
	fmt.Println("  so the type itself has no way to represent 'absent'.")

	fmt.Println("\n== 3. what `optional` changes ==")
	// `optional int32 humidity = 3;` makes the Go field a *int32. proto.Int32
	// is a helper that allocates one, because you cannot take the address of
	// a literal in Go.
	noHum := &l04.Reading{SensorId: "s1"}
	zeroHum := &l04.Reading{SensorId: "s1", Humidity: proto.Int32(0)} // deliberately zero!
	c, d := mustMarshal(noHum), mustMarshal(zeroHum)
	fmt.Printf("  Reading{SensorId: \"s1\"}                          -> %d bytes: %x\n", len(c), c)
	fmt.Printf("  Reading{SensorId: \"s1\", Humidity: proto.Int32(0)} -> %d bytes: %x\n", len(d), d)
	must(!bytes.Equal(c, d), "optional makes the explicit zero visible")
	fmt.Println("  DIFFERENT - the optional field emitted `18 00` = 'field 3, value 0'.")
	fmt.Printf("  Humidity == nil: unset -> %v, explicit 0 -> %v\n",
		noHum.Humidity == nil, zeroHum.Humidity == nil)
	must(noHum.Humidity == nil, "unset optional is nil")
	must(zeroHum.Humidity != nil && *zeroHum.Humidity == 0, "explicit zero is a non-nil pointer to 0")

	// Crucially, presence survives the round trip. It is carried by the bytes,
	// not by some flag that only exists in the sender's memory.
	reread := &l04.Reading{}
	must(proto.Unmarshal(d, reread) == nil, "unmarshal")
	must(reread.Humidity != nil && reread.GetHumidity() == 0, "presence survived")
	fmt.Printf("  after a full encode/decode, Humidity != nil is still %v\n", reread.Humidity != nil)
	fmt.Println("  -> presence is ON THE WIRE, not in RAM")

	// Setting the pointer back to nil is how you say "absent" again.
	reread.Humidity = nil
	must(reread.Humidity == nil && reread.GetHumidity() == 0, "back to absent")
	fmt.Println("  Humidity = nil -> absent again (and the getter reads 0 once more)")

	fmt.Println("\n== 4. the Go trap: GetX() is NOT a presence check ==")
	// The nil-safe getter dereferences for you and returns the default when
	// the pointer is nil. That is convenient, and it means the getter can
	// never tell you whether the field was set.
	fmt.Printf("  noHum.GetHumidity()   -> %d   (nil pointer, getter returns the default)\n",
		noHum.GetHumidity())
	fmt.Printf("  zeroHum.GetHumidity() -> %d   (pointer to 0, getter returns 0)\n",
		zeroHum.GetHumidity())
	must(noHum.GetHumidity() == zeroHum.GetHumidity(), "the getter cannot distinguish them")
	fmt.Println("  same answer for both! To ask about presence you must test the POINTER:")
	fmt.Println("      if r.Humidity != nil { ... }      // correct")
	fmt.Println("      if r.GetHumidity() != 0 { ... }   // WRONG - conflates 0 with absent")

	fmt.Println("\n== 5. which field kinds have presence already? ==")
	rows := [][2]string{
		{"plain scalar  (Celsius)", "NO  - 0 and unset are the same bytes"},
		{"optional scalar (Humidity)", "YES - the field is a *int32; nil means absent"},
		{"message field", "YES - always had it: a nil pointer (see level 02)"},
		{"oneof member", "YES - the interface field is nil (see level 07)"},
		{"repeated field", "NO  - and it does not need it: empty IS the empty state"},
	}
	for _, row := range rows {
		fmt.Printf("  %-27s %s\n", row[0], row[1])
	}

	fmt.Println("\n== 6. the practical rule ==")
	fmt.Println("  Ask: 'is the zero value a MEANINGFUL choice a user could make?'")
	fmt.Println("    RetryCount, BytesSent, ErrorTotal   -> plain scalar. 0 means nothing happened.")
	fmt.Println("    DiscountPercent, TemperatureC, Limit -> `optional`. 0 is a real, chosen value.")
	fmt.Println("  Any PATCH/update API needs `optional` almost everywhere, because there")
	fmt.Println("  the whole question is 'did the caller mention this field or not?'.")
	fmt.Println("  Cost of being wrong later: adding `optional` to a shipped plain scalar")
	fmt.Println("  is wire-compatible, so it is a safe fix - but it changes the Go type")
	fmt.Println("  from int32 to *int32, so every call site needs updating, and every")
	fmt.Println("  already-stored zero is gone for good.")

	fmt.Println("\nOK")
}
