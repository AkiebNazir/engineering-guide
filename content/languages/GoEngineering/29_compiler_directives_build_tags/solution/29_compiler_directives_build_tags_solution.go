// Package directives is the reference solution for Problem 29 — Compiler
// Directives & Build Tags.
//
// Files in this package and what each one demonstrates:
//
//	29_..._solution.go     //go:embed, //go:generate, -ldflags -X, build info
//	platform_unix.go       //go:build unix
//	platform_windows.go    implicit constraint from the _windows.go suffix
//	platform_other.go      //go:build !unix && !windows (fallback)
//	edition_default.go     //go:build !premium  (custom tag, default)
//	edition_premium.go     //go:build premium   (custom tag, opt-in)
//	gen_popcount.go        //go:build ignore    (generator program)
//	popcount_table_gen.go  generated output, committed, "DO NOT EDIT"
//	assets/                files embedded into the binary
package directives

import (
	"embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"runtime/debug"
	"slices"
	"strings"
	"text/template"
)

// go generate ./29_compiler_directives_build_tags/solution/ runs the command
// below with the package directory as the working directory. go build and
// go test NEVER run it — the generated file is committed.
//
//go:generate go run gen_popcount.go -o popcount_table_gen.go

// ============================================================================
// 1. //go:embed
// ============================================================================

// The directive must sit directly above a package-level var of type string,
// []byte or embed.FS, with only blank lines or line comments between. Paths
// are relative to this file's directory, may not contain "." or ".." path
// elements, and may not leave the module.

//go:embed assets/config.json
var defaultConfigJSON []byte

//go:embed assets/VERSION
var embeddedVersion string // contents are verbatim, including the trailing newline

// Embedding a directory skips files whose names start with "." or "_" ...
//
//go:embed assets/templates
var templatesFS embed.FS

// ... unless the pattern has the all: prefix.
//
//go:embed all:assets/templates
var allTemplatesFS embed.FS

// Config is the service configuration shipped inside the binary.
type Config struct {
	ServiceName string   `json:"service_name"`
	Port        int      `json:"port"`
	LogLevel    string   `json:"log_level"`
	Features    []string `json:"features"`
}

// DefaultConfig decodes the embedded config.json and appends any features
// enabled by build tags. The JSON is validated at runtime, not compile time:
// //go:embed only guarantees the file EXISTS when building — which is still a
// big win over reading a path from disk that may be missing in production.
func DefaultConfig() (Config, error) {
	var c Config
	if err := json.Unmarshal(defaultConfigJSON, &c); err != nil {
		return Config{}, fmt.Errorf("directives: embedded config.json: %w", err)
	}
	c.Features = append(c.Features, premiumFeatures()...)
	return c, nil
}

// EmbeddedVersion returns assets/VERSION without surrounding whitespace.
// Forgetting TrimSpace is the #1 //go:embed string bug: "1.4.0\n" != "1.4.0".
func EmbeddedVersion() string { return strings.TrimSpace(embeddedVersion) }

// TemplateNames lists the files visible in the default embedded directory.
func TemplateNames() ([]string, error) { return listFiles(templatesFS) }

// AllTemplateNames lists the files embedded with the all: prefix.
func AllTemplateNames() ([]string, error) { return listFiles(allTemplatesFS) }

func listFiles(fsys fs.FS) ([]string, error) {
	var names []string
	// embed.FS keeps the full relative path: files live under
	// "assets/templates/", not at the FS root. fs.Sub would re-root it.
	err := fs.WalkDir(fsys, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			names = append(names, d.Name())
		}
		return nil
	})
	slices.Sort(names)
	return names, err
}

// RenderTemplate executes one of the embedded templates by file name.
func RenderTemplate(name string, data any) (string, error) {
	// ParseFS works on any fs.FS, so the same code serves templates from the
	// binary in production and from os.DirFS("assets") during development.
	tmpl, err := template.ParseFS(templatesFS, "assets/templates/*.tmpl")
	if err != nil {
		return "", err
	}
	var sb strings.Builder
	if err := tmpl.ExecuteTemplate(&sb, name, data); err != nil {
		return "", err
	}
	return sb.String(), nil
}

// ============================================================================
// 2. Build constraints (see the platform_*.go and edition_*.go files)
// ============================================================================

// Platform reports which platform_*.go file was compiled into this binary.
func Platform() string { return platformName() }

// Edition reports which edition_*.go file was compiled: "community" by
// default, "premium" with -tags premium.
func Edition() string { return edition }

// ============================================================================
// 3. Version stamping with -ldflags -X, and embedded build info
// ============================================================================

// These are vars, not consts: the linker's -X flag can only overwrite
// package-level string variables (uninitialised or initialised to a constant
// string). A typo in the -X import path is silently ignored — the value just
// stays "dev" — which is why TestLdflagsStampingAndTags checks it.
//
//	go build -ldflags "-X goengineering/29_compiler_directives_build_tags/solution.Version=v1.2.3"
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
	VCSRevision string // stamped automatically by `go build` in a VCS checkout (Go 1.18+)
	VCSModified bool
}

// ReadInfo combines -X-stamped variables with debug.ReadBuildInfo, which the
// toolchain embeds in every binary (module versions, build flags, VCS state).
// Run `go version -m ./yourbinary` to see the same data from outside.
func ReadInfo() Info {
	info := Info{
		Version:   Version,
		Commit:    Commit,
		BuildDate: BuildDate,
		Edition:   Edition(),
		Platform:  Platform(),
	}
	if bi, ok := debug.ReadBuildInfo(); ok {
		info.GoVersion = bi.GoVersion
		for _, s := range bi.Settings {
			switch s.Key {
			case "vcs.revision":
				info.VCSRevision = s.Value
			case "vcs.modified":
				info.VCSModified = s.Value == "true"
			}
		}
	}
	return info
}

// ============================================================================
// 4. Using generated code
// ============================================================================

// PopCount counts set bits with the generated 256-entry table: 8 lookups
// instead of 64 shifts. math/bits.OnesCount64 is still faster — the compiler
// turns it into a dedicated CPU instruction (POPCNT on amd64, CNT on arm64).
// Measured on an Apple M4 Pro: table 2.87 ns/op vs math/bits 1.69 ns/op.
// The point here is the generate workflow, which is how real projects produce
// protobuf stubs, mocks, stringers, and lookup tables (the standard library
// generates its Unicode and CRC tables the same way).
func PopCount(x uint64) int {
	n := 0
	for range 8 {
		n += int(popcountTable[x&0xff])
		x >>= 8
	}
	return n
}
