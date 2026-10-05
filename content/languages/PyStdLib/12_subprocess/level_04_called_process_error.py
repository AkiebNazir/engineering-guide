"""
LEVEL 04 (basic) - subprocess.CalledProcessError: triggered and caught for real
==================================================================================
You will learn
  * check=True makes run() raise CalledProcessError on a non-zero exit code
  * the exception itself carries .returncode, .cmd, .stdout, .stderr (when
    captured) -- everything you need to report the failure properly
  * this is the real exception type and real attributes, not a description

Run: python level_04_called_process_error.py
"""
import subprocess
import sys


def main() -> None:
    failing_code = "import sys; print('some output'); print('some problem', file=sys.stderr); sys.exit(7)"

    # --- trigger the real exception ------------------------------------------
    try:
        subprocess.run(
            [sys.executable, "-c", failing_code],
            check=True,
            capture_output=True,
            text=True,
        )
        raised = False
        error = None
    except subprocess.CalledProcessError as exc:
        raised = True
        error = exc

    assert raised, "check=True with a non-zero exit code must raise CalledProcessError"
    assert error is not None

    # --- the exception carries everything needed to diagnose the failure ---
    assert error.returncode == 7
    assert error.cmd == [sys.executable, "-c", failing_code]
    assert error.stdout == "some output\n"
    assert error.stderr == "some problem\n"

    # --- str(error) is a ready-made, human-readable summary -----------------
    assert "returned non-zero exit status 7" in str(error)

    # --- CalledProcessError is a subclass of the more general SubprocessError
    assert isinstance(error, subprocess.SubprocessError)

    # --- a SUCCESSFUL command with check=True does not raise at all --------
    ok_result = subprocess.run(
        [sys.executable, "-c", "print('fine')"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert ok_result.returncode == 0
    assert ok_result.stdout == "fine\n"

    print("OK")


if __name__ == "__main__":
    main()
