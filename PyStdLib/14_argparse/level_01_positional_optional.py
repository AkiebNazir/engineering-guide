"""
LEVEL 01 (basic) - positional and optional arguments
========================================================
You will learn
  * ArgumentParser() + add_argument(): the two calls behind every CLI
  * positional arguments are required, matched by position, no leading dashes
  * optional arguments start with `-`/`--` and can appear in any order
  * parse_args() returns a plain Namespace with one attribute per argument

Run: python level_01_positional_optional.py
"""
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greet", description="Greet someone.")
    parser.add_argument("name", help="the person to greet (positional, required)")
    parser.add_argument("--greeting", help="word to greet with (optional, has a default)",
                         default="Hello")
    parser.add_argument("--shout", action="store_true", help="uppercase the whole greeting")
    return parser


if __name__ == "__main__":
    parser = build_parser()

    # ---- positional only: optional falls back to its default -------------
    args = parser.parse_args(["Ada"])
    assert args.name == "Ada"
    assert args.greeting == "Hello"
    assert args.shout is False
    print(f"parsed: {args}")

    # ---- positional + optional, in either order ---------------------------
    args2 = parser.parse_args(["--greeting", "Hi", "Grace"])
    assert args2.name == "Grace"
    assert args2.greeting == "Hi"

    args3 = parser.parse_args(["Grace", "--greeting", "Hi"])   # order doesn't matter
    assert args3.name == args2.name and args3.greeting == args2.greeting

    # ---- store_true: presence of the flag alone flips the boolean --------
    args4 = parser.parse_args(["Ada", "--shout"])
    assert args4.shout is True

    # ---- a missing REQUIRED positional is a real, catchable failure ------
    # argparse reports usage errors via SystemExit(2), not a Python exception type
    # you'd normally catch -- see level_04 for how to actually test this.
    raised = None
    try:
        parser.parse_args([])   # no name given
    except SystemExit as e:
        raised = e
    assert raised is not None
    assert raised.code == 2

    print("OK")
