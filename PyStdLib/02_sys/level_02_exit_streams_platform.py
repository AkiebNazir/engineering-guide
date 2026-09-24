"""
LEVEL 02 (core) - Core surface: sys.exit, the std streams, platform/version info
===================================================================================
You will learn
  * sys.exit(code) raises SystemExit(code); the interpreter turns it into a
    real process exit code once nothing catches it
  * sys.stdin/sys.stdout/sys.stderr are plain file objects (same .write() API
    as a file you opened yourself)
  * sys.platform and sys.version_info for portable environment checks
  * sys.getsizeof() reports the SHALLOW size of one object only

Run: python level_02_exit_streams_platform.py
"""
import subprocess
import sys

if __name__ == "__main__":
    # --- sys.exit / SystemExit -------------------------------------------
    # sys.exit(code) doesn't "kill" the process directly -- it raises
    # SystemExit(code). Prove this by catching it right here.
    try:
        sys.exit(7)
        raise AssertionError("unreachable")
    except SystemExit as e:
        assert e.code == 7

    # to see it actually END a process with that code, run a real child
    result = subprocess.run([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert result.returncode == 7

    # sys.exit() with no argument (or None) exits with status 0
    result = subprocess.run([sys.executable, "-c", "import sys; sys.exit()"])
    assert result.returncode == 0

    # sys.exit("message") is also legal: for a STRING argument, Python prints
    # the message to stderr and exits with status 1
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.exit('boom')"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "boom" in result.stderr

    # --- std streams as file objects --------------------------------------
    assert hasattr(sys.stdout, "write") and hasattr(sys.stdout, "flush")
    assert hasattr(sys.stderr, "write") and hasattr(sys.stderr, "flush")
    assert hasattr(sys.stdin, "read")
    # stdout and stderr are separate streams -- writing to one never appears
    # on the other, which is exactly why CLIs send normal output to stdout
    # and diagnostics/errors to stderr
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('to-out'); sys.stderr.write('to-err')"],
        capture_output=True, text=True,
    )
    assert result.stdout == "to-out"
    assert result.stderr == "to-err"

    # --- platform / version checks -----------------------------------------
    assert sys.platform in ("darwin", "linux", "win32", "cygwin", "aix") or sys.platform.startswith(("linux", "freebsd"))
    # version_info supports direct tuple comparison -- this is how real code
    # gates on a minimum Python version without string-parsing sys.version
    assert sys.version_info >= (3, 8)
    assert sys.version_info.major == 3
    assert isinstance(sys.version_info.minor, int)

    # --- getsizeof is SHALLOW ------------------------------------------------
    small_list = [1, 2, 3]
    bigger_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # more elements -> more pointer slots -> a bigger reported size ...
    assert sys.getsizeof(bigger_list) > sys.getsizeof(small_list)
    # ... but getsizeof does NOT add up what those elements themselves cost.
    # A list holding one huge string reports the same list overhead as a list
    # holding one tiny string -- the string's own bytes aren't in this number.
    list_of_tiny = ["x"]
    list_of_huge = ["x" * 100_000]
    assert sys.getsizeof(list_of_tiny) == sys.getsizeof(list_of_huge)

    print("OK")
