"""
LEVEL 07 (advanced) - argument_group() and mutually_exclusive_group()
=========================================================================
You will learn
  * argument_group() organizes --help output into labeled sections (cosmetic only --
    it does NOT change what combinations of args are valid)
  * mutually_exclusive_group() DOES change validity: at most one of its arguments
    may be given, enforced by argparse itself
  * a required mutually exclusive group forces exactly one of its members
  * combining both: grouped, mutually exclusive output-format flags

Run: python level_07_groups.py
"""
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy")

    # ---- argument_group(): purely cosmetic organization in --help --------
    conn = parser.add_argument_group("connection options")
    conn.add_argument("--host", default="localhost")
    conn.add_argument("--port", type=int, default=443)

    # ---- mutually_exclusive_group(): argparse ENFORCES at most one --------
    fmt_group = parser.add_argument_group("output format")
    exclusive = fmt_group.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--json", action="store_true")
    exclusive.add_argument("--yaml", action="store_true")
    exclusive.add_argument("--table", action="store_true")

    return parser


if __name__ == "__main__":
    parser = build_parser()

    # ---- exactly one of the exclusive flags is required --------------------
    args = parser.parse_args(["--json"])
    assert args.json is True and args.yaml is False and args.table is False

    # ---- two members of the SAME exclusive group together is rejected -----
    raised = None
    try:
        parser.parse_args(["--json", "--yaml"])
    except SystemExit as e:
        raised = e
    assert raised is not None and raised.code == 2

    # ---- required=True: giving NONE of them is also rejected ---------------
    raised2 = None
    try:
        parser.parse_args(["--host", "example.com"])
    except SystemExit as e:
        raised2 = e
    assert raised2 is not None and raised2.code == 2

    # ---- argument_group() membership does not restrict combinations -------
    # --host/--port are in a DIFFERENT group and combine freely with any format flag
    args2 = parser.parse_args(["--host", "example.com", "--port", "8443", "--yaml"])
    assert args2.host == "example.com" and args2.port == 8443 and args2.yaml is True

    # ---- the grouping shows up in --help, purely for readability ----------
    help_text = parser.format_help()
    print(help_text)
    assert "connection options:" in help_text
    assert "output format:" in help_text

    print("OK")
