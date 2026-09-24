"""
LEVEL 10 (advanced) - capstone: replicating a shell pipe from Python
=========================================================================
You will learn
  * how to wire one process's stdout directly into another's stdin using
    two Popen objects -- replicating `producer | consumer` from a shell,
    entirely from Python
  * combining that with a timeout-bounded wait, safe list-args commands
    (no shell=True anywhere), and proper pipe/process cleanup
  * this exercises most of levels 1-9 together: run()/Popen, check-style
    error handling, timeout handling, streaming-safe pipe wiring, and the
    list-args safety discipline

Run: python level_10_capstone_pipeline.py
"""
import subprocess
import sys

PRODUCER_CODE = """
import sys
for word in ["pear", "apple", "kiwi", "banana", "fig"]:
    print(word)
"""

CONSUMER_CODE = """
import sys
lines = [line.strip() for line in sys.stdin if line.strip()]
for line in sorted(lines):
    print(line)
"""


def run_piped_pipeline(producer_code: str, consumer_code: str, timeout: float) -> list[str]:
    """Replicate `producer | consumer` using two Popen objects."""
    producer = subprocess.Popen(
        [sys.executable, "-c", producer_code],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        consumer = subprocess.Popen(
            [sys.executable, "-c", consumer_code],
            stdin=producer.stdout,   # the pipe: consumer reads producer's stdout directly
            stdout=subprocess.PIPE,
            text=True,
        )
        # Closing our copy of producer.stdout lets producer receive SIGPIPE
        # (and the OS reclaim the pipe) once consumer is done reading, instead
        # of the pipe staying open because we too hold a reference to it.
        producer.stdout.close()

        try:
            output, _ = consumer.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            consumer.kill()
            consumer.communicate()
            raise
    finally:
        producer.wait(timeout=timeout)

    if producer.returncode != 0:
        raise subprocess.CalledProcessError(producer.returncode, producer.args)
    if consumer.returncode != 0:
        raise subprocess.CalledProcessError(consumer.returncode, consumer.args)

    return [line for line in output.splitlines() if line]


def main() -> None:
    # --- the happy path: producer | consumer, exactly like a shell pipe ----
    sorted_words = run_piped_pipeline(PRODUCER_CODE, CONSUMER_CODE, timeout=5)
    assert sorted_words == ["apple", "banana", "fig", "kiwi", "pear"]

    # --- a failing producer is detected, not silently swallowed -------------
    broken_producer = "import sys; sys.exit(9)"
    try:
        run_piped_pipeline(broken_producer, CONSUMER_CODE, timeout=5)
        raised = False
    except subprocess.CalledProcessError as exc:
        raised = True
        error = exc
    assert raised
    assert error.returncode == 9

    # --- a consumer that hangs trips the timeout, and is cleaned up ---------
    hanging_consumer = "import time; time.sleep(5)"
    try:
        run_piped_pipeline(PRODUCER_CODE, hanging_consumer, timeout=0.2)
        raised = False
    except subprocess.TimeoutExpired:
        raised = True
    assert raised, "a hanging consumer must trip the pipeline timeout"

    # --- list-args discipline held throughout: no shell=True anywhere, so a
    # "word" containing shell metacharacters flows through as inert data ----
    tricky_producer = "print('data; rm -rf /tmp/should-not-run')"
    result = run_piped_pipeline(tricky_producer, CONSUMER_CODE, timeout=5)
    assert result == ["data; rm -rf /tmp/should-not-run"]  # treated as one literal line

    print(f"pipeline result: {sorted_words}")
    print("OK")


if __name__ == "__main__":
    main()
