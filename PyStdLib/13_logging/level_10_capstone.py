"""
LEVEL 10 (advanced) - capstone: a small "service" wiring logging together
============================================================================
You will learn (ties together levels 01-09)
  * a library submodule that logs safely with a NullHandler (level 09)
  * an application logger with two handlers at two levels: console INFO + file DEBUG
    (level 07), assembled manually (level 05) with structured extra= context
  * getLogger(__name__)-style hierarchy so the "library" and the "app" don't collide
    (level 03)
  * cleanup of handlers in a finally block so the demo leaves nothing behind

Run: python level_10_capstone.py
"""
import io
import logging
import os
import shutil
import tempfile


# ---- "library" module: safe by default, silent unless the app opts in -------
_lib_logger = logging.getLogger("capstone_app.payments_lib")
_lib_logger.addHandler(logging.NullHandler())


def charge_card(amount: float, request_id: str) -> bool:
    """Pretends to be a third-party library function that logs its own internals."""
    _lib_logger.debug("charging card", extra={"request_id": request_id})
    if amount <= 0:
        _lib_logger.warning("rejected non-positive charge", extra={"request_id": request_id})
        return False
    _lib_logger.info("charge succeeded", extra={"request_id": request_id})
    return True


# ---- "application" module: configures its OWN logger + the library's --------
def run_app(tmp_dir: str) -> tuple[str, str]:
    app_logger = logging.getLogger("capstone_app")
    app_logger.handlers.clear()
    app_logger.setLevel(logging.DEBUG)

    console_stream = io.StringIO()
    console_handler = logging.StreamHandler(console_stream)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    log_path = os.path.join(tmp_dir, "capstone.log")
    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [req=%(request_id)s] %(name)s: %(message)s",
                           datefmt="%H:%M:%S")
    )

    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)

    # the app explicitly opts in to seeing the library's logs too, since
    # "capstone_app.payments_lib" propagates up into "capstone_app"'s handlers.
    request_id = "req-777"
    app_logger.info("processing order", extra={"request_id": request_id})
    ok = charge_card(42.50, request_id=request_id)
    app_logger.info(f"order result: {'paid' if ok else 'declined'}", extra={"request_id": request_id})

    rejected = charge_card(-5, request_id="req-778")
    assert rejected is False

    file_handler.flush()
    console_out = console_stream.getvalue()
    with open(log_path) as f:
        file_out = f.read()

    for h in list(app_logger.handlers):
        app_logger.removeHandler(h)
        h.close()

    return console_out, file_out


if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_logging_capstone_")
    try:
        console_out, file_out = run_app(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("console (INFO+ only, from BOTH app and library loggers):")
    print(console_out)
    print("file (DEBUG+, structured with request_id):")
    print(file_out)

    # ---- the app's own INFO lines reached the console ----------------------
    assert "processing order" in console_out
    assert "order result: paid" in console_out

    # ---- the library's DEBUG line was filtered by the console handler,
    #      but its INFO ("charge succeeded") DID make it through, because the
    #      library logger propagates up into the app's configured handlers ---
    assert "charging card" not in console_out           # DEBUG filtered by console_handler
    assert "charge succeeded" in console_out             # library's INFO reached the console
    assert "rejected non-positive charge" in console_out  # WARNING is >= INFO, so it passes too

    # ---- the file kept everything, tagged with the right request_id --------
    assert "charging card" in file_out                  # DEBUG survived in the file
    assert "[req=req-777]" in file_out
    assert "[req=req-778]" in file_out
    assert "rejected non-positive charge" in file_out

    print("OK")
