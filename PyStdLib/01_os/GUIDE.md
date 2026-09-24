# `os` — talking to the operating system

`os` is the thin, mostly-direct wrapper around POSIX/Win32 system calls: environment
variables, processes, file descriptors, directory entries, and the raw bits behind
"a file" (size, mtime, permission mode). Almost every other stdlib module that touches
the filesystem or a process (`pathlib`, `subprocess`, `shutil`, `tempfile`) is built on
top of `os` — so the mental model here is the foundation for all of them.

## When to reach for `os` vs alternatives already in this repo

- **Path manipulation (joining, suffixes, globbing, reading a whole file):** prefer
  `pathlib.Path` — see `PyStdLib/03_pathlib/`. `os.path` still exists and is what
  `pathlib` calls internally, and this module covers its basics, but new code should
  reach for `Path` first. Use raw `os` when you need something `pathlib` doesn't wrap:
  low-level file descriptors, `os.walk`'s in-place directory pruning, `os.stat` bit
  fields, or process/environment functions.
- **Running another program:** never build a shell command string and hand it to
  `os.system` — use `subprocess.run([...])` (a list of argv, no shell parsing). This
  repo's `os.system vs subprocess` coverage (level 9) exists only to show *why*, not to
  teach `subprocess` in depth.
- **Concurrency / async I/O:** `os` functions are all blocking, synchronous syscalls.
  For overlapping I/O see `PyEngineering/27_asyncio_deep_dive_event_loop`; for
  running blocking `os`/file work off an event loop, that same topic covers
  `run_in_executor`.
- **Atomic file writes / durability:** `PyEngineering/06_atomic_file_store` builds a
  production atomic-write pattern (temp file + `os.replace` + `fsync`) directly on top
  of what this module's level 7-10 files teach.

## Gotchas

| Gotcha | Detail |
|---|---|
| `os.putenv` doesn't update `os.environ` | `os.putenv` only changes the *process's* real environment (visible to subprocesses); the `os.environ` dict in your own process is a cached snapshot that `os.putenv` does not refresh. Always mutate `os.environ["KEY"] = value` instead — that updates both. |
| `os.listdir` vs `os.scandir` | `os.listdir` returns names only, so checking each entry's type/size costs one extra `stat` syscall per file. `os.scandir` returns `DirEntry` objects that usually cache that info from the directory read itself — often meaningfully faster on large directories (measured in level 6). |
| `os._exit()` skips everything | `os._exit(code)` terminates immediately at the C level: no buffered stdout flush, no `atexit` handlers, no `finally` blocks in outer frames. `sys.exit()` (or an uncaught `SystemExit`) unwinds normally and flushes. Calling `os._exit` from "regular" code silently drops your last buffered output — demonstrated for real in level 9. |
| `os.walk` mutates dirnames to prune | To skip descending into a subdirectory, mutate the `dirnames` list *in place* (`dirnames[:] = [...]`) inside the loop. Reassigning the name (`dirnames = [...]`) does nothing — `os.walk` already grabbed a reference to the original list. |
| `os.system` runs through a shell | `os.system("cmd " + user_input)` lets shell metacharacters (`;`, `&&`, `` ` ``) in `user_input` run as separate commands — a classic injection bug. `subprocess.run([...])` with a list of arguments never invokes a shell, so metacharacters are just literal text. |
| `os.rmdir`/`os.removedirs` only remove empty directories | Unlike `shutil.rmtree`, both raise `OSError` (`ENOTEMPTY` / `[Errno 66] Directory not empty` on macOS) the moment a directory still has anything in it — including hidden files you may have forgotten about. |

## What the 10 levels cover

Levels 1-2 build the core vocabulary: environment variables, `getcwd`/`chdir`,
`listdir`/`scandir`, `os.path` basics, and `stat` fields. Level 3 combines them into a
small directory-setup-and-cleanup idiom (`mkdir`/`makedirs`, `remove`/`rmdir`,
`rename`/`replace`). Level 4 triggers the real exceptions those calls raise. Level 5
uses `os.walk` for a realistic tree-processing pattern, and level 6 actually measures
`listdir`+`stat` against `scandir`. Level 7 covers low-level file descriptors
(`os.open`/`read`/`write`/`close`) and why they need `try`/`finally`. Level 8 pairs
`os.stat` with the `stat` module to interpret permission bits, and applies them with
`os.chmod`. Level 9 proves two production traps (`os._exit` losing output, `os.system`
shell injection) instead of just describing them. Level 10 is a small atomic backup
tool exercising most of the above together.
