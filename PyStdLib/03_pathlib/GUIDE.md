# `pathlib` — paths as objects, not strings

`pathlib.Path` represents a filesystem path as an object with methods, instead of a
plain string you slice and concatenate by hand. It wraps most of what `os` and
`os.path` do for path manipulation and simple file I/O, in a form that's easier to
read, chain, and get right. This module is the modern default for path work in this
repo — `os`/`os.path` (see `PyStdLib/01_os/`) still exist underneath and this module's
level 5 does a direct side-by-side comparison.

## When to reach for `pathlib` vs alternatives already in this repo

- **Any new code that builds, inspects, or joins paths:** use `Path`, not
  `os.path.join`/`os.path.split` string surgery. It reads better and a `Path` object
  is directly accepted almost everywhere a path string is (in `open()`, `os` functions,
  `subprocess`, etc. via `os.PathLike`).
- **Low-level file descriptors, `os.walk`'s in-place directory pruning, or raw
  `os.stat` bit-field work:** those stay in `os` — see `PyStdLib/01_os/`. `Path.stat()`
  (level 9 here) returns the exact same `os.stat_result`, so nothing is lost by
  starting from a `Path`.
- **Copying/moving/deleting whole trees:** `pathlib` only handles single
  files/directories directly (`.unlink()`, empty-dir `.rmdir()`); for a whole tree use
  `shutil.copytree`/`shutil.rmtree`, exactly as `PyEngineering/07_filesystem_walker`
  does on top of `pathlib`.
- **Config file loading (TOML/<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>) that needs a resolved, validated path:**
  `PyEngineering/08_config_loader` builds directly on `Path.read_text()`/`.exists()`
  patterns from level 2-3 here.

## Gotchas

| Gotcha | Detail |
|---|---|
| `.resolve()` touches the filesystem, `os.path.abspath` doesn't (fully) | `Path.resolve()` follows symlinks and normalizes `..`, which means it *can* raise or behave surprisingly on a path that doesn't exist yet (though by default it no longer raises, it just resolves what it can). `.absolute()` is the purely-syntactic version (cwd + path, no symlink following). |
| `Path("a") / "/etc"` throws away `"a"` | The `/` operator follows the *nix rule that joining with an **absolute** path discards everything before it — `Path("a") / "/etc" == Path("/etc")`. This is the same behavior as `os.path.join`, just easy to trip over. |
| `.glob("**/*.py")` and `.rglob("*.py")` are the same, `.glob("*.py")` isn't recursive | A single-star glob only matches the immediate directory. Forgetting `**/` (or not using `.rglob`) silently returns an empty/partial result instead of erroring. |
| `.unlink()` raises `FileNotFoundError` by default | Unlike some "delete if exists" APIs, `Path.unlink()` raises if the file is already gone — pass `missing_ok=True` for idempotent delete, mirroring `os.remove`'s stricter default. |
| `Path` is immutable | `.with_suffix()`, `.with_name()`, and friends all return a **new** `Path` — they never mutate the original. Forgetting to capture the return value is a no-op bug that's easy to miss since nothing raises. |
| `.stem`/`.suffix` on dotfiles | `Path(".bashrc").stem == ".bashrc"` and `.suffix == ""` — a leading dot is treated as part of the name, not as an extension separator, which surprises people expecting shell-style hidden-file handling. |

## What the 10 levels cover

Levels 1-2 build the vocabulary: constructing a `Path`, the `/` join operator, and the
core query methods (`.exists()`, `.is_file()`, `.is_dir()`, `.resolve()`). Level 3
combines them into a small idiom (create, write, read back, list). Level 4 triggers
the real exceptions (`FileNotFoundError`, `FileExistsError`) that `Path` methods raise.
Level 5 does the direct side-by-side comparison against equivalent `os`/`os.path`
calls. Level 6 measures `.glob()` vs `.rglob()` over a real tree. Level 7 covers safe,
idempotent creation/deletion (`.mkdir(parents=True, exist_ok=True)`,
`.unlink(missing_ok=True)`) as a lifecycle concern. Level 8 pairs `pathlib` with `os`
for interop (`.stat()`, permission bits). Level 9 demonstrates the `Path` immutability
trap for real. Level 10 is a small capstone tool that scans, filters, and reorganizes
a directory tree using most of the above together.
