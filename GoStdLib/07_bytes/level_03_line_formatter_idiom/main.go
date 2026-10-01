/*
LEVEL 03 (core) - combining basics: a small key=value line formatter

You will learn
  - bytes.Cut (Go 1.18+) splits a []byte on the first occurrence of a separator,
    the idiomatic replacement for Index+slicing when you only need two pieces
  - bytes.TrimSpace strips leading/trailing whitespace
  - bytes.HasPrefix filters lines
  - composing Split + Cut + TrimSpace + bytes.Buffer into one realistic idiom:
    parse "key = value" lines, skip comments, re-render them aligned

Run: go run ./GoStdLib/07_bytes/level_03_line_formatter_idiom
*/

package main

import (
	"bytes"
	"fmt"
)

func main() {
	input := []byte(`
# server config
host = localhost
port  =  8080
# trailing comment
debug=true
`)

	type kv struct{ key, value string }
	var entries []kv

	for _, line := range bytes.Split(input, []byte("\n")) {
		line = bytes.TrimSpace(line)
		if len(line) == 0 || bytes.HasPrefix(line, []byte("#")) {
			continue // skip blank lines and comments
		}

		key, value, found := bytes.Cut(line, []byte("="))
		if !found {
			panic(fmt.Sprintf("line %q has no '=' separator", line))
		}
		entries = append(entries, kv{
			key:   string(bytes.TrimSpace(key)),
			value: string(bytes.TrimSpace(value)),
		})
	}

	if len(entries) != 3 {
		panic(fmt.Sprintf("parsed %d entries, want 3: %+v", len(entries), entries))
	}
	want := []kv{{"host", "localhost"}, {"port", "8080"}, {"debug", "true"}}
	for i, e := range entries {
		if e != want[i] {
			panic(fmt.Sprintf("entry %d = %+v, want %+v", i, e, want[i]))
		}
	}

	// Re-render aligned, using bytes.Buffer as the io.Writer sink for fmt.Fprintf.
	var out bytes.Buffer
	for _, e := range entries {
		fmt.Fprintf(&out, "%-6s = %s\n", e.key, e.value)
	}

	wantOut := "host   = localhost\nport   = 8080\ndebug  = true\n"
	if out.String() != wantOut {
		panic(fmt.Sprintf("rendered output = %q, want %q", out.String(), wantOut))
	}

	fmt.Print(out.String())
	fmt.Println("OK")
}
