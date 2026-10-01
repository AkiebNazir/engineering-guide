"""
LEVEL 04 (core) - suppress(): replacing try/except/pass, with real exceptions
=================================================================================
You will learn
  * suppress(ExcType) is exactly try/except ExcType: pass, spelled as a context manager
  * it only swallows the EXACT types you name -- a different exception still propagates
  * suppress() accepts multiple types, just like a multi-type except clause
  * this is demonstrated against REAL, triggered exceptions, not just described

Run: python level_04_suppress.py
"""
import os
from contextlib import suppress


if __name__ == "__main__":
    # ---- the try/except/pass this replaces ---------------------------------
    def delete_if_exists_old_way(path: str):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    delete_if_exists_old_way("/tmp/pystdlib_does_not_exist_xyz_123")   # must not raise

    # ---- the same thing, as a real, triggered suppress() -------------------
    missing_path = "/tmp/pystdlib_does_not_exist_xyz_123"
    assert not os.path.exists(missing_path)
    with suppress(FileNotFoundError):
        os.remove(missing_path)      # this genuinely raises FileNotFoundError internally
    print("suppress() absorbed a real FileNotFoundError")

    # ---- suppress() does NOT catch a DIFFERENT exception type --------------
    raised = None
    try:
        with suppress(FileNotFoundError):
            raise PermissionError("not allowed")   # a different real exception
    except PermissionError as e:
        raised = e
    print(f"suppress(FileNotFoundError) let this escape: {raised!r}")
    assert raised is not None
    assert isinstance(raised, PermissionError)

    # ---- suppress() accepts multiple types at once, like except (A, B) ----
    for bad_value in ("not-an-int", None):
        with suppress(ValueError, TypeError):
            int(bad_value)     # str -> ValueError, None -> TypeError
    print("suppress(ValueError, TypeError) absorbed both real exception types")

    # ---- code AFTER the suppressed exception inside the block never runs --
    ran_after = False
    with suppress(ValueError):
        int("nope")
        ran_after = True     # unreachable: the exception cut the block short
    assert ran_after is False

    print("OK")
