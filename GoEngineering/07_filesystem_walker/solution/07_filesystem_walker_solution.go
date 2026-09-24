// Package fswalk is the reference implementation of Problem 07: a directory
// walker built entirely on io/fs.FS so it works identically against a real
// OS directory, an in-memory testing/fstest.MapFS, or any other fs.FS
// implementation (embed.FS, zip.Reader, ...). Read the header comment in
// ../explanation/07_filesystem_walker_explanation.go first for the full
// spec and rationale.
package fswalk

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"io/fs"
	"path"
	"sort"

	"golang.org/x/sync/errgroup"
)

// Result is one matched file's relative (slash-separated) path and size.
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
// for files, never directories. A nil Filter includes everything.
type Filter func(path string, d fs.DirEntry) bool

// WalkOptions configures a Walk call.
type WalkOptions struct {
	Filter         Filter
	PruneDir       func(path string, d fs.DirEntry) bool
	FollowSymlinks bool
}

// Walk walks fsys starting at root using fs.WalkDir and returns an
// aggregated Report.
//
// Step 1: fs.WalkDir over filepath.WalkDir. fs.WalkDir works against the
// fs.FS abstraction, so this exact function walks os.DirFS(dir),
// fstest.MapFS, or a zip.Reader without modification — the entire point of
// this exercise. filepath.WalkDir only ever walks the real OS filesystem.
func Walk(ctx context.Context, fsys fs.FS, root string, opts WalkOptions) (Report, error) {
	report := Report{ByExt: make(map[string]int)}

	walkErr := fs.WalkDir(fsys, root, func(p string, d fs.DirEntry, err error) error {
		// Step 2: honor cancellation on every single node visited, not
		// just once at the top — a walk over a huge tree (millions of
		// files) must be interruptible mid-traversal, and this check is
		// cheap enough to pay per-node.
		if ctxErr := ctx.Err(); ctxErr != nil {
			return ctxErr
		}

		// Step 3: fs.WalkDir surfaces errors from reading a directory
		// (e.g. permission denied) through this callback rather than
		// aborting silently. We choose to wrap and abort the whole walk;
		// a "best effort, skip unreadable dirs" policy is a valid
		// alternative (see ALTERNATIVE APPROACHES below) but changes the
		// semantics callers must be able to rely on, so we keep the
		// stricter default here.
		if err != nil {
			return fmt.Errorf("fswalk: walk %q: %w", p, err)
		}

		// Step 4: directories go through PruneDir. Returning fs.SkipDir
		// from this callback ONLY when d.IsDir() is true is deliberate —
		// per the fs.WalkDir contract, returning SkipDir for a
		// *non-directory* entry skips the remaining siblings in that
		// entry's directory instead of a subtree, which is almost never
		// what's intended and is a well-known footgun.
		if d.IsDir() {
			if opts.PruneDir != nil && opts.PruneDir(p, d) {
				report.SkippedDir++
				return fs.SkipDir
			}
			return nil
		}

		// Step 5: only regular files are candidates for the report.
		// fs.WalkDir also visits non-regular non-dir entries (symlinks,
		// device files under a real OS fs.FS) as DirEntry with
		// Type()&ModeType != 0; we exclude those explicitly rather than
		// silently treating them as regular files with an ambiguous size.
		if d.Type().IsRegular() {
			if opts.Filter != nil && !opts.Filter(p, d) {
				return nil
			}

			info, err := d.Info()
			if err != nil {
				return fmt.Errorf("fswalk: stat %q: %w", p, err)
			}

			report.Files = append(report.Files, Result{Path: p, Size: info.Size()})
			report.TotalSize += info.Size()

			// Step 6: path.Ext, not filepath.Ext — fs.FS paths are
			// defined by the io/fs contract to always use "/" as the
			// separator regardless of the host OS, so filepath (which is
			// OS-separator-aware) would silently misparse paths on
			// Windows.
			report.ByExt[path.Ext(p)]++
		}

		return nil
	})
	if walkErr != nil {
		return Report{}, walkErr
	}

	// Step 7: sort defensively. fs.WalkDir already visits each directory's
	// children in lexical filename order (guaranteed by the io/fs.WalkDir
	// doc), and recurses depth-first, so Report.Files as appended above
	// is, in practice, already sorted lexically by path. We still sort
	// explicitly: relying on "the docs say entries are lexical per
	// directory" to imply "the fully-joined paths across the whole walk
	// are globally sorted" is a small but real inferential leap (it holds
	// for depth-first lexical traversal, but a future refactor — e.g.
	// batching or the FollowSymlinks stretch goal — could break the
	// invariant silently). A defensive sort.Slice is O(n log n) on data
	// that's already sorted (effectively O(n) in most sort
	// implementations) and removes all doubt for callers who depend on
	// the ordering guarantee in the spec.
	sort.Slice(report.Files, func(i, j int) bool {
		return report.Files[i].Path < report.Files[j].Path
	})

	return report, nil
}

// HashMatched computes a SHA-256 hex digest for every file in
// report.Files, fanning the work out across `workers` goroutines.
//
// Step 1: bound the worker count defensively — 0 or negative is a caller
// bug, not a reason to spin up zero workers and hang forever waiting on an
// empty pool.
func HashMatched(ctx context.Context, fsys fs.FS, report Report, workers int) (map[string]string, error) {
	if workers < 1 {
		workers = 1
	}

	type digestResult struct {
		path   string
		digest string
	}

	// Step 2: errgroup.WithContext over hand-rolled sync.WaitGroup +
	// error channel. errgroup gives us three things for free: the first
	// error from any goroutine is captured and returned by Wait(), the
	// derived ctx is canceled the moment any goroutine returns an error
	// (so sibling workers can stop pulling new work promptly), and Wait()
	// blocks until every launched goroutine has actually returned (no
	// leaked goroutines on early return).
	g, gCtx := errgroup.WithContext(ctx)

	work := make(chan Result)
	results := make(chan digestResult)

	// Step 3: producer goroutine feeds the work channel. It must also
	// respect gCtx so that if a worker fails, the producer doesn't block
	// forever trying to send the next item into a channel nobody is
	// reading from anymore.
	g.Go(func() error {
		defer close(work)
		for _, r := range report.Files {
			select {
			case work <- r:
			case <-gCtx.Done():
				return gCtx.Err()
			}
		}
		return nil
	})

	// Step 4: fixed pool of `workers` goroutines consuming `work`. Each
	// worker streams the file through sha256 via io.Copy rather than
	// reading the whole file into memory first — correct for files far
	// larger than available RAM, at the cost of one read pass (which we'd
	// need anyway to hash it).
	for i := 0; i < workers; i++ {
		g.Go(func() error {
			for {
				select {
				case r, ok := <-work:
					if !ok {
						return nil
					}
					digest, err := hashFile(fsys, r.Path)
					if err != nil {
						return err
					}
					select {
					case results <- digestResult{path: r.Path, digest: digest}:
					case <-gCtx.Done():
						return gCtx.Err()
					}
				case <-gCtx.Done():
					return gCtx.Err()
				}
			}
		})
	}

	// Step 5: single goroutine owns the output map, eliminating the need
	// for a mutex entirely — every write to `out` happens on this one
	// goroutine, so there is no shared-memory race by construction. This
	// is generally preferable to "N workers + a mutex-guarded map" because
	// it makes the absence of races structurally obvious rather than
	// something -race merely fails to catch during a particular run.
	out := make(map[string]string, len(report.Files))
	done := make(chan struct{})
	go func() {
		defer close(done)
		for res := range results {
			out[res.path] = res.digest
		}
	}()

	// Step 6: close `results` only after every worker has finished
	// writing to it, otherwise the collector goroutine above would exit
	// (range over a closed channel with data still coming) and future
	// sends would panic. We do this by waiting for g.Wait() to return in
	// a separate goroutine, since a direct g.Wait() call would block
	// before results is ever closed and the collector would never see
	// EOF, deadlocking everyone.
	waitErrCh := make(chan error, 1)
	go func() {
		err := g.Wait()
		close(results)
		waitErrCh <- err
	}()

	err := <-waitErrCh
	<-done // ensure the collector has drained `results` before we read `out`

	if err != nil {
		return nil, fmt.Errorf("fswalk: hash matched files: %w", err)
	}
	return out, nil
}

// hashFile streams fsys's file at p through SHA-256 without buffering the
// whole contents in memory.
func hashFile(fsys fs.FS, p string) (string, error) {
	f, err := fsys.Open(p)
	if err != nil {
		return "", fmt.Errorf("fswalk: open %q: %w", p, err)
	}
	defer f.Close()

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", fmt.Errorf("fswalk: hash %q: %w", p, err)
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

/*
BEST PRACTICES DEMONSTRATED
  - Every function is written against io/fs.FS, never os.* directly — the
    entire library is filesystem-implementation-agnostic, which is what
    makes it trivially testable with fstest.MapFS and reusable against
    embed.FS/zip.Reader without a rewrite.
  - path.* (not filepath.*) for all fs.FS path manipulation, since fs.FS
    paths are contractually slash-separated regardless of host OS.
  - fs.SkipDir is only ever returned for directory entries, avoiding the
    well-known "SkipDir on a file skips siblings, not a subtree" footgun.
  - HashMatched's worker pool uses a single-owner-goroutine pattern for the
    result map instead of a mutex — a structural (not just tested)
    guarantee against data races.
  - errgroup.WithContext for fan-out/fan-in: first-error propagation,
    automatic cancellation of sibling goroutines, and no leaked goroutines,
    all without hand-rolled bookkeeping.
  - ctx.Err() checked per-node inside the WalkDir callback, not just once
    up front, so cancellation lands promptly even on a very large tree.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - "Best effort" directory-read errors: instead of aborting the whole walk
    on a permission-denied subdirectory, some tools (e.g. `du`, `find`) log
    a warning and continue. That's a legitimate choice for
    disk-usage-style tools but changes the caller contract from "you get a
    complete report or an error" to "you get a possibly-partial report" —
    worth making an explicit opt-in flag (e.g. `SkipUnreadableDirs bool`)
    rather than silently swallowing errors.
  - Mutex-guarded shared map instead of a single-owner collector goroutine
    in HashMatched: simpler to write, functionally equivalent, but relies
    on -race (and every future maintainer) never introducing an unguarded
    access; the channel-based single-owner design makes that class of bug
    impossible by construction at a small cost in complexity.
  - Streaming Results over a channel instead of building the full Report in
    memory (the stretch goal): necessary once a tree is too large to
    enumerate fully into a slice; adds backpressure/cancellation plumbing
    the caller now has to manage.

TESTING NOTES
  - The test suite runs the exact same table of scenarios against both
    os.DirFS(t.TempDir()) and an fstest.MapFS built in-memory, asserting
    identical Reports — this is the concrete proof that the code never
    leaked an OS-specific assumption.
  - HashMatched is tested with workers=1 and workers=8 against the same
    input and asserted to produce byte-identical digest maps — correctness
    must never depend on the concurrency level chosen.
  - `go test -race ./07_filesystem_walker/...` is mandatory given
    HashMatched's goroutine fan-out/fan-in.

FAILURE MODES TO KNOW ABOUT
  - A canceled context mid-walk returns ctx.Err() from Walk with a
    partially-built (and discarded — we return Report{} on error) result;
    callers that want the partial report on cancellation would need a
    variant that returns (Report, error) with the partial data preserved,
    a explicit design choice documented here rather than left ambiguous.
  - A file that's deleted between being listed by WalkDir and being opened
    by HashMatched (TOCTOU) surfaces as an *fs.PathError wrapped by
    hashFile — HashMatched aborts the whole batch on this via errgroup's
    first-error semantics; a "skip missing files" policy would need
    explicit errors.Is(err, fs.ErrNotExist) handling instead of treating
    every hashFile error as fatal.
  - Symlink cycles: this implementation does not implement FollowSymlinks
    at all (fs.WalkDir's default behavior — it reports symlinks as
    non-directory entries and never descends into them), which is
    deliberately the safe default; opting into FollowSymlinks requires
    tracking visited targets (e.g. by realpath) to avoid infinite
    recursion, left as a stretch goal.
*/
