/*
LEVEL 08 (advanced) - interop: encoding/json + os.ReadFile/os.WriteFile

You will learn
  - a realistic config-file round trip: marshal a struct with json.MarshalIndent
    for a human-readable file, write it with os.WriteFile, then read it back
    with os.ReadFile + json.Unmarshal
  - json.MarshalIndent for pretty-printed output vs the compact json.Marshal

Run: go run ./GoStdLib/09_encoding_json/level_08_interop_os_json_file
*/

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type ServerConfig struct {
	Host    string `json:"host"`
	Port    int    `json:"port"`
	Debug   bool   `json:"debug,omitempty"`
	Timeout int    `json:"timeout_seconds"`
}

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-json-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	cfg := ServerConfig{Host: "0.0.0.0", Port: 8443, Timeout: 30}

	pretty, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		panic(fmt.Sprintf("MarshalIndent failed: %v", err))
	}
	// MarshalIndent's output must actually contain real newlines and indentation,
	// unlike the compact form - verify both.
	compact, err := json.Marshal(cfg)
	if err != nil {
		panic(fmt.Sprintf("Marshal failed: %v", err))
	}
	if len(pretty) <= len(compact) {
		panic(fmt.Sprintf("expected indented output (%d bytes) to be longer than compact (%d bytes)", len(pretty), len(compact)))
	}

	path := filepath.Join(dir, "config.json")
	if err := os.WriteFile(path, pretty, 0644); err != nil {
		panic(fmt.Sprintf("WriteFile failed: %v", err))
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		panic(fmt.Sprintf("ReadFile failed: %v", err))
	}

	var loaded ServerConfig
	if err := json.Unmarshal(raw, &loaded); err != nil {
		panic(fmt.Sprintf("Unmarshal failed: %v", err))
	}
	if loaded != cfg {
		panic(fmt.Sprintf("loaded config = %+v, want %+v", loaded, cfg))
	}

	fmt.Printf("wrote %d bytes of pretty JSON to %s, read it back and matched\n", len(pretty), filepath.Base(path))
	fmt.Println("OK")
}
