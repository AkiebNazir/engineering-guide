"""
LEVEL 02 (core) - type=, default=, choices=: the core API surface
=====================================================================
You will learn
  * type= coerces the raw string into a real Python value (int, float, a callable)
  * default= supplies a value when the argument is never given at all
  * choices= restricts the accepted values and argparse validates it for you
  * these three cover the large majority of real-world argument definitions

Run: python level_02_types_defaults_choices.py
"""
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resize")
    parser.add_argument("--width", type=int, default=800,
                         help="output width in pixels (int, default 800)")
    parser.add_argument("--scale", type=float, default=1.0,
                         help="scale factor (float, default 1.0)")
    parser.add_argument("--format", choices=["png", "jpg", "webp"], default="png",
                         help="output format, restricted to a known set")
    parser.add_argument("--path", type=str, required=True,
                         help="input file path (required, no default)")
    return parser


if __name__ == "__main__":
    parser = build_parser()

    # ---- defaults apply when nothing is passed -----------------------------
    args = parser.parse_args(["--path", "photo.raw"])
    assert args.width == 800 and isinstance(args.width, int)
    assert args.scale == 1.0 and isinstance(args.scale, float)
    assert args.format == "png"

    # ---- type= genuinely converts the string, not just validates it -------
    args2 = parser.parse_args(["--path", "photo.raw", "--width", "1920", "--scale", "2.5"])
    assert args2.width == 1920 and isinstance(args2.width, int)        # "1920" -> int
    assert args2.scale == 2.5 and isinstance(args2.scale, float)       # "2.5" -> float

    # ---- choices= accepts a valid member -----------------------------------
    args3 = parser.parse_args(["--path", "photo.raw", "--format", "webp"])
    assert args3.format == "webp"

    # ---- choices= rejects anything outside the set, with SystemExit(2) ----
    raised = None
    try:
        parser.parse_args(["--path", "photo.raw", "--format", "bmp"])
    except SystemExit as e:
        raised = e
    assert raised is not None and raised.code == 2

    # ---- required=True without a default means omitting it is an error ----
    raised2 = None
    try:
        parser.parse_args(["--width", "100"])   # no --path at all
    except SystemExit as e:
        raised2 = e
    assert raised2 is not None and raised2.code == 2

    print("OK")
