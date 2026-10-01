"""
LEVEL 03 (core) - nargs: '+', '*', '?' in realistic idioms
===============================================================
You will learn
  * nargs='+' requires one-or-more values, collected into a list
  * nargs='*' accepts zero-or-more values, defaulting to an empty list
  * nargs='?' accepts zero-or-one value, useful for an optional positional
  * stacking two variadic POSITIONALS back to back is ambiguous -- argparse's
    nargs='+' greedily eats everything, leaving nothing for a nargs='?' that follows

Run: python level_03_nargs.py
"""
import argparse


def build_inputs_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="batch_convert")
    parser.add_argument("inputs", nargs="+", help="one or more input files")
    parser.add_argument("--include", nargs="*", default=[],
                         help="zero or more extra include directories")
    return parser


def build_output_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="save_as")
    parser.add_argument("output", nargs="?", default="out.bin",
                         help="optional output file name (defaults to out.bin)")
    return parser


if __name__ == "__main__":
    inputs_parser = build_inputs_parser()

    # ---- nargs='+' : at least one value, collected as a list ---------------
    args = inputs_parser.parse_args(["a.txt", "b.txt", "c.txt"])
    assert args.inputs == ["a.txt", "b.txt", "c.txt"]
    assert isinstance(args.inputs, list)

    # ---- nargs='+' with zero values is a real, rejected error -------------
    raised = None
    try:
        inputs_parser.parse_args(["--include"])   # nothing at all, not even one input
    except SystemExit as e:
        raised = e
    assert raised is not None and raised.code == 2

    # ---- nargs='*' : zero values is fine, defaults to [] -------------------
    args2 = inputs_parser.parse_args(["a.txt"])
    assert args2.include == []

    # ---- nargs='*' : one or more values collected the same way ------------
    args3 = inputs_parser.parse_args(["a.txt", "--include", "libs/", "vendor/"])
    assert args3.include == ["libs/", "vendor/"]

    # ---- both together: the optional flag can sit before or after the
    #      variadic positional without ambiguity, because --include is
    #      clearly marked by its `--` prefix -----------------------------
    combined = inputs_parser.parse_args(["a.txt", "b.txt", "--include", "libs/"])
    assert combined.inputs == ["a.txt", "b.txt"]
    assert combined.include == ["libs/"]

    # ---- nargs='?' : a lone optional positional is genuinely optional -----
    output_parser = build_output_parser()
    default_args = output_parser.parse_args([])
    assert default_args.output == "out.bin"          # not given -> default used

    given_args = output_parser.parse_args(["final.bin"])
    assert given_args.output == "final.bin"          # given -> used verbatim

    # ---- the gotcha: nargs='+' immediately followed by nargs='?' is
    #      ambiguous -- '+' is greedy and swallows everything, so the
    #      trailing '?' positional NEVER receives a value from argv --------
    ambiguous_parser = argparse.ArgumentParser(prog="ambiguous")
    ambiguous_parser.add_argument("inputs", nargs="+")
    ambiguous_parser.add_argument("output", nargs="?", default="out.bin")
    result = ambiguous_parser.parse_args(["a.txt", "final.bin"])
    # both tokens were consumed by the GREEDY nargs='+' positional...
    assert result.inputs == ["a.txt", "final.bin"]
    # ...leaving the nargs='?' positional stuck on its default, not "final.bin"
    assert result.output == "out.bin"

    print("OK")
