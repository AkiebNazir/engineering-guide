"""
LEVEL 10 (capstone) - a small log-ingestion pipeline using levels 1-9 together
================================================================================
You will learn
  * how open() modes, encoding recovery, seek()-based tailing, StringIO buffering,
    and durable writes combine into one realistic small program
  * a log ingester that: writes raw bytes (some invalid utf-8), reads them back
    tolerantly, builds an in-memory summary, tails the last N raw lines, and
    commits the summary to disk durably

Run: python level_10_capstone_log_pipeline.py
"""
import io
import os
import shutil
import tempfile


def write_raw_log(path: str) -> None:
    """Simulate a log with one corrupted line (invalid utf-8 byte sequence)."""
    lines = [
        b"INFO  starting worker\n",
        b"INFO  connected to queue\n",
        b"ERROR \xff\xfe bad encoding from upstream\n",   # not valid utf-8
        b"INFO  processed 42 items\n",
        b"ERROR disk almost full\n",
    ]
    with open(path, "wb", buffering=0) as f:   # unbuffered: each write is immediate
        for line in lines:
            f.write(line)


def summarize(path: str) -> tuple[str, list[str]]:
    """Read tolerantly, return (summary_text, error_lines)."""
    with open(path, "rb") as raw:
        text_view = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
        all_lines = text_view.readlines()

    error_lines = [ln.rstrip("\n") for ln in all_lines if ln.startswith("ERROR")]
    summary = io.StringIO()
    summary.write(f"total lines: {len(all_lines)}\n")
    summary.write(f"error lines: {len(error_lines)}\n")
    return summary.getvalue(), error_lines


def tail_raw(path: str, n_bytes: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(-min(n_bytes, size), 2)
        return f.read()


def commit_summary(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())   # durable: survives a crash right after this call returns


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    log_path = os.path.join(tmpdir, "worker.log")
    summary_path = os.path.join(tmpdir, "summary.txt")
    try:
        write_raw_log(log_path)

        summary_text, error_lines = summarize(log_path)
        assert "total lines: 5" in summary_text
        assert "error lines: 2" in summary_text
        assert len(error_lines) == 2
        assert "disk almost full" in error_lines[1]
        # the corrupted line was recovered, not lost -- replacement chars stand in
        assert "�" in error_lines[0]

        tail = tail_raw(log_path, 30)
        assert tail.endswith(b"disk almost full\n")

        commit_summary(summary_path, summary_text)
        with open(summary_path, encoding="utf-8") as f:
            reread = f.read()
        assert reread == summary_text
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
