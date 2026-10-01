"""
LEVEL 04 (core) - real errors: logger.exception() and handler failures
=========================================================================
You will learn
  * logger.exception() must be called from inside an except block; it captures the
    real traceback via sys.exc_info() automatically
  * logger.error(..., exc_info=True) does the same thing outside an "exception" call
  * FileHandler on a directory that doesn't exist raises a real FileNotFoundError
  * setLevel() with a bad name raises a real ValueError

Run: python level_04_error_handling.py
"""
import io
import logging
import os


if __name__ == "__main__":
    # ---- logger.exception() captures a REAL traceback ---------------------
    stream = io.StringIO()
    logger = logging.getLogger("level04.exc")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)

    def divide(a, b):
        return a / b

    try:
        divide(1, 0)
    except ZeroDivisionError:
        logger.exception("divide failed")   # implicitly logs at ERROR + traceback

    output = stream.getvalue()
    print("captured traceback:")
    print(output)
    assert "ERROR:divide failed" in output
    assert "Traceback (most recent call last)" in output
    assert "ZeroDivisionError: division by zero" in output

    # ---- exc_info=True does the same thing outside an except's "exception" name
    stream.truncate(0)
    stream.seek(0)
    try:
        int("not a number")
    except ValueError:
        logger.error("bad input received", exc_info=True)
    output2 = stream.getvalue()
    assert "ValueError: invalid literal for int()" in output2

    # ---- a real, triggered configuration error: bad level name -----------
    raised = None
    try:
        logger.setLevel("VERBOSE")     # not a real level name
    except ValueError as e:
        raised = e
    print(f"bad level name raised: {raised!r}")
    assert raised is not None
    assert "Unknown level" in str(raised)

    # ---- a real, triggered configuration error: FileHandler on a bad path
    raised2 = None
    bad_path = os.path.join("this_directory_does_not_exist_xyz", "app.log")
    try:
        logging.FileHandler(bad_path)
    except FileNotFoundError as e:
        raised2 = e
    print(f"FileHandler on missing directory raised: {raised2!r}")
    assert raised2 is not None
    assert isinstance(raised2, FileNotFoundError)

    print("OK")
