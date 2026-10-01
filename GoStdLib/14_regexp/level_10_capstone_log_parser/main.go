/*
LEVEL 10 (advanced) - capstone: a small log-line parser and redactor

You will learn
  - nothing new - this wires up levels 1-9 into one small realistic program:
    a fixed pattern compiled once at package scope (level 1/6), named
    groups read back via SubexpNames (level 3), a strings.Contains
    pre-filter before the regex (level 8), and ReplaceAllStringFunc to
    redact a field (level 5) - all driven over a small batch of log lines

Run: go run ./GoStdLib/14_regexp/level_10_capstone_log_parser
*/

package main

import (
	"fmt"
	"regexp"
	"strings"
)

// Compiled once at package scope - never inside the per-line loop below.
var logLineRe = regexp.MustCompile(
	`^(?P<level>[A-Z]+) user=(?P<user>\d+) msg="(?P<msg>[^"]*)"$`,
)

type parsedLine struct {
	level, user, msg string
}

// parseLine pre-filters on a cheap literal (every real log line here has an
// '=' sign) before running the regex, then reads groups back by name.
func parseLine(line string) (parsedLine, bool) {
	if !strings.Contains(line, "=") {
		return parsedLine{}, false
	}
	m := logLineRe.FindStringSubmatch(line)
	if m == nil {
		return parsedLine{}, false
	}
	var p parsedLine
	for i, name := range logLineRe.SubexpNames() {
		switch name {
		case "level":
			p.level = m[i]
		case "user":
			p.user = m[i]
		case "msg":
			p.msg = m[i]
		}
	}
	return p, true
}

// redactUserID is the level-5-style ReplaceAllStringFunc use: turn any
// user=<digits> into user=REDACTED, wherever it appears.
var userFieldRe = regexp.MustCompile(`user=\d+`)

func redactUserID(line string) string {
	return userFieldRe.ReplaceAllStringFunc(line, func(string) string {
		return "user=REDACTED"
	})
}

func main() {
	lines := []string{
		`ERROR user=42 msg="disk full"`,
		`INFO user=7 msg="request handled"`,
		`not a log line at all`,
		`ERROR user=99 msg="connection refused"`,
	}

	var parsed []parsedLine
	for _, line := range lines {
		p, ok := parseLine(line)
		if !ok {
			continue
		}
		parsed = append(parsed, p)
	}

	if len(parsed) != 3 {
		panic(fmt.Sprintf("parsed %d lines, want 3 (one line is not a log line)", len(parsed)))
	}
	if parsed[0].level != "ERROR" || parsed[0].user != "42" || parsed[0].msg != "disk full" {
		panic(fmt.Sprintf("parsed[0] = %+v, want {ERROR 42 disk full}", parsed[0]))
	}
	if parsed[1].level != "INFO" || parsed[1].user != "7" {
		panic(fmt.Sprintf("parsed[1] = %+v, want level=INFO user=7", parsed[1]))
	}

	errorCount := 0
	for _, p := range parsed {
		if p.level == "ERROR" {
			errorCount++
		}
	}
	if errorCount != 2 {
		panic(fmt.Sprintf("errorCount = %d, want 2", errorCount))
	}

	redacted := redactUserID(lines[0])
	wantRedacted := `ERROR user=REDACTED msg="disk full"`
	if redacted != wantRedacted {
		panic(fmt.Sprintf("redactUserID = %q, want %q", redacted, wantRedacted))
	}

	fmt.Printf("parsed %d real log lines, %d at ERROR level\n", len(parsed), errorCount)
	fmt.Printf("redacted sample: %s\n", redacted)
	fmt.Println("OK")
}
