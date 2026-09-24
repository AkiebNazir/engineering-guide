package config

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func fixedEnviron(pairs ...string) func() []string {
	return func() []string { return pairs }
}

func newTestLoader(t *testing.T, environ func() []string) *Loader {
	t.Helper()
	l := NewLoader(DefaultsFS)
	if environ != nil {
		l.environ = environ
	} else {
		l.environ = fixedEnviron() // empty env by default, hermetic
	}
	return l
}

func writeConfigFile(t *testing.T, content string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "config.json")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write config file: %v", err)
	}
	return path
}

func TestLoad_DefaultsOnly(t *testing.T) {
	l := newTestLoader(t, nil)
	cfg, err := l.Load("")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.ServerAddr != "0.0.0.0:8080" {
		t.Fatalf("ServerAddr = %q, want default", cfg.ServerAddr)
	}
	if cfg.LogLevel != "info" {
		t.Fatalf("LogLevel = %q, want default \"info\"", cfg.LogLevel)
	}
	if cfg.MaxConns != 100 {
		t.Fatalf("MaxConns = %d, want default 100", cfg.MaxConns)
	}
}

func TestLoad_EmbeddedDefaultsAreValid(t *testing.T) {
	// Guards against a broken defaults.json ever shipping: this should
	// never fail in CI. If it does, the embedded baseline itself is bad.
	l := newTestLoader(t, nil)
	cfg, err := l.Load("")
	if err != nil {
		t.Fatalf("embedded defaults produced an error: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("embedded defaults do not pass validation: %v", err)
	}
}

func TestLoad_FileOverridesDefaultsButLeavesOtherFieldsIntact(t *testing.T) {
	path := writeConfigFile(t, `{"log_level": "debug"}`)
	l := newTestLoader(t, nil)

	cfg, err := l.Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.LogLevel != "debug" {
		t.Fatalf("LogLevel = %q, want file override \"debug\"", cfg.LogLevel)
	}
	// ServerAddr wasn't in the override file — must still be the default.
	if cfg.ServerAddr != "0.0.0.0:8080" {
		t.Fatalf("ServerAddr = %q, want untouched default (file didn't mention it)", cfg.ServerAddr)
	}
}

func TestLoad_EnvOverridesFileAndDefaults(t *testing.T) {
	path := writeConfigFile(t, `{"log_level": "warn", "max_conns": 50}`)
	l := newTestLoader(t, fixedEnviron("LOG_LEVEL=error"))

	cfg, err := l.Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	// env (error) beats file (warn) beats default (info).
	if cfg.LogLevel != "error" {
		t.Fatalf("LogLevel = %q, want env override \"error\"", cfg.LogLevel)
	}
	// max_conns had no env override, so the file's value should survive.
	if cfg.MaxConns != 50 {
		t.Fatalf("MaxConns = %d, want file override 50", cfg.MaxConns)
	}
}

func TestLoad_FullPrecedenceChain(t *testing.T) {
	// read_timeout: default 15s < file 30s < env 45s. Prove env wins, then
	// drop env and prove file wins, then drop file and prove default wins.
	path := writeConfigFile(t, `{"read_timeout": "30s"}`)

	withEnv := newTestLoader(t, fixedEnviron("READ_TIMEOUT=45s"))
	cfg, err := withEnv.Load(path)
	if err != nil {
		t.Fatalf("Load with env: %v", err)
	}
	if cfg.ReadTimeout.String() != "45s" {
		t.Fatalf("ReadTimeout = %s, want env value 45s", cfg.ReadTimeout)
	}

	withoutEnv := newTestLoader(t, nil)
	cfg, err = withoutEnv.Load(path)
	if err != nil {
		t.Fatalf("Load without env: %v", err)
	}
	if cfg.ReadTimeout.String() != "30s" {
		t.Fatalf("ReadTimeout = %s, want file value 30s", cfg.ReadTimeout)
	}

	withoutFile := newTestLoader(t, nil)
	cfg, err = withoutFile.Load("")
	if err != nil {
		t.Fatalf("Load without file: %v", err)
	}
	if cfg.ReadTimeout.String() != "15s" {
		t.Fatalf("ReadTimeout = %s, want default value 15s", cfg.ReadTimeout)
	}
}

func TestLoad_MissingOverrideFileIsAnError(t *testing.T) {
	l := newTestLoader(t, nil)
	_, err := l.Load(filepath.Join(t.TempDir(), "does-not-exist.json"))
	if err == nil {
		t.Fatal("expected an error for a nonexistent override file")
	}
}

func TestLoad_MalformedEnvValueReportsFieldName(t *testing.T) {
	l := newTestLoader(t, fixedEnviron("MAX_CONNS=notanumber"))
	_, err := l.Load("")
	if err == nil {
		t.Fatal("expected an error for malformed MAX_CONNS")
	}
	if !strings.Contains(err.Error(), "MAX_CONNS") {
		t.Fatalf("expected error to name MAX_CONNS, got: %v", err)
	}
}

func TestLoad_MultipleEnvErrorsAllReported(t *testing.T) {
	l := newTestLoader(t, fixedEnviron("MAX_CONNS=abc", "READ_TIMEOUT=notaduration"))
	_, err := l.Load("")
	if err == nil {
		t.Fatal("expected an error")
	}
	msg := err.Error()
	if !strings.Contains(msg, "MAX_CONNS") || !strings.Contains(msg, "READ_TIMEOUT") {
		t.Fatalf("expected both MAX_CONNS and READ_TIMEOUT errors present, got: %v", msg)
	}
}

func TestValidate_ReportsEveryViolationAtOnce(t *testing.T) {
	cfg := Config{} // everything invalid
	err := cfg.Validate()
	if err == nil {
		t.Fatal("expected validation errors for a zero-value Config")
	}
	for _, sentinel := range []error{
		ErrMissingServerAddr,
		ErrInvalidTimeout,
		ErrInvalidMaxConns,
		ErrInvalidLogLevel,
		ErrMissingDSN,
	} {
		if !errors.Is(err, sentinel) {
			t.Errorf("expected errors.Is to find %v in joined error %v", sentinel, err)
		}
	}
}

func TestValidate_ValidConfigPasses(t *testing.T) {
	cfg := Config{
		ServerAddr:   "127.0.0.1:9090",
		ReadTimeout:  1,
		WriteTimeout: 1,
		MaxConns:     5,
		LogLevel:     "debug",
		DatabaseDSN:  "sqlite://test",
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("expected valid config to pass, got: %v", err)
	}
}
