"""
LEVEL 01 (basic) - Reading environment variables with os.environ / os.getenv
=============================================================================
You will learn
  * os.environ is a dict-like snapshot of the process environment
  * os.getenv(key, default) is the safe read (never raises KeyError)
  * writing os.environ["KEY"] = value is how you actually set one for real
  * why os.putenv exists but is NOT the way to update your own process's view

Run: python level_01_environment_variables.py
"""
import os

if __name__ == "__main__":
    # os.environ behaves like a dict: every currently-set environment variable
    # is a key. PATH exists on essentially every machine this could run on.
    assert "PATH" in os.environ
    assert isinstance(os.environ["PATH"], str)

    # os.getenv is the safe read: missing key -> default (None if you don't ask
    # for one), never a KeyError. This is the one you reach for 90% of the time.
    missing = os.getenv("THIS_VAR_DEFINITELY_DOES_NOT_EXIST_12345")
    assert missing is None

    with_default = os.getenv("THIS_VAR_DEFINITELY_DOES_NOT_EXIST_12345", "fallback")
    assert with_default == "fallback"

    # os.environ["KEY"] directly (no default) DOES raise KeyError if unset --
    # that's the difference between os.environ[...] and os.getenv(...).
    try:
        _ = os.environ["THIS_VAR_DEFINITELY_DOES_NOT_EXIST_12345"]
        raise AssertionError("expected KeyError")
    except KeyError:
        pass

    # The correct way to SET a variable so your own process sees the change
    # immediately is to assign into os.environ directly.
    os.environ["PYSTDLIB_DEMO_VAR"] = "hello"
    assert os.getenv("PYSTDLIB_DEMO_VAR") == "hello"

    # os.putenv() also exists and updates the real OS-level process environment
    # (what a child process launched afterwards would inherit), but it does NOT
    # refresh the os.environ dict cache in THIS process -- read the value back
    # through os.environ afterwards and it still shows the old value. This is
    # exactly why the docs say "don't call os.putenv directly, assign to
    # os.environ instead" -- assigning to os.environ calls putenv for you AND
    # keeps the dict in sync.
    os.environ["PYSTDLIB_DEMO_VAR"] = "before"
    os.putenv("PYSTDLIB_DEMO_VAR", "after-via-putenv")
    # the process-level environment changed, but our cached dict did not:
    assert os.environ["PYSTDLIB_DEMO_VAR"] == "before"

    # clean up after ourselves
    del os.environ["PYSTDLIB_DEMO_VAR"]
    assert "PYSTDLIB_DEMO_VAR" not in os.environ

    print("OK")
