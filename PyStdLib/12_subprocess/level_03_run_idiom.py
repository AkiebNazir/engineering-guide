"""
LEVEL 03 (basic) - a small realistic idiom: running a batch of checks
========================================================================
You will learn
  * a common real pattern: run several independent commands, collect
    each one's outcome, and summarize pass/fail without letting one
    failure abort the whole batch
  * checking result.returncode explicitly (rather than check=True) when
    you want to keep going after a failure and report on all of them

Run: python level_03_run_idiom.py
"""
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str


# Each "check" is a tiny Python one-liner standing in for a real validation
# script (a linter, a test, a config check, ...).
CHECKS = {
    "python_version_ok": "import sys; assert sys.version_info >= (3, 8); print('version ok')",
    "arithmetic_sane": "assert 2 + 2 == 4; print('math ok')",
    "deliberately_broken": "assert 1 == 2, 'one is not two'",
}


def run_check(name: str, code: str) -> CheckResult:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    output = result.stdout if passed else result.stderr
    return CheckResult(name=name, passed=passed, output=output.strip())


def main() -> None:
    results = [run_check(name, code) for name, code in CHECKS.items()]

    by_name = {r.name: r for r in results}
    assert by_name["python_version_ok"].passed
    assert by_name["python_version_ok"].output == "version ok"

    assert by_name["arithmetic_sane"].passed
    assert by_name["arithmetic_sane"].output == "math ok"

    # the broken check fails, but running it did NOT crash our batch runner --
    # this is the whole point of checking returncode rather than check=True
    # inside a loop that must finish reporting on everything.
    assert not by_name["deliberately_broken"].passed
    assert "AssertionError" in by_name["deliberately_broken"].output
    assert "one is not two" in by_name["deliberately_broken"].output

    passed_count = sum(1 for r in results if r.passed)
    failed_count = sum(1 for r in results if not r.passed)
    assert passed_count == 2
    assert failed_count == 1
    assert passed_count + failed_count == len(CHECKS)

    print(f"{passed_count}/{len(CHECKS)} checks passed")
    print("OK")


if __name__ == "__main__":
    main()
