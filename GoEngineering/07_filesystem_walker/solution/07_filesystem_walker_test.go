package fswalk

import (
	"context"
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"testing/fstest"
	"time"
)

// buildOSTree creates the same directory layout on real disk that
// buildMapFS builds in memory, so every test below can run the identical
// assertions against both fs.FS implementations.
func buildOSTree(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	files := map[string]string{
		"a.txt":             "hello",
		"b.log":             "logline",
		"sub/c.txt":         "world!!",
		"sub/d.bin":         "binarydata",
		"sub/nested/e.txt":  "deepfile",
		"skipme/f.txt":      "should not appear",
		"skipme/deep/g.txt": "also should not appear",
		"noext":             "no extension here",
	}
	for name, content := range files {
		full := filepath.Join(dir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(full), 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		if err := os.WriteFile(full, []byte(content), 0o644); err != nil {
			t.Fatalf("WriteFile: %v", err)
		}
	}
	return dir
}

func buildMapFS() fstest.MapFS {
	return fstest.MapFS{
		"a.txt":             {Data: []byte("hello")},
		"b.log":             {Data: []byte("logline")},
		"sub/c.txt":         {Data: []byte("world!!")},
		"sub/d.bin":         {Data: []byte("binarydata")},
		"sub/nested/e.txt":  {Data: []byte("deepfile")},
		"skipme/f.txt":      {Data: []byte("should not appear")},
		"skipme/deep/g.txt": {Data: []byte("also should not appear")},
		"noext":             {Data: []byte("no extension here")},
	}
}

// prune skips any directory literally named "skipme".
func prune(path string, d fs.DirEntry) bool {
	return d.Name() == "skipme"
}

func txtOnly(path string, d fs.DirEntry) bool {
	return strings.HasSuffix(path, ".txt")
}

func runWalkTableTest(t *testing.T, fsys fs.FS) {
	t.Helper()
	ctx := context.Background()

	t.Run("no filter, no prune sees everything", func(t *testing.T) {
		report, err := Walk(ctx, fsys, ".", WalkOptions{})
		if err != nil {
			t.Fatalf("Walk: %v", err)
		}
		if len(report.Files) != 8 {
			t.Fatalf("expected 8 files, got %d: %+v", len(report.Files), report.Files)
		}
		if report.SkippedDir != 0 {
			t.Fatalf("expected 0 skipped dirs, got %d", report.SkippedDir)
		}
	})

	t.Run("prune skips subtree entirely", func(t *testing.T) {
		report, err := Walk(ctx, fsys, ".", WalkOptions{PruneDir: prune})
		if err != nil {
			t.Fatalf("Walk: %v", err)
		}
		for _, r := range report.Files {
			if strings.HasPrefix(r.Path, "skipme/") {
				t.Fatalf("pruned directory leaked file: %s", r.Path)
			}
		}
		if report.SkippedDir != 1 {
			t.Fatalf("expected SkippedDir == 1, got %d", report.SkippedDir)
		}
		if len(report.Files) != 6 {
			t.Fatalf("expected 6 files after pruning, got %d: %+v", len(report.Files), report.Files)
		}
	})

	t.Run("filter selects only .txt files", func(t *testing.T) {
		report, err := Walk(ctx, fsys, ".", WalkOptions{Filter: txtOnly})
		if err != nil {
			t.Fatalf("Walk: %v", err)
		}
		want := map[string]bool{
			"a.txt":             true,
			"sub/c.txt":         true,
			"sub/nested/e.txt":  true,
			"skipme/f.txt":      true,
			"skipme/deep/g.txt": true,
		}
		if len(report.Files) != len(want) {
			t.Fatalf("expected %d .txt files, got %d: %+v", len(want), len(report.Files), report.Files)
		}
		for _, r := range report.Files {
			if !want[r.Path] {
				t.Fatalf("unexpected file in filtered report: %s", r.Path)
			}
		}
	})

	t.Run("files are sorted by path", func(t *testing.T) {
		report, err := Walk(ctx, fsys, ".", WalkOptions{})
		if err != nil {
			t.Fatalf("Walk: %v", err)
		}
		for i := 1; i < len(report.Files); i++ {
			if report.Files[i-1].Path >= report.Files[i].Path {
				t.Fatalf("files not sorted: %s >= %s", report.Files[i-1].Path, report.Files[i].Path)
			}
		}
	})

	t.Run("ByExt and TotalSize are consistent", func(t *testing.T) {
		report, err := Walk(ctx, fsys, ".", WalkOptions{})
		if err != nil {
			t.Fatalf("Walk: %v", err)
		}
		var sum int64
		byExt := map[string]int{}
		for _, r := range report.Files {
			sum += r.Size
			byExt[extOf(r.Path)]++
		}
		if sum != report.TotalSize {
			t.Fatalf("TotalSize mismatch: computed %d, report says %d", sum, report.TotalSize)
		}
		for ext, n := range byExt {
			if report.ByExt[ext] != n {
				t.Fatalf("ByExt[%q] = %d, want %d", ext, report.ByExt[ext], n)
			}
		}
	})

	t.Run("canceled context aborts the walk", func(t *testing.T) {
		cctx, cancel := context.WithCancel(context.Background())
		cancel()
		_, err := Walk(cctx, fsys, ".", WalkOptions{})
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("expected context.Canceled, got %v", err)
		}
	})
}

func extOf(p string) string {
	idx := strings.LastIndexByte(p, '.')
	slash := strings.LastIndexByte(p, '/')
	if idx <= slash {
		return ""
	}
	return p[idx:]
}

func TestWalk_OSFilesystem(t *testing.T) {
	dir := buildOSTree(t)
	runWalkTableTest(t, os.DirFS(dir))
}

func TestWalk_MapFS(t *testing.T) {
	runWalkTableTest(t, buildMapFS())
}

func TestHashMatched_ConsistentAcrossWorkerCounts(t *testing.T) {
	fsys := buildMapFS()
	ctx := context.Background()

	report, err := Walk(ctx, fsys, ".", WalkOptions{})
	if err != nil {
		t.Fatalf("Walk: %v", err)
	}

	digestsSerial, err := HashMatched(ctx, fsys, report, 1)
	if err != nil {
		t.Fatalf("HashMatched(workers=1): %v", err)
	}
	digestsParallel, err := HashMatched(ctx, fsys, report, 8)
	if err != nil {
		t.Fatalf("HashMatched(workers=8): %v", err)
	}

	if len(digestsSerial) != len(digestsParallel) {
		t.Fatalf("digest map size mismatch: serial=%d parallel=%d", len(digestsSerial), len(digestsParallel))
	}
	for path, digest := range digestsSerial {
		if digestsParallel[path] != digest {
			t.Fatalf("digest mismatch for %s: serial=%s parallel=%s", path, digest, digestsParallel[path])
		}
	}
	if len(digestsSerial) != len(report.Files) {
		t.Fatalf("expected a digest for every matched file, got %d of %d", len(digestsSerial), len(report.Files))
	}
}

func TestHashMatched_RespectsCancellation(t *testing.T) {
	fsys := buildMapFS()
	report, err := Walk(context.Background(), fsys, ".", WalkOptions{})
	if err != nil {
		t.Fatalf("Walk: %v", err)
	}

	cctx, cancel := context.WithTimeout(context.Background(), time.Nanosecond)
	defer cancel()
	time.Sleep(time.Millisecond)

	_, err = HashMatched(cctx, fsys, report, 4)
	if err == nil {
		t.Fatal("expected an error from HashMatched with an already-expired context")
	}
}

func TestHashMatched_KnownDigest(t *testing.T) {
	// SHA-256("hello") is a well-known constant, giving us a hard-coded
	// oracle instead of only comparing digests against each other.
	const wantHello = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
	fsys := fstest.MapFS{"a.txt": {Data: []byte("hello")}}
	report, err := Walk(context.Background(), fsys, ".", WalkOptions{})
	if err != nil {
		t.Fatalf("Walk: %v", err)
	}
	digests, err := HashMatched(context.Background(), fsys, report, 2)
	if err != nil {
		t.Fatalf("HashMatched: %v", err)
	}
	if digests["a.txt"] != wantHello {
		t.Fatalf("digest = %s, want %s", digests["a.txt"], wantHello)
	}
}
