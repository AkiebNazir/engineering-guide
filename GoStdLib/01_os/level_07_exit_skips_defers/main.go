/*
LEVEL 07 (advanced) - os.Exit skips deferred functions, for real

You will learn
  - os.Exit terminates the process immediately - no deferred function runs
  - a normal return from main() DOES run every pending defer first
  - the only reliable way to show this is to actually run a child process both
    ways and check its side effects, since os.Exit inside THIS process would
    end the whole demo

Run: go run ./GoStdLib/01_os/level_07_exit_skips_defers
*/

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// childMain is what runs when this same binary is re-invoked with -child.
// It defers writing a "ran" marker file, then either os.Exit()s (skipping the
// defer) or returns normally (running the defer), depending on -mode.
func childMain(markerPath, mode string) {
	defer func() {
		// This defer is the whole experiment: does it get to run or not?
		_ = os.WriteFile(markerPath, []byte("defer ran\n"), 0644)
	}()

	if mode == "exit" {
		os.Exit(3)
	}
	// mode == "normal": fall off the end of childMain, main returns, defer runs.
}

func main() {
	// Re-exec ourselves as a child process so os.Exit in the child can't kill
	// this demo. This is the only faithful way to observe skipped defers.
	if len(os.Args) >= 4 && os.Args[1] == "-child" {
		childMain(os.Args[2], os.Args[3])
		return
	}

	self, err := os.Executable()
	if err != nil {
		panic(fmt.Sprintf("os.Executable failed: %v", err))
	}

	dir, err := os.MkdirTemp("", "gostdlib-os-07-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	runChild := func(mode string) (exitCode int, markerExists bool) {
		marker := filepath.Join(dir, "marker-"+mode+".txt")
		cmd := exec.Command(self, "-child", marker, mode)
		err := cmd.Run()
		code := 0
		if exitErr, ok := err.(*exec.ExitError); ok {
			code = exitErr.ExitCode()
		} else if err != nil {
			panic(fmt.Sprintf("failed to run child (mode=%s): %v", mode, err))
		}
		_, statErr := os.Stat(marker)
		return code, statErr == nil
	}

	exitCode, exitMarker := runChild("exit")
	normalCode, normalMarker := runChild("normal")

	// os.Exit(3): process ends with code 3, and the defer never had a chance to run.
	if exitCode != 3 {
		panic(fmt.Sprintf("expected exit code 3 from os.Exit(3), got %d", exitCode))
	}
	if exitMarker {
		panic("BUG: the deferred write ran even though os.Exit was called - defer should have been skipped")
	}

	// Normal return: process ends with code 0, and the defer ran.
	if normalCode != 0 {
		panic(fmt.Sprintf("expected exit code 0 from a normal return, got %d", normalCode))
	}
	if !normalMarker {
		panic("expected the deferred write to have run on a normal return, but marker file is missing")
	}

	fmt.Println("child that called os.Exit(3): exit code 3, deferred marker file NOT written")
	fmt.Println("child that returned normally: exit code 0, deferred marker file WAS written")
	fmt.Println("OK")
}
