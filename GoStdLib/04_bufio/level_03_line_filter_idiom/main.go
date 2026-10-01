/*
LEVEL 03 (core) - idiom: Scanner in, Writer out, filtering lines

You will learn
  - the everyday shape of a line-processing tool: bufio.Scanner reads,
    bufio.Writer writes, and Flush() runs before the file is closed
  - combining basics (Scan/Text + WriteString/Flush) into one small program

Run: go run ./GoStdLib/04_bufio/level_03_line_filter_idiom
*/

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// filterLines copies every line from src to dst that contains substr,
// prefixing surviving lines with their original line number.
func filterLines(srcPath, dstPath, substr string) (kept int, err error) {
	src, err := os.Open(srcPath)
	if err != nil {
		return 0, err
	}
	defer src.Close()

	dst, err := os.Create(dstPath)
	if err != nil {
		return 0, err
	}
	defer dst.Close()

	scanner := bufio.NewScanner(src)
	writer := bufio.NewWriter(dst)
	defer writer.Flush() // must run before dst.Close() completes the write

	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := scanner.Text()
		if strings.Contains(line, substr) {
			kept++
			if _, err := fmt.Fprintf(writer, "%d: %s\n", lineNo, line); err != nil {
				return kept, err
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return kept, err
	}
	return kept, writer.Flush()
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-bufio-03-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	srcPath := filepath.Join(dir, "input.log")
	dstPath := filepath.Join(dir, "output.log")

	input := "INFO starting up\nERROR disk full\nINFO ready\nERROR timeout\nINFO shutting down\n"
	if err := os.WriteFile(srcPath, []byte(input), 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	kept, err := filterLines(srcPath, dstPath, "ERROR")
	if err != nil {
		panic(fmt.Sprintf("filterLines failed: %v", err))
	}
	if kept != 2 {
		panic(fmt.Sprintf("kept = %d, expected 2", kept))
	}

	out, err := os.ReadFile(dstPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}
	expected := "2: ERROR disk full\n4: ERROR timeout\n"
	if string(out) != expected {
		panic(fmt.Sprintf("output = %q, expected %q", out, expected))
	}

	fmt.Printf("kept %d matching lines:\n%s", kept, out)
	fmt.Println("OK")
}
