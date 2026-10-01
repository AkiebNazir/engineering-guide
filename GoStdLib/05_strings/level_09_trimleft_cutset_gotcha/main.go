/*
LEVEL 09 (advanced) - production trap: TrimLeft/TrimRight take a CUTSET, not a prefix

You will learn
  - strings.TrimLeft(s, cutset) removes a leading RUN of any characters that
    appear in cutset - it does not match the literal substring cutset
  - this silently over-trims whenever the content right after the "prefix"
    happens to start with a character that's also in the cutset
  - the fix: strings.TrimPrefix(s, prefix) for an exact, one-shot prefix

Run: go run ./GoStdLib/05_strings/level_09_trimleft_cutset_gotcha
*/

package main

import (
	"fmt"
	"strings"
)

func main() {
	// Intent: strip the 2-character prefix "xy" from an id.
	// Bug bait: the content right after that prefix ALSO starts with 'x',
	// which is one of the cutset characters.
	id := "xyxHello" // prefix "xy", real content "xHello"

	// --- BROKEN: TrimLeft treats "xy" as a set of characters {x, y}, not a
	// literal 2-byte prefix, so it keeps eating the leading 'x' of "xHello" too.
	broken := strings.TrimLeft(id, "xy")
	if broken != "Hello" {
		panic(fmt.Sprintf("expected the cutset bug to over-trim to %q, got %q (environment differs from what this level assumes)", "Hello", broken))
	}
	fmt.Printf("BROKEN: TrimLeft(%q, \"xy\") = %q (lost the leading 'x' of the real content)\n", id, broken)

	// --- FIXED: TrimPrefix removes the literal "xy" exactly once, nothing more.
	fixed := strings.TrimPrefix(id, "xy")
	if fixed != "xHello" {
		panic(fmt.Sprintf("TrimPrefix(%q, \"xy\") = %q, expected %q", id, fixed, "xHello"))
	}
	fmt.Printf("FIXED:   TrimPrefix(%q, \"xy\") = %q (content preserved)\n", id, fixed)

	// A case where TrimLeft happens to be "safe" - deceptive proof that the
	// bug is data-dependent, not something a quick manual test would catch.
	safeCase := "xyHello"
	if strings.TrimLeft(safeCase, "xy") != strings.TrimPrefix(safeCase, "xy") {
		panic("expected TrimLeft and TrimPrefix to happen to agree on this input")
	}
	fmt.Printf("NOTE: on %q both functions happen to agree (%q) - the bug only shows up depending on what follows the prefix\n",
		safeCase, strings.TrimPrefix(safeCase, "xy"))

	fmt.Println("OK")
}
