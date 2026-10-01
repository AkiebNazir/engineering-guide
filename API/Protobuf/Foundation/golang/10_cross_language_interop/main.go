/*
FOUNDATION LEVEL 10 - Cross-language interop: the headline feature
===================================================================
This is why protobuf exists. Everything else in this folder - the schema, the
field numbers, the evolution rules - is machinery in service of one claim:

	bytes encoded by ANY language decode correctly in EVERY other language,
	with no adapter, no negotiation and no shared runtime.

Both sides here were compiled from the same ../../proto/l10_interop.proto.
They share NOTHING else: not a library, not a process, not a runtime. Python
has no idea Go exists.

The demo works in two independent ways, so it proves the claim even if you
only ever run one of the two files:

 1. Each file carries BOTH languages' bytes as hex constants below. Go
    asserts it re-produces goEncodedHex and asserts it can decode
    pyEncodedHex. ../../python/10_cross_language_interop.py has the identical
    pair of constants and makes the mirror-image assertions. Neither file can
    pass unless the two languages really do agree byte-for-byte.
 2. Each file also WRITES its own bytes to a shared temp directory and, if
    the other language's file is already there, decodes it live. Run this
    and then the Python one (in either order) to see that half light up.

You will learn
  - that a .proto is the only contract needed between two languages
  - PROOF: Go decodes Python-encoded bytes, field for field
  - PROOF: Go's own encoding matches the byte sequence Python asserts
  - that non-ASCII text survives, because a protobuf string is defined as UTF-8
  - why this makes protobuf the default for polyglot systems, and what the
    corresponding obligation is (the .proto must be shared, not copy-pasted)

Run it   go run ./Protobuf/Foundation/golang/10_cross_language_interop
Then     python Protobuf/Foundation/python/10_cross_language_interop.py
*/
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf8"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l10"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// ---------------------------------------------------------------------------
// The two byte sequences, written down as constants in BOTH language files.
// They are not computed here - they are checked in, so this file makes a
// falsifiable claim about what the other language produces.
// ---------------------------------------------------------------------------
const (
	pyLanguage, pyText = "en", "hello from the other language"
	pyEncodedHex       = "0a02656e121d68656c6c6f2066726f6d20746865206f74686572206c616e67756167651801"

	// Note the non-ASCII characters: a protobuf `string` is defined as UTF-8,
	// so Python writes the same bytes Go does for the same characters.
	goLanguage, goText = "no", "hei fra det andre spraaket, med å og ø"
	goEncodedHex       = "0a026e6f1228686569206672612064657420616e6472652073707261616b65742c" +
		"206d656420c3a5206f6720c3b81801"

	schemaVersion = 1

	// Both languages agree on this one directory (under the OS temp dir,
	// which Go and Python both take from $TMPDIR), and nothing else.
	sharedDirName = "protobuf_foundation_interop"
	pyFile        = "from_python.pb"
	goFile        = "from_go.pb"
)

func main() {
	fmt.Println("== 1. Go encodes a Greeting ==")
	mine := &l10.Greeting{Language: goLanguage, Text: goText, SchemaVersion: schemaVersion}
	encoded, err := proto.Marshal(mine)
	must(err == nil, "marshal")
	fmt.Printf("  %q / %q\n", mine.GetLanguage(), mine.GetText())
	fmt.Printf("  %d bytes: %x\n", len(encoded), encoded)
	// Claim 1: these are exactly the bytes the Python file asserts Go makes.
	must(hex.EncodeToString(encoded) == goEncodedHex, "Go's encoding drifted from the shared constant")
	fmt.Println("  matches goEncodedHex, the constant the Python file also carries")
	fmt.Println("  (as GO_ENCODED_HEX) and decodes on every run.")

	fmt.Println("\n== 2. THE PROOF: Go decodes bytes that Python produced ==")
	// These bytes were produced by protoc-generated PYTHON code. Nothing in
	// this process has ever seen Python, and no conversion step is involved.
	raw, _ := hex.DecodeString(pyEncodedHex)
	fromPy := &l10.Greeting{}
	must(proto.Unmarshal(raw, fromPy) == nil, "unmarshal Python's bytes")
	fmt.Printf("  raw bytes from Python : %s...\n", pyEncodedHex[:48])
	fmt.Printf("  language              : %q\n", fromPy.GetLanguage())
	fmt.Printf("  text                  : %q\n", fromPy.GetText())
	fmt.Printf("  schema_version        : %d\n", fromPy.GetSchemaVersion())
	must(fromPy.GetLanguage() == pyLanguage, "language")
	must(fromPy.GetText() == pyText, "text")
	must(fromPy.GetSchemaVersion() == schemaVersion, "schema_version")
	fmt.Println("  every field, exactly as Python set it. No adapter, no shared runtime.")

	fmt.Println("\n== 3. UTF-8 is part of the contract ==")
	// `string` in a .proto means "UTF-8 bytes". Go strings are byte strings
	// that are conventionally UTF-8, so the two languages agree on non-ASCII
	// text without anyone configuring an encoding.
	var special []string
	for _, r := range goText {
		if r > 127 {
			special = append(special, string(r))
		}
	}
	fmt.Printf("  non-ASCII characters in our text: %q\n", special)
	fmt.Printf("  'å' occupies %d bytes on the wire (c3 a5), 'o' occupies %d\n",
		utf8.RuneLen('å'), utf8.RuneLen('o'))
	must(len(special) == 2 && special[0] == "å" && special[1] == "ø", "two non-ASCII runes")
	must(strings.Contains(goEncodedHex, "c3a5"), "the UTF-8 bytes for a-ring are in the wire data")
	// Go goes one step further than Python here: it REFUSES to encode a
	// proto3 `string` that is not valid UTF-8, because the receiver in another
	// language could not decode it.
	_, err = proto.Marshal(&l10.Greeting{Text: "\xff\xfe not utf-8"})
	must(err != nil, "invalid UTF-8 is rejected")
	fmt.Printf("  and invalid UTF-8 is refused at encode time: %v\n", err)
	fmt.Println("  a `bytes` field, by contrast, is arbitrary binary with NO encoding")
	fmt.Println("  promised - use `string` for text and `bytes` for everything else.")

	fmt.Println("\n== 4. and the reverse direction ==")
	// Re-encoding what Python sent gives Python's bytes back unchanged, so
	// the round trip through Go is lossless in both directions.
	again, err := proto.Marshal(fromPy)
	must(err == nil && hex.EncodeToString(again) == pyEncodedHex, "re-encode reproduces Python's bytes")
	fmt.Println("  re-encoding Python's message in Go reproduces Python's bytes exactly")
	fmt.Println("  -> the two implementations are not merely compatible, they are")
	fmt.Println("     byte-for-byte identical for this message.")
	fmt.Println("  (Protobuf does NOT promise canonical bytes in general - map order and")
	fmt.Println("  unknown fields can vary - so never hash or compare encodings as an")
	fmt.Println("  equality check across languages. Compare decoded messages instead.)")

	fmt.Println("\n== 5. live exchange through a shared file ==")
	shared := filepath.Join(os.TempDir(), sharedDirName)
	must(os.MkdirAll(shared, 0o755) == nil, "create shared dir")
	must(os.WriteFile(filepath.Join(shared, goFile), encoded, 0o644) == nil, "write our bytes")
	fmt.Printf("  wrote my bytes to %s\n", filepath.Join(shared, goFile))

	if data, err := os.ReadFile(filepath.Join(shared, pyFile)); err == nil {
		live := &l10.Greeting{}
		must(proto.Unmarshal(data, live) == nil, "decode Python's live file")
		fmt.Printf("  found %s from a real Python run and decoded it live:\n", pyFile)
		fmt.Printf("    language=%q text=%q version=%d\n",
			live.GetLanguage(), live.GetText(), live.GetSchemaVersion())
		must(live.GetLanguage() != "" && live.GetSchemaVersion() == schemaVersion, "live file content")
		fmt.Println("  that file was written by a Python process, on its own, at another time.")
	} else {
		fmt.Printf("  %s is not there yet - run the Python level to create it:\n", pyFile)
		fmt.Println("      python Protobuf/Foundation/python/10_cross_language_interop.py")
		fmt.Println("  then re-run this program to see it decoded live. (The hex constants")
		fmt.Println("  above already prove the point; this is the hands-on version.)")
	}

	fmt.Println("\n== 6. the obligation that comes with this ==")
	fmt.Println("  Interop is guaranteed by the SCHEMA, so the schema has to be shared")
	fmt.Println("  for real - one file, one source of truth, vendored or pulled from a")
	fmt.Println("  registry. Two hand-maintained copies of the same .proto in two repos")
	fmt.Println("  is the failure mode: they drift, level 06's rules get broken on one")
	fmt.Println("  side only, and the bytes stop meaning the same thing. Keeping that")
	fmt.Println("  from happening is exactly what buf's registry and `buf breaking`")
	fmt.Println("  (level 08) are for.")
	fmt.Printf("  (files exchanged under %s%c)\n", shared, os.PathSeparator)

	fmt.Println("\nOK")
}
