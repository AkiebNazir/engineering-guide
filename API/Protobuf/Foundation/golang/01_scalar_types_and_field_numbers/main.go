/*
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
  - the scalar types you will actually use: string, int32/int64, bool, double, bytes
  - that "= 1" is a permanent field number, not a value, index or ordering
  - PROOF: bytes encoded from a schema calling field 1 `title` decode perfectly
    under a schema calling field 1 `name` - because the name never travelled
  - why field numbers 1-15 are worth guarding: their tag costs one byte, 16+ cost two
  - that numbers need not be contiguous or in order - only unique and stable

Run it   go run ./Protobuf/Foundation/golang/01_scalar_types_and_field_numbers
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l01v1" // field 1 is called `title`
	"dsapractice/api/Protobuf/Foundation/golang/pb/l01v2" // field 1 is called `name`
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== 1. the scalar types you will actually use ==")
	book := &l01v1.Book{
		Title:          "The Go Programming Language",
		Year:           2015,                        // int32  - whole numbers, varint-encoded
		InPrint:        true,                        // bool   - one byte: 0 or 1
		Price:          39.99,                       // double - always 8 fixed bytes
		CopiesSold:     1250000,                     // int64  - same as int32, wider range
		CoverThumbnail: []byte{0x89, 'P', 'N', 'G'}, // bytes - arbitrary binary
	}
	fmt.Printf("  Title           = %q\n", book.GetTitle())
	fmt.Printf("  Year            = %d\n", book.GetYear())
	fmt.Printf("  InPrint         = %v\n", book.GetInPrint())
	fmt.Printf("  Price           = %v\n", book.GetPrice())
	fmt.Printf("  CopiesSold      = %d\n", book.GetCopiesSold())
	fmt.Printf("  CoverThumbnail  = %v\n", book.GetCoverThumbnail())
	// Note the naming: protoc converts snake_case proto fields into the
	// exported CamelCase Go names Go programmers expect. Only the spelling
	// changes; the field number is untouched.

	encoded, err := proto.Marshal(book)
	must(err == nil, "marshal")
	fmt.Printf("\n  encoded: %d bytes\n", len(encoded))
	fmt.Printf("  hex    : %x\n", encoded)
	// The strings are visible in the hex because a protobuf string is just its
	// UTF-8 bytes, stored verbatim. Everything AROUND them is the structure.
	must(bytes.Contains(encoded, []byte("The Go Programming Language")), "strings are stored verbatim")
	fmt.Println(`  the string bytes are stored verbatim - but "title" is not in there at all:`)
	must(!bytes.Contains(encoded, []byte("title")), "field names are never encoded")
	fmt.Printf("    bytes.Contains(encoded, []byte(\"title\")) -> %v\n",
		bytes.Contains(encoded, []byte("title")))

	fmt.Println("\n== 2. THE PROOF: rename the field, keep the number ==")
	// l01_v2.proto is a byte-for-byte copy of l01_v1.proto with ONE edit:
	//     string title = 1;   ->   string name = 1;
	// Nothing else changed. Now parse v1's bytes with v2's generated type.
	reread := &l01v2.Book{}
	must(proto.Unmarshal(encoded, reread) == nil, "v2 parses v1 bytes")
	fmt.Printf("  encoded with v1 (field 1 = `title`) : %q\n", book.GetTitle())
	fmt.Printf("  decoded with v2 (field 1 = `name`)  : %q\n", reread.GetName())
	must(reread.GetName() == book.GetTitle(), "the value landed in the renamed field")
	must(reread.GetYear() == 2015 && reread.GetPrice() == 39.99 && reread.GetInPrint(),
		"every other field decoded too")

	// And the reverse direction, for completeness: v2's bytes under v1's type.
	v2Bytes, err := proto.Marshal(reread)
	must(err == nil, "marshal v2")
	back := &l01v1.Book{}
	must(proto.Unmarshal(v2Bytes, back) == nil, "v1 parses v2 bytes")
	must(back.GetTitle() == "The Go Programming Language", "round trip back to v1")
	fmt.Println("  and back again, v2 -> v1: still correct")
	fmt.Println("  => renaming a field is a SAFE, invisible change. The name is for you,")
	fmt.Println("     not for the wire. (Renaming it in every codebase that reads it is")
	fmt.Println("     still work - it is just not a DATA-compatibility problem.)")

	// The real reason this works: encoding the same value under both schemas
	// produces literally the same bytes. The two schemas are wire-identical.
	must(bytes.Equal(v2Bytes, encoded), "v2 re-encodes to exactly v1's bytes")
	fmt.Printf("  re-encoded under v2 == original v1 bytes: %v\n", bytes.Equal(v2Bytes, encoded))

	fmt.Println("\n== 3. why 1-15 are precious ==")
	// A field's tag packs the number and the wire type together:
	//     tag = (field_number << 3) | wire_type
	// Three bits go to the wire type, so numbers 1-15 fit in the remaining
	// four bits of a single byte. Number 16 needs a second byte, forever.
	for _, number := range []int{1, 15, 16, 2047} {
		tag := number << 3 // wire type 0, just to size the tag
		size := 1
		switch {
		case tag >= 1<<14:
			size = 3
		case tag >= 1<<7:
			size = 2
		}
		fmt.Printf("  field number %4d -> tag value %6d -> %d tag byte(s)\n", number, tag, size)
	}
	fmt.Println("  => put your hottest, most-repeated fields in 1-15. In a message sent")
	fmt.Println("     a billion times a day, one byte per field per message is real money.")

	fmt.Println("\n== 4. numbers need not be tidy ==")
	// Only two rules: unique within the message, and never changed once
	// shipped. Gaps and out-of-order declarations are normal in mature
	// schemas, usually because fields were deleted (see level 06's `reserved`).
	sparse := &l01v1.Book{Title: "Sparse", CopiesSold: 5} // fields 1 and 5 only
	sparseBytes, err := proto.Marshal(sparse)
	must(err == nil, "marshal sparse")
	fmt.Printf("  only fields 1 and 5 set -> %d bytes (%x)\n", len(sparseBytes), sparseBytes)
	fmt.Println("  unset fields cost ZERO bytes. Nothing is reserved or padded for them.")
	must(len(sparseBytes) < len(encoded), "skipping fields really does shrink the payload")

	fmt.Println("\nOK")
}
