"""
LEVEL 10 (capstone) - A tiny atomic, mtime-aware backup tool
================================================================
You will learn (by combining almost everything from levels 1-9)
  * os.walk to find every source file, os.makedirs(exist_ok=True) to mirror
    directories, os.stat to skip files that are already up to date by mtime
  * raw os.open/os.read/os.write/os.close to copy file bytes without pulling
    in shutil
  * os.urandom to build a collision-safe temp filename, then os.replace to
    make the write atomic (either the old or the fully-written new file is
    visible -- never a half-written one)
  * os.chmod to carry the source file's permission bits over to the backup
  * os.getpid()/os.cpu_count() surfaced in a tiny summary, like a real tool

Run: python level_10_atomic_backup_tool.py
"""
import os
import shutil
import stat
import tempfile
import time


def backup_tree(src_root: str, dst_root: str) -> list[str]:
    """Mirror every file under src_root into dst_root, skipping files whose
    destination is already at least as new. Returns the relative paths that
    were actually (re)written."""
    written = []
    for dirpath, _dirnames, filenames in os.walk(src_root):
        rel_dir = os.path.relpath(dirpath, src_root)
        dst_dir = os.path.join(dst_root, rel_dir) if rel_dir != "." else dst_root
        os.makedirs(dst_dir, exist_ok=True)

        for name in filenames:
            src_path = os.path.join(dirpath, name)
            dst_path = os.path.join(dst_dir, name)
            src_info = os.stat(src_path)

            if os.path.exists(dst_path) and os.stat(dst_path).st_mtime >= src_info.st_mtime:
                continue   # destination already current -- nothing to do

            # copy bytes with raw file descriptors, into a uniquely-named
            # temp file so a crash mid-write never leaves a half-written
            # file at the real destination path
            temp_name = dst_path + ".tmp-" + os.urandom(4).hex()
            in_fd = os.open(src_path, os.O_RDONLY)
            try:
                out_fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                try:
                    while chunk := os.read(in_fd, 65536):
                        os.write(out_fd, chunk)
                finally:
                    os.close(out_fd)
            finally:
                os.close(in_fd)

            os.chmod(temp_name, stat.S_IMODE(src_info.st_mode))   # carry over permissions
            os.replace(temp_name, dst_path)                       # atomic: rename in place
            written.append(os.path.join(rel_dir, name) if rel_dir != "." else name)
    return written


if __name__ == "__main__":
    workspace = tempfile.mkdtemp(prefix="pystdlib_os_lvl10_")
    src = os.path.join(workspace, "src")
    dst = os.path.join(workspace, "backup")

    try:
        os.makedirs(os.path.join(src, "nested"))
        with open(os.path.join(src, "a.txt"), "w") as f:
            f.write("version 1")
        with open(os.path.join(src, "nested", "b.txt"), "w") as f:
            f.write("nested file")
        os.chmod(os.path.join(src, "a.txt"), 0o640)

        # first backup: everything is new, everything gets written
        first_pass = backup_tree(src, dst)
        assert sorted(first_pass) == sorted(["a.txt", os.path.join("nested", "b.txt")])
        with open(os.path.join(dst, "a.txt")) as f:
            assert f.read() == "version 1"
        with open(os.path.join(dst, "nested", "b.txt")) as f:
            assert f.read() == "nested file"
        # permissions carried over from the source file
        assert stat.S_IMODE(os.stat(os.path.join(dst, "a.txt")).st_mode) == 0o640

        # second backup with nothing changed: mtimes are equal, nothing to copy
        second_pass = backup_tree(src, dst)
        assert second_pass == []

        # modify one file with a strictly later mtime, then back up again --
        # only that one file should be (re)written
        time.sleep(0.01)
        with open(os.path.join(src, "a.txt"), "w") as f:
            f.write("version 2, changed")
        os.utime(os.path.join(src, "a.txt"), (time.time() + 1, time.time() + 1))

        third_pass = backup_tree(src, dst)
        assert third_pass == ["a.txt"]
        with open(os.path.join(dst, "a.txt")) as f:
            assert f.read() == "version 2, changed"
        with open(os.path.join(dst, "nested", "b.txt")) as f:
            assert f.read() == "nested file"   # untouched file, still correct

        # no leftover .tmp-* files: os.replace always cleans up the temp name
        assert not any(name.startswith("a.txt.tmp-") for name in os.listdir(dst))

        print(f"backup tool ran under pid={os.getpid()} on a machine with cpu_count={os.cpu_count()}")
        print("OK")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
