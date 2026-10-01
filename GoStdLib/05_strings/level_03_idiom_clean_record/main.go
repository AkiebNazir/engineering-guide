/*
LEVEL 03 (core) - idiom: cleaning a raw record into structured fields

You will learn
  - combining Split, TrimSpace, HasPrefix and ReplaceAll into one small,
    realistic parsing routine - the shape of a real "clean this input" helper

Run: go run ./GoStdLib/05_strings/level_03_idiom_clean_record
*/

package main

import (
	"fmt"
	"strings"
)

// record is a cleaned-up version of a raw "TAG: field1 | field2 | field3" line.
type record struct {
	tag    string
	fields []string
}

// parseRecord expects lines shaped like "LOG: alpha | beta  |gamma".
// It strips the "LOG:" prefix, splits on '|', and trims each field.
func parseRecord(raw string) (record, error) {
	const prefix = "LOG:"
	if !strings.HasPrefix(raw, prefix) {
		return record{}, fmt.Errorf("line %q does not start with %q", raw, prefix)
	}
	body := strings.TrimSpace(strings.TrimPrefix(raw, prefix))
	// Normalize any double spaces left after trimming individual fields.
	rawFields := strings.Split(body, "|")
	fields := make([]string, 0, len(rawFields))
	for _, f := range rawFields {
		clean := strings.ReplaceAll(strings.TrimSpace(f), "  ", " ")
		fields = append(fields, clean)
	}
	return record{tag: "LOG", fields: fields}, nil
}

func main() {
	rec, err := parseRecord("LOG: alpha | beta  world |gamma")
	if err != nil {
		panic(fmt.Sprintf("parseRecord failed: %v", err))
	}
	if rec.tag != "LOG" {
		panic(fmt.Sprintf("tag = %q, expected LOG", rec.tag))
	}
	expected := []string{"alpha", "beta world", "gamma"}
	if len(rec.fields) != len(expected) {
		panic(fmt.Sprintf("got %d fields, expected %d: %v", len(rec.fields), len(expected), rec.fields))
	}
	for i, want := range expected {
		if rec.fields[i] != want {
			panic(fmt.Sprintf("field %d = %q, expected %q", i, rec.fields[i], want))
		}
	}

	if _, err := parseRecord("NOPE: bad line"); err == nil {
		panic("expected an error for a line missing the LOG: prefix")
	}

	fmt.Printf("parsed record: tag=%s fields=%v\n", rec.tag, rec.fields)
	fmt.Println("OK")
}
