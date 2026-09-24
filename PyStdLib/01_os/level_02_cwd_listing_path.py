"""
LEVEL 02 (core) - The core surface: getcwd/chdir, listdir vs scandir, os.path, process info
=============================================================================================
You will learn
  * os.getcwd()/os.chdir() to read and change the working directory
  * os.listdir() (names only) vs os.scandir() (richer DirEntry objects)
  * the os.path basics: join, split, exists, isfile, isdir, abspath
  * os.getpid()/os.cpu_count() as cheap process/host info

Run: python level_02_cwd_listing_path.py
"""
import os
import shutil
import tempfile

if __name__ == "__main__":
    start_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_os_lvl02_")

    try:
        # os.chdir moves the process's working directory; os.getcwd reads it back.
        os.chdir(tmp_dir)
        # macOS may report /tmp/... vs the symlinked /private/tmp/... -- compare
        # through realpath so the assertion is robust on any platform.
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_dir)

        # populate a couple of files and a subdirectory to list
        with open(os.path.join(tmp_dir, "a.txt"), "w") as f:
            f.write("aaa")
        with open(os.path.join(tmp_dir, "b.txt"), "w") as f:
            f.write("bb")
        os.mkdir(os.path.join(tmp_dir, "subdir"))

        # os.listdir: just the names, in arbitrary order
        names = sorted(os.listdir(tmp_dir))
        assert names == ["a.txt", "b.txt", "subdir"]

        # os.scandir: an iterator of DirEntry objects -- name, path, and cheap
        # is_file()/is_dir()/stat() that often avoids a fresh syscall (level 6
        # measures the actual speed difference). Must be closed or used as a
        # context manager to release the underlying directory handle.
        with os.scandir(tmp_dir) as entries:
            by_name = {e.name: e for e in entries}
        assert set(by_name) == {"a.txt", "b.txt", "subdir"}
        assert by_name["a.txt"].is_file() is True
        assert by_name["subdir"].is_dir() is True
        assert by_name["a.txt"].stat().st_size == 3   # "aaa"

        # os.path basics -- join builds a platform-correct path, split reverses it
        joined = os.path.join(tmp_dir, "subdir", "c.txt")
        head, tail = os.path.split(joined)
        assert head == os.path.join(tmp_dir, "subdir")
        assert tail == "c.txt"

        assert os.path.exists(joined) is False
        with open(joined, "w") as f:
            f.write("c")
        assert os.path.exists(joined) is True
        assert os.path.isfile(joined) is True
        assert os.path.isdir(joined) is False
        assert os.path.isdir(os.path.dirname(joined)) is True

        # abspath resolves a relative path against the current working directory
        # (which we changed to tmp_dir above) without touching the filesystem.
        # Compare through realpath: os.getcwd() (which abspath uses internally)
        # returns the OS's resolved path, and on macOS /tmp is itself a symlink
        # to /private/tmp, so the raw strings can differ even when they name
        # the exact same location.
        os.chdir(tmp_dir)
        assert os.path.realpath(os.path.abspath("a.txt")) == os.path.realpath(os.path.join(tmp_dir, "a.txt"))

        # cheap process/host info, no filesystem involved
        pid = os.getpid()
        assert isinstance(pid, int) and pid > 0
        cpu_count = os.cpu_count()
        assert cpu_count is None or cpu_count >= 1

        print("OK")
    finally:
        os.chdir(start_dir)   # always restore -- a stale cwd would break later tests
        shutil.rmtree(tmp_dir)
