"""Running learners' code: one job format, two places to run it.

A job is plain data, so it can cross a socket:

    {"kind": "python" | "go-run" | "go-test" | "go-vet" | "gofmt",
     "files": {"rel/path.py": "source", ...},   # the whole working tree of the run
     "cwd": "rel/dir",                           # where the program runs ("" = the root)
     "pkg": "rel/dir",                           # Go: the package to build (go-run)
     "args": ["main.py"],                        # python: everything after the interpreter
     "python": "default" | "eng" | "api",        # which interpreter (local mode venvs)
     "stdin": "...",                             # gofmt
     "timeout": 15}

and the answer is {"ok", "stdout", "stderr", "exitCode", "ms", "timeout"?}.

Callers build the file set from the curriculum (see stage_* below), so a run never
writes into content/: the learner's buffer replaces one file inside a scratch copy.

  LocalRunner   the owner's own machine (`make app`): a temp directory, the
                system toolchains, no isolation, the same behaviour as always
  RemoteRunner  the hosted guide: the job goes over a Unix socket to runner.py,
                which runs it in a separate container with no network, as a
                throwaway user, under resource limits

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

KINDS = frozenset({"python", "go-run", "go-test", "go-vet", "gofmt"})
MAX_JOB_BYTES = 4_000_000          # the files of one run, all together
MAX_FILE_BYTES = 1_000_000         # one staged file; bigger ones are left out
MAX_OUTPUT = 256_000               # characters of stdout / stderr sent back
SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache",
             ".mypy_cache", ".ruff_cache", ".runtmp"}


class JobError(ValueError):
    """The job itself is malformed (never the learner's code failing)."""


def failure(message: str, **extra) -> dict:
    return {"ok": False, "stdout": "", "stderr": message, "exitCode": -1, "ms": 0, **extra}


def clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT] + f"\n… output cut at {MAX_OUTPUT:,} characters …\n"


def validate(job: dict) -> dict:
    """Shape and path checks shared by both runners. Raises JobError."""
    if not isinstance(job, dict) or job.get("kind") not in KINDS:
        raise JobError("unknown job kind")
    files = job.get("files") or {}
    if not isinstance(files, dict):
        raise JobError("files must be an object")
    total = 0
    for rel, text in files.items():
        safe_rel(rel)
        if not isinstance(text, str):
            raise JobError(f"{rel}: not text")
        total += len(text.encode())
    if total > MAX_JOB_BYTES:
        raise JobError("the files of this run are too large")
    for key in ("cwd", "pkg"):
        if job.get(key):
            safe_rel(job[key])
    args = job.get("args") or []
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise JobError("args must be strings")
    timeout = job.get("timeout", 15)
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
        raise JobError("timeout out of range")
    return job


def safe_rel(rel) -> str:
    """A relative path that stays inside the job's directory."""
    if not isinstance(rel, str) or not rel or len(rel) > 300 or "\\" in rel or "\0" in rel:
        raise JobError(f"bad path {rel!r}")
    parts = rel.split("/")
    if rel.startswith("/") or any(p in ("", ".", "..") for p in parts):
        raise JobError(f"bad path {rel!r}")
    return rel


def write_tree(root: Path, files: dict) -> None:
    for rel, text in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)


# ----------------------------------------------------------------------------
# Building the file set of a run from the curriculum
# ----------------------------------------------------------------------------
def _read_text(f: Path) -> str | None:
    try:
        if f.stat().st_size > MAX_FILE_BYTES:
            return None
        return f.read_text()
    except (OSError, UnicodeDecodeError):
        return None                   # binary or unreadable: not part of a run


def dir_files(d: Path, prefix: str = "", recursive: bool = False) -> dict[str, str]:
    """Text files of one directory (optionally its subdirectories), keyed prefix/name."""
    out: dict[str, str] = {}
    if not d.is_dir():
        return out
    for f in sorted(d.iterdir()):
        if f.name in SKIP_DIRS or f.is_symlink():
            continue
        key = f"{prefix}{f.name}"
        if f.is_file():
            text = _read_text(f)
            if text is not None:
                out[key] = text
        elif recursive and f.is_dir():
            out.update(dir_files(f, key + "/", recursive=True))
    return out


GO_IMPORT_RE = re.compile(r'"([^"\s]+)"')
GO_IMPORT_BLOCK_RE = re.compile(r'^import\s*(\((.*?)\)|[\w.]*\s*"[^"]+")', re.S | re.M)


def go_module_path(module_root: Path) -> str:
    m = re.search(r"^module\s+(\S+)", (module_root / "go.mod").read_text(), re.M)
    return m.group(1) if m else ""


def go_imports(source: str) -> set[str]:
    found: set[str] = set()
    for block in GO_IMPORT_BLOCK_RE.finditer(source):
        found.update(GO_IMPORT_RE.findall(block.group(1)))
    return found


def _parent(rel: str) -> str:
    return rel.rpartition("/")[0]


def stage_go_module(module_root: Path, pkg_rels: list[str], overrides: dict[str, str]) -> dict[str, str]:
    """go.mod, go.sum, the given package directories (module-relative, "" = the root,
    with their testdata) and every package of the same module they import, transitively.
    `overrides` (module-relative path -> source) replaces or adds files, e.g. the
    learner's buffer, and its imports are followed too."""
    files: dict[str, str] = {}
    for name in ("go.mod", "go.sum"):
        text = _read_text(module_root / name)
        if text is not None:
            files[name] = text
    modpath = go_module_path(module_root)
    base = module_root.resolve()
    todo = list(pkg_rels) + [_parent(rel) for rel in overrides if rel.endswith(".go")]
    seen: set[str] = set()
    while todo:
        rel = todo.pop().strip("/")
        if rel in seen:
            continue
        seen.add(rel)
        d = (module_root / rel) if rel else module_root
        if not d.resolve().is_relative_to(base):
            continue
        prefix = f"{rel}/" if rel else ""
        files.update(dir_files(d, prefix))
        files.update(dir_files(d / "testdata", f"{prefix}testdata/", recursive=True))
        files.update({k: v for k, v in overrides.items() if _parent(k) == rel})
        for k, src in files.items():
            if _parent(k) != rel or not k.endswith(".go"):
                continue
            for imp in go_imports(src):
                if modpath and imp.startswith(modpath + "/"):
                    todo.append(imp[len(modpath) + 1:])
    files.update(overrides)
    return files


# ----------------------------------------------------------------------------
# The owner's machine: run in a temp directory with the local toolchains
# ----------------------------------------------------------------------------
class LocalRunner:
    """No isolation: `make app` is the owner's own copy, running their own code."""

    remote = False

    def __init__(self, pythons: dict[str, str], go: str | None):
        self.pythons = pythons        # {"default": path, "eng": path, "api": path}
        self.go = go

    @property
    def available(self) -> dict:
        return {"python": True, "go": self.go is not None}

    def run(self, job: dict) -> dict:
        try:
            validate(job)
        except JobError as e:
            return failure(str(e))
        kind, timeout = job["kind"], job.get("timeout", 15)
        if kind != "python" and not self.go:
            return failure("Go toolchain not found on PATH. Install Go, or "
                           "set it up so `go` is runnable from a shell.")
        with tempfile.TemporaryDirectory(prefix="eg_run_") as tmp:
            root = Path(tmp)
            write_tree(root, job.get("files") or {})
            cwd = root / job["cwd"] if job.get("cwd") else root
            cwd.mkdir(parents=True, exist_ok=True)
            env = {**os.environ, "GOFLAGS": "-mod=mod"}
            stdin = None
            if kind == "python":
                py = self.pythons.get(job.get("python") or "default") or self.pythons["default"]
                cmd = [py, *job.get("args", [])]
            elif kind == "go-run":
                cmd = [self.go, "run", f"./{job['pkg']}" if job.get("pkg") else "."]
            elif kind == "go-test":
                cmd = [self.go, "test", "-v", "./..."]
            elif kind == "go-vet":
                cmd = [self.go, "vet", "./..."]
            else:
                gofmt = Path(self.go).parent / "gofmt"
                if not gofmt.exists():
                    return failure("gofmt not found.")
                cmd, stdin = [str(gofmt)], job.get("stdin", "")
            started = time.perf_counter()
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                      cwd=str(cwd), env=env, input=stdin)
            except subprocess.TimeoutExpired:
                return failure("", timeout=True, ms=round(timeout * 1000))
            return {"ok": proc.returncode == 0, "stdout": clip(proc.stdout), "stderr": clip(proc.stderr),
                    "exitCode": proc.returncode, "ms": round((time.perf_counter() - started) * 1000)}


class DisabledRunner:
    """The hosted guide without a runner container: every run gets the same explanation."""

    remote = True
    available = {"python": False, "go": False}

    def __init__(self, message: str):
        self.message = message

    def run(self, job: dict) -> dict:
        return failure(self.message, exitCode=1, error=self.message)

    def ping(self) -> bool:
        return False


# ----------------------------------------------------------------------------
# The hosted guide: hand the job to the runner container
# ----------------------------------------------------------------------------
def send_frame(sock: socket.socket, obj) -> None:
    data = json.dumps(obj).encode()
    sock.sendall(len(data).to_bytes(4, "big") + data)


def recv_frame(sock: socket.socket, limit: int) -> dict:
    head = _recv_exact(sock, 4)
    size = int.from_bytes(head, "big")
    if size > limit:
        raise JobError("message too large")
    return json.loads(_recv_exact(sock, size))


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf)))
        if not chunk:
            raise ConnectionError("connection closed early")
        buf += chunk
    return bytes(buf)


class RemoteRunner:
    """Client for runner.py over a Unix socket shared between the two containers."""

    remote = True

    def __init__(self, socket_path: str):
        self.socket_path = socket_path

    @property
    def available(self) -> dict:
        return {"python": True, "go": True}

    def run(self, job: dict) -> dict:
        try:
            validate(job)
        except JobError as e:
            return failure(str(e))
        # The runner queues and times out on its own; this only guards a hung socket.
        deadline = job.get("timeout", 15) * 2 + 60
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(deadline)
                s.connect(self.socket_path)
                send_frame(s, job)
                reply = recv_frame(s, MAX_OUTPUT * 8 + 65536)
        except (OSError, ValueError, ConnectionError) as e:
            return failure(f"The code runner is not reachable right now ({type(e).__name__}). "
                           "Try again in a minute.")
        if not isinstance(reply, dict):
            return failure("The code runner sent an unreadable answer.")
        return reply

    def ping(self) -> bool:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(self.socket_path)
                send_frame(s, {"kind": "ping"})
                return recv_frame(s, 4096).get("ok") is True
        except (OSError, ValueError, ConnectionError):
            return False


def which_go() -> str | None:
    found = shutil.which("go")
    if found:
        return found
    for candidate in ("/usr/local/go/bin/go", "/opt/homebrew/bin/go"):
        if Path(candidate).exists():
            return candidate
    return None
