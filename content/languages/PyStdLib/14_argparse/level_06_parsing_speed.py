"""
LEVEL 06 (advanced) - MEASURED: argparse vs a hand-rolled parser
====================================================================
You will learn
  * argparse's overhead vs a minimal hand-written parser doing the same job
  * this is measured with time.perf_counter() on THIS run -- not asserted from theory
  * argparse builds a NEW ArgumentParser cheaply, but parse_args() itself does far
    more validation work than a bespoke loop over sys.argv-like lists
  * the numbers below are whatever this run actually produced -- report honestly

Run: python level_06_parsing_speed.py
"""
import argparse
import time


ARGV = ["--width", "1920", "--height", "1080", "--name", "render", "input.png"]
N = 5_000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", add_help=False)
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--name", default="out")
    parser.add_argument("path")
    return parser


def parse_with_argparse(parser: argparse.ArgumentParser, argv: list[str]) -> dict:
    ns = parser.parse_args(argv)
    return {"width": ns.width, "height": ns.height, "name": ns.name, "path": ns.path}


def parse_by_hand(argv: list[str]) -> dict:
    """A minimal hand-rolled equivalent: no help text, no error messages,
    no type validation beyond int(), no usage generation."""
    result = {"width": 800, "height": 600, "name": "out", "path": None}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--width":
            result["width"] = int(argv[i + 1]); i += 2
        elif token == "--height":
            result["height"] = int(argv[i + 1]); i += 2
        elif token == "--name":
            result["name"] = argv[i + 1]; i += 2
        else:
            result["path"] = token; i += 1
    return result


if __name__ == "__main__":
    parser = build_parser()

    # ---- correctness first: both must agree on the parsed result ----------
    via_argparse = parse_with_argparse(parser, ARGV)
    via_hand = parse_by_hand(ARGV)
    assert via_argparse == via_hand == {"width": 1920, "height": 1080, "name": "render", "path": "input.png"}

    # ---- now measure real, repeated parsing cost of each approach ---------
    start = time.perf_counter()
    for _ in range(N):
        parse_with_argparse(build_parser(), ARGV)   # rebuild the parser each time, like a real CLI would
    argparse_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(N):
        parse_by_hand(ARGV)
    handrolled_elapsed = time.perf_counter() - start

    print(f"{N} parses each:")
    print(f"  argparse    : {argparse_elapsed:.4f}s ({argparse_elapsed / N * 1e6:.2f} us/call)")
    print(f"  hand-rolled : {handrolled_elapsed:.4f}s ({handrolled_elapsed / N * 1e6:.2f} us/call)")

    # ---- report what THIS run measured, without assuming the direction ---
    assert argparse_elapsed >= 0.0 and handrolled_elapsed >= 0.0
    slower = "argparse" if argparse_elapsed > handrolled_elapsed else "hand-rolled"
    ratio = max(argparse_elapsed, handrolled_elapsed) / max(min(argparse_elapsed, handrolled_elapsed), 1e-9)
    print(f"  measured slower on this run: {slower} (~{ratio:.1f}x)")
    # a hand-rolled loop with zero validation, zero help text, and zero usage
    # generation does strictly less work, so it is expected to measure faster --
    # but we print the real ratio rather than asserting a specific magnitude.
    assert argparse_elapsed > handrolled_elapsed, \
        "argparse does substantially more validation work per call than a bare loop"

    print("OK")
