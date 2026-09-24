/*
LEVEL 05 (advanced) - ReplaceAllString and ReplaceAllStringFunc

You will learn
  - ReplaceAllString substitutes every match with a replacement template,
    where $1, $2 (or ${name}) refer back to captured groups
  - ReplaceAllStringFunc instead calls a function with each raw match and
    substitutes whatever it returns - for replacements that need real logic,
    not just rearranging captured text

Run: go run ./GoStdLib/14_regexp/level_05_replace_all
*/

package main

import (
	"fmt"
	"regexp"
	"strings"
)

func main() {
	// ReplaceAllString: template-based, using $1/$2 to reference groups.
	dateRe := regexp.MustCompile(`(\d{4})-(\d{2})-(\d{2})`)
	in := "logged on 2024-01-15 and again on 2024-03-02"
	out := dateRe.ReplaceAllString(in, "$3/$2/$1")
	want := "logged on 15/01/2024 and again on 02/03/2024"
	if out != want {
		panic(fmt.Sprintf("ReplaceAllString = %q, want %q", out, want))
	}

	// ReplaceAllStringFunc: real logic per match - here, uppercasing every
	// standalone word "warn" or "error" for visibility, something a template
	// string alone cannot express.
	levelRe := regexp.MustCompile(`\b(warn|error)\b`)
	logLine := "warn: disk low; error: disk full; info: retrying"
	shouted := levelRe.ReplaceAllStringFunc(logLine, func(match string) string {
		return strings.ToUpper(match)
	})
	wantShouted := "WARN: disk low; ERROR: disk full; info: retrying"
	if shouted != wantShouted {
		panic(fmt.Sprintf("ReplaceAllStringFunc = %q, want %q", shouted, wantShouted))
	}

	// ReplaceAllStringFunc receives the WHOLE match text, not sub-groups -
	// if you need group data inside the func, re-run FindStringSubmatch (or
	// use ReplaceAllString's $N templating instead, as above).
	countRe := regexp.MustCompile(`\d+`)
	total := 0
	countRe.ReplaceAllStringFunc("3 apples, 5 oranges, 2 pears", func(match string) string {
		total++ // side effect just to prove the func runs once per match
		return match
	})
	if total != 3 {
		panic(fmt.Sprintf("ReplaceAllStringFunc ran %d times, want 3", total))
	}

	// No match: the string comes back completely unchanged.
	unchanged := dateRe.ReplaceAllString("no dates here", "REDACTED")
	if unchanged != "no dates here" {
		panic(fmt.Sprintf("ReplaceAllString on non-matching text = %q, want unchanged", unchanged))
	}

	fmt.Printf("reformatted dates: %q\n", out)
	fmt.Printf("shouted levels:    %q\n", shouted)
	fmt.Println("OK")
}
