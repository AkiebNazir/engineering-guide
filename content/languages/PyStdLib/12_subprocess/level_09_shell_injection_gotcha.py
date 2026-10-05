"""
LEVEL 09 (advanced) - shell=True + untrusted input: a real injection, demonstrated
======================================================================================
You will learn
  * shell=True runs your command STRING through a real shell, which
    interprets `;`, `|`, `&&`, backticks, etc. -- ANY of them, if they come
    from untrusted input, let an attacker run a second, unintended command
  * this is demonstrated for real: a crafted "filename" breaks out of an
    intended `echo` command and creates a file it was never supposed to
  * the fix: the list-args form (shell=False, the default) passes the
    string as ONE literal argument, no shell parsing involved at all

Run: python level_09_shell_injection_gotcha.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="pystdlib_subprocess_injection_"))
    proof_file = workdir / "should_not_exist.txt"
    safe_output_file = workdir / "output.txt"

    try:
        # --- the vulnerable code: shell=True with string concatenation -----
        # Pretend this "user_supplied_name" came from a web form, a CLI arg,
        # or any other untrusted source. It LOOKS like an innocent filename.
        user_supplied_name = f"pwned; touch {proof_file}"

        vulnerable_command = f"echo {user_supplied_name} > {safe_output_file}"
        subprocess.run(vulnerable_command, shell=True, capture_output=True)

        # --- the injection actually worked: a file that should never have
        # been created now exists, because the shell ran TWO commands ------
        assert proof_file.exists(), (
            "the injected `touch` command must have actually run via shell=True"
        )

        # cleanup before demonstrating the fix
        proof_file.unlink()

        # --- the SAFE fix: list-args form, shell=False (the default) --------
        # The same untrusted string is now passed as ONE literal argument to
        # `echo` -- there is no shell to interpret the embedded semicolon.
        safe_command = ["echo", user_supplied_name]
        result = subprocess.run(safe_command, capture_output=True, text=True)

        assert not proof_file.exists(), (
            "the list-args form must NOT execute the embedded `touch` command"
        )
        # the whole string, semicolon included, was printed as inert text
        assert user_supplied_name in result.stdout

        # --- same lesson, using our portable sys.executable child instead
        # of relying on the `echo` shell builtin, proving it generalizes ----
        proof_file2 = workdir / "should_also_not_exist.txt"
        malicious_arg = f"data; import os; open({str(proof_file2)!r}, 'w').close() #"
        safe_result = subprocess.run(
            [sys.executable, "-c", "import sys; print(sys.argv[1])", malicious_arg],
            capture_output=True,
            text=True,
        )
        assert not proof_file2.exists()
        assert safe_result.stdout.strip() == malicious_arg  # treated as inert data, not code

    finally:
        for f in (proof_file, safe_output_file, workdir / "should_also_not_exist.txt"):
            if f.exists():
                f.unlink()
        os.rmdir(workdir)

    print("OK")


if __name__ == "__main__":
    main()
