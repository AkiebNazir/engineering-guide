"""
LEVEL 08 (advanced) - interop: redirect_stdout/redirect_stderr for capturing output
========================================================================================
You will learn
  * redirect_stdout(target) temporarily replaces sys.stdout for the `with` block
  * redirect_stderr(target) does the same for sys.stderr
  * pairing this with io.StringIO is exactly how a test captures print() output
  * the redirect is undone automatically, even if the block raises

Run: python level_08_redirect_stdout.py
"""
import io
import sys
from contextlib import redirect_stderr, redirect_stdout


def noisy_function(should_fail: bool = False):
    print("starting work")
    print("a warning occurred", file=sys.stderr)
    if should_fail:
        raise RuntimeError("noisy_function failed")
    print("work finished")


if __name__ == "__main__":
    # ---- capture stdout the way a test would --------------------------------
    out = io.StringIO()
    with redirect_stdout(out):
        noisy_function()
    captured = out.getvalue()
    print(f"captured stdout: {captured!r}")
    assert "starting work" in captured
    assert "work finished" in captured

    # ---- stdout and stderr redirect independently ---------------------------
    out2, err2 = io.StringIO(), io.StringIO()
    with redirect_stdout(out2), redirect_stderr(err2):
        noisy_function()
    assert "starting work" in out2.getvalue()
    assert "a warning occurred" in err2.getvalue()
    assert "a warning occurred" not in out2.getvalue()   # each stream stayed separate

    # ---- the redirect is undone once the block ends -------------------------
    real_stdout_before = sys.stdout
    with redirect_stdout(io.StringIO()):
        assert sys.stdout is not real_stdout_before
    assert sys.stdout is real_stdout_before              # restored automatically

    # ---- redirect is undone even if the block raises -------------------------
    out3 = io.StringIO()
    raised = None
    try:
        with redirect_stdout(out3):
            noisy_function(should_fail=True)
    except RuntimeError as e:
        raised = e
    assert raised is not None
    assert sys.stdout is real_stdout_before              # still restored despite the exception
    assert "starting work" in out3.getvalue()             # output up to the failure was captured

    print("OK")
