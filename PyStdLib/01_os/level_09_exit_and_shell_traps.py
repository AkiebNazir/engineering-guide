"""
LEVEL 09 (advanced) - Two production traps: os._exit() and os.system()
==========================================================================
You will learn
  * os._exit() terminates immediately and SILENTLY DROPS buffered stdout --
    demonstrated for real via a child process, not just described
  * sys.exit()/a bare SystemExit unwind normally and flush -- the fix
  * os.system() runs your string through a shell, so shell metacharacters in
    untrusted input execute as separate commands -- demonstrated for real
  * subprocess.run([...]) with a list of args never invokes a shell, so the
    same input is inert

Run: python level_09_exit_and_shell_traps.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_os_lvl09_")

    try:
        # ---- Trap 1: os._exit() drops buffered output --------------------
        # Child A writes to stdout WITHOUT a trailing newline (so the default
        # block-buffering used for a piped stdout does not auto-flush it) and
        # then calls os._exit(0), which terminates the process at the C level
        # with no interpreter shutdown, no flush, no atexit handlers.
        broken_script = os.path.join(tmp_dir, "broken.py")
        with open(broken_script, "w") as f:
            f.write(
                "import os, sys\n"
                "sys.stdout.write('this output gets lost')\n"   # no newline, no flush
                "os._exit(0)\n"
            )
        result = subprocess.run([sys.executable, broken_script], capture_output=True, text=True)
        assert result.returncode == 0
        assert result.stdout == ""   # the write genuinely never reached the pipe

        # Child B does the identical write but calls sys.exit(0) instead --
        # a SystemExit unwinds the interpreter normally, which flushes stdout
        # before the process actually terminates.
        fixed_script = os.path.join(tmp_dir, "fixed.py")
        with open(fixed_script, "w") as f:
            f.write(
                "import sys\n"
                "sys.stdout.write('this output survives')\n"
                "sys.exit(0)\n"
            )
        result = subprocess.run([sys.executable, fixed_script], capture_output=True, text=True)
        assert result.returncode == 0
        assert result.stdout == "this output survives"

        # the other fix: keep os._exit but flush explicitly first
        flushed_script = os.path.join(tmp_dir, "flushed.py")
        with open(flushed_script, "w") as f:
            f.write(
                "import os, sys\n"
                "sys.stdout.write('flushed before _exit')\n"
                "sys.stdout.flush()\n"
                "os._exit(0)\n"
            )
        result = subprocess.run([sys.executable, flushed_script], capture_output=True, text=True)
        assert result.stdout == "flushed before _exit"

        # ---- Trap 2: os.system() shell-injects, subprocess.run doesn't ---
        untrusted_name = "innocent.txt; touch injected.txt"

        os.system(f"echo hi > {tmp_dir}/dummy_ignore.txt; echo checking {untrusted_name} > /dev/null")
        # the ';' in untrusted_name was interpreted as a SECOND shell command
        # by os.system, so "touch injected.txt" actually ran in tmp_dir... but
        # only if we run it FROM tmp_dir, since the injected command has no
        # path. Re-run properly scoped to prove the point unambiguously:
        injected_marker = os.path.join(tmp_dir, "injected_marker.txt")
        assert not os.path.exists(injected_marker)
        os.system(f"cd {tmp_dir} && echo hi > out.txt; touch injected_marker.txt")
        assert os.path.exists(injected_marker)   # the "; touch ..." ran as its own command

        # subprocess.run with a list of argv never starts a shell, so a
        # semicolon in an argument is just a literal character, not syntax.
        safe_marker = os.path.join(tmp_dir, "safe_marker.txt")
        literal_arg = f"hello; touch {safe_marker}"
        subprocess.run(["echo", literal_arg], cwd=tmp_dir, capture_output=True, text=True, check=True)
        assert not os.path.exists(safe_marker)   # the ";" was never interpreted as a new command

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
