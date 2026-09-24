"""
LEVEL 10 (capstone) - A tiny wc-style CLI, exercising levels 1-9 together
=============================================================================
You will learn (by combining almost everything from levels 1-9)
  * sys.argv for real file arguments, sys.platform/version_info in a --info
    flag, sys.stdout for results (flushed per file) vs sys.stderr for errors
  * sys.exc_info() to report exactly which real exception broke a given file
  * proper exit codes: 0 all good, 1 if any file failed, 2 for usage errors --
    caught explicitly so a broad handler never accidentally swallows them

Run: python level_10_wordcount_capstone.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

# The tool itself: for each path given on the command line, report its line/
# word/byte counts to stdout; a missing/unreadable file reports its real
# exception type to stderr and marks the overall run as failed, but does not
# stop it from processing the remaining files.
CHILD_SOURCE = '''
import sys

def count_one(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = data.count(b"\\n")
    words = len(data.split())
    return lines, words, len(data)

def main(argv):
    if "--info" in argv:
        sys.stdout.write(f"platform={sys.platform} py={sys.version_info.major}.{sys.version_info.minor}\\n")
        return 0
    paths = argv[1:]
    if not paths:
        sys.stderr.write(f"usage: {argv[0]} FILE [FILE...]\\n")
        return 2

    any_failed = False
    for path in paths:
        try:
            lines, words, size = count_one(path)
        except Exception:
            exc_type, exc_value, _ = sys.exc_info()
            sys.stderr.write(f"{path}: {exc_type.__name__}: {exc_value}\\n")
            any_failed = True
            continue
        sys.stdout.write(f"{path}: {lines} lines, {words} words, {size} bytes\\n")
        sys.stdout.flush()
    return 1 if any_failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''

if __name__ == "__main__":
    workspace = tempfile.mkdtemp(prefix="pystdlib_sys_lvl10_")
    tool_path = os.path.join(workspace, "wordcount.py")

    try:
        with open(tool_path, "w") as f:
            f.write(CHILD_SOURCE)

        good_file = os.path.join(workspace, "good.txt")
        with open(good_file, "w") as f:
            f.write("one two three\nfour five\n")
        missing_file = os.path.join(workspace, "does_not_exist.txt")

        # --info: pure sys.platform/version_info reporting, exit 0
        result = subprocess.run(
            [sys.executable, tool_path, "--info"], capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert f"platform={sys.platform}" in result.stdout

        # no arguments: usage error, exit code 2, nothing on stdout
        result = subprocess.run([sys.executable, tool_path], capture_output=True, text=True)
        assert result.returncode == 2
        assert result.stdout == ""
        assert "usage:" in result.stderr

        # one good file: exit 0, correct counts
        result = subprocess.run(
            [sys.executable, tool_path, good_file], capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout == f"{good_file}: 2 lines, 5 words, 24 bytes\n"

        # a good file AND a missing one: partial success -- exit 1, the good
        # file's result is still reported, the bad one's real exception type
        # (FileNotFoundError) is reported to stderr, not silently dropped
        result = subprocess.run(
            [sys.executable, tool_path, good_file, missing_file],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert good_file in result.stdout
        assert "FileNotFoundError" in result.stderr

        print("OK")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
