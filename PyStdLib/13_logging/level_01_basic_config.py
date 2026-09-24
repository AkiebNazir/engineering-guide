"""
LEVEL 01 (basic) - logging.basicConfig(): the one-line quick setup
====================================================================
You will learn
  * basicConfig() configures the root logger in one call: level + format + destination
  * the five standard severity levels and their integer values
  * setLevel() controls which messages actually get emitted
  * why a logger below its configured level produces no output at all

Run: python level_01_basic_config.py
"""
import io
import logging


def build_logger_writing_to(stream: io.StringIO, level: int) -> logging.Logger:
    """A tiny helper: basicConfig() only configures the ROOT logger, and only once
    per process. To keep this file re-runnable/testable we build a fresh logger by
    hand here instead of calling basicConfig() against the real (shared) root logger.
    Level 05 shows the full manual-assembly picture; this level only needs to prove
    basicConfig()'s *behavior*, so we replicate its defaults on an isolated logger.
    """
    logger = logging.getLogger(f"level01.{id(stream)}")
    logger.handlers.clear()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


if __name__ == "__main__":
    # ---- the five standard levels, in increasing severity ----------------
    assert logging.DEBUG == 10
    assert logging.INFO == 20
    assert logging.WARNING == 30
    assert logging.ERROR == 40
    assert logging.CRITICAL == 50

    # ---- default level is WARNING: INFO/DEBUG are silent unless raised ---
    buf = io.StringIO()
    log = build_logger_writing_to(buf, level=logging.WARNING)   # basicConfig()'s default
    log.debug("this is filtered out")
    log.info("so is this")
    log.warning("but this gets through")
    log.error("and this")
    output = buf.getvalue()
    print("WARNING-level logger output:")
    print(output)
    assert "this is filtered out" not in output
    assert "so is this" not in output
    assert "but this gets through" in output
    assert "and this" in output

    # ---- lowering the level (as basicConfig(level=logging.DEBUG) would) --
    buf2 = io.StringIO()
    verbose_log = build_logger_writing_to(buf2, level=logging.DEBUG)
    verbose_log.debug("now this shows up")
    output2 = buf2.getvalue()
    print("DEBUG-level logger output:")
    print(output2)
    assert "now this shows up" in output2
    assert "DEBUG:level01" in output2      # format string included levelname:name

    # ---- basicConfig() itself: real one-liner on the actual root logger --
    # basicConfig() is a no-op if the root logger already has handlers (e.g. from
    # a previous call, or from a test runner). force=True guarantees it applies here.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s", force=True)
    root = logging.getLogger()
    assert root.level == logging.INFO
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], logging.StreamHandler)

    print("OK")
