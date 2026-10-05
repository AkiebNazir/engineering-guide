/*
FOUNDATION LEVEL 05 - Enums, and the unknown value that will definitely arrive
===============================================================================
An enum is a named set of integers. On the wire it is just a varint, so an
enum field costs the same as an int32 - the names exist only in your code.

That last sentence is the whole lesson. Because only the NUMBER travels, a
newer sender can hand you a number your build has never heard of. This is not
a hypothetical: it happens every time two services are deployed minutes apart.
proto3 handles it gracefully - the unknown number is kept, not rejected, and
re-serialising gives it back untouched - but YOUR code has to expect it.

The two schemas here model exactly that deployment window:

  - ../../proto/l05_new.proto knows STATUS_ARCHIVED = 3  (the upgraded service)
  - ../../proto/l05_old.proto does not                   (a client not yet redeployed)

You will learn
  - declaring an enum, and why the zero value must exist and be *_UNSPECIFIED
  - that an enum field is a plain varint on the wire - names are compiled away
  - PROOF: a value of 3 sent by the new schema survives in the old schema
    and round-trips back out unchanged
  - that Go's generated enum type is an int32, so an unknown value is legal
  - why a `switch` over enum values without a default branch is a latent bug

Run it   go run ./Protobuf/Foundation/golang/05_enums_and_unknown_values
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l05new" // knows QUEUED, RUNNING, ARCHIVED
	"dsapractice/api/Protobuf/Foundation/golang/pb/l05old" // knows QUEUED, RUNNING only
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

// describeBadly looks exhaustive. It is not: it silently mislabels every
// future value as "waiting".
func describeBadly(status l05old.Status) string {
	switch status {
	case l05old.Status_STATUS_QUEUED:
		return "waiting"
	case l05old.Status_STATUS_RUNNING:
		return "in progress"
	}
	return "waiting" // <- the lie: an unknown status is reported as queued
}

// describeWell degrades visibly instead of inventing a state.
func describeWell(status l05old.Status) string {
	switch status {
	case l05old.Status_STATUS_QUEUED:
		return "waiting"
	case l05old.Status_STATUS_RUNNING:
		return "in progress"
	default:
		return fmt.Sprintf("unrecognised status %d (this build is older than the sender)", status)
	}
}

func main() {
	fmt.Println("== 1. an enum is a set of names for integers ==")
	// protoc prefixes the Go constants with the enum type name, so the proto
	// value STATUS_QUEUED becomes Status_STATUS_QUEUED.
	fmt.Printf("  Status_STATUS_UNSPECIFIED = %d\n", l05new.Status_STATUS_UNSPECIFIED)
	fmt.Printf("  Status_STATUS_QUEUED      = %d\n", l05new.Status_STATUS_QUEUED)
	fmt.Printf("  Status_STATUS_RUNNING     = %d\n", l05new.Status_STATUS_RUNNING)
	fmt.Printf("  Status_STATUS_ARCHIVED    = %d   (new schema only)\n",
		l05new.Status_STATUS_ARCHIVED)
	// The generated type has a String() method and name/number maps.
	fmt.Printf("  Status(2).String()        -> %q\n", l05new.Status(2).String())
	fmt.Printf("  Status_value[\"STATUS_QUEUED\"] -> %d\n", l05new.Status_value["STATUS_QUEUED"])
	must(l05new.Status_STATUS_ARCHIVED == 3, "archived is 3")
	must(l05new.Status(2).String() == "STATUS_RUNNING", "String() maps number to name")

	fmt.Println("\n== 2. why the zero value is mandatory ==")
	// proto3 requires the first enum value to be 0, because a plain enum field
	// is a plain scalar (level 04): unset reads as 0. If 0 meant a real state,
	// every message that forgot to set the field would silently claim it.
	job := &l05new.Job{Id: "j1"}
	fmt.Printf("  a Job with no status set reads as %q (= %d)\n",
		job.GetStatus().String(), job.GetStatus())
	must(job.GetStatus() == l05new.Status_STATUS_UNSPECIFIED, "unset enum is the zero value")
	fmt.Println("  => naming 0 *_UNSPECIFIED makes 'nobody set this' an explicit,")
	fmt.Println("     checkable state instead of an accidental default like QUEUED.")

	fmt.Println("\n== 3. on the wire, an enum is just a number ==")
	running := &l05new.Job{Id: "j1", Status: l05new.Status_STATUS_RUNNING}
	data := mustMarshal(running)
	fmt.Printf("  Job{Id: \"j1\", Status: RUNNING} -> %x\n", data)
	fmt.Println("    0a 02 6a31 = field 1, 2 bytes, 'j1'")
	fmt.Println("    10 02      = field 2, varint 2      <- the NAME is nowhere on the wire")
	must(fmt.Sprintf("%x", data) == "0a026a311002", "enum encodes as a bare varint")
	must(!bytes.Contains(data, []byte("RUNNING")), "enum names are never encoded")

	fmt.Println("\n== 4. THE PROOF: an unknown value arrives from a newer schema ==")
	// The upgraded service archives a job and sends it.
	archived := &l05new.Job{Id: "j1", Status: l05new.Status_STATUS_ARCHIVED}
	wire := mustMarshal(archived)
	fmt.Printf("  new schema sends status=3 : %x\n", wire)

	// The old client parses it. It has never heard of 3. It does NOT error,
	// and it does NOT reset the field - the number is retained as-is. This
	// works because the generated Go enum type is an int32, not a closed set.
	received := &l05old.Job{}
	must(proto.Unmarshal(wire, received) == nil, "old schema parses new bytes without error")
	fmt.Printf("  old schema parses it, no error. received.GetStatus() = %d\n", received.GetStatus())
	must(received.GetStatus() == 3, "the unknown number is kept verbatim")

	// The old client cannot NAME it, which is the honest outcome: String()
	// falls back to the bare number rather than guessing.
	fmt.Printf("  received.GetStatus().String() -> %q (no name in this build)\n",
		received.GetStatus().String())
	_, known := l05old.Status_name[3]
	must(!known, "the old schema genuinely has no name for 3")
	fmt.Printf("  Status_name[3] exists in the old build? %v\n", known)

	// ...and forwarding it on loses nothing. This is what makes rolling
	// deploys and proxies safe: a middleman that does not understand a value
	// still passes it through byte-for-byte.
	forwarded := mustMarshal(received)
	fmt.Printf("  old schema re-serialises  : %x\n", forwarded)
	must(bytes.Equal(forwarded, wire), "round trip through the old schema is lossless")
	fmt.Println("  IDENTICAL to what the new schema sent -> nothing was dropped.")
	roundTripped := &l05new.Job{}
	must(proto.Unmarshal(forwarded, roundTripped) == nil, "new schema re-reads it")
	must(roundTripped.GetStatus() == l05new.Status_STATUS_ARCHIVED, "value intact")
	fmt.Printf("  and the new schema reads it back as %q\n", roundTripped.GetStatus().String())

	fmt.Println("\n== 5. the bug this creates in ordinary-looking code ==")
	fmt.Printf("  no default   -> %q   <- WRONG, and silent\n", describeBadly(received.GetStatus()))
	fmt.Printf("  with default -> %q\n", describeWell(received.GetStatus()))
	must(describeBadly(received.GetStatus()) == "waiting", "the bad version mislabels it")
	must(describeWell(received.GetStatus()) !=
		describeBadly(received.GetStatus()), "the good version differs")
	fmt.Println("  => always write the default branch. Go will NOT warn you here: the")
	fmt.Println("     enum type is an int32, so the compiler considers any switch over")
	fmt.Println("     it non-exhaustive by nature. New enum values WILL arrive, from a")
	fmt.Println("     service that was deployed four minutes before yours.")

	fmt.Println("\nOK")
}
