/*
FOUNDATION BONUS - What IS a protobuf message, really? (optional, read last)
=============================================================================
Level 00 encoded a message with proto.Marshal and never asked what the
library did. This file answers that, completely, by decoding a real encoded
message BY HAND - no protobuf import anywhere. Check the imports: only fmt,
encoding/hex, bytes and math/bits. Everything below is arithmetic on bytes.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is the library actually doing for me?" once you are curious.

THE ENTIRE FORMAT, in three rules

 1. A message is a flat sequence of (tag, value) records. No header, no
    footer, no field count, no length for the message as a whole. That is
    why level 09 needed framing.
 2. Each record starts with a TAG, itself a varint:
    tag = (field_number << 3) | wire_type
    Three low bits are the wire type, everything above is the field number.
 3. The wire type says how to read the value that follows:
    0 = VARINT   int32/int64/uint/bool/enum
    1 = I64      fixed 8 bytes (double, fixed64)
    2 = LEN      a varint length, then that many bytes
    (string, bytes, nested message, packed repeated)
    5 = I32      fixed 4 bytes (float, fixed32)
    Rule 3 is why forward compatibility works (level 06): the wire type tells
    a parser how many bytes to skip even for a field number it has never seen.

VARINTS, the one trick worth knowing

	Small numbers should cost few bytes. So each byte carries 7 bits of the
	value in its low bits, and uses its HIGH bit as "another byte follows".
	Little-endian: the first byte holds the LEAST significant 7 bits.

You will learn
  - to read a tag byte and recover the field number and wire type
  - to decode a varint by hand, and why 300 needs two bytes
  - to read a length-delimited string: tag, length, then raw UTF-8
  - to ENCODE the same message from scratch and match the original bytes
  - why an unknown field can always be skipped safely
  - (Go extra) why int32 = -1 costs 10 bytes and sint32 = -1 costs 1 (zigzag)

Run it   go run ./Protobuf/Foundation/golang/13_bonus_decode_wire_format_by_hand
Twin     python Protobuf/Foundation/python/13_bonus_decode_wire_format_by_hand.py
*/
package main

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"math/bits"
)

// These bytes are real. They were produced by level 06's schema:
//
//	message Order { int64 id = 1; string sku = 2; int32 qty = 3; }
//
// holding Order{Id: 300, Sku: "WIDGET-1", Qty: 7}. The Python twin asserts
// the very same hex string.
const encodedHex = "08ac0212085749444745542d311807"

var wireTypeNames = map[uint64]string{0: "VARINT", 1: "I64", 2: "LEN", 5: "I32"}

// The schema, as a plain map - the ONLY thing the bytes cannot tell us. Field
// NAMES are not on the wire (level 01), so a hand decoder has to be told them.
// This map is standing in for the generated code.
type field struct{ name, declared string }

var schema = map[uint64]field{1: {"id", "int64"}, 2: {"sku", "string"}, 3: {"qty", "int32"}}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// readVarint decodes one varint. Returns value, next position, and a per-byte
// explanation.
func readVarint(data []byte, pos int) (uint64, int, []string) {
	var value uint64
	var shift uint
	var steps []string
	for {
		b := data[pos]
		pos++
		payload := uint64(b & 0x7f) // the 7 data bits
		more := b&0x80 != 0         // the high bit: "another byte follows"
		value |= payload << shift   // little-endian: first byte is least significant
		cont := 0
		if more {
			cont = 1
		}
		steps = append(steps, fmt.Sprintf("0x%02x = %08b -> continuation=%d, 7 bits %07b << %d = %d",
			b, b, cont, payload, shift, payload<<shift))
		if !more {
			return value, pos, steps
		}
		shift += 7
	}
}

// writeVarint is the exact inverse of readVarint.
func writeVarint(v uint64) []byte {
	var out []byte
	for v > 0x7f {
		out = append(out, byte(v&0x7f)|0x80) // low 7 bits + "more follows"
		v >>= 7
	}
	return append(out, byte(v)) // last byte, high bit clear
}

// decode walks the whole message, narrating every byte.
func decode(data []byte) map[string]any {
	fields := map[string]any{}
	pos := 0
	for pos < len(data) {
		start := pos
		tag, next, tagSteps := readVarint(data, pos)
		pos = next

		// Rule 2, undone: split the tag back into its two halves.
		num, wt := tag>>3, tag&0x07
		f, ok := schema[num]
		if !ok {
			f = field{fmt.Sprintf("<unknown %d>", num), "?"}
		}
		fmt.Printf("  byte %2d: tag varint\n", start)
		for _, s := range tagSteps {
			fmt.Println("            " + s)
		}
		fmt.Printf("            tag = %d = (field %d << 3) | %d  -> field %d (%s), wire type %d (%s)\n",
			tag, num, wt, num, f.name, wt, wireTypeNames[wt])

		switch wt {
		case 0:
			v, next, steps := readVarint(data, pos)
			pos = next
			for _, s := range steps {
				fmt.Println("            value: " + s)
			}
			fmt.Printf("            => %s = %d   (%s)\n", f.name, v, f.declared)
			fields[f.name] = int64(v)
		case 2:
			n, next, steps := readVarint(data, pos)
			pos = next
			for _, s := range steps {
				fmt.Println("            length: " + s)
			}
			raw := data[pos : pos+int(n)]
			pos += int(n)
			s := string(raw) // a protobuf string is UTF-8 (level 10)
			fmt.Printf("            %d bytes follow: %s\n", n, hex.EncodeToString(raw))
			fmt.Printf("            as UTF-8 -> %q\n", s)
			fmt.Printf("            => %s = %q   (%s)\n", f.name, s, f.declared)
			fields[f.name] = s
		default:
			panic(fmt.Sprintf("wire type %d not needed for this message", wt))
		}
		fmt.Println()
	}
	return fields
}

func main() {
	encoded, _ := hex.DecodeString(encodedHex)

	fmt.Println("== 1. the varint trick, in isolation ==")
	// Why 300 costs two bytes but 127 costs one.
	for _, n := range []uint64{0, 1, 7, 127, 128, 300, 16384} {
		enc := writeVarint(n)
		back, _, _ := readVarint(enc, 0)
		fmt.Printf("  %6d -> %-10s (%d byte(s))  -> decodes to %d\n", n, hex.EncodeToString(enc), len(enc), back)
		must(back == n, "varint round trip")
	}
	fmt.Println("  127 = 1111111 fits in one byte's 7 data bits. 128 needs an eighth bit,")
	fmt.Println("  so it spills: 0x80 0x01 = (0000000) + (0000001 << 7) = 128.")
	must(bytes.Equal(writeVarint(300), []byte{0xac, 0x02}), "300 is ac 02")
	must((0xac&0x7f)|(0x02<<7) == 300, "little-endian groups")
	fmt.Println("  300 = 0xac 0x02: (0xac & 0x7f) | (0x02 << 7) = 44 + 256 = 300")
	// The cost of a varint is ceil(significant bits / 7); a uint64 needs at most 10 bytes.
	must(len(writeVarint(^uint64(0))) == (bits.Len64(^uint64(0))+6)/7, "max varint is 10 bytes")

	fmt.Println("\n== 2. decoding the real message, byte by byte ==")
	fmt.Printf("  input: %d bytes  %s\n\n", len(encoded), encodedHex)
	fields := decode(encoded)

	fmt.Println("== 3. the result ==")
	fmt.Printf("  %v\n", fields)
	must(fields["id"] == int64(300) && fields["sku"] == "WIDGET-1" && fields["qty"] == int64(7), "decoded fields")
	fmt.Println("  decoded with zero protobuf code - just shifts, masks and a UTF-8 conversion.")

	fmt.Println("\n== 4. now ENCODE it again from scratch ==")
	// Build the same message the way the library does: for each field, emit a
	// tag, then the value in the form its wire type demands.
	sku := []byte("WIDGET-1")
	parts := [][]byte{
		append(writeVarint(1<<3|0), writeVarint(300)...),                              // id
		append(append(writeVarint(2<<3|2), writeVarint(uint64(len(sku)))...), sku...), // sku
		append(writeVarint(3<<3|0), writeVarint(7)...),                                // qty
	}
	rebuilt := bytes.Join(parts, nil)
	fmt.Printf("  field 1 (id=300)        : %s\n", hex.EncodeToString(parts[0]))
	fmt.Printf("  field 2 (sku=\"WIDGET-1\"): %s\n", hex.EncodeToString(parts[1]))
	fmt.Printf("  field 3 (qty=7)         : %s\n", hex.EncodeToString(parts[2]))
	fmt.Printf("  joined                  : %s\n", hex.EncodeToString(rebuilt))
	fmt.Printf("  original                : %s\n", encodedHex)
	must(bytes.Equal(rebuilt, encoded), "a hand-built message matches the library's output exactly")
	fmt.Println("  IDENTICAL. There is no hidden header, checksum or padding - a protobuf")
	fmt.Println("  message is exactly the concatenation of its encoded fields.")

	fmt.Println("\n== 5. why unknown fields can always be skipped ==")
	// Append a field number 99 the schema map has never heard of. This is
	// level 06's forward compatibility, seen from underneath.
	unknown := append(append(writeVarint(99<<3|2), writeVarint(4)...), 0xde, 0xad, 0xbe, 0xef)
	extended := append(append([]byte{}, encoded...), unknown...)
	fmt.Printf("  appended field 99 as LEN with 4 bytes -> %d bytes total\n", len(extended))
	pos, skipped := 0, []uint64{}
	for pos < len(extended) {
		tag, next, _ := readVarint(extended, pos)
		pos = next
		num, wt := tag>>3, tag&0x07
		switch wt {
		case 0:
			_, pos, _ = readVarint(extended, pos)
		case 2:
			var n uint64
			n, pos, _ = readVarint(extended, pos)
			pos += int(n)
		case 1:
			pos += 8
		case 5:
			pos += 4
		}
		if _, known := schema[num]; !known {
			skipped = append(skipped, num)
		}
	}
	fmt.Printf("  walked the whole message without error; unknown field numbers: %v\n", skipped)
	must(len(skipped) == 1 && skipped[0] == 99 && pos == len(extended), "skip unknown")
	fmt.Println("  The parser never needed to know what field 99 MEANS - only how long")
	fmt.Println("  it is, and the wire type in the tag always says that. Preserving")
	fmt.Println("  those skipped bytes is what makes level 06's round trip lossless.")

	fmt.Println("\n== 6. (Go extra) negative numbers: int32 vs sint32 ==")
	// int32/int64 encode a negative value as its 64-bit two's complement, so
	// -1 is 0xffffffffffffffff: ten varint bytes. sint32/sint64 first apply
	// ZIGZAG, which interleaves signs so small magnitudes stay small:
	//   0 -> 0, -1 -> 1, 1 -> 2, -2 -> 3, 2 -> 4 ...
	zigzag := func(n int64) uint64 { return uint64((n << 1) ^ (n >> 63)) }
	unzigzag := func(u uint64) int64 { return int64(u>>1) ^ -int64(u&1) }
	for _, n := range []int64{0, -1, 1, -2, 2, -300} {
		asInt := writeVarint(uint64(n))
		asSint := writeVarint(zigzag(n))
		fmt.Printf("  %5d  int32: %-22s (%2d B)   sint32: %-6s (%d B)\n",
			n, hex.EncodeToString(asInt), len(asInt), hex.EncodeToString(asSint), len(asSint))
		must(unzigzag(zigzag(n)) == n, "zigzag round trip")
	}
	minusOne := int64(-1)
	must(len(writeVarint(uint64(minusOne))) == 10 && len(writeVarint(zigzag(-1))) == 1, "zigzag wins")
	fmt.Println("  If a field is often negative (deltas, offsets, temperatures), declare it")
	fmt.Println("  sint32/sint64. The wire type is still VARINT; only the mapping differs.")

	fmt.Println("\n== 7. what you just did ==")
	fmt.Println("  You implemented a protobuf decoder and encoder. The real one adds")
	fmt.Println("  fixed-width types, packed repeated fields, maps and unknown-field")
	fmt.Println("  retention - but not a single new concept.")
	fmt.Println("  Tag, wire type, value. That is the format.")

	fmt.Println("\nOK")
}
