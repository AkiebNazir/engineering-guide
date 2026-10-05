"""
LEVEL 04 (core) - real errors: SystemExit and bad type= coercion
====================================================================
You will learn
  * argparse reports usage errors by calling sys.exit(2), raising SystemExit -- not
    a ValueError you can catch inline the way you might expect
  * capturing the actual stderr text argparse prints for a bad --width value
  * a custom type= function's ValueError becomes a clean argparse error message
  * a custom type= function's OTHER exception types are NOT handled cleanly

Run: python level_04_error_handling.py
"""
import argparse
import contextlib
import io


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="server")
    parser.add_argument("--port", type=int, help="port number")
    return parser


def positive_int(raw: str) -> int:
    value = int(raw)                      # can raise ValueError -- argparse handles that cleanly
    if value <= 0:
        raise argparse.ArgumentTypeError(f"{raw!r} is not a positive integer")
    return value


if __name__ == "__main__":
    parser = build_parser()

    # ---- a bad int() coercion raises SystemExit(2), with a real message --
    stderr = io.StringIO()
    raised = None
    with contextlib.redirect_stderr(stderr):
        try:
            parser.parse_args(["--port", "not-a-number"])
        except SystemExit as e:
            raised = e
    error_text = stderr.getvalue()
    print(f"real argparse error text:\n{error_text}")
    assert raised is not None and raised.code == 2
    assert "invalid int value: 'not-a-number'" in error_text

    # ---- a custom type= raising ValueError becomes a clean error too ------
    parser2 = argparse.ArgumentParser(prog="server2")
    parser2.add_argument("--port", type=positive_int)

    stderr2 = io.StringIO()
    raised2 = None
    with contextlib.redirect_stderr(stderr2):
        try:
            parser2.parse_args(["--port", "-5"])
        except SystemExit as e:
            raised2 = e
    error_text2 = stderr2.getvalue()
    print(f"custom type= error text:\n{error_text2}")
    assert raised2 is not None and raised2.code == 2
    assert "is not a positive integer" in error_text2

    # ---- a genuinely bad type= (raises something argparse doesn't wrap) ---
    def broken_type(raw: str) -> int:
        return {"a": 1}[raw]        # raises KeyError for anything else -- NOT handled cleanly

    parser3 = argparse.ArgumentParser(prog="server3")
    parser3.add_argument("--mode", type=broken_type)

    raised3 = None
    try:
        parser3.parse_args(["--mode", "z"])
    except KeyError as e:
        raised3 = e     # a REAL KeyError escapes -- argparse only catches ValueError/TypeError
    print(f"unhandled type= exception escaped as: {raised3!r}")
    assert raised3 is not None
    assert isinstance(raised3, KeyError)

    print("OK")
