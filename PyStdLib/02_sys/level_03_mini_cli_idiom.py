"""
LEVEL 03 (core) - Idiom: a tiny CLI built only from argv + streams + exit
============================================================================
You will learn
  * the shape of a real (if tiny) command-line tool using nothing but
    sys.argv, sys.stdout, sys.stderr, and sys.exit
  * validating required arguments and reporting errors to stderr, not stdout
  * flushing stdout explicitly so progress is visible even when piped
  * returning a specific, meaningful exit code instead of always 0/1

Run: python level_03_mini_cli_idiom.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

# A tiny "greet" CLI: requires exactly one argument, the name to greet.
# Exit codes: 0 = success, 2 = usage error (missing/extra argument).
CHILD_SOURCE = '''
import sys

def main(argv):
    if len(argv) != 2:
        sys.stderr.write(f"usage: {argv[0]} NAME\\n")
        return 2
    name = argv[1]
    sys.stdout.write(f"preparing greeting for {name}...\\n")
    sys.stdout.flush()          # visible immediately even if stdout is piped
    sys.stdout.write(f"Hello, {name}!\\n")
    sys.stdout.flush()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''

if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_sys_lvl03_")
    child_path = os.path.join(tmp_dir, "greet.py")

    try:
        with open(child_path, "w") as f:
            f.write(CHILD_SOURCE)

        # the happy path: correct usage, exit 0, both progress lines on stdout
        result = subprocess.run(
            [sys.executable, child_path, "World"], capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout == "preparing greeting for World...\nHello, World!\n"
        assert result.stderr == ""

        # missing the required argument: usage error on stderr, exit code 2,
        # NOTHING printed to stdout (the tool bailed before doing any work)
        result = subprocess.run(
            [sys.executable, child_path], capture_output=True, text=True,
        )
        assert result.returncode == 2
        assert result.stdout == ""
        assert "usage:" in result.stderr

        # too many arguments is the same usage error
        result = subprocess.run(
            [sys.executable, child_path, "a", "b"], capture_output=True, text=True,
        )
        assert result.returncode == 2
        assert "usage:" in result.stderr

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
