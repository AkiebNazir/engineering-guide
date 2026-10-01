// Package config is the reference implementation of Problem 08: a layered
// config loader (embedded defaults < override file < environment
// variables) with single-pass, complete validation. Read the header
// comment in ../explanation/08_config_loader_explanation.go first for the
// full spec and rationale.
package config

import (
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"
)

//go:embed defaults.json
var embeddedDefaults embed.FS

// DefaultsFS exposes this package's compiled-in baseline defaults so
// callers (and tests) can pass it to NewLoader without needing their own
// embed directive. Real services typically embed their OWN defaults.json
// next to their main package instead of reusing this one — this export
// exists purely so this package is self-contained and testable.
var DefaultsFS = embeddedDefaults

// Config is the fully-resolved configuration a service runs with.
type Config struct {
	ServerAddr   string        `json:"server_addr" env:"SERVER_ADDR"`
	ReadTimeout  time.Duration `json:"read_timeout" env:"READ_TIMEOUT"`
	WriteTimeout time.Duration `json:"write_timeout" env:"WRITE_TIMEOUT"`
	MaxConns     int           `json:"max_conns" env:"MAX_CONNS"`
	LogLevel     string        `json:"log_level" env:"LOG_LEVEL"`
	DatabaseDSN  string        `json:"database_dsn" env:"DATABASE_DSN"`
}

// jsonShadow mirrors Config but with Duration fields as strings, since
// time.Duration's default JSON encoding is a raw int64 nanosecond count,
// not the friendly "30s" form. We decode into this shape and convert,
// rather than giving Config itself an UnmarshalJSON, so json.Marshal(cfg)
// (e.g. for debug-dumping a Config) still round-trips durations as plain
// numbers if a caller ever wants that — the friendly string form is a
// config-*authoring* convenience, not a wire format decision this package
// needs to also own for the in-memory type.
type jsonShadow struct {
	ServerAddr   *string `json:"server_addr"`
	ReadTimeout  *string `json:"read_timeout"`
	WriteTimeout *string `json:"write_timeout"`
	MaxConns     *int    `json:"max_conns"`
	LogLevel     *string `json:"log_level"`
	DatabaseDSN  *string `json:"database_dsn"`
}

// applyJSON unmarshals data as a jsonShadow and overlays only the fields
// that were actually present in the JSON onto cfg (in place).
//
// Step: every shadow field is a pointer. json.Unmarshal leaves a pointer
// field nil if and only if its key was absent from the input (as opposed
// to present-but-zero, e.g. `"max_conns": 0`, which DOES set the pointer to
// a non-nil *int pointing at 0). This is the actual mechanism that makes
// "fields absent from the file keep the previous layer's value" work
// correctly — unmarshaling directly onto Config's plain (non-pointer)
// fields would get the "absent key leaves the field untouched" part right
// too (encoding/json's normal behavior), but the shadow+pointer approach
// makes the distinction explicit and lets us tell "absent" apart from
// "explicitly set to the zero value" if a future rule needs that (e.g.
// "max_conns: 0" meaning "unlimited" vs "not configured").
func applyJSON(cfg *Config, data []byte) error {
	var shadow jsonShadow
	if err := json.Unmarshal(data, &shadow); err != nil {
		return fmt.Errorf("config: parse json: %w", err)
	}

	if shadow.ServerAddr != nil {
		cfg.ServerAddr = *shadow.ServerAddr
	}
	if shadow.ReadTimeout != nil {
		d, err := time.ParseDuration(*shadow.ReadTimeout)
		if err != nil {
			return fmt.Errorf("config: read_timeout: %w", err)
		}
		cfg.ReadTimeout = d
	}
	if shadow.WriteTimeout != nil {
		d, err := time.ParseDuration(*shadow.WriteTimeout)
		if err != nil {
			return fmt.Errorf("config: write_timeout: %w", err)
		}
		cfg.WriteTimeout = d
	}
	if shadow.MaxConns != nil {
		cfg.MaxConns = *shadow.MaxConns
	}
	if shadow.LogLevel != nil {
		cfg.LogLevel = *shadow.LogLevel
	}
	if shadow.DatabaseDSN != nil {
		cfg.DatabaseDSN = *shadow.DatabaseDSN
	}
	return nil
}

// Loader resolves a Config from embedded defaults, an optional override
// file, and environment variables, in that ascending priority order.
type Loader struct {
	defaults embed.FS
	// environ returns the current environment as "KEY=VALUE" pairs, mirroring
	// os.Environ's signature. Injected (rather than calling os.Environ
	// directly in Load) so tests can supply a fixed, independent environment
	// per subtest instead of mutating real process-global env vars via
	// os.Setenv, which is unsafe to do from parallel tests.
	environ func() []string
}

// NewLoader returns a Loader whose defaults layer comes from defaults,
// which must contain a "defaults.json" entry.
func NewLoader(defaults embed.FS) *Loader {
	return &Loader{defaults: defaults, environ: os.Environ}
}

// lookupEnv turns Loader.environ()'s []string ("KEY=VALUE") into a map once
// per Load call — O(n) to build, O(1) per lookup, versus re-scanning the
// slice for each of Config's six env-tagged fields.
func lookupEnv(pairs []string) map[string]string {
	m := make(map[string]string, len(pairs))
	for _, kv := range pairs {
		for i := 0; i < len(kv); i++ {
			if kv[i] == '=' {
				m[kv[:i]] = kv[i+1:]
				break
			}
		}
	}
	return m
}

// Load resolves the final Config: embedded defaults.json, overlaid by
// filePath's JSON if filePath != "", overlaid by environment variables.
// Returns every env-parsing and validation problem joined together via
// errors.Join, or a valid Config and nil.
func (l *Loader) Load(filePath string) (Config, error) {
	// Step 1: defaults layer. A malformed embedded defaults.json is a
	// build-time programmer error, not a runtime condition callers should
	// have to handle gracefully — we still return it rather than panic,
	// but the accompanying test suite treats this path as "should never
	// happen in CI" and fails loudly if it ever does.
	defaultsData, err := l.defaults.ReadFile("defaults.json")
	if err != nil {
		return Config{}, fmt.Errorf("config: read embedded defaults.json: %w", err)
	}
	var cfg Config
	if err := applyJSON(&cfg, defaultsData); err != nil {
		return Config{}, fmt.Errorf("config: embedded defaults.json is invalid: %w", err)
	}

	// Step 2: optional override file layer. filePath == "" is a valid "no
	// override" signal; filePath naming a file that doesn't exist is an
	// error — an operator who names a config file expects it to be read,
	// and silently falling back to defaults on a typo'd path is exactly
	// the kind of surprise that turns into a production incident.
	if filePath != "" {
		fileData, err := os.ReadFile(filePath)
		if err != nil {
			return Config{}, fmt.Errorf("config: read override file %q: %w", filePath, err)
		}
		// Crucially: applyJSON mutates the ALREADY-POPULATED cfg from
		// step 1, not a fresh zero-value Config. This is what makes
		// "keys absent from the override file keep the default" work —
		// unmarshaling onto a fresh Config here would silently zero out
		// every field the file doesn't mention.
		if err := applyJSON(&cfg, fileData); err != nil {
			return Config{}, fmt.Errorf("config: override file %q: %w", filePath, err)
		}
	}

	// Step 3: environment layer. We accumulate every field-parsing error
	// instead of returning on the first (MAX_CONNS=abc and
	// READ_TIMEOUT=abc set at once should both be reported in one error,
	// not force two separate deploy-and-retry cycles).
	env := lookupEnv(l.environ())
	var envErrs []error

	if v, ok := env["SERVER_ADDR"]; ok {
		cfg.ServerAddr = v
	}
	if v, ok := env["READ_TIMEOUT"]; ok {
		d, err := time.ParseDuration(v)
		if err != nil {
			envErrs = append(envErrs, fmt.Errorf("config: env READ_TIMEOUT=%q: %w", v, err))
		} else {
			cfg.ReadTimeout = d
		}
	}
	if v, ok := env["WRITE_TIMEOUT"]; ok {
		d, err := time.ParseDuration(v)
		if err != nil {
			envErrs = append(envErrs, fmt.Errorf("config: env WRITE_TIMEOUT=%q: %w", v, err))
		} else {
			cfg.WriteTimeout = d
		}
	}
	if v, ok := env["MAX_CONNS"]; ok {
		n, err := strconv.Atoi(v)
		if err != nil {
			envErrs = append(envErrs, fmt.Errorf("config: env MAX_CONNS=%q: %w", v, err))
		} else {
			cfg.MaxConns = n
		}
	}
	if v, ok := env["LOG_LEVEL"]; ok {
		cfg.LogLevel = v
	}
	if v, ok := env["DATABASE_DSN"]; ok {
		cfg.DatabaseDSN = v
	}

	// Step 4: validate the fully-merged config, joining any validation
	// failures onto the env-parsing failures so a caller sees the
	// complete picture (bad env values AND bad final values) in one shot.
	if err := cfg.Validate(); err != nil {
		envErrs = append(envErrs, err)
	}

	// errors.Join returns nil if every element is nil / the slice is
	// empty, so no special-casing "clean load" is needed here.
	return cfg, errors.Join(envErrs...)
}

// Validate reports every problem with c at once, rather than failing fast
// on the first bad field — an operator fixing a broken config wants the
// complete list in one deploy-and-check cycle, not a discover-one-error-
// per-restart loop.
func (c Config) Validate() error {
	var violations []error

	if c.ServerAddr == "" {
		violations = append(violations, ErrMissingServerAddr)
	}
	if c.ReadTimeout <= 0 || c.WriteTimeout <= 0 {
		violations = append(violations, ErrInvalidTimeout)
	}
	if c.MaxConns <= 0 {
		violations = append(violations, ErrInvalidMaxConns)
	}
	switch c.LogLevel {
	case "debug", "info", "warn", "error":
	default:
		violations = append(violations, fmt.Errorf("%w: got %q", ErrInvalidLogLevel, c.LogLevel))
	}
	if c.DatabaseDSN == "" {
		violations = append(violations, ErrMissingDSN)
	}

	return errors.Join(violations...)
}

// Sentinel validation errors, so callers can errors.Is against a specific
// known problem (e.g. to decide whether a missing DSN should trigger a
// different remediation path than a bad log level).
var (
	ErrMissingServerAddr = errors.New("config: server_addr is required")
	ErrInvalidTimeout    = errors.New("config: read/write timeout must be positive")
	ErrInvalidMaxConns   = errors.New("config: max_conns must be positive")
	ErrInvalidLogLevel   = errors.New("config: log_level must be one of debug/info/warn/error")
	ErrMissingDSN        = errors.New("config: database_dsn is required")
)

/*
BEST PRACTICES DEMONSTRATED
  - Layering is implemented by mutating one Config value across three
    passes (defaults -> file -> env), never by unmarshaling onto a fresh
    zero-value struct after the first layer — this is the entire mechanism
    that makes "absent overrides don't zero out earlier layers" correct.
  - A shadow struct with pointer fields makes "JSON key absent" and "JSON
    key present with the zero value" distinguishable, which matters the
    moment a future field needs `0`/`""` to be a meaningful explicit
    override rather than indistinguishable from "not set".
  - The environment reader is injected (func() []string) rather than
    called directly via os.Environ, making Load's environment dependency
    explicit and the function testable without mutating real process state.
  - Every layer's errors are accumulated (errors.Join), not fail-fast —
    Validate and the env-parsing pass both report every problem found, not
    just the first.
  - Sentinel errors for each validation rule support errors.Is for callers
    that need to branch on a specific failure, while the human-readable
    joined error remains directly loggable as-is.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - reflect-based field walking keyed off the `env:"…"` struct tags
    (what envconfig/viper-style libraries do): scales to structs with
    dozens of fields without hand-writing a branch per field, at the cost
    of the code being harder to step through in a debugger and losing
    compile-time checking that every tag corresponds to a real field. For
    Config's six fields, the explicit switch used here is more readable
    and just as correct; the trade-off point is roughly "a dozen or more
    fields, or a family of similar config structs" in favor of reflection.
  - Config implementing json.Unmarshaler directly instead of a separate
    jsonShadow type: fewer types, but couples Config's *external* JSON
    representation (durations as "30s" strings) to its Go definition
    permanently — a caller who wants to json.Marshal(cfg) for structured
    logging or a debug endpoint would unexpectedly get string durations
    too, which may or may not be desired. Keeping the shadow separate
    keeps that decision local to config *loading*.
  - A fourth CLI-flags layer (stretch goal) would slot in as one more
    "overlay onto the already-populated cfg" pass, using the same pattern
    established here — the design generalizes cleanly to more layers.

TESTING NOTES
  - Tests inject a fixed environ func per subtest instead of os.Setenv,
    which is what makes t.Parallel() safe here — no shared process-global
    mutable state between subtests.
  - The precedence test sets all three layers to different values for the
    same field (e.g. read_timeout) and asserts the env value wins, then
    removes the env override and asserts the file value wins, then removes
    the file override and asserts the default wins — this is the only way
    to actually prove precedence rather than just "the loader produces
    *a* value".
  - Malformed env value tests assert both that Load returns a non-nil
    error AND that errors.Is / strings.Contains finds the specific
    complaint (MAX_CONNS) in the joined message, not just "an error
    happened somewhere".

FAILURE MODES TO KNOW ABOUT
  - An embedded defaults.json that fails to parse is treated as fatal
    (returns an error rather than panicking) but should be caught by CI
    long before it ships — a test in this package's suite loads
    DefaultsFS directly and fails the build if it's ever invalid.
  - A `MAX_CONNS` env var set to a very large value that overflows int on
    32-bit platforms would come back as a strconv.ErrRange from
    strconv.Atoi and be reported like any other malformed value — not a
    silent wraparound.
  - Concurrent Load calls sharing one *Loader are safe (Load has no
    mutable state on Loader itself beyond the injected environ func, which
    is expected to be side-effect-free) but concurrent MUTATION of the
    real environment (os.Setenv) while os.Environ-backed Loaders are
    Load()-ing concurrently is a pre-existing hazard of process
    environment variables in Go generally, unrelated to this package.
*/
