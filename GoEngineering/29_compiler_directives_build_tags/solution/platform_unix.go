//go:build unix

package directives

// platformName is chosen at compile time. This file is only compiled when
// GOOS is Unix-like (linux, darwin, freebsd, ...). The `unix` constraint
// exists since Go 1.19.
func platformName() string { return "unix" }
