"""
LEVEL 07 (advanced) - streaming a running process's stdout, line by line
============================================================================
You will learn
  * how to read a child process's output AS IT PRODUCES IT, rather than
    waiting for it to finish (what run()/communicate() do)
  * iterating `for line in proc.stdout` blocks until each line arrives,
    letting you react to output in real time
  * the resource-management/lifecycle discipline this needs: using Popen
    as a context manager so the process is always waited-on and its pipes
    closed, even if you stop reading early or an exception occurs

Run: python level_07_streaming_stdout.py
"""
import subprocess
import sys

# A child that prints one line, sleeps briefly, repeats -- standing in for
# any real long-running process (a build, a migration, a download).
CHILD_CODE = """
import sys, time
for i in range(5):
    print(f"step {i}", flush=True)
    time.sleep(0.02)
sys.exit(0)
"""


def main() -> None:
    seen_lines = []

    # --- the lifecycle-safe pattern: Popen as a context manager -------------
    # bufsize=1 (line-buffered) + text=True makes each `readline`/iteration
    # step return one decoded line as soon as it's flushed by the child.
    with subprocess.Popen(
        [sys.executable, "-c", CHILD_CODE],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as proc:
        for line in proc.stdout:            # blocks per line, not until EOF
            seen_lines.append(line.rstrip("\n"))
        # the `with` block's __exit__ calls proc.wait() for us, so by the
        # time we're back outside it, returncode is guaranteed to be set.

    assert seen_lines == ["step 0", "step 1", "step 2", "step 3", "step 4"]
    assert proc.returncode == 0
    assert proc.stdout.closed, "the context manager must close the pipe on exit"

    # --- stopping early: the context manager still cleans up properly ------
    stopped_lines = []
    with subprocess.Popen(
        [sys.executable, "-c", CHILD_CODE],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as proc2:
        for line in proc2.stdout:
            stopped_lines.append(line.rstrip("\n"))
            if len(stopped_lines) == 2:
                proc2.terminate()   # stop the child early; don't wait for all 5 lines
                break

    assert stopped_lines == ["step 0", "step 1"]
    # __exit__ waited for termination and closed the pipe even though we
    # broke out of the loop early -- no leaked process, no leaked file handle.
    assert proc2.returncode is not None
    assert proc2.stdout.closed

    print("OK")


if __name__ == "__main__":
    main()
