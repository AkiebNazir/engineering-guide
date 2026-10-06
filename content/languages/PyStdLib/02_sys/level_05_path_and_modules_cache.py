"""
LEVEL 05 (advanced) - sys.path resolution order and the sys.modules cache
=============================================================================
You will learn
  * sys.path is an ordered list of directories searched (in order!) for a
    module name -- the first match anywhere on the list wins
  * once imported, a module is cached in sys.modules by name; every later
    "import name" returns the SAME object without re-reading the file
  * editing the file on disk after the first import has NO effect until the
    cache entry is removed
  * del sys.modules[name] forces the next import to re-read the file fresh

Run: python level_05_path_and_modules_cache.py
"""
import importlib
import os
import shutil
import sys
import tempfile

MODULE_NAME = "pystdlib_demo_module_lvl05"

if __name__ == "__main__":
    dir_a = tempfile.mkdtemp(prefix="pystdlib_sys_lvl05_a_")
    dir_b = tempfile.mkdtemp(prefix="pystdlib_sys_lvl05_b_")

    assert MODULE_NAME not in sys.modules   # make sure we start clean

    try:
        # two directories, each with a module of the SAME name but different content
        with open(os.path.join(dir_a, f"{MODULE_NAME}.py"), "w") as f:
            f.write("SOURCE = 'a'\nVERSION = 1\n")
        with open(os.path.join(dir_b, f"{MODULE_NAME}.py"), "w") as f:
            f.write("SOURCE = 'b'\nVERSION = 99\n")

        # put dir_a FIRST on the search path -- sys.path[0] is checked before
        # anything else, so its copy of the module wins the name collision
        sys.path.insert(0, dir_a)
        sys.path.insert(1, dir_b)   # dir_b is present too, but later in the order

        mod = importlib.import_module(MODULE_NAME)
        assert mod.SOURCE == "a"          # dir_a's copy won, because it comes first
        assert sys.modules[MODULE_NAME] is mod   # now cached under its name

        # rewrite dir_a's file on disk -- the running module object is
        # unaffected: re-importing returns the SAME cached object, unchanged
        with open(os.path.join(dir_a, f"{MODULE_NAME}.py"), "w") as f:
            f.write("SOURCE = 'a-edited'\nVERSION = 2\n")
        mod_again = importlib.import_module(MODULE_NAME)
        assert mod_again is mod
        assert mod_again.SOURCE == "a"    # still the OLD value -- cache, not a re-read

        # force a fresh import by evicting the cache entry ourselves
        del sys.modules[MODULE_NAME]
        fresh = importlib.import_module(MODULE_NAME)
        assert fresh is not mod                # a brand new module object
        assert fresh.SOURCE == "a-edited"      # this time it actually re-read the file

        # now remove dir_a from the path entirely and clear the cache again --
        # dir_b's copy is the only one left to find, so IT wins this time,
        # proving path ORDER (not just presence) decides the winner
        sys.path.remove(dir_a)
        del sys.modules[MODULE_NAME]
        fallback = importlib.import_module(MODULE_NAME)
        assert fallback.SOURCE == "b"
        assert fallback.VERSION == 99

        print("OK")
    finally:
        sys.modules.pop(MODULE_NAME, None)
        for d in (dir_a, dir_b):
            if d in sys.path:
                sys.path.remove(d)
        shutil.rmtree(dir_a, ignore_errors=True)
        shutil.rmtree(dir_b, ignore_errors=True)
