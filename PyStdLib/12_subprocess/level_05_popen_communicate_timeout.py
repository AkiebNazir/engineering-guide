"""
LEVEL 05 (core) - Popen + communicate(timeout=): handling a real TimeoutExpired
==================================================================================
You will learn
  * Popen gives you a live handle to a running child process, lower-level
    than run()
  * communicate(timeout=...) waits up to `timeout` seconds for the child to
    finish, sending optional input and collecting all output
  * on a real timeout, communicate() raises TimeoutExpired -- and the child
    process is left RUNNING; you must kill it yourself and clean up

Run: python level_05_popen_communicate_timeout.py
"""
import subprocess
import sys


def main() -> None:
    # --- the normal, non-timing-out path -------------------------------------
    proc = subprocess.Popen(
        [sys.executable, "-c", "print('quick result')"],
        stdout=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(timeout=5)
    assert stdout == "quick result\n"
    assert proc.returncode == 0

    # --- trigger a REAL TimeoutExpired ----------------------------------------
    slow_proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        stdout=subprocess.PIPE,
    )
    try:
        slow_proc.communicate(timeout=0.2)
        raised = False
    except subprocess.TimeoutExpired as exc:
        raised = True
        error = exc

    assert raised, "a 5-second sleep must trip a 0.2-second communicate() timeout"
    assert error.timeout == 0.2
    assert error.cmd == slow_proc.args

    # --- the child is STILL RUNNING after the timeout -- communicate() does
    # not kill it for you. Confirm it, then clean it up properly.
    assert slow_proc.poll() is None, "the child must still be alive right after the timeout"

    slow_proc.kill()
    # after kill(), communicate() again both waits for exit and drains pipes,
    # which is required to avoid leaving a zombie process behind.
    slow_proc.communicate()
    assert slow_proc.poll() is not None, "the child must be reaped after kill()+communicate()"
    assert slow_proc.returncode != 0  # killed, not a clean exit

    print("OK")


if __name__ == "__main__":
    main()
