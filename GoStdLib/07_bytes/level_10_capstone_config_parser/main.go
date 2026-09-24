/*
LEVEL 10 (capstone) - a small config parser using most of levels 1-9 together

You will learn
  - how Split, Cut, TrimSpace, HasPrefix, Buffer, NewReader and io.Copy combine
    into one realistic small program: parse config text, validate it, and
    re-serialize it in canonical form

Run: go run ./GoStdLib/07_bytes/level_10_capstone_config_parser
*/

package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"sort"
)

var errMissingRequired = errors.New("config: missing required key")

// parseConfig parses "key = value" lines, skipping blanks and "#" comments.
func parseConfig(src []byte) (map[string]string, error) {
	cfg := make(map[string]string)
	for _, line := range bytes.Split(src, []byte("\n")) {
		line = bytes.TrimSpace(line)
		if len(line) == 0 || bytes.HasPrefix(line, []byte("#")) {
			continue
		}
		key, value, found := bytes.Cut(line, []byte("="))
		if !found {
			return nil, fmt.Errorf("config: malformed line %q (no '=')", line)
		}
		cfg[string(bytes.TrimSpace(key))] = string(bytes.TrimSpace(value))
	}
	return cfg, nil
}

// requireKeys returns errMissingRequired (wrapped with the key name) for the
// first required key that is absent.
func requireKeys(cfg map[string]string, keys ...string) error {
	for _, k := range keys {
		if _, ok := cfg[k]; !ok {
			return fmt.Errorf("%w: %s", errMissingRequired, k)
		}
	}
	return nil
}

// render writes cfg back out in canonical (sorted-key) "key = value" form.
func render(cfg map[string]string) []byte {
	keys := make([]string, 0, len(cfg))
	for k := range cfg {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var buf bytes.Buffer
	for _, k := range keys {
		fmt.Fprintf(&buf, "%s = %s\n", k, cfg[k])
	}
	return buf.Bytes()
}

func main() {
	input := []byte("# app config\nhost = localhost\n\nport=8080\ndebug = false\n")

	cfg, err := parseConfig(input)
	if err != nil {
		panic(fmt.Sprintf("parseConfig failed: %v", err))
	}
	if len(cfg) != 3 {
		panic(fmt.Sprintf("parsed %d keys, want 3: %+v", len(cfg), cfg))
	}

	if err := requireKeys(cfg, "host", "port"); err != nil {
		panic(fmt.Sprintf("requireKeys(host, port) failed unexpectedly: %v", err))
	}

	// Trigger the real missing-key error and confirm it is checkable via errors.Is.
	err = requireKeys(cfg, "host", "tls_cert")
	if !errors.Is(err, errMissingRequired) {
		panic(fmt.Sprintf("expected errMissingRequired for tls_cert, got %v", err))
	}
	fmt.Printf("validation caught missing key as expected: %v\n", err)

	canonical := render(cfg)
	wantCanonical := "debug = false\nhost = localhost\nport = 8080\n"
	if !bytes.Equal(canonical, []byte(wantCanonical)) {
		panic(fmt.Sprintf("render() = %q, want %q", canonical, wantCanonical))
	}

	// Round-trip the canonical bytes through a Reader -> io.Copy -> Buffer pipe,
	// the same interop pattern from level 8, to prove it survives unchanged.
	var roundTripped bytes.Buffer
	if _, err := io.Copy(&roundTripped, bytes.NewReader(canonical)); err != nil {
		panic(fmt.Sprintf("io.Copy round trip failed: %v", err))
	}
	if !bytes.Equal(roundTripped.Bytes(), canonical) {
		panic(fmt.Sprintf("round trip = %q, want %q", roundTripped.Bytes(), canonical))
	}

	fmt.Print(string(canonical))
	fmt.Println("OK")
}
