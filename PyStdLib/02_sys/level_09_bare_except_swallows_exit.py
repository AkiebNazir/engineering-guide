"""
LEVEL 09 (advanced) - Production trap: a bare "except:" swallows sys.exit()
==============================================================================
You will learn
  * SystemExit inherits from BaseException, NOT Exception -- so "except
    Exception:" correctly lets sys.exit() propagate and actually end the process
  * a bare "except:" (no type at all) catches EVERYTHING, including
    SystemExit and KeyboardInterrupt -- silently turning a real shutdown
    request into "nothing happened, keep going"
  * demonstrated for real via two child processes with real, different
    observable outcomes -- not just described

Run: python level_09_bare_except_swallows_exit.py
"""
import subprocess
import sys

# "except Exception:" is the CORRECT, narrow catch: SystemExit is not an
# Exception subclass, so it is never caught here, and the process really
# does exit with status 5 -- the print after the try/except never runs.
CORRECT_CHILD = '''
import sys
try:
    sys.exit(5)
except Exception:
    print("caught it (this should never print)")
print("execution continued (this should never print either)")
'''

# a bare "except:" is written to mean "catch any error", but it also catches
# BaseException subclasses like SystemExit -- so the intended shutdown is
# silently absorbed and the script just... keeps running.
BUGGY_CHILD = '''
import sys
try:
    sys.exit(5)
except:
    pass
print("execution continued")
sys.exit(0)
'''

if __name__ == "__main__":
    correct = subprocess.run(
        [sys.executable, "-c", CORRECT_CHILD], capture_output=True, text=True,
    )
    assert correct.returncode == 5           # the exit really happened
    assert correct.stdout == ""              # nothing after sys.exit ever ran

    buggy = subprocess.run(
        [sys.executable, "-c", BUGGY_CHILD], capture_output=True, text=True,
    )
    assert buggy.returncode == 0                          # NOT 5 -- the exit(5) was swallowed
    assert buggy.stdout == "execution continued\n"         # code after the "exit" kept running

    # the fix generalizes: always name the exception type(s) you actually
    # intend to handle. "except Exception:" is almost always what you meant
    # by a broad catch -- SystemExit/KeyboardInterrupt/GeneratorExit are
    # deliberately excluded from it for exactly this reason.
    assert not issubclass(SystemExit, Exception)
    assert issubclass(SystemExit, BaseException)

    print("OK")
