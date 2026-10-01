"""
LEVEL 05 (advanced) - add_subparsers() for git-style subcommands
====================================================================
You will learn
  * add_subparsers(dest=...) records WHICH subcommand was chosen
  * each subcommand gets its own independent ArgumentParser with its own arguments
  * required=True makes choosing a subcommand mandatory (off by default!)
  * a dispatch dict mapping subcommand name -> handler function is the idiomatic
    way to act on the parsed result

Run: python level_05_subparsers.py
"""
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="git-lite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser("commit", help="record changes")
    commit_parser.add_argument("-m", "--message", required=True)

    branch_parser = subparsers.add_parser("branch", help="list or create branches")
    branch_parser.add_argument("name", nargs="?", help="branch to create; omit to list")
    branch_parser.add_argument("-d", "--delete", action="store_true")

    return parser


def handle_commit(args: argparse.Namespace) -> str:
    return f"[main] committed: {args.message}"


def handle_branch(args: argparse.Namespace) -> str:
    if args.delete and args.name:
        return f"deleted branch {args.name}"
    if args.name:
        return f"created branch {args.name}"
    return "listing branches"


if __name__ == "__main__":
    parser = build_parser()
    DISPATCH = {"commit": handle_commit, "branch": handle_branch}

    # ---- each subcommand is its own little parser --------------------------
    args = parser.parse_args(["commit", "-m", "fix the bug"])
    assert args.command == "commit"
    assert args.message == "fix the bug"
    result = DISPATCH[args.command](args)
    print(result)
    assert result == "[main] committed: fix the bug"

    args2 = parser.parse_args(["branch", "feature/x"])
    assert args2.command == "branch"
    assert args2.name == "feature/x"
    result2 = DISPATCH[args2.command](args2)
    print(result2)
    assert result2 == "created branch feature/x"

    args3 = parser.parse_args(["branch", "feature/x", "--delete"])
    result3 = DISPATCH[args3.command](args3)
    assert result3 == "deleted branch feature/x"

    args4 = parser.parse_args(["branch"])
    result4 = DISPATCH[args4.command](args4)
    assert result4 == "listing branches"

    # ---- an argument that belongs to a DIFFERENT subcommand is rejected --
    raised = None
    try:
        parser.parse_args(["branch", "-m", "not valid here"])
    except SystemExit as e:
        raised = e
    assert raised is not None and raised.code == 2

    # ---- required=True: omitting the subcommand entirely is an error -----
    raised2 = None
    try:
        parser.parse_args([])
    except SystemExit as e:
        raised2 = e
    assert raised2 is not None and raised2.code == 2

    print("OK")
