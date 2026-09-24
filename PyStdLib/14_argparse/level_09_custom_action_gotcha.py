"""
LEVEL 09 (advanced) - production gotcha: lambda type= gives a useless error
================================================================================
You will learn
  * type=<lambda> "works" until the user gives bad input -- then the error message
    is useless: argparse can only report the lambda's repr, not what was wrong
  * a custom argparse.Action subclass gets full control over validation AND the
    error message, via parser.error() from inside __call__
  * this is the correct way to go "beyond store_true": custom logic per argument

Run: python level_09_custom_action_gotcha.py
"""
import argparse
import contextlib
import io


# ---- the naive approach: looks fine until it fails ---------------------------
def build_naive_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="setup")
    # a lambda that validates a "HOST:PORT" string looks convenient...
    parser.add_argument("--endpoint", type=lambda s: (s.partition(":")[0], int(s.partition(":")[2])))
    return parser


# ---- the fix: a custom Action with a real, helpful error message ------------
class EndpointAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if ":" not in values:
            parser.error(f"argument {option_string}: expected HOST:PORT, got {values!r}")
        host, _, raw_port = values.partition(":")
        if not raw_port.isdigit():
            parser.error(f"argument {option_string}: port must be a number, got {raw_port!r} in {values!r}")
        setattr(namespace, self.dest, (host, int(raw_port)))


def build_good_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="setup")
    parser.add_argument("--endpoint", action=EndpointAction)
    return parser


if __name__ == "__main__":
    # ---- the naive lambda-based parser works for valid input ---------------
    naive_parser = build_naive_parser()
    ok_args = naive_parser.parse_args(["--endpoint", "localhost:8080"])
    assert ok_args.endpoint == ("localhost", 8080)

    # ---- but bad input produces an error message with NO useful detail -----
    stderr = io.StringIO()
    raised = None
    with contextlib.redirect_stderr(stderr):
        try:
            naive_parser.parse_args(["--endpoint", "no-port-here"])
        except SystemExit as e:
            raised = e
    naive_error = stderr.getvalue()
    print(f"naive lambda error message:\n{naive_error}")
    assert raised is not None and raised.code == 2
    # the message only shows argparse's generic "invalid <lambda> value" wrapper --
    # it never explains WHAT was wrong (missing colon? bad port?) because the
    # ValueError raised inside the lambda (from int()) carries no such context here
    assert "invalid <lambda>" in naive_error or "invalid " in naive_error
    assert "expected HOST:PORT" not in naive_error   # no real guidance for the user

    # ---- the custom Action subclass gives a genuinely helpful message ------
    good_parser = build_good_parser()
    good_args = good_parser.parse_args(["--endpoint", "localhost:8080"])
    assert good_args.endpoint == ("localhost", 8080)

    stderr2 = io.StringIO()
    raised2 = None
    with contextlib.redirect_stderr(stderr2):
        try:
            good_parser.parse_args(["--endpoint", "no-port-here"])
        except SystemExit as e:
            raised2 = e
    good_error = stderr2.getvalue()
    print(f"custom Action error message:\n{good_error}")
    assert raised2 is not None and raised2.code == 2
    assert "expected HOST:PORT, got 'no-port-here'" in good_error   # actually actionable

    print("OK")
