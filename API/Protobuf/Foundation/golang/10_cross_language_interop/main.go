/*
FOUNDATION LEVEL 10 - Cross-language interop: the headline feature
===================================================================
This is why protobuf exists. Everything else in this folder - the schema, the
field numbers, the evolution rules - is machinery in service of one claim:

    bytes encoded by ANY language decode correctly in EVERY other language,
    with no adapter, no negotiation and no shared runtime.

Both sides here were compiled from the same ../proto/l10_interop.proto. They
share NOTHING else: not a library, not a process, not an interpreter. Go has
no idea Python exists.

Run it   go run ./10_cross_language_interop
*/
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l10"
)

const (
	PY_LANGUAGE    = "en"
	PY_TEXT        = "hello from the other language"
	PY_ENCODED_HEX = "0a02656e121d68656c6c6f2066726f6d20746865206f74686572206c616e67756167651801"

	GO_LANGUAGE    = "no"
	GO_TEXT        = "hei fra det andre spraaket, med å og ø"
	GO_ENCODED_HEX = "0a026e6f1228686569206672612064657420616e6472652073707261616b65742c206d656420c3a5206f6720c3b81801"

	SCHEMA_VERSION = 1
	
	PY_FILE = "from_python.pb"
	GO_FILE = "from_go.pb"
)

func must(err error, what string) {
	if err != nil {
		panic(fmt.Sprintf("FAILED %s: %v", what, err))
	}
}

func mustBe(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== 1. Go encodes a Greeting ==")
	mine := &l10.Greeting{
		Language:      GO_LANGUAGE,
		Text:          GO_TEXT,
		SchemaVersion: SCHEMA_VERSION,
	}
	
	encoded, err := proto.Marshal(mine)
	must(err, "marshal")
	fmt.Printf("  %q / %q\n", mine.Language, mine.Text)
	fmt.Printf("  %d bytes: %x\n", len(encoded), encoded)
	mustBe(hex.EncodeToString(encoded) == GO_ENCODED_HEX, "Go's encoding drifted from the shared constant")
	fmt.Println("  matches GO_ENCODED_HEX, the constant the Python file also carries.")

	fmt.Println("\n== 2. THE PROOF: Go decodes bytes that Python produced ==")
	pyBytes, _ := hex.DecodeString(PY_ENCODED_HEX)
	fromPy := &l10.Greeting{}
	err = proto.Unmarshal(pyBytes, fromPy)
	must(err, "unmarshal")
	
	fmt.Printf("  raw bytes from Python: %s...\n", PY_ENCODED_HEX[:48])
	fmt.Printf("  language             : %q\n", fromPy.Language)
	fmt.Printf("  text                 : %q\n", fromPy.Text)
	fmt.Printf("  schema_version       : %d\n", fromPy.SchemaVersion)
	
	mustBe(fromPy.Language == PY_LANGUAGE, "language matches")
	mustBe(fromPy.Text == PY_TEXT, "text matches")
	mustBe(fromPy.SchemaVersion == SCHEMA_VERSION, "version matches")
	fmt.Println("  every field, exactly as Python set it. No adapter, no shared runtime.")

	fmt.Println("\n== 3. UTF-8 is part of the contract ==")
	fmt.Println("  `string` in a .proto means \"UTF-8 bytes\". That is why the two languages")
	fmt.Println("  agree on non-ASCII text without anyone configuring an encoding.")
	fmt.Println("  Go strings are naturally UTF-8, so this is seamless.")

	fmt.Println("\n== 4. and the reverse direction ==")
	reEncoded, _ := proto.Marshal(fromPy)
	mustBe(hex.EncodeToString(reEncoded) == PY_ENCODED_HEX, "re-encoded py matches")
	fmt.Println("  re-encoding Python's message in Go reproduces Python's bytes exactly")
	fmt.Println("  -> the two implementations are not merely compatible, they are")
	fmt.Println("     byte-for-byte deterministic for this message.")

	fmt.Println("\n== 5. live exchange through a shared file ==")
	tmp := os.TempDir()
	sharedDir := filepath.Join(tmp, "protobuf_foundation_interop")
	os.MkdirAll(sharedDir, 0755)
	
	err = os.WriteFile(filepath.Join(sharedDir, GO_FILE), encoded, 0644)
	must(err, "write file")
	fmt.Printf("  wrote my bytes to %s\n", filepath.Join(sharedDir, GO_FILE))
	
	pyPath := filepath.Join(sharedDir, PY_FILE)
	if pyData, err := os.ReadFile(pyPath); err == nil {
		live := &l10.Greeting{}
		must(proto.Unmarshal(pyData, live), "unmarshal live")
		fmt.Printf("  found %s from a real Python run and decoded it live:\n", PY_FILE)
		fmt.Printf("    language=%q text=%q version=%d\n", live.Language, live.Text, live.SchemaVersion)
		mustBe(live.Language != "" && live.SchemaVersion == SCHEMA_VERSION, "live decoded")
		fmt.Println("  that file was written by a Python process, on its own, at another time.")
	} else {
		fmt.Printf("  %s is not there yet - run the Python level to create it:\n", PY_FILE)
		fmt.Println("      python 10_cross_language_interop.py")
		fmt.Println("  then re-run this file to see it decoded live.")
	}

	fmt.Println("\n== 6. the obligation that comes with this ==")
	fmt.Println("  Interop is guaranteed by the SCHEMA, so the schema has to be shared")
	fmt.Println("  for real - one file, one source of truth, vendored or pulled from a")
	fmt.Println("  registry. Two hand-maintained copies of the same .proto in two repos")
	fmt.Println("  is the failure mode.")

	fmt.Println("\nOK")
}
