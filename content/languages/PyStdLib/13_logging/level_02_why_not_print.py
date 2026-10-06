"""
LEVEL 02 (core) - why print() doesn't scale: levels, filtering, handlers
==========================================================================
You will learn
  * print() has no concept of severity: every call is unconditional and unfilterable
  * a logger can route the SAME call to two destinations at two different verbosities
  * changing verbosity means changing one setLevel() call, not editing every call site
  * the core API surface: debug/info/warning/error/critical, setLevel, addHandler

Run: python level_02_why_not_print.py
"""
import io
import logging


if __name__ == "__main__":
    # ---- the print() way: no filtering is possible after the fact --------
    console_only = io.StringIO()

    def do_work_with_print(verbose: bool):
        # the ONLY way to "filter" print output is an if-statement at every call site
        if verbose:
            print("DEBUG: entering do_work_with_print", file=console_only)
        print("INFO: work started", file=console_only)
        print("INFO: work finished", file=console_only)

    do_work_with_print(verbose=False)
    printed = console_only.getvalue()
    assert "entering" not in printed
    assert printed.count("INFO:") == 2
    # to change verbosity here you must edit the function itself and redeploy it.

    # ---- the logging way: same call sites, verbosity set from OUTSIDE ----
    console_stream = io.StringIO()
    file_stream = io.StringIO()

    logger = logging.getLogger("level02.demo")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)          # the LOGGER lets everything through...

    console_handler = logging.StreamHandler(console_stream)
    console_handler.setLevel(logging.INFO)  # ...but this HANDLER only takes INFO+
    file_handler = logging.StreamHandler(file_stream)
    file_handler.setLevel(logging.DEBUG)    # ...while this one takes everything

    fmt = logging.Formatter("%(levelname)s:%(message)s")
    console_handler.setFormatter(fmt)
    file_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    def do_work_with_logging():
        logger.debug("entering do_work_with_logging")
        logger.info("work started")
        logger.info("work finished")

    do_work_with_logging()

    console_out = console_stream.getvalue()
    file_out = file_stream.getvalue()
    print("console (INFO+):")
    print(console_out)
    print("file (DEBUG+):")
    print(file_out)

    # ONE call site (do_work_with_logging) produced TWO destinations at TWO verbosities:
    assert "entering" not in console_out         # console filtered DEBUG out
    assert console_out.count("INFO:") == 2
    assert "entering" in file_out                # file kept everything, DEBUG included
    assert file_out.count("INFO:") == 2

    # ---- toggling verbosity needs no code change at the call site --------
    console_handler.setLevel(logging.DEBUG)      # turn the console up, from OUTSIDE
    console_stream.truncate(0)
    console_stream.seek(0)
    do_work_with_logging()
    assert "entering" in console_stream.getvalue()   # now the console gets DEBUG too

    print("OK")
