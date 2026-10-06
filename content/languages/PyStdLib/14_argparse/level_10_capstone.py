"""
LEVEL 10 (advanced) - capstone: a small git-style task CLI
==============================================================
You will learn (ties together levels 01-09)
  * subcommands (level 05) each with their own positional/optional args (level 01/02)
  * a mutually exclusive group for the "list" subcommand's filters (level 07)
  * a custom Action for validating a "tag:value" filter (level 09)
  * capturing --help for the whole tool (level 08)
  * real errors (SystemExit) surfacing for bad input (level 04)

Run: python level_10_capstone.py
"""
import argparse
import contextlib
import io


class TagFilterAction(argparse.Action):
    """Validates 'key:value' and stores it as a (key, value) tuple."""
    def __call__(self, parser, namespace, values, option_string=None):
        if ":" not in values:
            parser.error(f"argument {option_string}: expected key:value, got {values!r}")
        key, _, value = values.partition(":")
        setattr(namespace, self.dest, (key, value))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasks", description="A tiny task tracker.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add a task")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", type=int, choices=[1, 2, 3], default=2)

    list_parser = subparsers.add_parser("list", help="list tasks")
    list_parser.add_argument("--tag", action=TagFilterAction, default=None,
                              help="filter by key:value, e.g. status:done")
    filters = list_parser.add_mutually_exclusive_group()
    filters.add_argument("--all", action="store_true")
    filters.add_argument("--pending", action="store_true")

    return parser


TASKS = [
    {"title": "write report", "priority": 1, "status": "pending"},
    {"title": "review PR", "priority": 2, "status": "done"},
]


def run(argv: list[str]) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        return f"added '{args.title}' at priority {args.priority}"

    if args.command == "list":
        tasks = TASKS
        if args.pending:
            tasks = [t for t in tasks if t["status"] == "pending"]
        if args.tag:
            key, value = args.tag
            tasks = [t for t in tasks if t.get(key) == value]
        return "\n".join(t["title"] for t in tasks) or "(no tasks)"

    raise AssertionError("unreachable")   # required=True guarantees a valid command


if __name__ == "__main__":
    # ---- add: type= and choices= together ----------------------------------
    result = run(["add", "write report", "--priority", "1"])
    print(result)
    assert result == "added 'write report' at priority 1"

    # ---- choices= rejects an out-of-range priority --------------------------
    raised = None
    try:
        run(["add", "x", "--priority", "9"])
    except SystemExit as e:
        raised = e
    assert raised is not None and raised.code == 2

    # ---- list with a mutually exclusive filter ------------------------------
    result2 = run(["list", "--pending"])
    print(result2)
    assert result2 == "write report"

    # ---- list with the custom TagFilterAction -------------------------------
    result3 = run(["list", "--tag", "status:done"])
    print(result3)
    assert result3 == "review PR"

    # ---- the custom action's real, helpful validation error -----------------
    raised2 = None
    try:
        run(["list", "--tag", "no-colon-here"])
    except SystemExit as e:
        raised2 = e
    assert raised2 is not None and raised2.code == 2

    # ---- --all and --pending are mutually exclusive -------------------------
    raised3 = None
    try:
        run(["list", "--all", "--pending"])
    except SystemExit as e:
        raised3 = e
    assert raised3 is not None and raised3.code == 2

    # ---- --help works for the whole tool, capturable via redirect_stdout ---
    parser = build_parser()
    help_capture = io.StringIO()
    with contextlib.redirect_stdout(help_capture):
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            pass
    help_text = help_capture.getvalue()
    print(help_text)
    assert "A tiny task tracker." in help_text
    assert "{add,list}" in help_text

    print("OK")
