//go:build !unix && !windows

package directives

// Fallback for everything else (js/wasm, wasip1, plan9). Without a fallback,
// building for those targets fails with "undefined: platformName".
func platformName() string { return "other" }
