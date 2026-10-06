/*
Problem 29 — Compiler Directives & Build Tags (//go:build, file suffixes,
//go:embed, //go:generate, -ldflags -X, build info, compiler pragmas)

WHAT WE'RE BUILDING

A package whose behaviour is decided at BUILD time, not run time:

 1. Embedded assets — a default config.json, a VERSION file and a directory
    of text/templates compiled INTO the binary with //go:embed, including
    the dot-file / underscore-file exclusion rule and the all: prefix.
 2. Build-constrained files — platform_unix.go / platform_windows.go /
    platform_other.go select an implementation per GOOS; edition_default.go
    and edition_premium.go select a feature set with a custom -tags flag.
 3. Code generation — gen_popcount.go (a //go:build ignore program) is run
    by //go:generate to produce popcount_table_gen.go, which is committed
    and verified fresh by a test.
 4. Version stamping — Version/Commit/BuildDate vars overwritten by
    `-ldflags -X`, plus the VCS and module data the toolchain embeds
    automatically, read with debug.ReadBuildInfo.

The companion files (platform_*.go, edition_*.go, gen_popcount.go,
popcount_table_gen.go, assets/) are already provided in this directory —
read them, they are part of the lesson. You implement this file.

WHY THIS MATTERS IN REAL SYSTEMS

  - Single static binary deploys: SQL migrations, HTML templates, a React
    build, OpenAPI specs and default configs shipped with //go:embed means
    "FROM scratch" containers with nothing to mount and nothing to go
    missing at 3am.
  - Every Go codebase with protobuf, gRPC, mocks (mockgen), enums
    (stringer), SQL (sqlc) or DI (wire) depends on //go:generate and on the
    team convention of committing generated code.
  - Cross-platform code (file locking, signals, syscalls, terminal handling)
    is split with build constraints — the standard library does this
    thousands of times (os/file_unix.go, os/file_windows.go...).
  - "Which build is running in prod?" is answered by -ldflags -X and
    debug.ReadBuildInfo, surfaced through /version endpoints and startup logs.
  - Enterprise/open-core editions, debug-only instrumentation, and
    integration-test-only code are selected with custom tags.

MENTAL MODEL 1 — HOW GO DECIDES WHICH FILES TO COMPILE

    for each .go file in the package directory:
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. name starts with "_" or "."?              ──▶ skip        │
    │ 2. name ends in _test.go and not `go test`?  ──▶ skip        │
    │ 3. filename suffix constraint                                │
    │      *_GOOS.go  *_GOARCH.go  *_GOOS_GOARCH.go                │
    │      does it match the target?  no           ──▶ skip        │
    │ 4. //go:build expression (if present)                        │
    │      evaluate with the active tags          false ──▶ skip   │
    │ 5. import "C" and CGO_ENABLED=0?             ──▶ skip        │
    └─────────────────────────────────────────────────────────────┘
                              │ survived all checks
                              ▼
                     compiled into the package

Active tags = GOOS, GOARCH, "unix" (on Unix-like GOOS, Go 1.19+), "cgo"
(when enabled), every go1.N release tag up to the toolchain version,
"gc" / "gccgo", and anything passed with -tags a,b,c.

You never have to guess: `go list -f '{{.GoFiles}} {{.IgnoredGoFiles}}' .`
prints the exact selection, and GOOS=windows go list ... shows it for
another target without compiling anything. The tests do exactly this.

MENTAL MODEL 2 — BUILD CONSTRAINT SYNTAX AND PLACEMENT

	//go:build (linux || darwin) && !premium

	package directives

  - Operators: || && ! and parentheses. Terms are tag names.
  - It must appear BEFORE the package clause, preceded only by blank lines
    and other line comments, and must be followed by a blank line —
    otherwise it is just a comment attached to the package doc and is
    silently IGNORED. (gofmt and `go vet`'s buildtag check help catch this.)
  - Old-style `// +build linux darwin` lines are pre-Go 1.17 syntax; modern
    modules need only //go:build.
  - One file per variant, and the variants must be EXHAUSTIVE or some
    target fails with "undefined: platformName":

    platform_unix.go      //go:build unix
    platform_windows.go   (no line: the _windows suffix is the constraint)
    platform_other.go     //go:build !unix && !windows

  - A custom tag pair must be complementary: premium / !premium. If both
    files could compile at once you get "edition redeclared"; if neither
    can you get "undefined: edition".
  - Common real tags: integration (slow tests), debug / race-only
    helpers, purego (disable assembly), netgo / osusergo (pure-Go resolver
    for static binaries), timetzdata (embed the tz database).

MENTAL MODEL 3 — EMBEDDING FILES INTO THE BINARY

    source tree                         binary
    ───────────                         ──────
    solution/
    ├── assets/
    │   ├── VERSION        ──embed──▶  var embeddedVersion string  "1.4.0\n"
    │   ├── config.json    ──embed──▶  var defaultConfigJSON []byte
    │   └── templates/
    │       ├── welcome.tmpl ─┐
    │       ├── reset.tmpl  ──┼─embed─▶ var templatesFS embed.FS
    │       ├── .draft.tmpl   │         (dot/underscore files SKIPPED)
    │       └── _wip.tmpl   ──┴─all:──▶ var allTemplatesFS embed.FS
    │                                   (all: prefix INCLUDES them)
    └── *.go

	import "embed"

	//go:embed assets/config.json
	var defaultConfigJSON []byte

	//go:embed all:assets/templates
	var allTemplatesFS embed.FS

Rules that bite:
  - Package-level vars only; types string, []byte or embed.FS. For string
    and []byte exactly one file. You must import "embed" (use `_ "embed"`
    when only string/[]byte vars use it).
  - Paths are slash-separated, relative to the source file's directory,
    cannot contain . or .. elements, cannot leave the module, and symlinks
    are not followed. A missing file is a COMPILE error — a feature.
  - Directory embeds skip names starting with . or _ (and do so
    recursively). The all: prefix disables that. `dir/*` also includes
    dot-files matched explicitly by the glob.
  - embed.FS paths keep the directory prefix: open
    "assets/templates/welcome.tmpl", not "welcome.tmpl"; use fs.Sub to
    re-root.
  - Embedded content is read-only and lives in the binary's data segment:
    big embeds make big binaries, and every byte counts toward image pulls.
  - embed.FS implements fs.FS, so http.FileServerFS, template.ParseFS and
    fs.WalkDir all accept it; in dev, swap in os.DirFS for live reload.

MENTAL MODEL 4 — CODE GENERATION WITH GO GENERATE

    developer / CI                           go build / go test
    ──────────────                           ──────────────────
    $ go generate ./...                      never runs generators
          │                                  just compiles the
          │ scans .go files for              committed output
          │ "//go:generate cmd args"
          ▼
    runs `go run gen_popcount.go -o popcount_table_gen.go`
          │  cwd = package dir
          │  env: $GOFILE $GOLINE $GOPACKAGE $GOARCH $GOOS $DOLLAR
          ▼
    popcount_table_gen.go  ──git commit──▶  reviewed like any code

  - The line must start exactly with `//go:generate` (no space after //).
  - Generated files start with a line matching
    `^// Code generated .* DO NOT EDIT\.$` — tools rely on it.
  - The generator program lives next to the package with //go:build ignore
    so it is never part of the package, or in an internal/cmd directory.
  - Commit generated code. Consumers of your module run `go build`, never
    `go generate`; and module proxies serve exactly what you committed.
  - CI should regenerate and fail on a diff (TestGeneratedFileIsUpToDate).
  - Pin generator versions: `go run golang.org/x/tools/cmd/stringer@v0.x.y`
    or a `tool` directive in go.mod (Go 1.24+), then `go tool stringer`.

MENTAL MODEL 5 — STAMPING THE BINARY

	go build -ldflags "-s -w \
	  -X 'goengineering/29_compiler_directives_build_tags/solution.Version=v1.4.0' \
	  -X 'goengineering/29_compiler_directives_build_tags/solution.Commit=$(git rev-parse --short HEAD)'"

  - -X importpath.name=value works only on package-level STRING VARIABLES
    (not consts, not ints). A wrong import path is silently ignored.
  - -s -w strip the symbol table and DWARF: smaller binary, worse
    debugging/profiling symbolization. Know which you're shipping.
  - Since Go 1.18, `go build` inside a git checkout automatically embeds
    vcs.revision, vcs.time and vcs.modified (-buildvcs=auto). Read them
    with debug.ReadBuildInfo(), or from outside with
    `go version -m ./binary`. Test binaries don't carry VCS stamps.

MENTAL MODEL 6 — COMPILER PRAGMAS YOU WILL MEET IN THE WILD

    | Directive               | What it does                                   | Use it?            |
    |-------------------------|------------------------------------------------|--------------------|
    | //go:noinline           | forbid inlining this function                  | benchmarks, tests  |
    | //go:nosplit            | no stack-growth check in the prologue          | runtime code only  |
    | //go:noescape           | assembly func: pointer args don't escape       | with .s files only |
    | //go:norace             | skip race instrumentation for this function    | almost never       |
    | //go:linkname local pkg | bind to another package's unexported symbol    | avoid (see below)  |
    | //go:uintptrescapes     | uintptr args keep their objects alive          | syscall wrappers   |
    | //go:wasmimport mod fn  | import a host function in wasm builds          | wasm only          |
    | //line file:line        | rewrite positions (used by code generators)    | generators         |

//go:linkname deserves a warning: since Go 1.23 the linker refuses "pull"
linknames into standard-library internals unless the target is explicitly
marked, because packages that did this broke on every Go release.
Pragmas apply to the NEXT declaration and require no space after //.

SPEC

	//go:embed assets/config.json      var defaultConfigJSON []byte
	//go:embed assets/VERSION          var embeddedVersion string
	//go:embed assets/templates        var templatesFS embed.FS
	//go:embed all:assets/templates    var allTemplatesFS embed.FS

	type Config struct { ServiceName string `json:"service_name"`; Port int `json:"port"`;
	                     LogLevel string `json:"log_level"`; Features []string `json:"features"` }
	func DefaultConfig() (Config, error)      // decode embedded JSON, append premiumFeatures()
	func EmbeddedVersion() string             // trimmed
	func TemplateNames() ([]string, error)    // sorted base names in templatesFS
	func AllTemplateNames() ([]string, error) // sorted base names in allTemplatesFS
	func RenderTemplate(name string, data any) (string, error)

	func Platform() string   // platformName() from the build-selected file
	func Edition() string    // edition const from the build-selected file

	var Version, Commit, BuildDate = "dev", "none", "unknown"
	type Info struct { Version, Commit, BuildDate, GoVersion, Edition, Platform, VCSRevision string; VCSModified bool }
	func ReadInfo() Info

	func PopCount(x uint64) int   // 8 lookups into the generated popcountTable

ACCEPTANCE CRITERIA

  - `go test -v ./29_compiler_directives_build_tags/solution/...` passes,
    including the tests that:
      - list which files `go list` compiles for darwin, linux -tags premium,
        windows and js/wasm;
      - build a child test binary with -tags premium and -ldflags -X and
        read the stamped values back;
      - regenerate popcount_table_gen.go and byte-compare it to the
        committed file.
  - `go generate ./29_compiler_directives_build_tags/solution/` leaves
    `git status` clean.

HOW TO RUN

	go test -v ./29_compiler_directives_build_tags/solution/...
	go test -tags premium -run TestEmbeddedConfig -v ./29_compiler_directives_build_tags/solution/
	go generate ./29_compiler_directives_build_tags/solution/
	GOOS=windows go list -f '{{.GoFiles}}' ./29_compiler_directives_build_tags/solution/
	go test -short ./29_compiler_directives_build_tags/solution/   # skip tests that call the go tool

HINTS

  - Only a blank line or line comments may separate //go:embed from its var.
  - fs.WalkDir(fsys, ".", ...) walks an embed.FS from its root; collect
    d.Name() for non-directories, then slices.Sort.
  - template.ParseFS(templatesFS, "assets/templates/*.tmpl") then
    ExecuteTemplate by base file name.
  - debug.ReadBuildInfo().Settings is a []debug.BuildSetting of Key/Value.

COMMON PITFALLS

  - `// go:build linux` (space) or //go:build directly above `package`
    without a blank line → constraint ignored, file compiled everywhere.
  - Adding a platform file without a fallback → some GOOS fails to build;
    you find out when someone runs it on FreeBSD or wasm.
  - Forgetting strings.TrimSpace on an embedded VERSION file.
  - Expecting //go:embed to include .env / _partials in a directory embed.
  - Editing popcount_table_gen.go by hand; the next go generate wipes it.
  - -X on a const, or with the wrong import path: silently no effect.
  - Using build tags for things that should be runtime config — every tag
    combination is a separate binary you must build and test.

STRETCH GOALS

  - Add an `integration` tag guarding a test file that needs Docker, and a
    Makefile target that runs `go test -tags integration`.
  - Replace gen_popcount.go with a generator that parses a Go file
    (go/parser) and emits String() methods for an enum — then compare with
    golang.org/x/tools/cmd/stringer. (Problem 30 builds exactly this.)
  - Serve assets/ over HTTP with http.FileServerFS(fs.Sub(...)), switching
    to os.DirFS under a `dev` build tag.
*/

package directives

import (
	"embed"
)

// go generate runs the directive below; go build/test never do.
//
//go:generate go run gen_popcount.go -o popcount_table_gen.go

// ============================================================================
// 1. //go:embed
// ============================================================================

// TODO: add `//go:embed assets/config.json` directly above this var.
var defaultConfigJSON []byte

// TODO: add `//go:embed assets/VERSION`.
var embeddedVersion string

// TODO: add `//go:embed assets/templates`.
var templatesFS embed.FS

// TODO: add `//go:embed all:assets/templates`.
var allTemplatesFS embed.FS

// Config is the service configuration shipped inside the binary.
type Config struct {
	ServiceName string   `json:"service_name"`
	Port        int      `json:"port"`
	LogLevel    string   `json:"log_level"`
	Features    []string `json:"features"`
}

// DefaultConfig decodes the embedded config.json and appends premiumFeatures().
func DefaultConfig() (Config, error) {
	// TODO: json.Unmarshal(defaultConfigJSON, &c); c.Features = append(c.Features, premiumFeatures()...)
	panic("not implemented")
}

// EmbeddedVersion returns assets/VERSION without surrounding whitespace.
func EmbeddedVersion() string {
	// TODO
	panic("not implemented")
}

// TemplateNames lists base names of files in templatesFS, sorted.
func TemplateNames() ([]string, error) {
	// TODO: fs.WalkDir(templatesFS, ".", ...)
	panic("not implemented")
}

// AllTemplateNames lists base names of files in allTemplatesFS, sorted.
func AllTemplateNames() ([]string, error) {
	// TODO
	panic("not implemented")
}

// RenderTemplate executes one of the embedded templates by file name.
func RenderTemplate(name string, data any) (string, error) {
	// TODO: template.ParseFS + ExecuteTemplate into a strings.Builder.
	panic("not implemented")
}

// ============================================================================
// 2. Build constraints
// ============================================================================

// Platform reports which platform_*.go file was compiled.
func Platform() string {
	// TODO: return platformName()
	panic("not implemented")
}

// Edition reports which edition_*.go file was compiled.
func Edition() string {
	// TODO: return edition
	panic("not implemented")
}

// ============================================================================
// 3. Version stamping
// ============================================================================

// Version, Commit and BuildDate are overwritten at link time with -ldflags -X.
var (
	Version   = "dev"
	Commit    = "none"
	BuildDate = "unknown"
)

// Info describes the running binary.
type Info struct {
	Version     string
	Commit      string
	BuildDate   string
	GoVersion   string
	Edition     string
	Platform    string
	VCSRevision string
	VCSModified bool
}

// ReadInfo combines the stamped vars with debug.ReadBuildInfo.
func ReadInfo() Info {
	// TODO: fill from vars, Edition(), Platform(); GoVersion and vcs.* from debug.ReadBuildInfo().
	panic("not implemented")
}

// ============================================================================
// 4. Generated code
// ============================================================================

// PopCount counts set bits using the generated popcountTable.
func PopCount(x uint64) int {
	// TODO: 8 iterations of n += int(popcountTable[x&0xff]); x >>= 8
	panic("not implemented")
}
