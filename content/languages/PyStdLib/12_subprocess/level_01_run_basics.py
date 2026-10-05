"""
LEVEL 01 (basic) - subprocess.run(): launch a command, get its result
========================================================================
You will learn
  * run() launches a program, waits for it to finish, and returns a
    CompletedProcess with .returncode, .stdout, .stderr
  * capture_output=True captures both streams; text=True decodes them as
    str instead of bytes
  * command + arguments are passed as a LIST, not one shell string --
    this is the safe default (more on why in a later level)

Run: python level_01_run_basics.py
"""
import subprocess
import sys


def main() -> None:
    # A "command" other programs can run: here, a tiny Python child process.
    # Using [sys.executable, "-c", ...] keeps this demo fully portable --
    # no dependency on any particular OS binary being installed.
    result = subprocess.run(
        [sys.executable, "-c", "print('hello from child process')"],
        capture_output=True,
        text=True,
    )

    # --- CompletedProcess exposes exactly what happened ---------------------
    assert result.returncode == 0                              # 0 means success
    assert result.stdout == "hello from child process\n"       # captured, decoded to str
    assert result.stderr == ""                                 # nothing was written to stderr
    assert isinstance(result.stdout, str)                      # text=True -> str, not bytes

    # --- args are echoed back on the result for inspection/debugging --------
    assert result.args == [sys.executable, "-c", "print('hello from child process')"]

    # --- without text=True, streams come back as raw bytes ------------------
    raw_result = subprocess.run(
        [sys.executable, "-c", "print('raw bytes')"],
        capture_output=True,
    )
    assert isinstance(raw_result.stdout, bytes)
    assert raw_result.stdout == b"raw bytes\n"

    # --- a non-zero exit code is just data on the result -- run() does NOT
    # raise for it unless you ask (see check=True in a later level)
    failing = subprocess.run(
        [sys.executable, "-c", "import sys; sys.exit(3)"],
        capture_output=True,
        text=True,
    )
    assert failing.returncode == 3
    assert failing.stdout == ""

    print("OK")


if __name__ == "__main__":
    main()
