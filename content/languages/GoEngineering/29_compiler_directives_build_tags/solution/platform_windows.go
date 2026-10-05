package directives

// No //go:build line needed: the _windows.go filename suffix is itself an
// implicit build constraint (GOOS=windows). Same for _linux.go, _arm64.go,
// _linux_arm64.go, etc.
func platformName() string { return "windows" }
