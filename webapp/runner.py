"""The code runner of the hosted guide: runs learners' code away from everything else.

The web server (server.py, EG_AUTH=1) sends each run here as a job (see sandbox.py)
over a Unix socket on a volume only the two containers share. This process runs in
its own container (deploy/compose.yaml) which has:

  * no network at all (network_mode: none), so code cannot reach the internet,
    the web container, or the laptop's home network; only its own loopback
  * a read-only root filesystem; scratch space is a size-capped tmpfs
  * no accounts database, no secrets, no curriculum: a job carries only the files
    of that one run
  * capped memory, CPU and process count for the whole container

Inside, every run gets:

  * its own throwaway user from a pool (one per concurrent run, never shared at
    the same time), with no supplementary groups and no capabilities
  * a fresh directory nobody else can read, deleted afterwards
  * per-process limits: CPU seconds, processes, open files, file size, memory
    (Python), no core dumps; a wall-clock timeout after which every process of
    that user is killed, including anything it left running in the background
  * output capped in size

Go is compiled by a separate build user that owns the shared build cache (so runs
stay fast); compiling runs no learner code (cgo is off), and the program itself
then runs as the throwaway user, which cannot write to that cache.

Must start as root (to switch users); see deploy/Dockerfile.runner. Standard library only.
"""
from __future__ import annotations

import os
import resource
import secrets
import shutil
import signal
import socketserver
import subprocess
import sys
import threading
import time
import queue
from pathlib import Path

import sandbox

SOCKET = os.environ.get("EG_RUNNER_SOCKET", "/run/eg-runner/runner.sock")
WORK = Path(os.environ.get("EG_RUNNER_WORK", "/work"))
SLOTS = max(1, int(os.environ.get("EG_RUNNER_SLOTS", "3")))   # runs at the same time
QUEUE_WAIT = 30            # seconds a run may wait for a free slot
BUILD_UID = 2000           # owns the Go build cache; runs only the Go toolchain
SANDBOX_UID0 = 3000        # throwaway users 3000 … 3000+SLOTS-1
CLIENT_GID = int(os.environ.get("EG_RUNNER_CLIENT_GID", "10001"))   # the web container's group
SHARED_TMP = ("/tmp", "/dev/shm", "/var/tmp")    # swept after each run for files it left
PYTHON = os.environ.get("EG_RUNNER_PYTHON", sys.executable)
GO = os.environ.get("EG_RUNNER_GO", "/usr/local/go/bin/go")
GOFMT = str(Path(GO).parent / "gofmt")
GO_CACHE = os.environ.get("EG_RUNNER_GOCACHE", "/var/cache/go")
GO_MODCACHE = os.environ.get("EG_RUNNER_GOMODCACHE", "/opt/go/mod")
PATH = f"{Path(GO).parent}:/usr/local/bin:/usr/bin:/bin"
MAX_REQUEST = sandbox.MAX_JOB_BYTES * 2

MB = 1024 * 1024
RUN_LIMITS = {               # the learner's program
    resource.RLIMIT_NPROC: 256,          # processes + threads of this user (Go and gRPC use threads)
    resource.RLIMIT_NOFILE: 512,
    resource.RLIMIT_FSIZE: 16 * MB,      # any one file it writes, stdout included
    resource.RLIMIT_CORE: 0,
}
PYTHON_AS = 1024 * MB                    # address space for Python (Go reserves too much to cap)
BUILD_LIMITS = {
    resource.RLIMIT_NOFILE: 4096,
    resource.RLIMIT_FSIZE: 512 * MB,
    resource.RLIMIT_CORE: 0,
}

_slots: "queue.Queue[int]" = queue.Queue()


def log(msg: str) -> None:
    print(f"[runner] {time.strftime('%H:%M:%S')} {msg}", file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------
# Processes
# ----------------------------------------------------------------------------
def _limits(limits: dict, cpu_seconds: float):
    def apply() -> None:            # runs in the child, after it switched user
        for res, value in limits.items():
            resource.setrlimit(res, (value, value))
        cpu = int(cpu_seconds) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    return apply


def kill_user(uid: int) -> None:
    """SIGKILL every process of `uid`, including ones that left the process group."""
    for _ in range(50):
        found = False
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            try:
                with open(f"/proc/{entry.name}/status") as f:
                    for line in f:
                        if line.startswith("Uid:"):
                            if int(line.split()[1]) == uid:
                                found = True
                                os.kill(int(entry.name), signal.SIGKILL)
                            break
            except (OSError, ValueError):
                continue
        if not found:
            return
        time.sleep(0.02)


def _oom_first(pid: int) -> None:
    """Make a learner's process the first to go if the container runs out of memory."""
    try:
        with open(f"/proc/{pid}/oom_score_adj", "w") as f:
            f.write("1000")
    except OSError:
        pass


def _scratch_full() -> bool:
    try:
        st = os.statvfs(WORK)
    except OSError:
        return False
    return st.f_bavail * st.f_frsize < 2 * MB


def _read(path: Path) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sandbox.clip(f.read(sandbox.MAX_OUTPUT + 1))
    except OSError:
        return ""


class Run:
    """One job: its directory, its user, its deadline."""

    def __init__(self, job: dict, uid: int):
        self.job, self.uid = job, uid
        self.deadline = time.monotonic() + job.get("timeout", 15)
        self.dir = WORK / f"j-{secrets.token_hex(12)}"
        self.src = self.dir / "src"
        self.home = self.dir / "home"
        self.bin = self.dir / "bin"
        self.btmp = self.dir / "btmp"
        self.n = 0

    # -- layout -----------------------------------------------------------------
    def prepare(self) -> None:
        self.dir.mkdir(mode=0o711)
        os.chmod(self.dir, 0o711)
        self.src.mkdir()
        sandbox.write_tree(self.src, self.job.get("files") or {})
        if self.job.get("cwd"):
            (self.src / self.job["cwd"]).mkdir(parents=True, exist_ok=True)
        # the learner's user owns its tree; the build user reads it through the group
        for root, dirs, files in os.walk(self.src):
            os.chown(root, self.uid, BUILD_UID)
            os.chmod(root, 0o770)
            for name in files:
                os.chown(os.path.join(root, name), self.uid, BUILD_UID)
                os.chmod(os.path.join(root, name), 0o660)
        self.home.mkdir(mode=0o700)
        os.chown(self.home, self.uid, self.uid)
        # binaries: written by the build user, readable only by this run's user
        self.bin.mkdir()
        os.chown(self.bin, BUILD_UID, self.uid)
        os.chmod(self.bin, 0o2750)
        self.btmp.mkdir(mode=0o700)
        os.chown(self.btmp, BUILD_UID, BUILD_UID)

    def cwd(self, rel: str | None = None) -> Path:
        rel = self.job.get("cwd") if rel is None else rel
        return self.src / rel if rel else self.src

    def remaining(self) -> float:
        return self.deadline - time.monotonic()

    # -- one process -------------------------------------------------------------
    def _spawn(self, argv: list[str], cwd: Path, *, as_build: bool, stdin: str | None = None,
               env_extra: dict | None = None) -> dict:
        left = self.remaining()
        if left <= 0:
            return {"timeout": True}
        self.n += 1
        out, err = self.dir / f"out{self.n}", self.dir / f"err{self.n}"
        if as_build:
            uid, limits = BUILD_UID, dict(BUILD_LIMITS)
            env = {"PATH": PATH, "HOME": f"{GO_CACHE}/home", "TMPDIR": str(self.btmp)}
        else:
            uid, limits = self.uid, dict(RUN_LIMITS)
            if argv[0] == PYTHON:
                limits[resource.RLIMIT_AS] = PYTHON_AS
            env = {"PATH": PATH, "HOME": str(self.home), "TMPDIR": str(self.home), "LANG": "C.UTF-8",
                   "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONUNBUFFERED": "1"}
        env.update(env_extra or {})
        started = time.perf_counter()
        with open(out, "wb") as fo, open(err, "wb") as fe:
            proc = subprocess.Popen(
                argv, cwd=str(cwd), env=env, user=uid, group=uid, extra_groups=[],
                start_new_session=True, close_fds=True,
                stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                stdout=fo, stderr=fe, preexec_fn=_limits(limits, left))
        if not as_build:
            _oom_first(proc.pid)
        timed_out = False
        try:
            if stdin is not None:
                proc.communicate(stdin.encode(), timeout=left)
            else:
                proc.wait(timeout=left)
        except subprocess.TimeoutExpired:
            timed_out = True
            if as_build:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
            else:
                kill_user(uid)
            proc.wait()
        ms = round((time.perf_counter() - started) * 1000)
        result = {"exitCode": proc.returncode, "stdout": _read(out), "stderr": _read(err), "ms": ms}
        if timed_out:
            result["timeout"] = True
        elif proc.returncode == -signal.SIGXFSZ:
            result["stderr"] += "\nStopped: the program wrote more than 16 MB to one file or to its output.\n"
        elif proc.returncode in (-signal.SIGXCPU, -signal.SIGKILL):
            result["stderr"] += "\nStopped: the program used too much CPU time or memory.\n"
        if proc.returncode and _scratch_full():
            result["stderr"] += "\nStopped: the run filled its scratch disk space.\n"
        return result

    def build(self, argv: list[str], cwd: Path) -> dict:
        return self._spawn(argv, cwd, as_build=True, env_extra={
            "GOCACHE": f"{GO_CACHE}/build", "GOMODCACHE": GO_MODCACHE, "GOPROXY": "off",
            "GOSUMDB": "off", "GOFLAGS": "-mod=mod -trimpath", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0",
            "GOTELEMETRY": "off"})

    def run(self, argv: list[str], cwd: Path, stdin: str | None = None) -> dict:
        return self._spawn(argv, cwd, as_build=False, stdin=stdin)

    # -- the job kinds -------------------------------------------------------------
    def execute(self) -> dict:
        kind = self.job["kind"]
        started = time.perf_counter()
        if kind == "python":
            r = self.run([PYTHON, *self.job.get("args", [])], self.cwd())
        elif kind == "gofmt":
            r = self.run([GOFMT], self.cwd(), stdin=self.job.get("stdin", ""))
        elif kind == "go-vet":
            r = self.build([GO, "vet", "./..."], self.cwd())
        elif kind == "go-run":
            r = self.go_run()
        else:
            r = self.go_test()
        if r.get("timeout"):
            return sandbox.failure("", timeout=True, ms=round(self.job.get("timeout", 15) * 1000))
        code = r.get("exitCode", -1)
        return {"ok": code == 0, "stdout": sandbox.clip(r.get("stdout", "")),
                "stderr": sandbox.clip(r.get("stderr", "")), "exitCode": code,
                "ms": round((time.perf_counter() - started) * 1000)}

    def go_run(self) -> dict:
        pkg = self.job.get("pkg")
        b = self.build([GO, "build", "-o", str(self.bin / "prog"), f"./{pkg}" if pkg else "."], self.cwd())
        if b.get("timeout") or b["exitCode"] != 0:
            return b
        r = self.run([str(self.bin / "prog")], self.cwd())
        if not r.get("timeout") and r["exitCode"] != 0:
            r["stderr"] += f"exit status {r['exitCode']}\n"        # what `go run` prints
        return r

    def go_test(self) -> dict:
        """`go test -v ./...`, split in two: compile each test binary as the build
        user, then run it as the learner's user. Output follows `go test`."""
        listing = self.build([GO, "list", "-f", "{{.ImportPath}}\t{{.Dir}}\t{{len .TestGoFiles}}\t"
                              "{{len .XTestGoFiles}}", "./..."], self.cwd())
        if listing.get("timeout") or listing["exitCode"] != 0:
            return listing
        stdout, stderr, failed = [], [listing["stderr"]] if listing["stderr"].strip() else [], False
        for i, line in enumerate(listing["stdout"].splitlines()):
            parts = line.split("\t")
            if len(parts) != 4:
                continue
            ip, pkg_dir, tests, xtests = parts[0], Path(parts[1]), int(parts[2]), int(parts[3])
            if not pkg_dir.resolve().is_relative_to(self.src.resolve()):
                continue
            if tests + xtests == 0:
                stdout.append(f"?   \t{ip}\t[no test files]\n")
                continue
            binary = self.bin / f"t{i}.test"
            b = self.build([GO, "test", "-c", "-o", str(binary), ip], self.cwd())
            if b.get("timeout"):
                return b
            if b["exitCode"] != 0:
                failed = True
                stderr.append(b["stderr"])
                stdout.append(f"FAIL\t{ip} [build failed]\n")
                continue
            r = self.run([str(binary), "-test.v"], pkg_dir)
            if r.get("timeout"):
                return r
            stdout.append(r["stdout"])
            if r["stderr"]:
                stderr.append(r["stderr"])
            secs = r["ms"] / 1000
            if r["exitCode"] == 0:
                stdout.append(f"ok  \t{ip}\t{secs:.3f}s\n")
            else:
                failed = True
                stdout.append(f"FAIL\t{ip}\t{secs:.3f}s\n")
        return {"exitCode": 1 if failed else 0, "stdout": "".join(stdout), "stderr": "".join(stderr)}

    def cleanup(self) -> None:
        kill_user(self.uid)
        shutil.rmtree(self.dir, ignore_errors=True)
        sweep_user_files(self.uid)


def sweep_user_files(uid: int) -> None:
    """Delete what a run left in world-writable places (e.g. /dev/shm), so the next
    run under the same user finds nothing of it."""
    for top in SHARED_TMP:
        try:
            entries = list(os.scandir(top))
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.stat(follow_symlinks=False).st_uid != uid:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path, ignore_errors=True)
                else:
                    os.unlink(entry.path)
            except OSError:
                pass


def handle(job) -> dict:
    if isinstance(job, dict) and job.get("kind") == "ping":
        return {"ok": True, "slots": SLOTS}
    try:
        sandbox.validate(job)
    except sandbox.JobError as e:
        return sandbox.failure(str(e))
    try:
        uid = _slots.get(timeout=QUEUE_WAIT)
    except queue.Empty:
        return sandbox.failure("The code runner is busy with other people's code. Try again in a moment.")
    run = Run(job, uid)
    try:
        run.prepare()
        return run.execute()
    except Exception as e:                 # never let one job take the runner down
        log(f"job failed: {type(e).__name__}: {e}")
        return sandbox.failure("The code runner hit an internal error with this run.")
    finally:
        run.cleanup()
        _slots.put(uid)


class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.settimeout(30)
        try:
            job = sandbox.recv_frame(self.request, MAX_REQUEST)
        except (OSError, ValueError, ConnectionError):
            return
        self.request.settimeout(None)
        t = time.perf_counter()
        reply = handle(job)
        log(f"{job.get('kind', '?') if isinstance(job, dict) else '?'}: exit {reply.get('exitCode')} "
            f"{'timeout ' if reply.get('timeout') else ''}{round((time.perf_counter() - t) * 1000)} ms")
        try:
            sandbox.send_frame(self.request, reply)
        except OSError:
            pass


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    request_queue_size = 64


def main() -> None:
    if os.geteuid() != 0:
        sys.exit("runner.py must start as root so it can run each job as its own user "
                 "(the container drops every other privilege; see deploy/compose.yaml).")
    WORK.mkdir(parents=True, exist_ok=True)
    os.chmod(WORK, 0o711)
    for leftover in WORK.iterdir():
        shutil.rmtree(leftover, ignore_errors=True)
    for i in range(SLOTS):
        kill_user(SANDBOX_UID0 + i)
        sweep_user_files(SANDBOX_UID0 + i)
        _slots.put(SANDBOX_UID0 + i)
    sock = Path(SOCKET)
    sock.parent.mkdir(parents=True, exist_ok=True)
    if sock.exists() or sock.is_symlink():
        sock.unlink()
    server = Server(str(sock), Handler)
    # Only the web container's group may connect, not the code this runner executes.
    os.chown(sock, 0, CLIENT_GID)
    os.chmod(sock, 0o660)
    log(f"listening on {sock}, {SLOTS} slots, python {PYTHON}, go {GO if Path(GO).exists() else 'missing'}")
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    try:
        server.serve_forever()
    finally:
        server.server_close()
        sock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
