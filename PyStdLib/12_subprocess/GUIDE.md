# subprocess

`subprocess` lets Python launch and talk to other programs: run a command and
capture its output, feed it input, stream its output as it runs, wire two processes
together like a shell pipe, or fail loudly when a command errors out. It is the
stdlib's replacement for `os.system`/backticks-style shelling out.

## When to reach for it

- Running an external command and getting its result → `subprocess.run()`, the
  high-level, blocking, "do this and give me the outcome" <abbr title="Application Programming Interface">API</abbr> — covers the vast
  majority of real usage.
- Needing to interact with a long-running process while it runs (stream output,
  send input mid-flight, enforce a timeout) → `subprocess.Popen`, the lower-level
  handle `run()` is built on.
- Needing real <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>-level parallelism across <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> cores, shared memory, or process
  pools for <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound work in your OWN Python code → that's a different problem
  (`multiprocessing`), covered in `PyEngineering/33_concurrency_models_ipc`.
  `subprocess` is for talking to *other programs*, not for parallelizing your own
  Python functions.
- Building a shell-like command string dynamically and safely → `shlex.split()` /
  `shlex.quote()` alongside `subprocess`'s list-args form, never raw string
  concatenation into `shell=True`.

## Gotchas

| Gotcha | Detail |
|---|---|
| `shell=True` + untrusted input is a command-injection hole | A crafted argument like `"; rm -rf ." can break out of the intended command entirely. Use the list-of-args form (`shell=False`, the default) whenever any part of the command comes from outside your program. |
| `check=True` is off by default | `run()` does not raise on a non-zero exit code unless you pass `check=True` — a silently "successful" call may have actually failed. |
| `communicate(timeout=...)` doesn't kill the process for you | A `TimeoutExpired` leaves the child running; you must `.kill()`/`.terminate()` it yourself and then call `communicate()` again to clean up pipes. |
| Reading `.stdout`/`.stderr` directly on a `Popen` can deadlock | With large output, the child can fill the OS pipe buffer and block forever if you're not draining both streams; `communicate()` (or the streaming pattern with threads/select) avoids this. |
| `text=True` decoding assumes a text encoding | Binary-safe protocols (e.g. reading raw image bytes from a tool) need `text=False` (the default) and manual `.decode()` where appropriate. |
| Forgetting to close a piped `stdout` when chaining processes | Not calling `.close()` on the first process's `stdout` after handing it to the second's `stdin` can prevent the first process from receiving SIGPIPE and exiting when the reader stops early. |

## What the 10 levels cover

Levels 1-3 build the core: `run()` with `capture_output`/`text`, the exit-code/
`check=True` idiom, and a small realistic idiom combining them. Level 4 triggers a
real `CalledProcessError` and catches it. Level 5 covers `Popen` + `communicate
(timeout=)` and handling a real `TimeoutExpired`. Level 6 *measures* two ways of
running several commands (sequential vs pipelined) with real timing. Level 7 covers
streaming a long-running child's stdout line by line as it produces output. Level 8
combines `subprocess` with `shlex` for safe dynamic command construction and `env=`
overrides. Level 9 is the `shell=True` injection trap, demonstrated actually breaking
out of the intended command, then fixed with list-args. Level 10 is a capstone: a
small pipeline that builds a command safely, streams output, enforces a timeout, and
replicates a two-stage shell pipe (`producer | consumer`) from Python.
