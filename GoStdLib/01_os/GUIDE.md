# os — operating system interface

`os` is Go's window onto the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>: files, directories, environment variables, the
process's own argv/exit code, and low-level process plumbing like pipes. Reach
for it whenever you need to touch the filesystem or the environment the
program is running in.

## When to reach for it vs alternatives already in this repo

- File contents as one shot → `os.ReadFile` / `os.WriteFile` (Go 1.16+), not
  hand-rolled `os.Open` + `io.ReadAll` unless you need streaming or flags.
- Streaming a file (don't want it all in memory) → `os.Open`/`os.OpenFile`
  combined with `io` (see `../03_io`) — an `*os.File` already implements
  `io.Reader`/`io.Writer`/`io.Closer`.
- Formatting what you write to a file → pair with `fmt.Fprintf` (see
  `../02_fmt`), not manual byte concatenation.
- Walking a whole directory tree → `io/fs` + `filepath.WalkDir` (out of scope
  here; this module's `os` levels stick to single files/dirs, per assignment).
- Command-line flags beyond raw `os.Args` → `flag` package, not manual parsing
  (out of scope here too — this module only reads `os.Args` directly).

## Gotchas

| Gotcha | Detail |
|---|---|
| `os.Exit` skips deferred functions | `defer f.Close()` never runs if `os.Exit` is called before the function returns normally — level 7 proves this with a real defer that never fires. |
| Permission bits are filtered by umask | `os.Mkdir(path, 0755)` does NOT guarantee mode `0755` on disk; the process umask masks bits out. Always check `Stat().Mode()` if the exact mode matters. |
| `errors.Is(err, fs.ErrNotExist)`, not string matching | `os.Stat` returns a `*PathError` wrapping `fs.ErrNotExist`; comparing `err == os.ErrNotExist` directly also happens to work (it's an alias) but `errors.Is` is the idiomatic, wrapper-safe check. |
| `Remove` vs `RemoveAll` | `os.Remove` fails on a non-empty directory; `os.RemoveAll` recurses and does not error if the path is already gone. |
| `Rename` is not always atomic across devices | `os.Rename` is atomic on the same filesystem/volume but can fail or fall back to copy+delete across different mounted filesystems. |
| `O_APPEND` vs seeking manually | `os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)` guarantees each write lands at end-of-file atomically per write; manually `Seek`ing to the end first is a race under concurrent writers. |

## What the 10 levels cover

Levels 1-3 build up the everyday <abbr title="Application Programming Interface">API</abbr>: reading/writing whole files, opening
with explicit flags plus `Stat`, and the working-directory/environment
functions (`Getwd`, `Chdir`, `Getenv`, `LookupEnv`, `Setenv`). Level 4 triggers
a real not-exist error and handles it with `errors.Is`. Level 5 contrasts
`Mkdir` vs `MkdirAll` and `Remove` vs `RemoveAll`. Level 6 measures
`os.ReadFile` against manual `Open`+`Read` loop with real timings. Level 7
proves `os.Exit` skips deferred cleanup. Level 8 covers `os.Pipe` and
permission-bit/umask interaction. Level 9 demonstrates a `Rename` correctness
trap (renaming over an open file handle) and its fix. Level 10 is a capstone
that writes a config file atomically using a temp file + rename, exercising
most of the above together.
