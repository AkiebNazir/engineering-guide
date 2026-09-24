/*
LEVEL 10 (advanced) - capstone: a small config-line parser

You will learn
  - putting it together: Atoi/ParseFloat/ParseBool with real *strconv.NumError
    handling, Quote for safe display of raw values, FormatInt with a base,
    and AppendInt building a summary buffer - the same shapes as levels 1-9

Run: go run ./GoStdLib/06_strconv/level_10_capstone_config
*/

package main

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
)

// config holds the typed values parsed out of "key=value" lines.
type config struct {
	maxRetries int
	timeoutSec float64
	debug      bool
}

// parseConfig parses lines like "max_retries=5", reporting every bad line
// instead of stopping at the first one.
func parseConfig(lines []string) (cfg config, badLines []string) {
	for _, line := range lines {
		key, val, ok := strings.Cut(line, "=")
		if !ok {
			badLines = append(badLines, strconv.Quote(line))
			continue
		}
		var err error
		switch key {
		case "max_retries":
			var n int
			if n, err = strconv.Atoi(val); err == nil {
				cfg.maxRetries = n
			}
		case "timeout_sec":
			var f float64
			if f, err = strconv.ParseFloat(val, 64); err == nil {
				cfg.timeoutSec = f
			}
		case "debug":
			var d bool
			if d, err = strconv.ParseBool(val); err == nil {
				cfg.debug = d
			}
		default:
			err = fmt.Errorf("unknown key %q", key)
		}
		if err != nil {
			var numErr *strconv.NumError
			if errors.As(err, &numErr) {
				badLines = append(badLines, fmt.Sprintf("%s (bad %s value %s)", strconv.Quote(line), key, strconv.Quote(numErr.Num)))
			} else {
				badLines = append(badLines, strconv.Quote(line))
			}
		}
	}
	return cfg, badLines
}

// summarize builds "retries=<hex> timeout=<f> debug=<b>" using AppendInt with
// base 16 for the retry count, straight into a growing []byte.
func summarize(cfg config) string {
	buf := []byte("retries=0x")
	buf = strconv.AppendInt(buf, int64(cfg.maxRetries), 16)
	buf = append(buf, " timeout="...)
	buf = strconv.AppendFloat(buf, cfg.timeoutSec, 'f', 1, 64)
	buf = append(buf, " debug="...)
	buf = strconv.AppendBool(buf, cfg.debug)
	return string(buf)
}

func main() {
	lines := []string{
		"max_retries=5",
		"timeout_sec=2.5",
		"debug=true",
		"no-equals-sign",
		"max_retries=not-a-number",
		"unknown_key=123",
	}

	cfg, bad := parseConfig(lines)

	if cfg.maxRetries != 5 {
		panic(fmt.Sprintf("maxRetries = %d, expected 5", cfg.maxRetries))
	}
	if cfg.timeoutSec != 2.5 {
		panic(fmt.Sprintf("timeoutSec = %v, expected 2.5", cfg.timeoutSec))
	}
	if !cfg.debug {
		panic("debug should be true")
	}
	if len(bad) != 3 {
		panic(fmt.Sprintf("expected 3 bad lines, got %d: %v", len(bad), bad))
	}
	if !strings.Contains(bad[1], "bad max_retries value") {
		panic(fmt.Sprintf("expected the second bad line to mention max_retries, got %q", bad[1]))
	}

	summary := summarize(cfg)
	if summary != "retries=0x5 timeout=2.5 debug=true" {
		panic(fmt.Sprintf("summary = %q, expected %q", summary, "retries=0x5 timeout=2.5 debug=true"))
	}

	fmt.Println(summary)
	fmt.Printf("rejected %d malformed lines: %v\n", len(bad), bad)
	fmt.Println("OK")
}
