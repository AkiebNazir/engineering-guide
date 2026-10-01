// Package filestore is the reference implementation of Problem 06: an
// atomic file store built on the temp-file + fsync + rename pattern. Read
// the header comment in ../explanation/06_atomic_file_store_explanation.go
// first — it has the full spec and rationale; this file focuses on *how*
// and *why* each line is written the way it is.
package filestore

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
)

// Store writes files atomically into a single fixed directory.
//
// We resolve dir to an absolute path once, in NewStore, rather than on every
// call. This matters because os.Open/os.Rename resolve relative paths
// against the process's *current* working directory, which — in a long-
// running service — could change (rare, but some frameworks os.Chdir during
// startup) or simply be ambiguous to reason about. Pinning to an absolute
// path at construction time makes the Store's behavior independent of any
// later Chdir and makes bugs reproducible regardless of caller cwd.
type Store struct {
	dir string
}

// NewStore returns a Store rooted at dir. dir must already exist and be a
// directory.
//
// We deliberately do NOT create the directory here (no MkdirAll): a store
// silently creating its own root on first use hides misconfiguration (wrong
// path, missing mount, typo) that's much cheaper to catch at startup than
// mid-write in production. Fail fast.
func NewStore(dir string) (*Store, error) {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return nil, fmt.Errorf("filestore: resolve abs path for %q: %w", dir, err)
	}

	info, err := os.Stat(abs)
	if err != nil {
		return nil, fmt.Errorf("filestore: stat store dir %q: %w", abs, err)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("filestore: %q is not a directory", abs)
	}

	return &Store{dir: abs}, nil
}

// WriteFile atomically replaces (or creates) <dir>/<name> with data.
//
// The core durability contract — readers never observe a partial write, and
// a crash never corrupts the destination — comes entirely from doing the
// work on a temp file and only exposing it to the world via one atomic
// rename. Every step before the rename is "invisible" to any other process;
// every step is either idempotent-safe to retry or cheap to clean up.
func (s *Store) WriteFile(ctx context.Context, name string, data []byte, perm os.FileMode) error {
	// Step 1: bail out early if the caller already canceled. Cheap check,
	// avoids doing any I/O at all for a doomed call.
	if err := ctx.Err(); err != nil {
		return err
	}

	destPath := filepath.Join(s.dir, name)

	// Step 2: create the temp file IN THE SAME DIRECTORY as the
	// destination. This is the single most important correctness detail in
	// this whole file: os.Rename (POSIX rename(2)) is only guaranteed
	// atomic when source and destination are on the same filesystem. A temp
	// file under os.TempDir() is very often a different mount (tmpfs vs the
	// real disk, or a different volume entirely), which makes Rename either
	// fail outright (EXDEV, "invalid cross-device link") or — in libraries
	// that "helpfully" paper over that — silently fall back to a
	// non-atomic copy-then-delete, which reintroduces every problem this
	// pattern exists to solve.
	//
	// The "." prefix hides the temp file from casual `ls`; the "*" is
	// replaced by os.CreateTemp with a random string, so concurrent writers
	// for the same `name` never collide on the temp path even though they
	// share a directory.
	pattern := fmt.Sprintf(".%s.tmp-*", name)
	tmp, err := os.CreateTemp(s.dir, pattern)
	if err != nil {
		return fmt.Errorf("filestore: create temp file for %q: %w", name, err)
	}
	tmpPath := tmp.Name()

	// From here on, ANY early return must clean up tmpPath. We centralize
	// that with a closure instead of duplicating os.Remove at every return
	// site — the classic Go "defer + named error checks" idiom is overkill
	// here because we want cleanup to run only on the failure paths (a
	// successful rename makes tmpPath = destPath, and removing that would
	// delete the file we just published). So we use an explicit "did we
	// succeed" flag instead of defer.
	succeeded := false
	defer func() {
		if !succeeded {
			// Best-effort: a cleanup failure must never mask the original
			// error, and there's nothing more useful to do than log it in
			// a real system (slog.Warn here). We swallow it deliberately.
			_ = os.Remove(tmpPath)
		}
	}()

	// Step 3: write the full payload. tmp.Write on an *os.File does not
	// short-write for []byte in practice on POSIX (it loops internally
	// until done or an error), but we defensively check the returned count
	// against len(data) anyway — cheap, and correct if that assumption ever
	// changes (e.g. wrapping tmp in something else later).
	n, err := tmp.Write(data)
	if err != nil {
		tmp.Close()
		return fmt.Errorf("filestore: write temp file for %q: %w", name, err)
	}
	if n != len(data) {
		tmp.Close()
		return fmt.Errorf("filestore: short write for %q: wrote %d of %d bytes", name, n, len(data))
	}

	// Step 4: fsync the temp file's data. This is the step that actually
	// buys durability: Close() alone does NOT force a flush to durable
	// storage on most OSes — the kernel is free to keep dirty pages in the
	// page cache and write them back later on its own schedule. Sync()
	// issues fsync(2), which blocks until the data (and, per POSIX, the
	// file's metadata) has reached the storage device. Skip this and a
	// power cut between Close and the kernel's own writeback can lose data
	// that Write already returned success for.
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		return fmt.Errorf("filestore: fsync temp file for %q: %w", name, err)
	}

	// Step 5: set the final permission bits on the TEMP file before
	// renaming, not after. os.CreateTemp always creates files at mode 0600
	// regardless of what the caller wants for the final artifact. Chmod-ing
	// the temp file means the rename step atomically publishes both the
	// new content AND the new permissions together — there's no window
	// where the destination exists with the wrong mode. If we instead
	// renamed first and chmod'd second, a reader (or another writer racing
	// us) could observe the file at the old/wrong permission bits for a
	// brief moment after it's already "live" under its real name.
	if err := tmp.Chmod(perm); err != nil {
		tmp.Close()
		return fmt.Errorf("filestore: chmod temp file for %q: %w", name, err)
	}

	if err := tmp.Close(); err != nil {
		return fmt.Errorf("filestore: close temp file for %q: %w", name, err)
	}

	// Step 6: re-check cancellation before the rename. The write+fsync
	// above can be slow for large payloads; if the caller's context died
	// while we were doing that work, honor it now rather than publishing a
	// file the caller no longer wants written. (We already have the fully
	// durable temp file on disk either way — its cleanup happens in the
	// deferred Remove above since succeeded is still false.)
	if err := ctx.Err(); err != nil {
		return err
	}

	// Step 7: the atomic publish. POSIX guarantees rename(2) within one
	// filesystem is atomic: any process that opens destPath at any instant
	// sees either the complete old file or the complete new file, never a
	// mix, a truncated file, or ENOENT in between (if destPath already
	// existed). This is the entire reason this pattern exists.
	if err := os.Rename(tmpPath, destPath); err != nil {
		return fmt.Errorf("filestore: rename %q to %q: %w", tmpPath, destPath, err)
	}
	succeeded = true // tmpPath no longer exists under that name; don't try to remove it

	// Step 8: fsync the containing directory. A rename is, from the
	// filesystem's point of view, a metadata update to the directory (the
	// entry now points at a different inode). That metadata change can
	// itself be lost on crash if the directory's own dirty metadata hasn't
	// been flushed — on some filesystems/mount options you can end up,
	// after a hard crash right after a successful rename() call returns,
	// with the new file's *data* durably on disk but the directory *entry*
	// still stale. fsyncing the directory fd closes that gap. This is the
	// step almost every hand-rolled "atomic write" in the wild skips.
	dir, err := os.Open(s.dir)
	if err != nil {
		// The rename already succeeded and is durable-enough on most
		// mainstream filesystems/configurations in practice; we still
		// report the error since we promised directory durability, but we
		// do NOT roll back the rename — the new content is live and
		// correct, just not maximally crash-safe.
		return fmt.Errorf("filestore: open dir %q for fsync: %w", s.dir, err)
	}
	syncErr := dir.Sync()
	closeErr := dir.Close()
	if syncErr != nil {
		return fmt.Errorf("filestore: fsync dir %q: %w", s.dir, syncErr)
	}
	if closeErr != nil {
		return fmt.Errorf("filestore: close dir %q: %w", s.dir, closeErr)
	}

	return nil
}

// ReadFile reads <dir>/<name> in full.
//
// We wrap the error with %w rather than returning os.ReadFile's error
// directly so callers get a message that identifies which store/name failed
// while errors.Is(err, os.ErrNotExist) still works — %w preserves the chain,
// unlike %v or manual string formatting.
func (s *Store) ReadFile(name string) ([]byte, error) {
	data, err := os.ReadFile(filepath.Join(s.dir, name))
	if err != nil {
		return nil, fmt.Errorf("filestore: read %q: %w", name, err)
	}
	return data, nil
}

/*
BEST PRACTICES DEMONSTRATED
  - Fail fast at construction (NewStore validates the directory exists
    rather than lazily discovering problems on first write).
  - Every error is wrapped with %w and enough context to know which
    operation and which logical file failed, without leaking raw
    implementation details the caller shouldn't parse.
  - Cleanup-on-failure is centralized in one deferred closure guarded by a
    boolean, rather than repeated at every early return — reduces the
    chance of a future edit adding a new failure path that forgets to clean
    up.
  - Permissions are applied to the temp file BEFORE the publishing rename,
    so the rename atomically publishes content and mode together.
  - Context is checked both before starting (cheap, avoids wasted I/O) and
    again after the expensive write+fsync but before the also-somewhat-
    expensive rename+directory-fsync — this bounds how much "pointless" work
    a canceled call can do without adding checks inside tight loops.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - copy+truncate (write into the existing file in place, O_TRUNC): faster,
    no rename needed, but NOT atomic — a reader can observe a truncated or
    partially-written file, and a crash mid-write corrupts the only copy.
    Never use this for anything that must survive concurrent readers or
    crashes.
  - Write-ahead log + separate compaction (what real databases like SQLite
    and etcd's boltdb do): higher throughput for many small updates because
    you're appending instead of rewriting the whole file, but much higher
    implementation complexity (log replay, checkpointing, corruption
    detection). Appropriate once you're doing high-frequency small updates
    to a large object, not appropriate for "write this whole config file".
  - Skipping the directory fsync: saves a syscall and is what most
    hand-rolled implementations do; the failure window it leaves open is
    narrow (needs a crash in the brief window after rename returns, on a
    filesystem/mount configuration where directory metadata isn't
    synchronously durable) but real — worth paying for anything you'd call
    "the source of truth" (ledgers, cluster state, credentials), arguably
    skippable for caches/derived data you can always regenerate.
  - Locking: this implementation relies on os.CreateTemp's random suffix and
    the atomicity of rename to make concurrent WriteFile calls for the SAME
    name safe without an explicit mutex — the last rename to complete wins,
    and every writer's temp file is independent. If you need
    read-modify-write semantics (read current value, compute a new one,
    write it back) instead of "write this blob", you need additional
    coordination (a mutex, or optimistic concurrency — see Problem 10).

TESTING NOTES
  - The test file races many concurrent WriteFile calls (increasing-size
    payloads) against concurrent ReadFile calls and asserts every observed
    read is one of the lengths that was actually, fully written — this is
    the property-based way to catch "torn read" bugs without needing to
    literally kill the process mid-write.
  - `go test -race ./06_atomic_file_store/...` is mandatory given the
    goroutine fan-out in the concurrency test.
  - True crash-safety (does fsync actually survive a real power loss) is not
    testable in a normal unit test — that requires tools like ALICE/dm-flakey
    or manually killing a VM, out of scope here, but worth knowing exists.

FAILURE MODES TO KNOW ABOUT
  - Disk full during Write or Sync: WriteFile returns an error, temp file is
    cleaned up, destination is untouched — safe, just out of space.
  - Process killed (SIGKILL) between successful Rename and the directory
    fsync: on most modern Linux filesystems (ext4 with default
    data=ordered, XFS, btrfs) in practice the rename survives; this is the
    narrow theoretical gap the directory fsync closes, at the cost of one
    extra syscall per write.
  - Cross-device rename (EXDEV): only possible here if the caller passes a
    `name` containing path separators that escape s.dir onto another mount,
    or if s.dir itself is a union/overlay filesystem boundary — worth a
    stretch-goal validation on `name` (reject separators) in a hardened
    version.
*/
