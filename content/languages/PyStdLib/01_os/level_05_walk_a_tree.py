"""
LEVEL 05 (advanced) - os.walk: a real tree-processing pattern
=================================================================
You will learn
  * os.walk() yields (dirpath, dirnames, filenames) top-down, one dir at a time
  * building a real report (total bytes per file extension) while walking
  * pruning a subtree from the walk by mutating dirnames IN PLACE
  * why reassigning dirnames (instead of mutating it) silently does nothing

Run: python level_05_walk_a_tree.py
"""
import os
import shutil
import tempfile
from collections import defaultdict

if __name__ == "__main__":
    root = tempfile.mkdtemp(prefix="pystdlib_os_lvl05_")

    try:
        # build a small tree:
        #   root/a.txt (3 bytes)          root/skip_me/big.txt (100 bytes, must be skipped)
        #   root/sub/b.txt (4 bytes)      root/sub/c.log (2 bytes)
        os.makedirs(os.path.join(root, "sub"))
        os.makedirs(os.path.join(root, "skip_me"))
        with open(os.path.join(root, "a.txt"), "w") as f:
            f.write("aaa")
        with open(os.path.join(root, "sub", "b.txt"), "w") as f:
            f.write("bbbb")
        with open(os.path.join(root, "sub", "c.log"), "w") as f:
            f.write("cc")
        with open(os.path.join(root, "skip_me", "big.txt"), "w") as f:
            f.write("x" * 100)

        bytes_by_ext = defaultdict(int)
        visited_dirs = []

        for dirpath, dirnames, filenames in os.walk(root):
            visited_dirs.append(dirpath)

            # prune: never descend into a directory named "skip_me". This MUST
            # mutate dirnames in place (slice assignment) -- os.walk keeps its
            # own reference to this exact list object and reads it again before
            # recursing into each entry.
            dirnames[:] = [d for d in dirnames if d != "skip_me"]

            for name in filenames:
                full = os.path.join(dirpath, name)
                ext = os.path.splitext(name)[1]
                bytes_by_ext[ext] += os.stat(full).st_size

        # the pruned directory was never visited or measured
        assert not any(v.endswith("skip_me") for v in visited_dirs)
        assert bytes_by_ext[".txt"] == 3 + 4          # a.txt + b.txt, NOT big.txt
        assert bytes_by_ext[".log"] == 2
        assert ".txt" in bytes_by_ext and bytes_by_ext.get(".txt") != 3 + 4 + 100

        # prove the "reassign instead of mutate" mistake really does nothing:
        # walk again but reassign the name -- skip_me gets visited anyway.
        visited_again = []
        for dirpath, dirnames, filenames in os.walk(root):
            visited_again.append(dirpath)
            dirnames = [d for d in dirnames if d != "skip_me"]   # BUG: rebinds the local name only
        assert any(v.endswith("skip_me") for v in visited_again)

        print("OK")
    finally:
        shutil.rmtree(root, ignore_errors=True)
