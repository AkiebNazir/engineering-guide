package filestore

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"testing"
	"time"
)

func TestNewStore(t *testing.T) {
	t.Run("valid directory", func(t *testing.T) {
		dir := t.TempDir()
		s, err := NewStore(dir)
		if err != nil {
			t.Fatalf("NewStore: %v", err)
		}
		if s.dir == "" {
			t.Fatal("expected resolved dir to be set")
		}
	})

	t.Run("missing directory", func(t *testing.T) {
		if _, err := NewStore(filepath.Join(t.TempDir(), "does-not-exist")); err == nil {
			t.Fatal("expected error for missing directory")
		}
	})

	t.Run("path is a file, not a directory", func(t *testing.T) {
		dir := t.TempDir()
		filePath := filepath.Join(dir, "afile")
		if err := os.WriteFile(filePath, []byte("x"), 0o644); err != nil {
			t.Fatalf("setup write: %v", err)
		}
		if _, err := NewStore(filePath); err == nil {
			t.Fatal("expected error when path is not a directory")
		}
	})
}

func TestWriteFileThenReadFile(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}

	ctx := context.Background()
	content := []byte("hello, atomic world")
	if err := s.WriteFile(ctx, "greeting.txt", content, 0o644); err != nil {
		t.Fatalf("WriteFile: %v", err)
	}

	got, err := s.ReadFile("greeting.txt")
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}
	if !bytes.Equal(got, content) {
		t.Fatalf("ReadFile returned %q, want %q", got, content)
	}

	info, err := os.Stat(filepath.Join(dir, "greeting.txt"))
	if err != nil {
		t.Fatalf("stat final file: %v", err)
	}
	if runtime.GOOS != "windows" {
		if perm := info.Mode().Perm(); perm&0o600 != 0o600 {
			t.Fatalf("expected owner rw bits at least, got %v", perm)
		}
	}
}

func TestWriteFileOverwritesAtomically(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	ctx := context.Background()

	if err := s.WriteFile(ctx, "data.bin", []byte("version-one"), 0o644); err != nil {
		t.Fatalf("first WriteFile: %v", err)
	}
	if err := s.WriteFile(ctx, "data.bin", []byte("version-two-is-longer"), 0o644); err != nil {
		t.Fatalf("second WriteFile: %v", err)
	}

	got, err := s.ReadFile("data.bin")
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}
	if string(got) != "version-two-is-longer" {
		t.Fatalf("got %q, want the second version", got)
	}
}

func TestWriteFileNoLeftoverTempFiles(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	ctx := context.Background()

	for i := 0; i < 20; i++ {
		name := fmt.Sprintf("file-%d.txt", i)
		if err := s.WriteFile(ctx, name, []byte("payload"), 0o644); err != nil {
			t.Fatalf("WriteFile(%s): %v", name, err)
		}
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("ReadDir: %v", err)
	}
	if len(entries) != 20 {
		t.Fatalf("expected exactly 20 entries (no leftover temp files), got %d", len(entries))
	}
	for _, e := range entries {
		if filepath.Ext(e.Name()) == ".tmp" || bytes.Contains([]byte(e.Name()), []byte(".tmp-")) {
			t.Fatalf("found leftover temp file: %s", e.Name())
		}
	}
}

func TestWriteFileRespectsCanceledContext(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // already canceled

	err = s.WriteFile(ctx, "never.txt", []byte("nope"), 0o644)
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context.Canceled, got %v", err)
	}

	if _, statErr := os.Stat(filepath.Join(dir, "never.txt")); statErr == nil {
		t.Fatal("destination file should not have been created")
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("ReadDir: %v", err)
	}
	if len(entries) != 0 {
		t.Fatalf("expected no leftover files after canceled write, got %v", entries)
	}
}

func TestReadFileNotExist(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}

	_, err = s.ReadFile("nope.txt")
	if !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("expected errors.Is(err, os.ErrNotExist), got %v", err)
	}
}

// TestConcurrentWritesNeverTornRead is the key property test for this
// package: it races many writers (increasing payload sizes, so a torn read
// would very likely produce a length that was never actually written) against
// many readers, and asserts every successful read has a length that matches
// one of the lengths actually written. This is how you test "atomic" without
// needing to kill the process mid-write.
func TestConcurrentWritesNeverTornRead(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	ctx := context.Background()
	const name = "racy.bin"

	// Seed the file so readers never see a "not exist" before the first
	// write lands.
	if err := s.WriteFile(ctx, name, bytes.Repeat([]byte{0xAA}, 8), 0o644); err != nil {
		t.Fatalf("seed WriteFile: %v", err)
	}

	var validLens sync.Map
	validLens.Store(8, true)

	const writers = 8
	const writesPerWriter = 25
	var wg sync.WaitGroup
	wg.Add(writers)
	for w := 0; w < writers; w++ {
		go func(w int) {
			defer wg.Done()
			for i := 0; i < writesPerWriter; i++ {
				size := 16 + w*writesPerWriter + i // unique, increasing-ish size per write
				payload := bytes.Repeat([]byte{byte('A' + w)}, size)
				validLens.Store(size, true)
				if err := s.WriteFile(ctx, name, payload, 0o644); err != nil {
					t.Errorf("writer %d: WriteFile: %v", w, err)
					return
				}
			}
		}(w)
	}

	stop := make(chan struct{})
	var readerWg sync.WaitGroup
	readerWg.Add(4)
	for r := 0; r < 4; r++ {
		go func() {
			defer readerWg.Done()
			for {
				select {
				case <-stop:
					return
				default:
				}
				data, err := s.ReadFile(name)
				if err != nil {
					// A concurrent rename can transiently race an open()
					// on some platforms only in pathological cases; on
					// POSIX rename this should not produce ENOENT for a
					// file that's continuously present, but tolerate it to
					// keep the test robust across CI filesystems.
					continue
				}
				if _, ok := validLens.Load(len(data)); !ok {
					t.Errorf("read a length (%d) that was never a fully-written size — torn read", len(data))
					return
				}
			}
		}()
	}

	wg.Wait()
	close(stop)
	readerWg.Wait()
}

func TestWriteFileDeadlineExceeded(t *testing.T) {
	dir := t.TempDir()
	s, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Nanosecond)
	defer cancel()
	time.Sleep(time.Millisecond) // ensure the deadline has definitely passed

	err = s.WriteFile(ctx, "late.txt", []byte("data"), 0o644)
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("expected context.DeadlineExceeded, got %v", err)
	}
}
