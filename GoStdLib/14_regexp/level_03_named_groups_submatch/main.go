/*
LEVEL 03 (advanced) - named capture groups: FindStringSubmatch + SubexpNames

You will learn
  - (?P<name>...) names a capture group inside the pattern
  - FindStringSubmatch returns a []string: index 0 is the whole match,
    indexes 1..N are the groups in the order they appear in the pattern
  - SubexpNames() returns the name for each of those same indexes (index 0
    is always "") - zip the two together to read matches by name instead of
    fragile positional index

Run: go run ./GoStdLib/14_regexp/level_03_named_groups_submatch
*/

package main

import (
	"fmt"
	"regexp"
)

var kv = regexp.MustCompile(`(?P<key>[a-zA-Z_]+)=(?P<value>[^;]+)`)

// parseKV turns "key=value" into a map, reading groups back BY NAME via
// SubexpNames - robust against someone later reordering groups in the
// pattern, unlike hardcoding match[1]/match[2].
func parseKV(s string) map[string]string {
	match := kv.FindStringSubmatch(s)
	if match == nil {
		return nil
	}
	names := kv.SubexpNames()
	result := make(map[string]string)
	for i, name := range names {
		if i == 0 || name == "" {
			continue // index 0 is the whole match; unnamed groups have name ""
		}
		result[name] = match[i]
	}
	return result
}

func main() {
	got := parseKV("user_id=42;other=stuff")
	if got == nil {
		panic("parseKV returned nil, want a match")
	}
	if got["key"] != "user_id" {
		panic(fmt.Sprintf(`got["key"] = %q, want "user_id"`, got["key"]))
	}
	if got["value"] != "42" {
		panic(fmt.Sprintf(`got["value"] = %q, want "42"`, got["value"]))
	}

	// Confirm SubexpNames' shape directly: index 0 empty, then our two names
	// in pattern order.
	names := kv.SubexpNames()
	wantNames := []string{"", "key", "value"}
	if len(names) != len(wantNames) {
		panic(fmt.Sprintf("SubexpNames() = %v, want %v", names, wantNames))
	}
	for i := range wantNames {
		if names[i] != wantNames[i] {
			panic(fmt.Sprintf("SubexpNames()[%d] = %q, want %q", i, names[i], wantNames[i]))
		}
	}

	// FindAllStringSubmatch: every match, each as its own []string.
	multi := regexp.MustCompile(`(?P<num>\d+)`)
	allMatches := multi.FindAllStringSubmatch("a1 b22 c333", -1)
	if len(allMatches) != 3 {
		panic(fmt.Sprintf("len(allMatches) = %d, want 3", len(allMatches)))
	}
	wantNums := []string{"1", "22", "333"}
	for i, m := range allMatches {
		if m[1] != wantNums[i] {
			panic(fmt.Sprintf("allMatches[%d][1] = %q, want %q", i, m[1], wantNums[i]))
		}
	}

	// No match: FindStringSubmatch returns nil, not an empty non-nil slice.
	if m := kv.FindStringSubmatch("no equals sign here"); m != nil {
		panic(fmt.Sprintf("FindStringSubmatch on non-matching text = %v, want nil", m))
	}

	fmt.Printf("parsed: %+v\n", got)
	fmt.Println("OK")
}
