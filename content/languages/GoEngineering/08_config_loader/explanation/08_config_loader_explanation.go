/*
Package config — Layered Config Loader (Problem 08)

WHAT WE'RE BUILDING

A config loader for a hypothetical service, with three layers applied in
increasing priority:

 1. Defaults embedded into the binary at compile time (embed.FS).
 2. A JSON config file on disk, if present, overriding the defaults.
 3. Environment variables, overriding both, for per-deployment secrets and
    ops-controlled tuning (timeouts, log level) without a redeploy.

Then everything is validated once, at the end, so callers get ONE clear error
listing everything wrong instead of failing on the first bad field, restarting,
failing on the second, and so on — a real operational annoyance in services
with many required settings.

# WHY IT MATTERS IN REAL SYSTEMS

Every non-trivial service needs configuration from more than one source: a
baseline that ships with the binary (so it runs with sane defaults out of the
box), an optional file for environment-specific overrides (staging vs prod
config, checked into a separate ops repo), and environment variables for the
handful of values that must never live in a file (API keys, DB passwords) or
that ops wants to flip without touching a file (LOG_LEVEL=debug for one
incident). Getting the *precedence* right and *validating once with a
complete error report* are the two things that separate a config loader that
survives a real on-call rotation from one that causes a 2am guessing game.

CONCEPTS COVERED
  - embed.FS for compiling a defaults file directly into the binary (no
    "make sure defaults.json ships next to the binary" deployment footgun)
  - Layered override: struct-level merge where a "present" field in a later
    layer wins, but an *absent* field in a later layer keeps the earlier
    layer's value — this needs pointer fields or an explicit "was this set"
    tracking mechanism, not plain zero-value structs (a zero-value bool
    false is indistinguishable from "not set" otherwise)
  - Environment variable parsing with type conversion and per-field error
    accumulation (strconv errors reported per-field, not the first one
    aborting the whole load)
  - Validation as a single pass returning errors.Join of every violation,
    not fail-fast on the first bad field
  - time.Duration parsing from both JSON (string form, "30s") and env
    (string form as well, but a different unmarshal path)

REQUIREMENTS / SPEC

	//go:embed defaults.json
	var defaultsFS embed.FS
	    The compiled-in baseline. Ships inside the binary; see the solution
	    file for the actual embed directive and JSON content.

	type Config struct {
	    ServerAddr   string        `json:"server_addr" env:"SERVER_ADDR"`
	    ReadTimeout  time.Duration `json:"read_timeout" env:"READ_TIMEOUT"`
	    WriteTimeout time.Duration `json:"write_timeout" env:"WRITE_TIMEOUT"`
	    MaxConns     int           `json:"max_conns" env:"MAX_CONNS"`
	    LogLevel     string        `json:"log_level" env:"LOG_LEVEL"`
	    DatabaseDSN  string        `json:"database_dsn" env:"DATABASE_DSN"`
	}
	    The fully-resolved config a service actually runs with. Durations are
	    JSON strings ("30s") that unmarshal via time.Duration's
	    UnmarshalJSON-compatible representation — actually time.Duration does
	    NOT implement json.Unmarshaler by default (it (un)marshals as a plain
	    int64 nanoseconds count), which is a very common gotcha; the solution
	    must handle "30s"-style strings explicitly.

	type Loader struct { ... }
	    Holds the embedded defaults FS and an environ-reading function (make
	    it injectable — func() []string — instead of calling os.Environ()
	    directly, so tests can supply a fixed environment without mutating
	    real process env vars, which is inherently racy across parallel
	    tests).

	func NewLoader(defaults embed.FS) *Loader
	func (l *Loader) Load(filePath string) (Config, error)
	    1. Parse the embedded defaults.json into a Config (always succeeds —
	       it's compiled in and should be a build-breaking test failure if
	       it's ever invalid JSON).
	    2. If filePath != "" and the file exists, parse it and overlay onto
	       the defaults (fields present in the file's JSON override; fields
	       absent keep the default). If filePath != "" and the file does NOT
	       exist, treat that as an error (a caller who names a file expects
	       it to be there) — but filePath == "" is a valid "no override file"
	       signal, not an error.
	    3. Overlay environment variables (using the injected environ
	       function): for each struct field with an `env:"NAME"` tag, if
	       NAME is set in the environment, parse it into the field's type
	       and overlay it. Collect (don't abort on) individual parse errors
	       (e.g. MAX_CONNS=notanumber) and return them all joined via
	       errors.Join at the end alongside any validation errors.
	    4. Validate the final merged Config (see Validate below). Return the
	       Config and a joined error containing every problem found across
	       env-parsing and validation, or (Config, nil) if everything's
	       clean.

	func (c Config) Validate() error
	    Returns errors.Join of every violation (not just the first):
	      - ServerAddr must be non-empty.
	      - ReadTimeout and WriteTimeout must be > 0.
	      - MaxConns must be > 0.
	      - LogLevel must be one of "debug", "info", "warn", "error".
	      - DatabaseDSN must be non-empty.

ACCEPTANCE CRITERIA
  - Precedence is exactly defaults < file < env, verified by a test that sets
    all three layers to different values for the same field and asserts env
    wins.
  - A field absent from the override file does NOT get zeroed out — it keeps
    the default (this is the part naive `json.Unmarshal(data, &cfg)` onto an
    already-populated struct actually gets right for missing keys, but ONLY
    if you unmarshal onto the existing Config rather than a fresh zero-value
    one — the solution must explain this explicitly).
  - filePath == "" loads cleanly from defaults+env only.
  - filePath naming a nonexistent file is an error.
  - Multiple validation failures at once are all present in the returned
    error (use errors.Join + errors.Is checks against sentinel errors in the
    test, or substring checks on the joined message).
  - Malformed env values (e.g. MAX_CONNS=abc) produce a clear, field-named
    error rather than a panic or a silently-ignored bad value.

Read the HINTS and PITFALLS at the bottom before opening the solution file.
*/
package config

import (
	"embed"
	"errors"
	"time"
)

// Config is the fully-resolved configuration a service runs with.
type Config struct {
	ServerAddr   string        `json:"server_addr" env:"SERVER_ADDR"`
	ReadTimeout  time.Duration `json:"read_timeout" env:"READ_TIMEOUT"`
	WriteTimeout time.Duration `json:"write_timeout" env:"WRITE_TIMEOUT"`
	MaxConns     int           `json:"max_conns" env:"MAX_CONNS"`
	LogLevel     string        `json:"log_level" env:"LOG_LEVEL"`
	DatabaseDSN  string        `json:"database_dsn" env:"DATABASE_DSN"`
}

// Loader resolves a Config from embedded defaults, an optional override
// file, and environment variables, in that ascending priority order.
type Loader struct {
	// TODO: hold the embedded defaults FS and an "environ" func() []string
	// (default os.Environ, but overridable for hermetic tests).
}

// NewLoader returns a Loader that reads its baseline defaults from
// defaults (expected to contain a "defaults.json" entry).
func NewLoader(defaults embed.FS) *Loader {
	// TODO: store defaults and default the environ func to os.Environ.
	panic("TODO: implement NewLoader")
}

// Load resolves the final Config: embedded defaults, overlaid by filePath's
// JSON if filePath != "", overlaid by environment variables tagged `env:"…"`
// on Config's fields. filePath == "" skips the file layer. Returns every
// env-parsing and validation problem joined together, or a valid Config and
// nil.
func (l *Loader) Load(filePath string) (Config, error) {
	// TODO:
	//  1. Read+unmarshal defaults.json from the embedded FS into a Config.
	//     This should never fail in a correctly-built binary; if it does,
	//     that's a programmer error worth a distinct wrapped message.
	//  2. If filePath != "": os.ReadFile it (missing file => error, do not
	//     silently ignore); json.Unmarshal ONTO the existing defaults
	//     Config value (not a fresh zero-value one!) so JSON keys absent
	//     from the file leave the corresponding fields untouched.
	//  3. Walk the Config's struct fields via reflection (or a manual
	//     switch, simpler and arguably clearer for six fields — your call,
	//     state which and why in the solution) looking for each field's
	//     `env:"NAME"` tag; if NAME is present in l.environ(), parse it
	//     into the field's type (special-case time.Duration via
	//     time.ParseDuration, everything else via strconv). Accumulate
	//     parse errors with errors.Join instead of returning on the first.
	//  4. Call cfg.Validate() and join any validation errors onto the
	//     env-parsing errors.
	//  5. Return (cfg, joinedErrOrNil).
	panic("TODO: implement Load")
}

// Validate reports every problem with c at once (via errors.Join), rather
// than failing fast on the first bad field.
func (c Config) Validate() error {
	// TODO: accumulate one error per violated rule (see spec above) into a
	// []error and return errors.Join(violations...) (errors.Join returns
	// nil for an empty/all-nil slice, so no special-casing "no errors" is
	// needed).
	panic("TODO: implement Validate")
}

// Sentinel-style validation errors a caller might want to errors.Is against
// for a specific known problem (useful for e.g. distinguishing "bad log
// level" from "missing DSN" in a caller that wants to react differently).
var (
	ErrMissingServerAddr = errors.New("config: server_addr is required")
	ErrInvalidTimeout    = errors.New("config: read/write timeout must be positive")
	ErrInvalidMaxConns   = errors.New("config: max_conns must be positive")
	ErrInvalidLogLevel   = errors.New("config: log_level must be one of debug/info/warn/error")
	ErrMissingDSN        = errors.New("config: database_dsn is required")
)

/*
HINTS
  - json.Unmarshal only overwrites fields whose keys are actually present in
    the input JSON — unmarshaling `{"log_level":"debug"}` onto a Config that
    already has ServerAddr set from defaults leaves ServerAddr untouched.
    This is exactly the layering mechanism you want, but only works if you
    unmarshal onto the PREVIOUS layer's already-populated struct, never onto
    a fresh `var cfg Config`.
  - time.Duration's default JSON representation is a raw int64 (nanoseconds),
    NOT a "30s"-style string — encoding/json has no built-in support for the
    friendly string form. To accept `"read_timeout": "30s"` in the config
    file, either (a) give Config a custom UnmarshalJSON that decodes
    durations as strings via time.ParseDuration, or (b) use a shadow struct
    with `ReadTimeout string` fields for unmarshaling and convert
    afterward. Pick one and be consistent for both the file layer and the
    env layer.
  - reflect is a legitimate, idiomatic choice here for genericizing the
    env-tag walk across all fields (viper, envconfig, and most real config
    libraries do exactly this) — but for a six-field struct, a plain
    explicit switch/if-chain reading each env var by name is also completely
    reasonable and arguably more readable/debuggable. Either is acceptable;
    just document the trade-off you picked.
  - Inject the environment reader (func() []string, or even more simply
    func(name string) (string, bool)) rather than calling os.Getenv/
    os.Environ directly inside Load — tests that need different env values
    per subtest cannot safely use os.Setenv with t.Parallel() (shared
    process-global state), but an injected function is trivially fakeable
    per test with no shared state at all.

COMMON PITFALLS
  - Unmarshaling the override file onto a fresh `var cfg Config` instead of
    the defaults-populated one — silently zeroes every field the file
    doesn't mention, which is the single most common bug in hand-rolled
    layered config loaders.
  - Treating a missing override file path as "use defaults" when filePath
    was explicitly given — masks operator typos (a mistyped --config flag
    silently running on bare defaults in production is a bad night).
  - Fail-fast validation (return on the first bad field) — forces an
    operator through N redeploy-and-retry cycles to discover all N problems
    instead of seeing the complete list once.
  - Forgetting that env var values are always strings — MAX_CONNS="10"
    needs strconv.Atoi, and a malformed value must produce a field-named
    error, not silently fall back to zero or panic.

STRETCH GOALS
  - Add a `Dump() map[string]string` that reports, per field, which layer
    (default/file/env) actually supplied its final value — invaluable for
    debugging "why is this service using the wrong timeout" in production.
  - Support a fourth layer: CLI flags (highest priority), using the
    standard `flag` package.
  - Add hot-reload: a `Watch(ctx, filePath, onChange func(Config))` that
    re-loads when the file changes (fsnotify-style, or simple polling) and
    re-validates before calling onChange, never handing the caller an
    invalid Config.
  - Redact DatabaseDSN (and any future secret field) in a String()/LogValue()
    method so accidentally logging a Config never leaks credentials.
*/
