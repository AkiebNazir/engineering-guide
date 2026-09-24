/*
LEVEL 08 (advanced) - interop: strconv + strings.Builder

You will learn
  - strings.Builder has WriteString but no numeric-append method of its own -
    pair it with strconv.Itoa/FormatFloat/Quote to build a formatted report
  - Builder.Write accepts the []byte strconv.AppendInt produces directly,
    no intermediate string needed

Run: go run ./GoStdLib/06_strconv/level_08_interop_builder
*/

package main

import (
	"fmt"
	"strconv"
	"strings"
)

type reading struct {
	sensor string
	value  float64
	ok     bool
}

// renderReport builds a CSV-like report using strings.Builder plus strconv,
// with no += concatenation and no fmt.Sprintf per field.
func renderReport(readings []reading) string {
	var b strings.Builder
	var numBuf []byte // reused scratch buffer for AppendInt/AppendFloat

	for i, r := range readings {
		if i > 0 {
			b.WriteByte('\n')
		}
		b.WriteString(strconv.Quote(r.sensor))
		b.WriteByte(',')

		numBuf = strconv.AppendFloat(numBuf[:0], r.value, 'f', 2, 64)
		b.Write(numBuf) // Builder.Write takes the []byte straight from strconv
		b.WriteByte(',')

		b.WriteString(strconv.FormatBool(r.ok))
	}
	return b.String()
}

func main() {
	readings := []reading{
		{sensor: "temp-1", value: 21.567, ok: true},
		{sensor: "temp-2", value: -3.2, ok: false},
	}

	report := renderReport(readings)
	expected := `"temp-1",21.57,true` + "\n" + `"temp-2",-3.20,false`
	if report != expected {
		panic(fmt.Sprintf("report =\n%q\nexpected\n%q", report, expected))
	}

	lines := strings.Split(report, "\n")
	if len(lines) != len(readings) {
		panic(fmt.Sprintf("got %d report lines, expected %d", len(lines), len(readings)))
	}

	fmt.Println(report)
	fmt.Println("OK")
}
