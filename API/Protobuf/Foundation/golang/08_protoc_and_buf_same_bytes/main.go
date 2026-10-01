/*
FOUNDATION LEVEL 08 - Two toolchains, one schema, identical bytes
==================================================================
Every level so far used `protoc`, the official compiler. In real teams you
will meet a second toolchain, `buf`, and the obvious worry is whether it
produces different, incompatible code. This level settles that by comparing
what both of them generated from ../../proto/l08_toolchains.proto.

The short answer: buf replaces the DRIVER, not the code generator. Look at
../../buf.gen.yaml - it says `local: protoc-gen-go`, the exact same plugin
binary protoc invokes. So the generated Go is identical, and therefore the
encoded bytes are identical. buf's value is entirely in the workflow around
codegen:

	protoc                                    buf
	------------------------------------      ------------------------------------
	every include path and input file on      the schema is declared once in
	the command line, every time              buf.yaml and checked in
	plugin flags memorised or buried in       plugin config declared in
	a Makefile                                buf.gen.yaml, reproducible in CI
	imports resolved from your filesystem     dependencies resolved and version-
	(vendor other people's protos by hand)    pinned from a registry
	no opinion on schema quality              `buf lint` enforces conventions
	no protection against rule 2 of           `buf breaking` diffs against the
	level 06                                  last release and FAILS the build

That last row is the one that makes teams switch: level 06 listed a pile of
changes that break compatibility silently, and `buf breaking` is how you stop
them at review time instead of discovering them in production.

Where the two outputs live (both checked in, so neither tool is needed to run
this level):

	protoc -> ../pb/l08/l08_toolchains.pb.go
	buf    -> ../../buf_out/golang/pb/l08/l08_toolchains.pb.go

WHY THIS LEVEL COMPARES SOURCE FILES INSTEAD OF IMPORTING BOTH. Both packages
register a file called "l08_toolchains.proto" and a message called
found.l08.Metric in the process-wide protobuf registry when they initialise.
Linking both into one binary makes the second registration PANIC at startup
("file ... is already registered"). That is a feature: two definitions of one
message name in one process is almost always a vendoring bug. The Python twin
works around it with a subprocess; in Go the generated SOURCE is the more
direct evidence anyway, because it is literally the code that would run.

You will learn
  - that both toolchains call the SAME codegen plugin, so neither owns the format
  - PROOF: the protoc- and buf-generated Go files differ only in a version comment
  - PROOF: the encoded bytes match a constant the Python twin also asserts
  - why a Go binary cannot link two copies of the same .proto
  - what buf adds that protoc has no answer for: lint and breaking-change checks

Run it   go run ./Protobuf/Foundation/golang/08_protoc_and_buf_same_bytes
*/
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoregistry"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l08" // the protoc-generated package
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// The message both toolchains' code is asked to encode, and the bytes it must
// produce. The identical constant is in ../../python/08_protoc_and_buf_same_bytes.py,
// so this is a claim about BOTH languages, not a value computed here.
const (
	name        = "cpu.load"
	value       = 0.75
	expectedHex = "0a086370752e6c6f616411000000000000e83f1a06686f73743d611a08656e763d70726f64"
)

var labels = []string{"host=a", "env=prod"}

// foundationDir finds API/Protobuf/Foundation from wherever this was started
// (`go run` from API/, from the repo root, or from inside the folder).
func foundationDir() (string, bool) {
	dir, err := os.Getwd()
	if err != nil {
		return "", false
	}
	for i := 0; i < 8; i++ {
		for _, candidate := range []string{
			dir,
			filepath.Join(dir, "Protobuf", "Foundation"),
			filepath.Join(dir, "API", "Protobuf", "Foundation"),
		} {
			if _, err := os.Stat(filepath.Join(candidate, "buf.gen.yaml")); err == nil {
				return candidate, true
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return "", false
}

func main() {
	fmt.Println("== 1. encode with the protoc-generated code ==")
	metric := &l08.Metric{Name: name, Value: value, Labels: labels}
	encoded, err := proto.Marshal(metric)
	must(err == nil, "marshal")
	fmt.Printf("  Metric{Name: %q, Value: %v, Labels: %q}\n", name, value, labels)
	fmt.Printf("  %d bytes: %x\n", len(encoded), encoded)
	must(hex.EncodeToString(encoded) == expectedHex, "protoc-generated Go matches the shared constant")
	fmt.Println("  matches EXPECTED_HEX - the same constant the Python protoc AND buf")
	fmt.Println("  code are asserted against in the Python twin of this level.")

	root, ok := foundationDir()
	protocPath := filepath.Join(root, "golang", "pb", "l08", "l08_toolchains.pb.go")
	bufPath := filepath.Join(root, "buf_out", "golang", "pb", "l08", "l08_toolchains.pb.go")
	protocSrc, errA := os.ReadFile(protocPath)
	bufSrc, errB := os.ReadFile(bufPath)
	if !ok || errA != nil || errB != nil {
		// Graceful degradation: the lesson still stands, we just cannot show
		// the comparison from this working directory.
		fmt.Println("\n== 2. buf ==")
		fmt.Println("  SKIPPED: could not find the two generated files from this working")
		fmt.Println("  directory. Run from API/:  go run ./Protobuf/Foundation/golang/08_protoc_and_buf_same_bytes")
		fmt.Println("  or install buf and re-run ../../generate.sh to regenerate buf_out/.")
		fmt.Println("\nOK")
		return
	}

	fmt.Println("\n== 2. compare the two generated Go files, line by line ==")
	a := strings.Split(string(protocSrc), "\n")
	b := strings.Split(string(bufSrc), "\n")
	fmt.Printf("  protoc output : %5d bytes, %d lines  (golang/pb/l08/)\n", len(protocSrc), len(a))
	fmt.Printf("  buf output    : %5d bytes, %d lines  (buf_out/golang/pb/l08/)\n", len(bufSrc), len(b))
	must(len(a) == len(b), "same number of lines")
	var differing []int
	for i := range a {
		if a[i] != b[i] {
			differing = append(differing, i)
		}
	}
	for _, i := range differing {
		fmt.Printf("  line %d differs:\n    protoc: %s\n    buf   : %s\n", i+1, a[i], b[i])
		// Every difference must be a COMMENT. Anything else would be a real
		// codegen difference and this level's claim would be false.
		must(strings.HasPrefix(strings.TrimSpace(a[i]), "//") &&
			strings.HasPrefix(strings.TrimSpace(b[i]), "//"), "only comments differ")
	}
	must(len(differing) <= 1, "at most the version comment differs")
	fmt.Printf("  %d of %d lines differ, and every one is a comment: the header records\n",
		len(differing), len(a))
	fmt.Println("  which protoc VERSION produced the file. buf does not run protoc at all")
	fmt.Println("  (it has its own compiler), so it writes `(unknown)` there.")

	fmt.Println("\n== 3. THE PROOF ==")
	fmt.Println("  Every line of executable code - the struct, the getters, the embedded")
	fmt.Println("  raw descriptor - is identical. Identical code encodes identical bytes,")
	fmt.Printf("  so buf's package produces %s too.\n", expectedHex[:24]+"...")
	fmt.Println("  Neither toolchain owns the wire format. The .proto file does.")

	fmt.Println("\n== 4. why you cannot link both packages into one binary ==")
	// The protoc package registered itself when this program started. Ask the
	// global registry what it holds - this is what the buf package would
	// collide with if it were imported too.
	fd, err := protoregistry.GlobalFiles.FindFileByPath("l08_toolchains.proto")
	must(err == nil, "the protoc package registered its file")
	fmt.Printf("  global registry already holds %q (package %s)\n", fd.Path(), fd.Package())
	fmt.Println("  importing dsapractice/api/Protobuf/Foundation/buf_out/golang/pb/l08 as")
	fmt.Println("  well would register the same path and the same message name again,")
	fmt.Println("  and protobuf-go's default policy for that is to PANIC at init:")
	fmt.Println("      proto: file \"l08_toolchains.proto\" is already registered")
	fmt.Println("  (GOLANG_PROTOBUF_REGISTRATION_CONFLICT=warn downgrades it - don't; fix")
	fmt.Println("  the duplicate instead. It means two copies of a schema, which is level")
	fmt.Println("  10's 'shared, not copy-pasted' rule being broken.)")

	// And a detail the Python twin has to explain away: in Go the embedded
	// descriptors match exactly, json_name included, because protoc always
	// fills json_name when it hands a file to an EXTERNAL plugin such as
	// protoc-gen-go, and buf's compiler always writes it too.
	fdp := protodesc.ToFileDescriptorProto(fd)
	field := fdp.GetMessageType()[0].GetField()[0]
	fmt.Printf("  embedded descriptor: field %q has json_name=%q recorded explicitly\n",
		field.GetName(), field.GetJsonName())
	must(field.GetJsonName() == "name", "json_name present in the protoc-generated Go descriptor")

	fmt.Println("\n== 5. what buf adds that protoc cannot ==")
	fmt.Println("  ../../buf.yaml declares the schema once, so `buf generate` needs no flags:")
	fmt.Println("      protoc -I proto --go_out=. --go_opt=module=... proto/*.proto")
	fmt.Println("      buf generate")
	fmt.Println("  and it unlocks two commands protoc has no equivalent for:")
	fmt.Println("      buf lint      - enforce naming/structure conventions across the repo")
	fmt.Println("      buf breaking  - diff this schema against the last released version")
	fmt.Println("                      and FAIL if any change from level 06's breaking list")
	fmt.Println("                      slipped in (renumbered field, changed type, reused tag)")
	fmt.Println("  Try it:  cd Protobuf/Foundation && buf lint && buf breaking \\")
	fmt.Println("            --against '../../../.git#branch=main,subdir=API/Protobuf/Foundation'")
	fmt.Println("  That is the real reason to adopt buf. Not different bytes - the same")
	fmt.Println("  bytes, with rule 2 of level 06 enforced by CI instead of by memory.")

	fmt.Println("\nOK")
}
