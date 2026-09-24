/*
LEVEL 10 (advanced) - capstone: a log-line normalizer

You will learn
  - putting it together: prefix stripping, splitting, trimming, a Replacer,
    strconv parsing, case-insensitive dedup, sorting, and a Builder report -
    the same shapes as levels 1-9, combined into one realistic pass

Run: go run ./GoStdLib/05_strings/level_10_capstone_normalizer
*/

package main

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

var wordFix = strings.NewReplacer("teh", "the", "recieved", "received")

// entry is a normalized log record: who did what, and how many times.
type entry struct {
	who   string
	what  string
	count int
}

// normalize turns raw "USER: message | count" lines into deduplicated (by
// case-insensitive user), sorted entries, skipping malformed lines.
func normalize(lines []string) []entry {
	byUser := map[string]entry{} // folded lowercase user -> entry (first occurrence wins)
	var order []string
	for _, raw := range lines {
		line := strings.TrimSpace(raw)
		if !strings.Contains(line, ":") || !strings.Contains(line, "|") {
			continue // malformed, skip
		}
		who, rest, _ := strings.Cut(line, ":")
		who = strings.TrimSpace(who)
		msgPart, countPart, _ := strings.Cut(rest, "|")
		msg := wordFix.Replace(strings.TrimSpace(msgPart))
		count, err := strconv.Atoi(strings.TrimSpace(countPart))
		if err != nil {
			continue // bad count, skip
		}

		key := strings.ToLower(who)
		if _, exists := byUser[key]; !exists {
			order = append(order, key)
			byUser[key] = entry{who: who, what: msg, count: count}
		}
	}

	sort.Slice(order, func(i, j int) bool { return strings.Compare(order[i], order[j]) < 0 })
	out := make([]entry, 0, len(order))
	for _, k := range order {
		out = append(out, byUser[k])
	}
	return out
}

// report builds a human-readable summary with a Builder instead of +=.
func report(entries []entry) string {
	var b strings.Builder
	for _, e := range entries {
		b.WriteString(e.who)
		b.WriteString(": ")
		b.WriteString(e.what)
		b.WriteString(" (x")
		b.WriteString(strconv.Itoa(e.count))
		b.WriteString(")\n")
	}
	return b.String()
}

func main() {
	lines := []string{
		"  Bob: teh file was recieved | 3",
		"malformed line with no separators",
		"alice: all good here | 5",
		"ALICE: duplicate, should be ignored | 99",
		"Charlie: bad count | not-a-number",
		"dave:   teh backup recieved twice | 2 ",
	}

	entries := normalize(lines)
	expected := []entry{
		{who: "alice", what: "all good here", count: 5},
		{who: "Bob", what: "the file was received", count: 3},
		{who: "dave", what: "the backup received twice", count: 2},
	}
	if len(entries) != len(expected) {
		panic(fmt.Sprintf("got %d entries, expected %d: %+v", len(entries), len(expected), entries))
	}
	for i, want := range expected {
		if entries[i] != want {
			panic(fmt.Sprintf("entry %d = %+v, expected %+v", i, entries[i], want))
		}
	}

	out := report(entries)
	if strings.Count(out, "\n") != len(entries) {
		panic(fmt.Sprintf("report has %d lines, expected %d", strings.Count(out, "\n"), len(entries)))
	}
	if !strings.Contains(out, "the file was received (x3)") {
		panic(fmt.Sprintf("report missing fixed word substitution: %q", out))
	}

	fmt.Print(out)
	fmt.Println("OK")
}
