"""
LEVEL 09 (advanced) - production gotcha: a library that logs without NullHandler
====================================================================================
You will learn
  * a logger with NO handler anywhere in its ancestor chain falls back to
    logging.lastResort, which prints WARNING+ straight to stderr
  * this silently leaks a "library's" internal logging into any application that
    imports it and never configured logging itself
  * the fix: a library-style logger attaches a NullHandler at import time
  * NullHandler makes the library silent by default, while still letting an
    application attach its OWN handler later to see the library's logs on purpose

Run: python level_09_nullhandler_gotcha.py
"""
import contextlib
import io
import logging


def make_naive_library_logger(name: str) -> logging.Logger:
    """What a library looks like if it forgets logging best practice: it just
    calls getLogger() and logs, assuming someone else configured handlers."""
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = True     # default -- but there is no ancestor handler either
    return logger


def make_well_behaved_library_logger(name: str) -> logging.Logger:
    """The stdlib-documented pattern for library code (see the logging HOWTO):
    attach a NullHandler so the library is silent unless the APPLICATION using
    it explicitly configures its own handler."""
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return logger


if __name__ == "__main__":
    # ---- reproduce the gotcha for real: capture what lands on stderr -----
    naive = make_naive_library_logger("level09.naive_lib")

    captured_stderr = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr):
        naive.warning("internal retry happened")   # the "library" just logs...

    stderr_output = captured_stderr.getvalue()
    print(f"naive library's warning leaked to stderr: {stderr_output!r}")
    # ...and because NO handler exists anywhere in its ancestor chain, Python's
    # logging.lastResort handler silently printed it to stderr -- something the
    # application importing this "library" never asked for and never configured.
    assert "internal retry happened" in stderr_output

    # ---- the fix: NullHandler makes the library silent by default --------
    well_behaved = make_well_behaved_library_logger("level09.good_lib")

    captured_stderr2 = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr2):
        well_behaved.warning("internal retry happened, but nobody asked to see it")

    assert captured_stderr2.getvalue() == ""    # NullHandler swallowed it -- correctly silent
    print("well-behaved library: no stderr leakage (correctly silent by default)")

    # ---- but the application CAN still opt in and see the library's logs --
    app_stream = io.StringIO()
    app_handler = logging.StreamHandler(app_stream)
    app_handler.setFormatter(logging.Formatter("%(name)s:%(levelname)s:%(message)s"))
    # the application attaches its OWN handler to the library's logger, on purpose
    well_behaved.addHandler(app_handler)

    well_behaved.warning("this time the application wants to see it")
    app_output = app_stream.getvalue()
    print(f"application opted in and saw: {app_output.strip()!r}")
    assert "this time the application wants to see it" in app_output

    # cleanup so this logger doesn't leak state to any other file run in-process
    well_behaved.removeHandler(app_handler)
    app_handler.close()

    print("OK")
