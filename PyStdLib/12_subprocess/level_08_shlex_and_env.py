"""
LEVEL 08 (advanced) - interop: shlex for safe command building, env= overrides
==================================================================================
You will learn
  * shlex.split() turns a human-typed command STRING into the list-args
    form subprocess wants, without a shell in the middle
  * shlex.quote() safely escapes a value for the rare case you must build
    a shell string yourself
  * env= REPLACES the child's entire environment rather than extending it --
    a real gotcha -- so the idiom is always `{**os.environ, "KEY": "value"}`

Run: python level_08_shlex_and_env.py
"""
import os
import shlex
import subprocess
import sys


def main() -> None:
    # --- shlex.split(): a typed command string -> a safe argument list -----
    typed_command = f'{shlex.quote(sys.executable)} -c "print(1 + 1)"'
    args = shlex.split(typed_command)
    assert args == [sys.executable, "-c", "print(1 + 1)"]

    result = subprocess.run(args, capture_output=True, text=True)
    assert result.stdout == "2\n"

    # --- shlex.split correctly handles quoted strings with spaces inside ---
    typed_command_with_spaces = f'{shlex.quote(sys.executable)} -c "print(\'hello world\')"'
    args2 = shlex.split(typed_command_with_spaces)
    assert args2[-1] == "print('hello world')"  # one argument, not two

    # --- shlex.quote(): safely embed a value that might contain shell
    # metacharacters, for the rare case you must build a shell string.
    dangerous_value = "hello; rm -rf /"
    quoted = shlex.quote(dangerous_value)
    assert quoted == "'hello; rm -rf /'"  # wrapped so the shell treats it as ONE literal string
    # proof: asking a real shell to echo it back yields the literal string,
    # semicolon and all, never executing it as a second command.
    echoed = subprocess.run(f"echo {quoted}", shell=True, capture_output=True, text=True)
    assert echoed.stdout.strip() == dangerous_value

    # --- env=: THE GOTCHA -- it replaces the whole environment, not extends it
    result_missing_path = subprocess.run(
        [sys.executable, "-c", "import os; print(os.environ.get('PATH', '<MISSING>'))"],
        env={"CUSTOM_VAR": "just this one"},
        capture_output=True,
        text=True,
    )
    assert result_missing_path.stdout.strip() == "<MISSING>", (
        "env= with a bare dict replaces the ENTIRE environment -- PATH is gone too"
    )

    # --- the correct idiom: copy the parent's environment, then extend it ---
    child_env = {**os.environ, "CUSTOM_VAR": "hello from parent"}
    result_with_path = subprocess.run(
        [sys.executable, "-c",
         "import os; print(os.environ.get('PATH', '<MISSING>')); print(os.environ['CUSTOM_VAR'])"],
        env=child_env,
        capture_output=True,
        text=True,
    )
    lines = result_with_path.stdout.splitlines()
    assert lines[0] != "<MISSING>"  # PATH survived because we copied it in
    assert lines[1] == "hello from parent"

    # --- env=None (the default): child fully inherits the parent's env -----
    os.environ["PYSTDLIB_DEMO_VAR"] = "inherited"
    try:
        inherited = subprocess.run(
            [sys.executable, "-c", "import os; print(os.environ['PYSTDLIB_DEMO_VAR'])"],
            capture_output=True,
            text=True,
        )
        assert inherited.stdout.strip() == "inherited"
    finally:
        del os.environ["PYSTDLIB_DEMO_VAR"]

    print("OK")


if __name__ == "__main__":
    main()
