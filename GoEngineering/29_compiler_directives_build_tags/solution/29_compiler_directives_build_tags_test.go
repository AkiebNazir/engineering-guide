package directives

import (
	"bytes"
	"fmt"
	"math/bits"
	"math/rand/v2"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"slices"
	"strings"
	"testing"
)

// ----------------------------------------------------------------------------
// //go:embed
// ----------------------------------------------------------------------------

func TestEmbeddedConfig(t *testing.T) {
	c, err := DefaultConfig()
	if err != nil {
		t.Fatal(err)
	}
	if c.ServiceName != "orders-api" || c.Port != 8080 || c.LogLevel != "info" {
		t.Fatalf("unexpected config: %+v", c)
	}
	want := []string{"healthz", "metrics"}
	if Edition() == "premium" {
		want = append(want, "sso", "audit-log")
	}
	if !slices.Equal(c.Features, want) {
		t.Fatalf("features = %v, want %v (edition %s)", c.Features, want, Edition())
	}
}

func TestEmbeddedStringKeepsTrailingNewline(t *testing.T) {
	if !strings.HasSuffix(embeddedVersion, "\n") {
		t.Fatalf("expected raw embedded string to keep the file's newline, got %q", embeddedVersion)
	}
	if EmbeddedVersion() != "1.4.0" {
		t.Fatalf("EmbeddedVersion = %q", EmbeddedVersion())
	}
}

func TestLesson_EmbedSkipsDotAndUnderscoreFiles(t *testing.T) {
	plain, err := TemplateNames()
	if err != nil {
		t.Fatal(err)
	}
	all, err := AllTemplateNames()
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(plain, []string{"reset.tmpl", "welcome.tmpl"}) {
		t.Fatalf("//go:embed assets/templates → %v", plain)
	}
	if !slices.Equal(all, []string{".draft.tmpl", "_wip.tmpl", "reset.tmpl", "welcome.tmpl"}) {
		t.Fatalf("//go:embed all:assets/templates → %v", all)
	}
	t.Logf("without all: %v", plain)
	t.Logf("with    all: %v", all)
}

func TestRenderTemplate(t *testing.T) {
	got, err := RenderTemplate("welcome.tmpl", map[string]string{"Name": "Ada", "Plan": "pro"})
	if err != nil {
		t.Fatal(err)
	}
	if got != "Welcome, Ada! Your plan is pro.\n" {
		t.Fatalf("got %q", got)
	}
	if _, err := RenderTemplate(".draft.tmpl", nil); err == nil {
		t.Fatal("hidden template should not be in the default embed")
	}
}

// ----------------------------------------------------------------------------
// Build constraints — inspected with `go list`, no compilation needed
// ----------------------------------------------------------------------------

func goTool(t *testing.T) string {
	t.Helper()
	if testing.Short() {
		t.Skip("invokes the go command")
	}
	p, err := exec.LookPath("go")
	if err != nil {
		t.Skip("go command not on PATH")
	}
	return p
}

// goList returns the Go files the build would compile, plus files excluded by
// constraints, for this package under the given environment and flags.
func goList(t *testing.T, env []string, args ...string) (compiled, ignored []string) {
	t.Helper()
	cmd := exec.Command(goTool(t), append(append([]string{"list"}, args...),
		"-f", "{{join .GoFiles \",\"}}|{{join .IgnoredGoFiles \",\"}}", ".")...)
	cmd.Env = append(os.Environ(), env...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("go list: %v\n%s", err, out)
	}
	a, b, _ := strings.Cut(strings.TrimSpace(string(out)), "|")
	return strings.Split(a, ","), strings.Split(b, ",")
}

func TestLesson_BuildTagsSelectFiles(t *testing.T) {
	scenarios := []struct {
		name     string
		env      []string
		args     []string
		want     []string
		excluded []string
	}{
		{"default darwin", []string{"GOOS=darwin", "GOARCH=arm64"}, nil,
			[]string{"edition_default.go", "platform_unix.go"},
			[]string{"edition_premium.go", "platform_windows.go", "platform_other.go", "gen_popcount.go"}},
		{"-tags premium", []string{"GOOS=linux", "GOARCH=amd64"}, []string{"-tags", "premium"},
			[]string{"edition_premium.go", "platform_unix.go"},
			[]string{"edition_default.go"}},
		{"GOOS=windows", []string{"GOOS=windows", "GOARCH=amd64"}, nil,
			[]string{"platform_windows.go"},
			[]string{"platform_unix.go", "platform_other.go"}},
		{"GOOS=js GOARCH=wasm", []string{"GOOS=js", "GOARCH=wasm"}, nil,
			[]string{"platform_other.go"},
			[]string{"platform_unix.go", "platform_windows.go"}},
	}
	for _, s := range scenarios {
		t.Run(s.name, func(t *testing.T) {
			compiled, ignored := goList(t, s.env, s.args...)
			for _, f := range s.want {
				if !slices.Contains(compiled, f) {
					t.Errorf("%s should be compiled; compiled=%v", f, compiled)
				}
			}
			for _, f := range s.excluded {
				if !slices.Contains(ignored, f) {
					t.Errorf("%s should be excluded; ignored=%v", f, ignored)
				}
			}
			t.Logf("compiled: %v", compiled)
		})
	}
}

func TestPlatformMatchesGOOS(t *testing.T) {
	want := "unix"
	switch runtime.GOOS {
	case "windows":
		want = "windows"
	case "js", "wasip1", "plan9":
		want = "other"
	}
	if Platform() != want {
		t.Fatalf("Platform() = %q on GOOS=%s, want %q", Platform(), runtime.GOOS, want)
	}
}

// ----------------------------------------------------------------------------
// -ldflags -X and -tags at runtime — one child `go test` build
// ----------------------------------------------------------------------------

const printInfoEnv = "DIRECTIVES_PRINT_INFO"

// TestPrintInfoHelper only does something inside the child process started
// by TestLdflagsStampingAndTags.
func TestPrintInfoHelper(t *testing.T) {
	if os.Getenv(printInfoEnv) != "1" {
		t.Skip("helper for TestLdflagsStampingAndTags")
	}
	i := ReadInfo()
	fmt.Printf("VERSION=%s COMMIT=%s EDITION=%s\n", i.Version, i.Commit, i.Edition)
}

func TestLdflagsStampingAndTags(t *testing.T) {
	gobin := goTool(t)
	pathOut, err := exec.Command(gobin, "list", "-f", "{{.ImportPath}}", ".").Output()
	if err != nil {
		t.Fatal(err)
	}
	pkg := strings.TrimSpace(string(pathOut))

	ldflags := fmt.Sprintf("-X %s.Version=v9.9.9 -X %s.Commit=abc1234", pkg, pkg)
	cmd := exec.Command(gobin, "test", "-count=1", "-tags", "premium",
		"-ldflags", ldflags, "-run", "^TestPrintInfoHelper$", "-v", ".")
	cmd.Env = append(os.Environ(), printInfoEnv+"=1")
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("child go test failed: %v\n%s", err, out)
	}
	if !strings.Contains(string(out), "VERSION=v9.9.9 COMMIT=abc1234 EDITION=premium") {
		t.Fatalf("stamping/tags not applied:\n%s", out)
	}
	t.Logf("child binary built with -tags premium -ldflags -X reported: VERSION=v9.9.9 COMMIT=abc1234 EDITION=premium")

	if in := ReadInfo(); in.Version != "dev" || in.Edition != "community" {
		t.Logf("note: this binary itself was built with custom flags: %+v", in)
	}
}

// ----------------------------------------------------------------------------
// //go:generate — generated code must be fresh and correct
// ----------------------------------------------------------------------------

// TestGeneratedFileIsUpToDate is the check CI should run: regenerate into a
// temp file and diff against the committed copy. Someone editing the
// generator without re-running go generate fails here, not in production.
func TestGeneratedFileIsUpToDate(t *testing.T) {
	gobin := goTool(t)
	tmp := filepath.Join(t.TempDir(), "popcount_table_gen.go")
	cmd := exec.Command(gobin, "run", "gen_popcount.go", "-o", tmp)
	cmd.Env = append(os.Environ(), "GOPACKAGE=directives")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("generator failed: %v\n%s", err, out)
	}
	fresh, err := os.ReadFile(tmp)
	if err != nil {
		t.Fatal(err)
	}
	committed, err := os.ReadFile("popcount_table_gen.go")
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(fresh, committed) {
		t.Fatal("popcount_table_gen.go is stale: run `go generate` and commit the result")
	}
	if !bytes.HasPrefix(committed, []byte("// Code generated by gen_popcount.go; DO NOT EDIT.")) {
		t.Fatal("generated file must start with the standard 'Code generated ... DO NOT EDIT.' header")
	}
}

func TestPopCountMatchesMathBits(t *testing.T) {
	r := rand.New(rand.NewPCG(1, 2))
	cases := []uint64{0, 1, 0xff, 1 << 63, ^uint64(0)}
	for range 10_000 {
		cases = append(cases, r.Uint64())
	}
	for _, x := range cases {
		if got, want := PopCount(x), bits.OnesCount64(x); got != want {
			t.Fatalf("PopCount(%#x) = %d, want %d", x, got, want)
		}
	}
}

var sinkInt int

func BenchmarkPopCountTable(b *testing.B) {
	for i := uint64(0); b.Loop(); i++ {
		sinkInt = PopCount(i * 0x9E3779B97F4A7C15)
	}
}

func BenchmarkPopCountMathBits(b *testing.B) {
	for i := uint64(0); b.Loop(); i++ {
		sinkInt = bits.OnesCount64(i * 0x9E3779B97F4A7C15)
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleRenderTemplate() {
	out, _ := RenderTemplate("reset.tmpl", map[string]string{"Name": "Lin", "Link": "https://example.com/r/42"})
	fmt.Print(out)
	// Output: Hi Lin, use this link to reset your password: https://example.com/r/42
}

func ExampleEmbeddedVersion() {
	fmt.Printf("%q vs %q\n", embeddedVersion, EmbeddedVersion())
	// Output: "1.4.0\n" vs "1.4.0"
}

func ExamplePopCount() {
	fmt.Println(PopCount(0b1011), PopCount(^uint64(0)))
	// Output: 3 64
}
