"""
LEVEL 08 (advanced) - interop: capturing the auto-generated --help output
=============================================================================
You will learn
  * format_help() returns the help text as a string, with no I/O at all
  * parser.print_help() writes it to a stream (stdout by default) -- interop with
    contextlib.redirect_stdout and io.StringIO lets you capture it like a test would
  * passing ["--help"] to parse_args() triggers SystemExit(0) after printing help
  * the generated text includes usage, positional args, and optional args sections

Run: python level_08_capture_help.py
"""
import argparse
import contextlib
import io


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="convert", description="Convert a file between formats.")
    parser.add_argument("path", help="input file path")
    parser.add_argument("--to", choices=["json", "csv"], help="target format")
    return parser


if __name__ == "__main__":
    parser = build_parser()

    # ---- format_help(): pure string, no I/O -------------------------------
    help_text = parser.format_help()
    print("format_help() output:")
    print(help_text)
    assert "usage: convert" in help_text
    assert "Convert a file between formats." in help_text
    assert "--to {json,csv}" in help_text

    # ---- print_help() writes to a stream -- capture it like a test would --
    captured = io.StringIO()
    parser.print_help(captured)
    assert captured.getvalue() == help_text     # same content, different delivery mechanism

    # ---- print_help() defaults to real stdout -- redirect_stdout captures it
    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        parser.print_help()
    assert stdout_capture.getvalue() == help_text

    # ---- passing --help to parse_args() prints help AND exits with code 0 -
    exit_capture = io.StringIO()
    raised = None
    with contextlib.redirect_stdout(exit_capture):
        try:
            parser.parse_args(["--help"])
        except SystemExit as e:
            raised = e
    print(f"--help triggered SystemExit(code={raised.code if raised else None})")
    assert raised is not None
    assert raised.code == 0                     # 0 = success, unlike the 2 for usage errors
    assert "usage: convert" in exit_capture.getvalue()

    print("OK")
