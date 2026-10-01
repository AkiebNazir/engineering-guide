"""
LEVEL 01 (basic) - sys.argv: the raw command-line arguments
===============================================================
You will learn
  * sys.argv[0] is the script path; sys.argv[1:] are the actual arguments
  * argv is always a list of strings -- you convert types yourself
  * spawning a real child process is how we prove argv changes with input,
    since this file itself is normally run with no arguments

Run: python level_01_argv.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

# A tiny standalone script that just reports what it received as argv.
CHILD_SOURCE = (
    "import sys\n"
    "print(len(sys.argv))\n"
    "for arg in sys.argv[1:]:\n"
    "    print(arg)\n"
)

if __name__ == "__main__":
    # When THIS file is run normally, sys.argv has exactly one element: the
    # path to this script. No flags were passed on the command line.
    assert len(sys.argv) == 1
    assert sys.argv[0].endswith("level_01_argv.py")

    # To see argv respond to real input, run a tiny child script with
    # different arguments -- argv[0] there is the CHILD's own path, and
    # everything after it is exactly what we passed on the command line.
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_sys_lvl01_")
    child_path = os.path.join(tmp_dir, "child.py")
    try:
        with open(child_path, "w") as f:
            f.write(CHILD_SOURCE)

        result = subprocess.run(
            [sys.executable, child_path, "--verbose", "42", "some file.txt"],
            capture_output=True, text=True, check=True,
        )
        lines = result.stdout.splitlines()

        # argv[0] (the script path) plus 3 real arguments = 4 total elements
        assert lines[0] == "4"
        # every element of argv is a STRING -- "42" arrives as "42", not 42
        assert lines[1:] == ["--verbose", "42", "some file.txt"]
        assert isinstance(lines[1], str)

        # running with no extra arguments at all leaves only argv[0]
        result_bare = subprocess.run(
            [sys.executable, child_path], capture_output=True, text=True, check=True,
        )
        assert result_bare.stdout.splitlines() == ["1"]

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
