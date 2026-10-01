/*
Package filestore — Atomic File Store (Problem 06)

WHAT WE'RE BUILDING

A small library that writes files to disk *atomically*: readers never observe a
partially-written file, and a crash (power loss, SIGKILL, panic mid-write) never
leaves a corrupt file where a good one used to be. This is the pattern behind
every "safe config write", local database WAL checkpoint, and CLI tool that
edits a file in place (kubectl config, git's index, Terraform state, etc).

# WHY IT MATTERS IN REAL SYSTEMS

Naively doing:

	f, _ := os.Create(path)
	f.Write(data)
	f.Close()

has two failure windows:
 1. Between truncate-on-create and the write completing, any concurrent
    reader (or a crash) sees a zero-length or half-written file.
 2. Even after Close returns, the data may still be sitting in the OS page
    cache, not on durable storage — a power cut can lose it entirely, or
    leave the file's metadata (size) updated but content stale/torn on some
    filesystems.

The standard fix, used by etcd, Consul, containerd, and most Unix editors
(vim, sed -i) is the "temp file + fsync + rename" pattern:

 1. Create a temp file in the SAME DIRECTORY as the destination (same
    filesystem/mount — rename() is only atomic within one filesystem).
 2. Write the full contents to the temp file.
 3. fsync the temp file's data to disk (forces the write out of the page
    cache onto durable storage).
 4. Close the temp file.
 5. rename(tempPath, destPath) — POSIX guarantees this is atomic: any
    concurrent open() of destPath sees either the fully-old or fully-new
    file, never a mix, never a gap.
 6. fsync the CONTAINING DIRECTORY. On most POSIX filesystems the rename
    itself is a metadata change to the directory, which can also be lost on
    crash unless the directory's fd is fsynced. Without this step you can
    legitimately end up, after a crash, with the new file's data safely on
    disk but the directory entry still pointing at the old inode (or a
    torn/missing entry) — the "rename didn't survive the crash" bug class.

CONCEPTS COVERED
  - os.CreateTemp for collision-free temp file naming
  - File.Sync (fsync) and why Close() alone is not durable
  - os.Rename atomicity guarantees and its same-filesystem requirement
  - Directory fsync (opening a directory with os.Open and calling Sync)
  - File permission handling (temp files default to 0600; we need to set the
    final mode explicitly since CreateTemp doesn't respect a requested mode)
  - Cleanup-on-error (must remove the temp file if anything fails before
    rename, or you leak files on every error path)
  - context.Context cancellation mid-write
  - Concurrency safety: multiple goroutines calling Write concurrently for
    the same store must not corrupt each other's temp files or race on the
    final rename

REQUIREMENTS / SPEC

Implement a `Store` type bound to a directory, with:

	NewStore(dir string) (*Store, error)
	    Validates dir exists and is a directory. Returns *Store.

	(*Store) WriteFile(ctx context.Context, name string, data []byte, perm os.FileMode) error
	    Atomically writes `data` to <dir>/<name> using the temp+fsync+rename
	    pattern described above. Must:
	      - Create the temp file in the same directory as the target (NOT
	        os.TempDir()).
	      - Respect ctx cancellation: check ctx.Err() before starting and
	        before the (relatively slow) fsync/rename steps; if canceled,
	        clean up the temp file and return ctx.Err().
	      - Set the final file's permission bits to `perm` (temp files are
	        created 0600 by os.CreateTemp; you must Chmod before or after
	        rename to get the caller's requested mode onto the final path).
	      - fsync the temp file before renaming.
	      - fsync the containing directory after renaming.
	      - On ANY error prior to a successful rename, remove the leftover
	        temp file (best-effort — log/ignore removal errors, don't mask the
	        original error).
	      - Be safe for concurrent callers writing DIFFERENT names in the same
	        store (they must not interfere with each other).

	(*Store) ReadFile(name string) ([]byte, error)
	    Plain read of <dir>/<name>. Wrap os.ErrNotExist-producing errors so
	    callers can `errors.Is(err, os.ErrNotExist)`.

ACCEPTANCE CRITERIA
  - WriteFile never leaves a *.tmp* file behind on success.
  - A concurrent reader opening the destination path during a WriteFile call
    always sees either the fully old content or the fully new content — this
    is testable by racing many goroutines writing increasing-size payloads
    against a goroutine repeatedly opening+reading the file, and asserting
    the length always matches a length that was actually written.
  - Canceling ctx before WriteFile completes returns context.Canceled/
    DeadlineExceeded and leaves the destination file untouched (old content
    or nonexistent), with no leaked temp file.
  - Final file has the requested permission bits (masked by umask, as usual
    on POSIX).
  - `go test -race` is clean.
*/
package filestore

import (
	"context"
	"os"
)

// Store writes files atomically into a single fixed directory.
type Store struct {
	// TODO: store the target directory (absolute path is safest — resolve
	// with filepath.Abs in NewStore so later os.Open(s.dir) calls are
	// unambiguous regardless of the process's current working directory).
}

// NewStore returns a Store rooted at dir. dir must already exist and be a
// directory; NewStore does not create it.
func NewStore(dir string) (*Store, error) {
	// TODO:
	//  1. os.Stat(dir); if error, wrap and return.
	//  2. Confirm it's a directory (info.IsDir()); if not, return a clear
	//     error.
	//  3. Resolve to an absolute path (filepath.Abs) and store it.
	panic("TODO: implement NewStore")
}

// WriteFile atomically replaces (or creates) <dir>/<name> with data, using
// the temp-file + fsync + rename pattern. perm sets the final file's mode.
//
// See the package doc comment above for the full durability contract this
// must satisfy.
func (s *Store) WriteFile(ctx context.Context, name string, data []byte, perm os.FileMode) error {
	// TODO:
	//  1. Check ctx.Err() up front — bail early if already canceled.
	//  2. os.CreateTemp(s.dir, ".<name>.tmp-*") to get a sibling temp file
	//     with a random suffix (collision-free for concurrent writers).
	//  3. Write data to it in full (Write can short-write; loop or use
	//     io.Copy/Write with a check, though for a single []byte a direct
	//     tmp.Write(data) length-checked against len(data) is enough).
	//  4. tmp.Sync() — fsync the file data.
	//  5. tmp.Chmod(perm) (or os.Chmod after close — either works, but doing
	//     it before Close means one fewer syscall pair) then tmp.Close().
	//  6. Check ctx.Err() again before the rename (cheap insurance against
	//     racing a long write against a very tight deadline).
	//  7. os.Rename(tmpPath, destPath).
	//  8. Open the containing directory and Sync() it, then Close() it.
	//  9. On any error in steps 2-7, os.Remove(tmpPath) best-effort before
	//     returning the original error.
	panic("TODO: implement WriteFile")
}

// ReadFile reads <dir>/<name> in full. Errors that indicate the file does
// not exist must satisfy errors.Is(err, os.ErrNotExist).
func (s *Store) ReadFile(name string) ([]byte, error) {
	// TODO: os.ReadFile(filepath.Join(s.dir, name)), wrapping errors with
	// fmt.Errorf("%w: ...") so os.ErrNotExist is preserved through errors.Is.
	panic("TODO: implement ReadFile")
}

/*
HINTS
  - filepath.Join(s.dir, name) for both the temp file's directory argument
    and the final destination — never write into os.TempDir(), it's very
    likely a different filesystem/mount, which makes os.Rename fail with
    "invalid cross-device link" (EXDEV) instead of being atomic.
  - os.CreateTemp's pattern argument supports a "*" wildcard that gets
    replaced with a random string; put it in the middle of the name (e.g.
    ".config.json.tmp-*") so the temp file sorts near the real file and is
    easy to spot/clean up if something goes wrong.
  - Don't forget: os.CreateTemp files are mode 0600 regardless of the
    destination's desired permissions — you must Chmod explicitly.
  - The directory fsync step is the one everyone forgets. It matters: without
    it, a crash right after rename() can lose the directory-entry update on
    some filesystems/configurations even though the file's own data is safe.

COMMON PITFALLS
  - Writing the temp file to os.TempDir() (different filesystem -> rename
    fails or, worse, silently falls back to non-atomic copy+delete on some
    libraries).
  - Forgetting to clean up the temp file on error paths — leaks accumulate
    silently in the target directory over time.
  - Calling Close() and assuming durability — Close() does not imply fsync
    on most OSes; you must call Sync() explicitly before renaming.
  - Chmod-ing after rename on a path that no longer matches perm because a
    concurrent writer already replaced it with a *different* new version —
    prefer chmod-then-rename (chmod the temp file, so the rename is what
    publishes the final permission atomically with the content).
  - Ignoring ctx cancellation entirely, or checking it only once at the very
    top (a write of a large payload can take a while; check again before the
    slow fsync/rename phase too).

STRETCH GOALS
  - Add a `WriteReader(ctx, name string, r io.Reader, perm) error` variant
    that streams into the temp file via io.Copy instead of taking a []byte,
    for large payloads that shouldn't be buffered fully in memory.
  - Add an optional checksum: write a sidecar `<name>.sha256` atomically
    alongside the content (two atomic writes — think about what "atomic" now
    means for the *pair*, and document the limitation).
  - Support Linux's renameat2(RENAME_NOREPLACE) via golang.org/x/sys/unix to
    offer a CreateFileExclusive that fails if the destination already
    exists, instead of always overwriting.
  - Benchmark WriteFile with and without the directory fsync to see the real
    cost of durability (b.ReportMetric with ns/op) — discuss when you'd skip
    it (e.g. bulk-loading data you can regenerate) vs never skip it (financial
    ledgers, embedded databases).
*/
