/*
LEVEL 03 (core) - Getwd/Chdir, os.Args, and Getenv/LookupEnv/Setenv

You will learn
  - os.Args[0] is the program path; os.Args[1:] are the real arguments
  - os.Getwd reports the process's current directory; os.Chdir changes it
  - os.Setenv/os.Getenv/os.LookupEnv: LookupEnv distinguishes "unset" from "set to empty"
  - environment changes here are per-process, not visible to the parent shell

Run: go run ./GoStdLib/01_os/level_03_working_dir_and_env
*/

package main

import (
	"fmt"
	"os"
)

func main() {
	// os.Args always has at least one element: the binary's own path.
	if len(os.Args) < 1 {
		panic("os.Args unexpectedly empty")
	}
	fmt.Printf("program invoked as: %s (argc=%d)\n", os.Args[0], len(os.Args))

	// Getwd / Chdir: move around and come back.
	start, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd failed: %v", err))
	}

	dir, err := os.MkdirTemp("", "gostdlib-os-03-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	if err := os.Chdir(dir); err != nil {
		panic(fmt.Sprintf("Chdir failed: %v", err))
	}
	here, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd after Chdir failed: %v", err))
	}
	if here == start {
		panic("Chdir had no effect: still in the original directory")
	}

	if err := os.Chdir(start); err != nil {
		panic(fmt.Sprintf("Chdir back failed: %v", err))
	}
	back, err := os.Getwd()
	if err != nil {
		panic(fmt.Sprintf("Getwd after returning failed: %v", err))
	}
	if back != start {
		panic(fmt.Sprintf("failed to return to start dir: got %q, want %q", back, start))
	}

	// LookupEnv distinguishes "not set" from "set to empty string" - Getenv cannot.
	const key = "GOSTDLIB_LEVEL03_VAR"
	os.Unsetenv(key)
	if _, ok := os.LookupEnv(key); ok {
		panic("expected variable to be unset before Setenv")
	}
	if v := os.Getenv(key); v != "" {
		panic(fmt.Sprintf("Getenv on unset var should return \"\", got %q", v))
	}

	if err := os.Setenv(key, ""); err != nil {
		panic(fmt.Sprintf("Setenv failed: %v", err))
	}
	v, ok := os.LookupEnv(key)
	if !ok {
		panic("LookupEnv reports unset right after Setenv to empty string")
	}
	if v != "" {
		panic(fmt.Sprintf("expected empty value, got %q", v))
	}
	// This is the whole point of LookupEnv: Getenv("") and Getenv(unset) look identical,
	// but LookupEnv's second return value tells them apart.

	if err := os.Setenv(key, "hello"); err != nil {
		panic(fmt.Sprintf("Setenv failed: %v", err))
	}
	if got := os.Getenv(key); got != "hello" {
		panic(fmt.Sprintf("Getenv mismatch: got %q, want %q", got, "hello"))
	}
	os.Unsetenv(key)

	fmt.Printf("wd round trip ok, env var was set(empty)=%v then updated ok\n", ok)
	fmt.Println("OK")
}
