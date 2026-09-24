/*
LEVEL 10 (capstone) - an atomic config writer, using most of levels 1-9 together

You will learn
  - combining MkdirAll, WriteFile, Stat, Rename and errors.Is into one small,
    realistic utility: a function that publishes a config file without ever
    leaving a half-written file at the real path if the process crashes mid-write
  - Getenv driving behaviour, os.TempDir for scratch space, and Getwd/Chdir left
    untouched by a well-behaved library function (it should never change the
    caller's working directory)

Run: go run ./GoStdLib/01_os/level_10_capstone_atomic_write
*/

package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

// writeAtomic publishes data at path without ever exposing a partially
// written file: write to a sibling temp file first, then Rename it into
// place. Rename within the same directory is atomic on the same filesystem,
// so readers always see either the fully-old or fully-new content.
func writeAtomic(path string, data []byte, perm os.FileMode) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("writeAtomic: ensure dir: %w", err)
	}

	tmp, err := os.CreateTemp(dir, ".tmp-*")
	if err != nil {
		return fmt.Errorf("writeAtomic: create temp: %w", err)
	}
	tmpPath := tmp.Name()

	// If anything below fails, clean up the temp file rather than littering it.
	success := false
	defer func() {
		if !success {
			os.Remove(tmpPath)
		}
	}()

	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return fmt.Errorf("writeAtomic: write temp: %w", err)
	}
	if err := tmp.Close(); err != nil {
		return fmt.Errorf("writeAtomic: close temp: %w", err)
	}
	if err := os.Chmod(tmpPath, perm); err != nil {
		return fmt.Errorf("writeAtomic: chmod temp: %w", err)
	}
	if err := os.Rename(tmpPath, path); err != nil {
		return fmt.Errorf("writeAtomic: rename into place: %w", err)
	}

	success = true
	return nil
}

func main() {
	root, err := os.MkdirTemp(os.TempDir(), "gostdlib-os-10-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(root)

	startWD, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd failed: %v", err))
	}

	// Env var decides the config subpath, the way a real service might.
	os.Setenv("GOSTDLIB_CAPSTONE_SUBDIR", "config/app")
	defer os.Unsetenv("GOSTDLIB_CAPSTONE_SUBDIR")
	subdir := os.Getenv("GOSTDLIB_CAPSTONE_SUBDIR")

	configPath := filepath.Join(root, subdir, "settings.json")

	// The target directory does not exist yet - writeAtomic must create it.
	if _, err := os.Stat(filepath.Dir(configPath)); !errors.Is(err, fs.ErrNotExist) {
		panic(fmt.Sprintf("expected config dir to not exist yet, Stat err=%v", err))
	}

	if err := writeAtomic(configPath, []byte(`{"version":1}`), 0644); err != nil {
		panic(fmt.Sprintf("first writeAtomic failed: %v", err))
	}
	v1, err := os.ReadFile(configPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile after first write failed: %v", err))
	}
	if string(v1) != `{"version":1}` {
		panic(fmt.Sprintf("unexpected content after first write: %q", v1))
	}

	// No leftover temp files after a successful publish.
	entries, err := os.ReadDir(filepath.Dir(configPath))
	if err != nil {
		panic(fmt.Sprintf("ReadDir failed: %v", err))
	}
	if len(entries) != 1 {
		panic(fmt.Sprintf("expected exactly 1 file (no temp leftovers), found %d", len(entries)))
	}

	// Publish a new version; readers only ever see complete content.
	if err := writeAtomic(configPath, []byte(`{"version":2}`), 0644); err != nil {
		panic(fmt.Sprintf("second writeAtomic failed: %v", err))
	}
	v2, err := os.ReadFile(configPath)
	if err != nil {
		panic(fmt.Sprintf("ReadFile after second write failed: %v", err))
	}
	if string(v2) != `{"version":2}` {
		panic(fmt.Sprintf("unexpected content after second write: %q", v2))
	}

	info, err := os.Stat(configPath)
	if err != nil {
		panic(fmt.Sprintf("Stat failed: %v", err))
	}
	if info.Mode().Perm()&0400 == 0 {
		panic("expected the published file to at least be owner-readable")
	}

	// A well-behaved library function must not change the caller's working directory.
	endWD, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd failed: %v", err))
	}
	if endWD != startWD {
		panic(fmt.Sprintf("working directory changed unexpectedly: started %q, ended %q", startWD, endWD))
	}

	fmt.Printf("published v1 then v2 atomically at %s, final content: %s\n", configPath, v2)
	fmt.Println("OK")
}
