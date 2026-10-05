/*
FOUNDATION LEVEL 02 - Nested messages: a message inside a message
==================================================================
So far every field has been a scalar. This level adds the other kind: a field
whose type is another MESSAGE. That is how protobuf builds structure, and it
is the same mechanism all the way down - there is no special "object" type,
just messages containing messages.

The one genuinely new behaviour is PRESENCE. A scalar string has no way to
say "absent" (level 04 explains why), but a message field always does: a
Person with no Home at all is a different, detectable state from a Person
with a Home whose every field happens to be empty. In Go this falls out of
the representation - a nested message is a POINTER, and nil means absent.

You will learn
  - how to declare and set a message-typed field
  - that a nested message is encoded length-delimited: exactly like a string,
    but the "text" inside is itself a little protobuf message
  - that nil vs &Address{} is real, detectable presence
  - why generated getters are the safe way to read through a nested chain:
    p.GetHome().GetCity() never panics, p.Home.City does
  - that nesting costs only a tag + a length byte, so deep structure is cheap

Run it   go run ./Protobuf/Foundation/golang/02_nested_messages
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l02"
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
	fmt.Println("== 1. building a nested value ==")
	// A message-typed field is a pointer to another generated struct. You set
	// it exactly like any other field, with a composite literal.
	ada := &l02.Person{
		Name: "Ada",
		Home: &l02.Address{Street: "12 Dean St", City: "Oslo", CountryCode: "NO"},
	}
	// The mutating style, for when you fill a message gradually. Note you must
	// create the sub-message before writing through it - unlike Python, Go
	// will not conjure it for you, it will panic on a nil dereference.
	grace := &l02.Person{Name: "Grace"}
	grace.Home = &l02.Address{}
	grace.Home.Street = "1 Navy Yard"
	grace.Home.City = "Arlington"
	grace.Home.CountryCode = "US"

	fmt.Printf("  ada.GetHome().GetCity()   = %q\n", ada.GetHome().GetCity())
	fmt.Printf("  grace.GetHome().GetCity() = %q\n", grace.GetHome().GetCity())
	must(ada.GetHome().GetCity() == "Oslo", "ada's city")
	must(grace.GetHome().GetCity() == "Arlington", "grace's city")

	fmt.Println("\n== 2. how nesting looks on the wire ==")
	data := mustMarshal(ada)
	fmt.Printf("  %d bytes: %x\n", len(data), data)
	// Field 2 (`home`) has tag byte 0x12 = (2 << 3) | 2, i.e. "field 2,
	// length-delimited". The very next byte is the LENGTH of the whole encoded
	// Address, and then the Address's own fields follow, using their OWN field
	// numbers 1/2/3 - restarting from 1 inside the nested scope.
	inner := mustMarshal(ada.GetHome())
	fmt.Printf("  the Address alone encodes to %d bytes: %x\n", len(inner), inner)
	framed := append([]byte{0x12, byte(len(inner))}, inner...)
	must(bytes.Contains(data, framed), "parent embeds child verbatim after a length")
	fmt.Printf("  and the parent contains exactly  12 %02x <those %d bytes>\n", len(inner), len(inner))
	fmt.Println("  => a nested message is encoded like a string whose contents happen")
	fmt.Println("     to be another message. That single rule is all of protobuf's")
	fmt.Println("     structure; there is nothing else to learn about nesting.")
	// name "Ada" costs 2 (tag+len) + 3 bytes; the rest is the wrapped Address.
	fmt.Printf("  total overhead for wrapping the Address: %d bytes (one tag + one length)\n",
		len(data)-len(inner)-len("Ada")-2)

	fmt.Println("\n== 3. presence: absent vs present-but-empty ==")
	// Same name in both, so the ONLY difference in the byte counts below is
	// the address field itself.
	nobody := &l02.Person{Name: "Blank"}                         // no home at all
	homeless := &l02.Person{Name: "Blank", Home: &l02.Address{}} // a home, entirely empty
	nobodyBytes, homelessBytes := mustMarshal(nobody), mustMarshal(homeless)
	fmt.Printf("  Home == nil        : %v, %d bytes\n", nobody.GetHome() == nil, len(nobodyBytes))
	fmt.Printf("  Home == &Address{} : %v, %d bytes\n", homeless.GetHome() != nil, len(homelessBytes))
	must(nobody.Home == nil, "absent is nil")
	must(homeless.Home != nil, "present-but-empty is non-nil")
	// The two are genuinely different bytes: the empty Address still emits its
	// own tag and a length of zero, which is what makes it detectable.
	must(!bytes.Equal(nobodyBytes, homelessBytes), "the two states differ on the wire")
	must(len(homelessBytes) == len(nobodyBytes)+2, "an empty sub-message costs a tag plus a length")
	fmt.Println("  the empty one costs 2 extra bytes (12 00 = 'field 2, length 0'):")
	fmt.Printf("    absent : %x\n", nobodyBytes)
	fmt.Printf("    empty  : %x\n", homelessBytes)
	fmt.Println("  => this matters for real APIs: 'the user cleared their address' and")
	fmt.Println("     'the user did not mention their address' are different intents,")
	fmt.Println("     and a message field can carry that difference. A string cannot.")

	// And presence survives the round trip - it is carried by the bytes.
	reparsed := &l02.Person{}
	must(proto.Unmarshal(homelessBytes, reparsed) == nil, "unmarshal empty-home")
	must(reparsed.Home != nil, "present-but-empty survived encoding")
	fmt.Println("  after encode/decode, the empty Address is still non-nil")

	fmt.Println("\n== 4. why you should use the getters ==")
	// This is the Go-specific trap. A nested field is a pointer, so reading
	// straight through it on an absent message is a nil dereference panic.
	// The generated getters are nil-safe at every level of the chain.
	var missing *l02.Person
	fmt.Printf("  a nil *Person: GetHome().GetCity() -> %q (no panic, at any depth)\n",
		missing.GetHome().GetCity())
	fmt.Printf("  nobody.GetHome().GetCountryCode()  -> %q (Home is nil, still fine)\n",
		nobody.GetHome().GetCountryCode())
	// nobody.Home.CountryCode  <- this WOULD panic: nil pointer dereference
	fmt.Println("  nobody.Home.CountryCode would PANIC. Prefer GetX() in library code;")
	fmt.Println("  reach for the raw field only when you are checking nil deliberately.")

	fmt.Println("\n== 5. round trip ==")
	back := &l02.Person{}
	must(proto.Unmarshal(data, back) == nil, "unmarshal")
	must(proto.Equal(back, ada), "nested values survive encode/decode exactly")
	must(back.GetHome().GetCountryCode() == "NO", "the nested country code")
	fmt.Printf("  decoded: name=%q city=%q cc=%q\n",
		back.GetName(), back.GetHome().GetCity(), back.GetHome().GetCountryCode())

	fmt.Println("\nOK")
}
