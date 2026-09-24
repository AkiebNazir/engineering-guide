"""
LEVEL 07 (advanced) - Lifecycle: idempotent setup/teardown, and Path.open() safety
======================================================================================
You will learn
  * writing setup/teardown helpers that are safe to call MORE THAN ONCE --
    essential once code can be retried (a flaky step, a re-run job, a retried
    RPC) since a naive version would crash the second time
  * .mkdir(parents=True, exist_ok=True) and .unlink(missing_ok=True) as the
    two building blocks that make this possible
  * Path.open() used as a context manager closes the file even if the code
    inside raises -- a bare Path.open() call without "with" does not

Run: python level_07_idempotent_setup_and_teardown.py
"""
import shutil
import tempfile
from pathlib import Path


def ensure_workspace(root: Path) -> Path:
    """Set up a scratch workspace. Safe to call repeatedly (e.g. from a
    retried job) -- never raises just because it already ran once."""
    lock_dir = root / "workspace" / "lock"
    lock_dir.mkdir(parents=True, exist_ok=True)
    marker = lock_dir / "READY"
    marker.write_text("ready\n")   # write_text always overwrites, so this is idempotent too
    return lock_dir


def teardown_workspace(root: Path) -> None:
    """Tear the workspace back down. Safe to call repeatedly, and safe to
    call even if setup partially failed and never finished."""
    lock_dir = root / "workspace" / "lock"
    (lock_dir / "READY").unlink(missing_ok=True)   # would raise FileNotFoundError without this
    if lock_dir.exists():
        lock_dir.rmdir()
    workspace_dir = root / "workspace"
    if workspace_dir.exists() and not any(workspace_dir.iterdir()):
        workspace_dir.rmdir()


if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl07_"))

    try:
        # calling setup TWICE must not raise -- this is the retry-safety property
        first = ensure_workspace(tmp_dir)
        second = ensure_workspace(tmp_dir)
        assert first == second
        assert (tmp_dir / "workspace" / "lock" / "READY").exists()

        # tearing down twice must ALSO not raise
        teardown_workspace(tmp_dir)
        teardown_workspace(tmp_dir)   # nothing left to remove -- must be a safe no-op, not a crash
        assert not (tmp_dir / "workspace").exists()

        # --- Path.open() as a context manager: guaranteed close on error -----
        target = tmp_dir / "resource.txt"
        target.write_text("payload")

        closed_via_context_manager = False
        with target.open("r") as f:
            handle = f
            _ = f.read()
        closed_via_context_manager = handle.closed
        assert closed_via_context_manager is True

        # if the body raises, the context manager STILL closes the handle --
        # this is the whole point of preferring "with path.open(...)" over a
        # bare "f = path.open(...)" that skips closing on the error path
        handle2 = None
        try:
            with target.open("r") as f:
                handle2 = f
                raise RuntimeError("pretend something goes wrong mid-read")
        except RuntimeError:
            pass
        assert handle2.closed is True   # closed despite the exception

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
