/*
FOUNDATION BONUS - What protoc actually generated (optional, read after level 00)
=====================================================================================
Level 00 ran `../../generate.sh`, imported `pingpb`, and never asked what was in
it. This file answers that in two steps: first what the generator PRODUCED for
`PingRequest`, then what that produces ON THE WIRE - decoded by hand, with no
protobuf library involved at all.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is protoc actually doing for me?" once you are curious.

WHERE THE FULL WALKTHROUGH LIVES

	This is the SAME exercise as `../../../Protobuf/Foundation`'s own bonus level.
	That folder is about the message/wire format as its whole subject - varints,
	ZigZag, wire types, length-delimited fields, packed repeated fields, unknown
	field preservation - and it walks the bytes properly. Go there for the full
	byte-by-byte treatment. This file stays shallow on purpose: just enough to
	prove the bytes are not magic, in the context of the RPC you already ran.
	Everything ELSE in this Foundation folder is about the RPC layer - services,
	interceptors, streaming, status codes - which protobuf itself knows nothing
	about.

You will learn
  - the generated Go struct is real and readable, and its `protobuf:"..."` struct
    tags ARE the wire rules, written down where you can see them
  - reflection lets you read the .proto back out of the binary, because protoc
    embedded a serialized descriptor in the generated package
  - the whole protobuf encoding rule for a string field, in one line:
    tag byte = (field_number << 3) | wire_type, then a length, then the bytes
  - why the encoding is so small: field NAMES are never transmitted, only numbers
  - that gRPC frames each message with 1 compression byte + 4 length bytes
    before handing it to HTTP/2

Run it   go run ./gRPC/Foundation/golang/13_bonus_generated_code_and_raw_wire_bytes
*/
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"reflect"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/gRPC/Foundation/golang/pb/pingpb"
)

func main() {
	// -----------------------------------------------------------------------
	// PART 1 - what the generator produced for level 00's PingRequest
	// -----------------------------------------------------------------------
	fmt.Println("PART 1: the generated struct")
	fmt.Println("============================================================")

	msg := &pingpb.PingRequest{Name: "world"}

	// Unlike Python, Go's generated message is a real struct you can inspect
	// with reflect. The `protobuf:"..."` tag on each field is where protoc wrote
	// down the wire rules - wire type, field number, name, syntax.
	// .Elem() on the POINTER type, never reflect.TypeOf(*msg): dereferencing
	// would copy the message, and a protobuf message contains a mutex, so
	// `go vet` rightly refuses to let you copy one.
	t := reflect.TypeOf(msg).Elem()
	fmt.Printf("Go type          : %s\n", t)
	fmt.Printf("proto full name  : %s\n", msg.ProtoReflect().Descriptor().FullName())
	fmt.Printf("defined in       : %s  (package %s)\n",
		msg.ProtoReflect().Descriptor().ParentFile().Path(),
		msg.ProtoReflect().Descriptor().ParentFile().Package())
	fmt.Println("struct fields    :")
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		tag := f.Tag.Get("protobuf")
		if tag == "" {
			// state / sizeCache / unknownFields: protobuf-runtime bookkeeping,
			// not part of your contract. unknownFields is how a message
			// round-trips fields your binary has never heard of.
			fmt.Printf("  %-14s %-32s (runtime bookkeeping, not a contract field)\n", f.Name, f.Type)
			continue
		}
		fmt.Printf("  %-14s %-32s protobuf:%q\n", f.Name, f.Type, tag)
	}

	// The descriptor is the .proto, parsed, carried inside the binary.
	fields := msg.ProtoReflect().Descriptor().Fields()
	fmt.Println("the contract, read back out of the binary:")
	for i := 0; i < fields.Len(); i++ {
		fd := fields.Get(i)
		fmt.Printf("  field %d: %s (%s)\n", fd.Number(), fd.Name(), fd.Kind())
	}
	if msg.ProtoReflect().Descriptor().FullName() != "foundation.ping.v1.PingRequest" {
		panic("FAILED")
	}
	if fields.Len() != 1 || fields.Get(0).Number() != 1 {
		panic("FAILED")
	}

	fmt.Println(`
the equivalent in Python is much thinner - a nearly empty class plus a
DESCRIPTOR built from an embedded serialized .proto (see ../../python/13_*.py):

    class PingRequest(_message.Message):
        __slots__ = ("name",)
        name: str`)

	// -----------------------------------------------------------------------
	// PART 2 - the bytes, decoded by hand
	// -----------------------------------------------------------------------
	fmt.Println("\nPART 2: decoding PingRequest{Name: \"world\"} with no protobuf library")
	fmt.Println("============================================================")

	raw, err := proto.Marshal(msg)
	if err != nil {
		panic(err)
	}
	fmt.Printf("proto.Marshal() -> %#v   (%d bytes)\n", raw, len(raw))
	if !bytes.Equal(raw, []byte{0x0a, 0x05, 'w', 'o', 'r', 'l', 'd'}) {
		panic("FAILED")
	}

	decoded := decodeByHand(raw)
	fmt.Printf("\nby hand : field 1 = %#v  ->  %q\n", decoded[1], string(decoded[1]))
	fmt.Printf("protobuf: Name    = %q\n", msg.GetName())
	if string(decoded[1]) != msg.GetName() {
		panic("FAILED")
	}

	// THE POINT: the string "name" appears nowhere in those 7 bytes. Only the
	// NUMBER 1 does. That is why renaming a field is free and renumbering one is
	// fatal (level 01), and it is most of why protobuf is so much smaller than JSON.
	jsonEquivalent := []byte(`{"name":"world"}`)
	fmt.Printf("\nprotobuf: %d bytes  %#v\n", len(raw), raw)
	fmt.Printf("JSON    : %d bytes %s\n", len(jsonEquivalent), jsonEquivalent)
	fmt.Println("  the field NAME is never transmitted - only field number 1")
	if len(raw) >= len(jsonEquivalent) {
		panic("FAILED")
	}

	// One more layer: gRPC does not put those 7 bytes straight onto HTTP/2. It
	// prefixes every message with a 5-byte frame header so the receiver knows
	// where each message ends within the stream (essential for levels 03-05,
	// where many messages share one call).
	framed := make([]byte, 5+len(raw))
	framed[0] = 0 // 0 = not compressed, 1 = compressed with the call's codec
	binary.BigEndian.PutUint32(framed[1:5], uint32(len(raw)))
	copy(framed[5:], raw)
	fmt.Printf("\non the wire, gRPC frames it: %#v\n", framed)
	fmt.Println("  byte 0    = 0    -> not compressed")
	fmt.Printf("  bytes 1-4 = %d    -> message length, big-endian uint32\n", len(raw))
	fmt.Printf("  bytes 5-%d -> the %d protobuf bytes decoded above\n", 4+len(raw), len(raw))
	if len(framed) != 5+len(raw) {
		panic("FAILED")
	}

	fmt.Println("\nfor varints, ZigZag, packed repeated fields, nested messages and")
	fmt.Println("unknown-field preservation, read ../../../Protobuf/Foundation - that")
	fmt.Println("folder is the wire format's full walkthrough, and this was its first page.")

	fmt.Println("\nOK")
}

// decodeByHand is a deliberately tiny protobuf reader. It handles exactly the
// two wire types this message needs. ../../../Protobuf/Foundation does this properly.
func decodeByHand(data []byte) map[int]([]byte) {
	out := make(map[int][]byte)
	i := 0
	for i < len(data) {
		// The TAG is a varint packing two things together:
		//   field_number = tag >> 3
		//   wire_type    = tag & 0b111
		tag := data[i]
		i++
		fieldNumber, wireType := int(tag>>3), int(tag&0b111)
		fmt.Printf("  byte 0x%02x = %08b -> field_number=%d wire_type=%d\n",
			tag, tag, fieldNumber, wireType)

		switch wireType {
		case 2: // length-delimited: string, bytes, or a nested message
			length := int(data[i]) // a varint too; a single byte for anything under 128
			i++
			value := data[i : i+length]
			i += length
			fmt.Printf("    length-delimited, %d bytes -> %#v\n", length, value)
			out[fieldNumber] = value
		case 0: // varint: int32/int64/bool/enum
			var value uint64
			var shift uint
			for {
				b := data[i]
				i++
				value |= uint64(b&0x7F) << shift // 7 payload bits per byte...
				if b&0x80 == 0 {                 // ...top bit means "one more byte follows"
					break
				}
				shift += 7
			}
			fmt.Printf("    varint -> %d\n", value)
			out[fieldNumber] = []byte(fmt.Sprint(value))
		default:
			panic(fmt.Sprintf("wire type %d - see ../../../Protobuf/Foundation", wireType))
		}
	}
	return out
}
