/*
Package fswalk — Filesystem Walker (Problem 07)

WHAT WE'RE BUILDING

A small library that walks a directory tree — real disk, an embed.FS, a zip
archive, or an in-memory fake — and produces a filtered, aggregated report
(matching files, total size, per-extension counts) without ever coupling to
os.* directly. The whole point of this problem is the abstraction: everything
is written against io/fs.FS, so the exact same code walks a live directory,
a fake in-memory tree built with testing/fstest, or a tar/zip archive opened
as an fs.FS, with zero changes.

# WHY IT MATTERS IN REAL SYSTEMS

Before Go 1.16, "walk a directory" meant filepath.Walk, which is hardwired to
the OS filesystem — you could not point it at an embedded asset bundle, a
zip file serving a web app's static assets, or a synthetic tree in a unit
test without spinning up real files on disk (slow, flaky in parallel test
runs, awkward permissions/cleanup). io/fs.FS decouples "a tree of files" from
"the OS filesystem" as an interface, and fs.WalkDir (its filepath.WalkDir
counterpart) walks anything that implements it. This is the same pattern
behind embed.FS (compile assets into the binary), http.FileServer(http.FS(...)),
archive/zip's zip.Reader (which implements fs.FS), and testing/fstest.MapFS
for hermetic, no-disk-I/O directory-tree tests.

CONCEPTS COVERED
  - io/fs.FS, fs.DirEntry, fs.FileInfo — the read-only filesystem abstraction
  - fs.WalkDir vs the deprecated filepath.Walk (DirEntry avoids a Stat call
    per entry that filepath.Walk's os.FileInfo-based callback forces)
  - fs.SkipDir / fs.SkipAll for pruning subtrees or stopping early
  - Symlink handling: fs.WalkDir does NOT follow symlinks (it reports them as
    files via Lstat-like semantics) — walking into them yourself requires
    explicit fs.Stat + recursion and a visited-set to avoid cycles
  - testing/fstest.MapFS for building synthetic trees in tests, and
    fstest.TestFS for validating an fs.FS implementation's contract
  - Concurrency: fanning work out per matched file (e.g. hashing) while the
    walk itself stays single-threaded (fs.WalkDir is not safe to parallelize
    directly — you parallelize the *processing*, not the walk)
  - context cancellation threaded through a long walk over a huge tree

REQUIREMENTS / SPEC

Implement, against io/fs.FS:

	type Result struct {
	    Path string // slash-separated path relative to the FS root
	    Size int64
	}

	type Report struct {
	    Files      []Result       // every file that matched the filter, sorted by Path
	    TotalSize  int64          // sum of Size across matched files
	    ByExt      map[string]int // extension (including the leading '.', "" for none) -> count
	    SkippedDir int            // count of directories pruned via a filter's fs.SkipDir
	}

	type Filter func(path string, d fs.DirEntry) bool
	    Returns true to include a regular file in the report. Called only for
	    files, not directories (directory pruning is a separate mechanism,
	    see WalkOptions.PruneDir below).

	type WalkOptions struct {
	    Filter      Filter                        // nil means "include everything"
	    PruneDir    func(path string, d fs.DirEntry) bool // true => skip this dir's subtree entirely
	    FollowSymlinks bool                        // see spec below; default false
	}

	func Walk(ctx context.Context, fsys fs.FS, root string, opts WalkOptions) (Report, error)
	    Walks fsys starting at root using fs.WalkDir. For every directory,
	    calls PruneDir (if non-nil); if it returns true, skip that whole
	    subtree (fs.SkipDir) and increment Report.SkippedDir. For every
	    regular file, calls Filter (if non-nil); if it returns true (or
	    Filter is nil), add a Result to the report. Must check ctx.Err()
	    on each visited entry and abort the walk early (returning ctx.Err())
	    if canceled — a walk over a huge tree must be interruptible.
	    Report.Files must be returned sorted by Path (fs.WalkDir already
	    visits in lexical order per directory, but don't rely on incidental
	    ordering here — state explicitly why it's already sorted or sort
	    defensively).

	func HashMatched(ctx context.Context, fsys fs.FS, report Report, workers int) (map[string]string, error)
	    Given a Report (from Walk), computes a SHA-256 hex digest for every
	    matched file's contents, using `workers` goroutines processing the
	    file list concurrently (a worker pool — bounded fan-out, not one
	    goroutine per file). Returns path -> hex digest. Must respect ctx
	    cancellation and propagate the first error encountered (use
	    golang.org/x/sync/errgroup or an equivalent hand-rolled pattern).

ACCEPTANCE CRITERIA
  - Works identically against os.DirFS(dir) (real disk, via t.TempDir()) and
    fstest.MapFS (synthetic, no disk I/O) — the test suite must exercise both
    to prove the abstraction actually decouples from the OS.
  - PruneDir correctly skips an entire subtree (files inside a pruned
    directory never appear in Report.Files, and SkippedDir counts it once,
    not once per descendant).
  - A canceled context stops the walk promptly and returns a context error,
    not a partial success.
  - HashMatched with workers=1 and workers=N produce identical digests for
    the same input (correctness must not depend on concurrency level).
  - go test -race is clean for HashMatched's worker pool.

Read the HINTS and PITFALLS at the bottom before opening the solution file.
*/
package fswalk

import (
	"context"
	"io/fs"
)

// Result is one matched file's relative path and size.
type Result struct {
	Path string
	Size int64
}

// Report aggregates the outcome of a Walk call.
type Report struct {
	Files      []Result
	TotalSize  int64
	ByExt      map[string]int
	SkippedDir int
}

// Filter decides whether a regular file belongs in the Report. Called only
// for files (not directories). A nil Filter means "include everything".
type Filter func(path string, d fs.DirEntry) bool

// WalkOptions configures a Walk call.
type WalkOptions struct {
	// Filter selects which regular files are included. nil = include all.
	Filter Filter
	// PruneDir, if non-nil and returning true for a directory, skips that
	// directory's entire subtree (files and nested dirs) without visiting
	// any of it.
	PruneDir func(path string, d fs.DirEntry) bool
	// FollowSymlinks controls whether symlinked directories are recursed
	// into. fs.WalkDir does not do this natively; TODO in the solution
	// explains the approach and its cycle-safety requirement.
	FollowSymlinks bool
}

// Walk walks fsys starting at root, applying opts, and returns an aggregated
// Report. See the package doc comment for the full spec.
func Walk(ctx context.Context, fsys fs.FS, root string, opts WalkOptions) (Report, error) {
	// TODO:
	//  1. Initialize Report{ByExt: map[string]int{}}.
	//  2. fs.WalkDir(fsys, root, func(path string, d fs.DirEntry, err error) error { ... }).
	//  3. Inside the callback: check ctx.Err() first; if non-nil, return it
	//     (fs.WalkDir propagates any non-nil, non-SkipDir error out of
	//     WalkDir itself, aborting the walk).
	//  4. If err != nil (fs.WalkDir surfaces errors from reading a
	//     directory here), decide whether to wrap-and-abort or skip; for
	//     this exercise, wrap and abort.
	//  5. If d.IsDir(): call opts.PruneDir if set; if it returns true,
	//     increment SkippedDir and return fs.SkipDir.
	//  6. If !d.IsDir(): call opts.Filter if set (else include); if
	//     included, d.Info() for size, append a Result, update TotalSize
	//     and ByExt[filepath.Ext-equivalent — use path.Ext since fs.FS
	//     paths are always slash-separated per the io/fs contract].
	//  7. After WalkDir returns, sort report.Files by Path (sort.Slice) —
	//     state in a comment why this is likely already true but sorting
	//     defensively costs little and removes any doubt.
	panic("TODO: implement Walk")
}

// HashMatched computes SHA-256 digests for every file in report.Files,
// fanning the work out across `workers` goroutines. Returns path -> hex
// digest. Must be safe to run with -race and must respect ctx cancellation.
func HashMatched(ctx context.Context, fsys fs.FS, report Report, workers int) (map[string]string, error) {
	// TODO:
	//  1. Guard workers < 1 -> treat as 1.
	//  2. Build a channel of work items (report.Files) and fan `workers`
	//     goroutines out to consume it, each opening fsys.Open(path),
	//     streaming through sha256.New() + io.Copy, and writing into a
	//     shared map GUARDED BY A MUTEX (or send results back over a
	//     results channel and have the single caller goroutine own the map
	//     — preferred, avoids a mutex entirely).
	//  3. Use golang.org/x/sync/errgroup.WithContext(ctx) (already in
	//     go.mod) to get first-error propagation and automatic goroutine
	//     bookkeeping instead of hand-rolling sync.WaitGroup + error
	//     channel.
	//  4. Each worker must check ctx.Err() (or rely on the errgroup's
	//     derived context / g.Go returning early) so a cancellation stops
	//     new work promptly instead of draining the whole channel first.
	panic("TODO: implement HashMatched")
}

/*
HINTS
  - fs.FS paths are ALWAYS slash-separated and never have a leading "/" or a
    "." root component beyond the literal string "." for the root itself —
    use the "path" package (path.Ext, path.Join), never "path/filepath",
    when manipulating fs.FS paths. filepath is for OS paths and uses
    OS-specific separators, which silently misbehaves on Windows if you feed
    it fs.FS paths.
  - fs.WalkDir gives you an fs.DirEntry, not an fs.FileInfo — call d.Info()
    only when you actually need size/mtime/mode, since some fs.FS
    implementations can answer DirEntry questions (IsDir, Type, Name)
    without a syscall, but Info() may require one.
  - Returning fs.SkipDir from the callback when d.IsDir() skips that
    directory's subtree; returning it when d is a *file* just skips the rest
    of that file's siblings in some walkers historically, but per current
    stdlib docs, returning SkipDir for a non-directory skips the remaining
    files in the containing directory — avoid this ambiguity by only ever
    returning SkipDir when d.IsDir() is true.
  - fs.SkipAll (Go 1.20+) stops the entire walk immediately, useful for
    "found what I need, stop" cases — not required by this spec but worth
    knowing.

COMMON PITFALLS
  - Using filepath.Join/filepath.Ext on fs.FS paths — breaks on Windows
    because filepath uses "\" there while fs.FS always uses "/".
  - Following symlinks naively (os.DirFS's Open follows symlinks for the
    final path component but fs.WalkDir's directory *traversal* does not
    descend into symlinked directories on its own) without cycle detection —
    a self-referential symlink loop will recurse forever if you bolt on
    manual recursion for FollowSymlinks without tracking visited real paths
    (via os.Lstat + a visited-inode set).
  - Forgetting that fs.WalkDir calls your function for the root itself first
    (path == root, often "."), which is a directory, not a file — a Filter
    that assumes every callback invocation is a file will panic or
    misbehave on the very first call.
  - Building the worker pool in HashMatched with an unbounded number of
    goroutines (one per file) instead of a fixed worker count — defeats the
    purpose of bounding concurrency for, e.g., 500k small files where
    goroutine overhead and fd pressure both matter.
  - Sharing a map across HashMatched goroutines without synchronization —
    a classic data race that only -race reliably catches.

STRETCH GOALS
  - Add a Depth-limited walk (max recursion depth from root).
  - Add support for archive/zip.Reader as the fs.FS (zip.Reader implements
    fs.FS natively) and confirm the exact same Walk/HashMatched code works
    against a zip archive with zero changes.
  - Add a streaming variant that reports Results over a channel as they're
    found instead of buffering the whole Report, for trees too large to hold
    in memory at once.
  - Benchmark Walk against filepath.WalkDir(directly on os) to quantify the
    fs.FS abstraction's overhead (should be near-zero — it's an interface
    dispatch, not a different algorithm).
*/
