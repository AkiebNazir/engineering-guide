"""
LEVEL 04 (core) - Error handling: sys.exc_info() inside a real except block
==============================================================================
You will learn
  * sys.exc_info() returns (None, None, None) outside of exception handling
  * inside an except block it returns (exc_type, exc_value, exc_traceback)
    for whatever exception is currently being handled
  * the traceback object's tb_frame/tb_lineno point at the actual failure site
  * exc_info() still works when you catch a broader type than what was raised

Run: python level_04_exc_info.py
"""
import sys

if __name__ == "__main__":
    # outside any exception handling, there's nothing to report
    assert sys.exc_info() == (None, None, None)

    # trigger a REAL exception -- int() on a non-numeric string -- and
    # inspect it through sys.exc_info() rather than the `as e` binding
    try:
        int("not-a-number")
        raise AssertionError("unreachable")
    except ValueError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        assert exc_type is ValueError
        assert "not-a-number" in str(exc_value)
        # the traceback points at THIS file, at the int() call above
        assert exc_tb.tb_frame.f_code.co_filename == __file__
        assert exc_tb.tb_lineno > 0

    # back outside the handler, exc_info is cleared again
    assert sys.exc_info() == (None, None, None)

    # exc_info() also works if you catch a broader ancestor type than what
    # was actually raised -- it still reports the REAL, specific type
    try:
        _ = [1, 2, 3][10]
        raise AssertionError("unreachable")
    except Exception:   # broader than the actual IndexError
        exc_type, exc_value, _ = sys.exc_info()
        assert exc_type is IndexError
        assert exc_type is not Exception   # the real type, not the caught alias

    # a nested try/except: the inner handler's exc_info doesn't leak out
    # to the outer one once the inner block has finished
    try:
        try:
            raise KeyError("inner")
        except KeyError:
            inner_type, _, _ = sys.exc_info()
            assert inner_type is KeyError
        # inner exception handling has ended here
        assert sys.exc_info() == (None, None, None)
        raise TypeError("outer")
    except TypeError:
        outer_type, _, _ = sys.exc_info()
        assert outer_type is TypeError

    print("OK")
