"""
LEVEL 02 (basic) - the core subprocess.run() API surface
============================================================
You will learn
  * input= sends data to the child's stdin
  * cwd= runs the child in a different working directory
  * subprocess.DEVNULL discards a stream instead of capturing it
  * check=True vs the default (check=False): when run() raises vs doesn't
  * timeout= bounds how long run() will wait before giving up

Run: python level_02_core_api.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    # --- input=: feed data to the child's stdin -----------------------------
    result = subprocess.run(
        [sys.executable, "-c", "import sys; data = sys.stdin.read(); print(data.upper())"],
        input="hello world",
        capture_output=True,
        text=True,
    )
    assert result.stdout == "HELLO WORLD\n"

    # --- cwd=: run the child somewhere specific -----------------------------
    workdir = Path(tempfile.mkdtemp(prefix="pystdlib_subprocess_"))
    try:
        (workdir / "marker.txt").write_text("found me")
        result = subprocess.run(
            [sys.executable, "-c", "print(open('marker.txt').read())"],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "found me"
    finally:
        (workdir / "marker.txt").unlink(missing_ok=True)
        workdir.rmdir()

    # --- DEVNULL: discard a stream instead of capturing or inheriting it ----
    result = subprocess.run(
        [sys.executable, "-c", "print('to stdout'); import sys; print('to stderr', file=sys.stderr)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    assert result.stdout == "to stdout\n"
    assert result.stderr is None  # discarded, not captured

    # --- check=False (the default): non-zero exit does NOT raise -----------
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.exit(1)"],
        capture_output=True,
    )
    assert result.returncode == 1  # no exception -- you must check it yourself

    # --- check=True: the same failure NOW raises -----------------------------
    try:
        subprocess.run(
            [sys.executable, "-c", "import sys; sys.exit(1)"],
            check=True,
            capture_output=True,
        )
        raised = False
    except subprocess.CalledProcessError:
        raised = True
    assert raised

    # --- timeout=: bounds how long run() will wait ---------------------------
    try:
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.2,
        )
        raised = False
    except subprocess.TimeoutExpired:
        raised = True
    assert raised, "a 5-second sleep must trip a 0.2-second timeout"

    print("OK")


if __name__ == "__main__":
    main()
