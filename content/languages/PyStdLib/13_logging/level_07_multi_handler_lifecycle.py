"""
LEVEL 07 (advanced) - multiple handlers at different levels, and their lifecycle
===================================================================================
You will learn
  * one logger can fan out to a console handler (INFO) and a file handler (DEBUG)
  * each handler filters independently of the logger's own level
  * handlers are resources: file handlers hold an open file descriptor until closed
  * removeHandler()/close() in a finally block avoids leaking descriptors and avoids
    duplicate log lines if the setup code runs more than once (e.g. in a test suite)

Run: python level_07_multi_handler_lifecycle.py
"""
import logging
import os
import shutil
import tempfile


if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_logging_")
    log_path = os.path.join(tmp_dir, "app.log")

    logger = logging.getLogger("level07.multi")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)   # logger itself must allow DEBUG through

    console_records = []

    class ListHandler(logging.Handler):
        """Stand-in for a real console handler so we can assert on captured
        records without depending on real stdout capture in this level."""
        def emit(self, record):
            console_records.append(self.format(record))

    console_handler = ListHandler()
    console_handler.setLevel(logging.INFO)      # console: INFO and above only
    console_handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(logging.DEBUG)        # file: everything, for later debugging
    file_handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    try:
        logger.debug("connecting to db")
        logger.info("server started")
        logger.warning("slow query detected")

        # ---- each handler filtered independently of the others -----------
        assert len(console_records) == 2                 # DEBUG line skipped by console
        assert not any("connecting" in r for r in console_records)
        assert any("server started" in r for r in console_records)

        file_handler.flush()
        with open(log_path) as f:
            file_contents = f.read()
        print("file handler content (DEBUG+):")
        print(file_contents)
        assert "connecting to db" in file_contents        # file kept the DEBUG line
        assert file_contents.count("\n") == 3             # all 3 log calls landed in the file

    finally:
        # ---- lifecycle: release the file descriptor and detach handlers --
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # ---- proof the cleanup actually happened -------------------------------
    assert logger.handlers == []
    reopened_ok = True
    try:
        open(log_path)  # the temp dir was removed above
        reopened_ok = False
    except FileNotFoundError:
        pass
    assert reopened_ok, "temp log directory should have been cleaned up"

    # ---- running the same setup twice without cleanup would duplicate ----
    # handlers on the SAME logger object (getLogger returns the same instance).
    # This is exactly the bug removeHandler()/close() above prevents.
    logger2 = logging.getLogger("level07.multi")   # same name -> same object
    assert logger2 is logger
    assert len(logger2.handlers) == 0              # proven clean thanks to the finally block

    print("OK")
