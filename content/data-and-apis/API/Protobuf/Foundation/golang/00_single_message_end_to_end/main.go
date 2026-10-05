/*
FOUNDATION LEVEL 00 (start here) - A single Protobuf message, end to end
=========================================================================
If someone says "build me a basic Protobuf message", THIS is what they mean:
one .proto file describing one message, compiled into real code, then a value
built, encoded to bytes, and decoded back. Four steps, one field. Everything
later in this folder is "add one more piece" instead of "understand it all".

THE MENTAL MODEL (read this before the code). Protobuf is two things bolted
together, and a compiler joins them:

  - a SCHEMA language - ../../proto/l00_ping.proto says a Ping has one string
    called `text`, numbered 1. You write this once, by hand.
  - a BINARY ENCODING - a compact byte layout for values of that schema.

protoc reads the schema and writes you a struct; the proto package knows how
to turn that struct into the encoding and back.

The trade-off, stated plainly: protobuf gives up being human-readable to
become small and fast to parse. JSON ships the field NAME with every value
("text" costs 6 bytes every single time) and every number as ASCII digits;
protobuf ships a one-byte tag instead of the name, and packs numbers as raw
bytes. You cannot read the result in a text editor, and you cannot decode it
at all without the schema - that is the price. In exchange you get a payload
that is typically 20-60% smaller and parses several times faster, plus a
schema the compiler can check for you in every language at once.

You will learn
  - the four steps of every protobuf program: schema -> generate -> encode -> decode
  - that generated types are used via a POINTER (*l00.Ping), never copied by value
  - proto.Marshal / proto.Unmarshal, and what the resulting bytes look like
  - why protobuf is smaller than the equivalent JSON, measured, not asserted
  - that decoding is exact, and that proto.Equal - not == - is how you compare

Run it   go run ./Protobuf/Foundation/golang/00_single_message_end_to_end
*/
package main

import (
	"encoding/json"
	"fmt"

	"google.golang.org/protobuf/proto"

	// STEP 2 of 4 happened before you ran this: ../../generate.sh ran protoc
	// over ../../proto/l00_ping.proto and wrote ../pb/l00/l00_ping.pb.go.
	// That generated package is checked in, so there is nothing to build right
	// now. Open it if you are curious - but you never edit generated code.
	"dsapractice/api/Protobuf/Foundation/golang/pb/l00"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== step 3: build a value ==")
	// Generated messages are always used as POINTERS. They carry internal
	// state and a no-copy lock, so copying one by value is a bug that `go vet`
	// will report. Build them with &T{...} every time.
	ping := &l00.Ping{Text: "hello, protobuf"}
	fmt.Printf("  in go     : &l00.Ping{Text: %q}\n", ping.GetText())

	// Generated getters are nil-safe, which matters more as messages nest
	// (level 02). Prefer GetText() over .Text in library code.
	var nilPing *l00.Ping
	fmt.Printf("  a nil *Ping's GetText() returns %q instead of panicking\n", nilPing.GetText())

	fmt.Println("\n== step 4a: encode to bytes ==")
	// proto.Marshal returns the encoded bytes - what you would write to a
	// file, put on a queue, or hand to gRPC.
	data, err := proto.Marshal(ping)
	must(err == nil, "marshal")
	fmt.Printf("  %d bytes, as hex : %x\n", len(data), data)
	fmt.Printf("  the same bytes   : %q\n", data)
	fmt.Println("  notice: the field NAME 'text' is nowhere in there. Byte 0x0a is a")
	fmt.Println("  one-byte tag meaning 'field number 1, length-delimited'. Level 13")
	fmt.Println("  decodes all of this by hand if you want to see every byte.")

	// proto.Size predicts the length without doing the work, which is handy
	// for pre-allocating buffers.
	must(proto.Size(ping) == len(data), "proto.Size agrees with the encoded length")

	fmt.Println("\n== step 4b: decode it back ==")
	// Unmarshal REPLACES the contents of the destination, so start from a
	// zero value. Parsing needs the schema - specifically, the same message
	// type. The bytes alone do not say what they are.
	decoded := &l00.Ping{}
	must(proto.Unmarshal(data, decoded) == nil, "unmarshal")
	fmt.Printf("  decoded.GetText() = %q\n", decoded.GetText())

	must(decoded.GetText() == "hello, protobuf", "the text survived the round trip")
	// Compare messages with proto.Equal, never ==. Two messages can be
	// logically equal while differing in internal bookkeeping.
	must(proto.Equal(ping, decoded), "a decoded message equals the one that was encoded")
	fmt.Println("  proto.Equal(original, decoded) -> true   (use this, never ==)")

	fmt.Println("\n== why bother? the size trade-off, measured ==")
	asJSON, err := json.Marshal(map[string]string{"text": "hello, protobuf"})
	must(err == nil, "json marshal")
	fmt.Printf("  protobuf : %3d bytes  %x\n", len(data), data)
	fmt.Printf("  JSON     : %3d bytes  %s\n", len(asJSON), asJSON)
	saved := 100 - (100 * len(data) / len(asJSON))
	fmt.Printf("  -> %d%% smaller on a message with ONE short field. The gap widens\n", saved)
	fmt.Println("     with more fields and with numbers, because JSON re-sends every")
	fmt.Println("     field name as text and every number as ASCII digits.")
	must(len(data) < len(asJSON), "protobuf is smaller than the equivalent JSON")

	// ... and the cost, stated honestly: without the l00 package these bytes
	// are unreadable noise. JSON is self-describing; protobuf is not. That is
	// the deal you are making, and levels 01 and 06 are about living with it.
	fmt.Println("\n== the cost ==")
	fmt.Println("  JSON can be read by anyone with a text editor. These 17 bytes cannot")
	fmt.Println("  be decoded by anyone who does not also have l00_ping.proto. Protobuf")
	fmt.Println("  trades self-description for size; the schema becomes a hard dependency.")

	fmt.Println("\nOK")
}
