"""
LEVEL 08 (advanced) - RotatingFileHandler, interop with pathlib
==================================================================
You will learn
  * RotatingFileHandler rolls the log file over once it exceeds maxBytes
  * backupCount caps how many old rotated files are kept (app.log.1, app.log.2, ...)
  * pathlib.Path is the natural stdlib partner for inspecting the resulting files
  * rotation happens on the NEXT write after the size is exceeded, not mid-write

Run: python level_08_rotating_file_handler.py
"""
import logging
import logging.handlers
import pathlib
import shutil
import tempfile


if __name__ == "__main__":
    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="pystdlib_rotating_"))
    log_path = tmp_dir / "app.log"

    logger = logging.getLogger("level08.rotating")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=200, backupCount=3, mode="w",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    try:
        # each line is ~40 bytes; maxBytes=200 means roughly every 5 lines rotates
        for i in range(40):
            logger.info(f"log line number {i:03d} with some padding to take up space")

        handler.flush()
        handler.close()

        # ---- interop: pathlib to see what rotation actually produced -----
        rotated_files = sorted(tmp_dir.glob("app.log*"))
        names = [p.name for p in rotated_files]
        print(f"files after rotation in {tmp_dir}:")
        for p in rotated_files:
            print(f"  {p.name}: {p.stat().st_size} bytes")

        # the live file always exists
        assert log_path.exists()
        # backupCount=3 caps rotated files at app.log.1 .. app.log.3 (never more)
        assert "app.log.1" in names
        assert "app.log.4" not in names
        assert len(names) <= 4   # app.log + at most 3 backups

        # every existing rotated file should be at or under the cap (allowing the
        # single line that pushed it over threshold before rotation triggered)
        for p in rotated_files:
            assert p.stat().st_size < 400

        # the current (live) file holds the most recently written lines
        current_content = log_path.read_text()
        assert "log line number 039" in current_content

    finally:
        logger.removeHandler(handler)
        handler.close()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("OK")
