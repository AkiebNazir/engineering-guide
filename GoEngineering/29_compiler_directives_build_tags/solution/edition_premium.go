//go:build premium

package directives

// Compiled only with `-tags premium`.
const edition = "premium"

func premiumFeatures() []string { return []string{"sso", "audit-log"} }
