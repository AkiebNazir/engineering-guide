"""
LEVEL 03 (core) - a realistic idiom: temporarily changing then restoring state
==================================================================================
You will learn
  * a very common @contextmanager pattern: save state, change it, restore it after
  * this generalizes to logging levels, working directories, env vars, config flags
  * the restore step belongs in `finally` so it runs even if the block raises
  * nesting two of these composes cleanly, each restoring its own piece of state

Run: python level_03_temporary_state.py
"""
import logging
from contextlib import contextmanager


@contextmanager
def temporary_log_level(logger: logging.Logger, level: int):
    """Temporarily raise/lower a logger's level, restoring it afterwards --
    handy in tests that want to silence or amplify logging for one block."""
    previous = logger.level
    logger.setLevel(level)
    try:
        yield logger
    finally:
        logger.setLevel(previous)


@contextmanager
def temporary_dict_value(d: dict, key: str, value):
    """The same save/change/restore idiom applied to a plain dict -- config
    flags, feature toggles, anything keyed and mutable."""
    had_key = key in d
    previous = d.get(key)
    d[key] = value
    try:
        yield d
    finally:
        if had_key:
            d[key] = previous
        else:
            del d[key]


if __name__ == "__main__":
    logger = logging.getLogger("level03.temp_state")
    logger.setLevel(logging.WARNING)

    # ---- state is changed inside the block, restored right after ----------
    assert logger.level == logging.WARNING
    with temporary_log_level(logger, logging.DEBUG):
        assert logger.level == logging.DEBUG
    assert logger.level == logging.WARNING            # restored automatically

    # ---- restoration happens even if the block raises ----------------------
    raised = None
    try:
        with temporary_log_level(logger, logging.CRITICAL):
            assert logger.level == logging.CRITICAL
            raise RuntimeError("boom")
    except RuntimeError as e:
        raised = e
    assert raised is not None
    assert logger.level == logging.WARNING            # still restored, despite the exception

    # ---- the same idiom on a plain dict, including a NEW key -------------
    config = {"debug": False}
    with temporary_dict_value(config, "debug", True):
        assert config["debug"] is True
    assert config["debug"] is False                   # restored to its old value

    with temporary_dict_value(config, "feature_x", "on"):
        assert config["feature_x"] == "on"
    assert "feature_x" not in config                  # key didn't exist before -- removed after

    # ---- nesting composes cleanly: each manager restores only its own piece
    with temporary_log_level(logger, logging.INFO):
        with temporary_dict_value(config, "debug", True):
            assert logger.level == logging.INFO
            assert config["debug"] is True
        assert config["debug"] is False                # inner restored first
        assert logger.level == logging.INFO             # outer still active
    assert logger.level == logging.WARNING              # outer restored last

    print("OK")
