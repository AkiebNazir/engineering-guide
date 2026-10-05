"""
LEVEL 08 (advanced) - Interop: os.stat() + the stat module, then os.chmod()
==============================================================================
You will learn
  * os.stat().st_mode packs file type AND permission bits into one integer
  * the stat module's helpers (S_ISDIR, S_ISREG, S_IMODE, filemode) decode it
  * os.chmod() to change permission bits, and reading them back to confirm
  * os.access() as a quick "can I actually do X" check that doesn't require
    decoding st_mode yourself

Run: python level_08_stat_module_and_chmod.py
"""
import os
import shutil
import stat
import tempfile

if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_os_lvl08_")
    file_path = os.path.join(tmp_dir, "secret.txt")

    try:
        with open(file_path, "w") as f:
            f.write("shh")
        os.chmod(file_path, 0o644)   # rw-r--r--

        info = os.stat(file_path)

        # st_mode mixes "this is a regular file" with "these are its
        # permission bits" into one integer -- the stat module's S_IS*
        # predicates and S_IMODE isolate each piece correctly.
        assert stat.S_ISREG(info.st_mode)
        assert not stat.S_ISDIR(info.st_mode)
        assert stat.S_IMODE(info.st_mode) == 0o644

        # stat.filemode renders the same bits the way `ls -l` does -- handy
        # for debugging/logging, and a good sanity check that we decoded the
        # permission octal correctly.
        assert stat.filemode(info.st_mode) == "-rw-r--r--"

        # now lock it down to owner-read-only and confirm the change round-trips
        os.chmod(file_path, 0o400)
        info = os.stat(file_path)
        assert stat.S_IMODE(info.st_mode) == 0o400
        assert stat.filemode(info.st_mode) == "-r--------"

        # os.access() is the quick yes/no check -- it asks the OS directly
        # rather than making you decode st_mode by hand
        assert os.access(file_path, os.R_OK) is True
        # os.W_OK on a 0o400 file: on POSIX this correctly reports "not
        # writable"; skip this specific assertion when running as root, since
        # root ignores the write bit and the check would report True instead.
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            assert os.access(file_path, os.W_OK) is False

        # restore a normal writable mode so shutil.rmtree can clean up freely
        os.chmod(file_path, 0o644)
        assert os.access(file_path, os.W_OK) is True

        # the same S_IS* trick applies to directories
        dir_info = os.stat(tmp_dir)
        assert stat.S_ISDIR(dir_info.st_mode)
        assert not stat.S_ISREG(dir_info.st_mode)

        print("OK")
    finally:
        os.chmod(file_path, 0o644)   # belt-and-braces: guarantee cleanup can delete it
        shutil.rmtree(tmp_dir, ignore_errors=True)
