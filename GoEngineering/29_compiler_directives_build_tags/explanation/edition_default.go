//go:build !premium

package directives

// Compiled by default. `go build -tags premium` swaps this file out for
// edition_premium.go — exactly one of the pair is ever compiled, so they can
// declare the same identifiers.
const edition = "community"

func premiumFeatures() []string { return nil }
