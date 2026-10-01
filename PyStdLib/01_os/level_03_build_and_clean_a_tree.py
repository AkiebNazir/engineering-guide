"""
LEVEL 03 (core) - Idiom: build a directory tree, inspect it, clean it up
==========================================================================
You will learn
  * os.makedirs(exist_ok=True) to create nested directories without failing
    on ones that already exist
  * os.stat() for size, mtime (modification time), and mode (permission bits)
  * os.rename()/os.replace() for renaming/overwriting a file
  * os.remove()/os.rmdir()/os.removedirs() for tearing a tree back down

Run: python level_03_build_and_clean_a_tree.py
"""
import os
import shutil
import stat
import tempfile
import time

if __name__ == "__main__":
    root = tempfile.mkdtemp(prefix="pystdlib_os_lvl03_")

    try:
        # makedirs(exist_ok=True) creates every missing intermediate directory
        # and does NOT raise if the deepest one already exists -- unlike a bare
        # os.mkdir, which only makes one level and always fails on a duplicate.
        project = os.path.join(root, "project", "data", "raw")
        os.makedirs(project, exist_ok=True)
        os.makedirs(project, exist_ok=True)   # calling it again is a no-op, not an error
        assert os.path.isdir(project)

        # write a file, then inspect it with os.stat
        draft_path = os.path.join(project, "draft.csv")
        with open(draft_path, "w") as f:
            f.write("id,value\n1,10\n")

        info = os.stat(draft_path)
        assert info.st_size == len("id,value\n1,10\n")
        assert info.st_mtime <= time.time()          # modified at-or-before "now"
        # st_mode packs the file type AND the permission bits together; the
        # stat module's helpers pull the piece you actually want out of it.
        assert stat.S_ISREG(info.st_mode)             # "is a regular file"
        assert not stat.S_ISDIR(info.st_mode)

        # rename: move/rename within the same filesystem, fails if the
        # destination already exists on Windows (works either way on POSIX --
        # os.replace below is the portable, always-overwrite alternative).
        final_path = os.path.join(project, "final.csv")
        os.rename(draft_path, final_path)
        assert not os.path.exists(draft_path)
        assert os.path.exists(final_path)

        # replace: like rename, but guaranteed atomic-overwrite on every
        # platform even if the destination already exists -- the right choice
        # for "swap this file in" style updates (PyEngineering's atomic file
        # store topic builds directly on this).
        updated_path = os.path.join(project, "updated.csv")
        with open(updated_path, "w") as f:
            f.write("id,value\n1,999\n")
        os.replace(updated_path, final_path)
        with open(final_path) as f:
            assert f.read() == "id,value\n1,999\n"
        assert not os.path.exists(updated_path)

        # tear it back down: os.remove deletes a file, os.rmdir deletes ONE
        # empty directory, os.removedirs walks back up removing each now-empty
        # parent -- all three raise loudly on the wrong kind of target
        # (level 4 proves that), so remove the file before removing dirs.
        os.remove(final_path)
        assert not os.path.exists(final_path)

        os.removedirs(project)   # removes data/raw, then data, then project (all now empty)
        assert not os.path.exists(os.path.join(root, "project"))

        print("OK")
    finally:
        shutil.rmtree(root, ignore_errors=True)
