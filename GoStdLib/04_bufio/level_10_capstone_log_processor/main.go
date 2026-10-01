/*
LEVEL 10 (advanced) - capstone: a small log-line processor

You will learn
  - putting it together: Scanner reading with a resized buffer (level 4),
    Reader-style delimiter parsing, a Writer that must be Flushed (level 7),
    and copying Bytes() before storing them (level 9) - all in one program

Run: go run ./GoStdLib/04_bufio/level_10_capstone_log_processor
*/

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// processLog reads "LEVEL:message" lines from src, writes only ERROR lines
// (with their length) to dst, and returns a level -> count summary. Lines
// are copied out of the scanner's buffer before being stored, since Bytes()
// aliases the scanner's internal buffer (level 9's lesson).
func processLog(srcPath, dstPath string) (counts map[string]int, err error) {
	src, err := os.Open(srcPath)
	if err != nil {
		return nil, err
	}
	defer src.Close()

	dst, err := os.Create(dstPath)
	if err != nil {
		return nil, err
	}
	defer dst.Close()

	scanner := bufio.NewScanner(src)
	scanner.Buffer(make([]byte, 0, 4096), 1<<20) // allow lines up to 1MiB, not just the 64KB default

	writer := bufio.NewWriter(dst)
	defer writer.Flush() // must run so the last buffered lines aren't lost

	counts = map[string]int{}
	for scanner.Scan() {
		raw := scanner.Bytes()
		line := make([]byte, len(raw))
		copy(line, raw) // own the bytes before the next Scan() reuses the buffer

		level, msg, ok := strings.Cut(string(line), ":")
		if !ok {
			continue
		}
		counts[level]++

		if level == "ERROR" {
			if _, err := fmt.Fprintf(writer, "%s (len=%s)\n", msg, strconv.Itoa(len(msg))); err != nil {
				return counts, err
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return counts, err
	}
	return counts, writer.Flush()
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-bufio-10-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	srcPath := filepath.Join(dir, "app.log")
	dstPath := filepath.Join(dir, "errors.log")

	longLine := "ERROR:" + strings.Repeat("x", 70_000) // longer than the 64KB default limit
	input := strings.Join([]string{
		"INFO:starting up",
		"ERROR:disk full",
		"INFO:ready",
		longLine,
		"ERROR:timeout",
	}, "\n") + "\n"

	if err := os.WriteFile(srcPath, []byte(input), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	counts, err := processLog(srcPath, dstPath)
	if err != nil {
		panic(fmt.Sprintf("processLog failed: %v", err))
	}

	if counts["INFO"] != 2 {
		panic(fmt.Sprintf("INFO count = %d, expected 2", counts["INFO"]))
	}
	if counts["ERROR"] != 3 {
		panic(fmt.Sprintf("ERROR count = %d, expected 3", counts["ERROR"]))
	}

	out, err := os.ReadFile(dstPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	outLines := strings.Split(strings.TrimRight(string(out), "\n"), "\n")
	if len(outLines) != 3 {
		panic(fmt.Sprintf("expected 3 ERROR lines in output, got %d: %v", len(outLines), outLines))
	}
	if outLines[0] != "disk full (len=9)" {
		panic(fmt.Sprintf("outLines[0] = %q, expected %q", outLines[0], "disk full (len=9)"))
	}
	if outLines[2] != "timeout (len=7)" {
		panic(fmt.Sprintf("outLines[2] = %q, expected %q", outLines[2], "timeout (len=7)"))
	}
	if !strings.HasPrefix(outLines[1], "xxxx") || !strings.HasSuffix(outLines[1], "(len=70000)") {
		panic(fmt.Sprintf("outLines[1] did not match the 70000-byte error line summary: %q...(truncated)", outLines[1][:30]))
	}

	fmt.Printf("level counts: %v\n", counts)
	fmt.Printf("wrote %d ERROR summaries to %s\n", len(outLines), filepath.Base(dstPath))
	fmt.Println("OK")
}
