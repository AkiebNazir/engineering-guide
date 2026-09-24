"""
LEVEL 05 (advanced) - assembling Logger + Handler + Formatter by hand
========================================================================
You will learn
  * building a logger from scratch without basicConfig(): Logger, Handler, Formatter
  * a Formatter's format string pulls from LogRecord attributes (%(name)s, %(message)s...)
  * extra= injects custom fields into a LogRecord for a Formatter to consume
  * extra= keys that collide with existing LogRecord attributes raise KeyError

Run: python level_05_manual_assembly.py
"""
import io
import logging


if __name__ == "__main__":
    # ---- manual assembly: no basicConfig() anywhere in this block --------
    logger = logging.getLogger("level05.manual")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)          # 1. a Handler: where records go
    handler.setLevel(logging.DEBUG)

    # 2. a Formatter with a custom field (request_id) that only exists because
    #    we will pass it via extra= at the call site.
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [req=%(request_id)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)                        # 3. wire Logger -> Handler

    # ---- structured context via extra= ------------------------------------
    logger.info("order placed", extra={"request_id": "abc-123"})
    logger.warning("payment retried", extra={"request_id": "abc-123"})

    output = stream.getvalue()
    print("manually assembled output:")
    print(output)
    assert "[req=abc-123]" in output
    assert output.count("[req=abc-123]") == 2
    assert "level05.manual" in output

    # ---- omitting extra= for a Formatter that requires the field fails ---
    # This is the flip side: the Formatter demands %(request_id)s on every record.
    # Note: going through logger.info() -> Handler.emit() would SWALLOW this error
    # (emit() wraps formatting in try/except and reports it via handleError() to
    # stderr instead of raising) -- that swallowing is itself a real gotcha. To see
    # the actual exception the Formatter raises, call it directly on a record.
    record = logger.makeRecord(logger.name, logging.INFO, __file__, 0,
                                "no request id supplied", (), None)
    raised = None
    try:
        formatter.format(record)   # no request_id was ever set on this record
    except (KeyError, ValueError) as e:
        raised = e
    print(f"missing extra field raised: {raised!r}")
    assert raised is not None
    assert "request_id" in str(raised)

    # ---- extra= keys that COLLIDE with real LogRecord attributes fail ----
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))  # drop the custom field
    raised2 = None
    try:
        logger.info("collision test", extra={"message": "not allowed"})
    except KeyError as e:
        raised2 = e
    print(f"colliding extra key raised: {raised2!r}")
    assert raised2 is not None
    assert "message" in str(raised2) or "Attempt to overwrite" in str(raised2)

    print("OK")
