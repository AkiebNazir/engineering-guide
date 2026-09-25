# path/filepath — OS-aware filesystem paths

`filepath` manipulates filesystem paths using the current <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>'s conventions:
`/` on Unix/macOS, `\` on Windows, and the matching list-separator (`:` vs
`;`). Reach for it any time you build, split, or normalize a path that will
be handed to the filesystem (`os.Open`, `os.Stat`, ...).

## When to reach for it vs alternatives already in this repo

- Building or splitting a filesystem path → `path/filepath`, always - never
  hand-roll `strings.Split(p, "/")`, which breaks the moment the program runs
  on Windows.
- Building or splitting a URL path or anything that is conceptually
  slash-separated regardless of <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> (e.g. an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> route, an S3 key) → the
  sibling `path` package, which always uses `/` and never asks the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>. Mixing
  the two up is level 9's entire point.
- Reading the resulting file → `os` (see `../01_os`) once you have the path.
- Walking an entire directory tree → `filepath.WalkDir` (this guide), backed
  by `io/fs` types - prefer it over the deprecated `filepath.Walk`, which
  calls `os.Lstat` on every entry instead of getting file-type info for free
  from the directory read itself.
- Formatting a path into a log line or error → `fmt` (see `../02_fmt`), not
  manual concatenation.

## Gotchas

| Gotcha | Detail |
|---|---|
| `filepath` behavior is fixed at compile time, not runtime | A Go binary built for Windows uses `\` throughout; one built for Unix uses `/`. You cannot "switch modes" at runtime - cross-platform path *strings* need `filepath.ToSlash`/`FromSlash` to move between conventions. |
| `path` vs `filepath` is a real, silent trap | Both packages export `Join`, `Base`, `Dir`, `Clean` with matching signatures - importing the wrong one still compiles. On Unix they even behave identically (both use `/`). The bug only appears when that code runs on Windows against real <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> paths. See level 9. |
| `Walk` is deprecated in favor of `WalkDir` | `filepath.Walk` calls `os.Lstat` per entry; `filepath.WalkDir` (Go 1.16+) uses `fs.DirEntry` from the directory read directly, avoiding a syscall per file. |
| Returning `fs.SkipDir` from a `WalkDir` callback skips the rest of that directory | Returning a plain `error` aborts the entire walk; `fs.SkipDir` specifically means "don't descend into (or continue) this directory," which is easy to conflate. |
| `Abs` is not free | `filepath.Abs` calls `os.Getwd()` internally when the path is already relative - calling it in a hot loop repeats that syscall every time. See level 6. |
| `Match`/`Glob` patterns can be malformed | An unterminated character class like `"["` returns `filepath.ErrBadPattern`, not a panic - always check the error. |

## What the 10 levels cover

Levels 1-2 build the everyday surface: `Join` (<abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> separators), `Clean`
(normalizing `..`/`.`/double slashes), `Base`/`Dir`/`Ext`. Level 3 combines
them plus `Abs` into a small path-resolution idiom. Level 4 triggers a real
`filepath.ErrBadPattern` from a malformed `Match`/`Glob` pattern. Level 5
walks a real temp directory tree with `WalkDir`, using `fs.SkipDir` to prune
a subtree. Level 6 measures repeated `Abs` calls (each paying for
`os.Getwd`) against caching the working directory once. Level 7 covers
`Glob` pattern matching and `Rel` (computing one path relative to another).
Level 8 is interop: `WalkDir` + `os` to sum real file sizes on disk. Level 9
is the production trap: using `path` instead of `filepath` for <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> paths
compiles and even runs fine on Unix, then silently mishandles a
Windows-style path - demonstrated directly against a manually-constructed
`C:\...` string. Level 10 is a capstone directory report combining `WalkDir`,
`Glob`, `Rel`, `Ext`, and `fs.SkipDir` together.
