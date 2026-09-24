"""
================================================================================
LLD 007 · Logging Framework                                        [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement a logging library (think log4j / Python logging / zap).

The interviewer says: "Design a logger." These are the agreed requirements.

REQUIREMENTS
------------
  1. Levels DEBUG 10 < INFO 20 < WARNING 30 < ERROR 40 < CRITICAL 50.
  2. LoggerRegistry(clock) owns loggers. get_logger("a.b.c") always returns the
     same Logger for a name and creates missing ancestors; registry.root is the
     logger named "". Each Logger has .parent, .level (None = inherit),
     .propagate (default True), .appenders. Root starts at INFO.
     set_level() and add_appender() return the logger (chainable).
  3. logger.info(template, *args) etc. Formatting is `template % args`, done
     only if the record is actually written. No args -> the template is used
     as-is ("100% done" is fine). Bad args must not raise.
  4. Dispatch: if the level is below the logger's EFFECTIVE level (own, else
     nearest ancestor's), do nothing. Otherwise build a LogRecord and hand it
     to this logger's appenders, then its parent's, up to root — stopping after
     a logger whose propagate is False.
  5. Appender(formatter=None, level=DEBUG, filters=()):
        handle(record) skips records below its level or rejected by any
        filter(record) -> bool, formats, then calls emit(line) under a lock.
     ListAppender keeps .lines. StreamAppender(stream, ...) writes line + "\n".
  6. An appender that raises must not reach the caller; count it in
     registry.appender_errors and keep delivering to the other appenders.
  7. Formatters:
        TextFormatter(pattern) — str.format with time, level (name), name,
        message, thread; if the record has context, append " k=v" pairs sorted.
        JsonFormatter() — json.dumps({time, level, logger, message, **context},
        sort_keys=True). Root's name appears as "root".
  8. logger.bind(**context) returns a logger-like object whose records carry
     that context; bind() can be chained.
  9. AsyncAppender(inner, capacity=10_000, block=True) wraps any appender with a
     bounded queue and a worker thread. block=False drops when full.
     .dropped counts drops (including records logged after close()).
     flush() waits until everything queued is written. close() stops the worker.
 10. A module-level get_logger(name) uses a default registry — but nothing may
     depend on it being a singleton.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Which classes? Where does "should I log this" vs "how" vs "where" live?
  * Singleton or not? How do tests stay isolated?
  * How do you avoid paying for disabled debug lines?
  * What happens when the disk is full, or the log sink is slow?
  * How do lines from many threads not interleave?

FOLLOW-UPS TO PREPARE
---------------------
  rotation · sampling · request-id propagation · remote shipping with
  batching · changing levels at runtime · multi-process.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, TextIO


class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass(frozen=True, slots=True)
class LogRecord:
    name: str
    level: Level
    template: str
    args: tuple
    time: float
    thread: str
    context: dict = field(default_factory=dict)


class TextFormatter:
    def __init__(self, pattern: str = "{time:.3f} {level:<8} {name}: {message}") -> None:
        raise NotImplementedError

    def format(self, record: LogRecord) -> str:
        raise NotImplementedError


class JsonFormatter:
    def format(self, record: LogRecord) -> str:
        raise NotImplementedError


class Appender:
    def __init__(self, formatter=None, level: Level = Level.DEBUG, filters=()) -> None:
        raise NotImplementedError

    def handle(self, record: LogRecord) -> None:
        raise NotImplementedError

    def emit(self, line: str) -> None:
        raise NotImplementedError

    def flush(self) -> None: ...
    def close(self) -> None: ...


class ListAppender(Appender):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.lines: list[str] = []


class StreamAppender(Appender):
    def __init__(self, stream: TextIO, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stream = stream


class AsyncAppender(Appender):
    def __init__(self, inner: Appender, capacity: int = 10_000, block: bool = True) -> None:
        self.dropped = 0
        # YOUR CODE HERE
        raise NotImplementedError


class Logger:
    # YOUR CODE HERE: parent, level, propagate, appenders, set_level, add_appender,
    # debug/info/warning/error/critical, bind
    pass


class LoggerRegistry:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.appender_errors = 0
        # YOUR CODE HERE (self.root)
        raise NotImplementedError

    def get_logger(self, name: str = "") -> Logger:
        raise NotImplementedError


def get_logger(name: str = "") -> Logger:
    raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


class Boom(Appender):
    def emit(self, line):
        raise OSError("disk full")


class SlowList(ListAppender):
    def __init__(self, delay_s: float, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.delay_s = delay_s

    def emit(self, line):
        time.sleep(self.delay_s)
        super().emit(line)


def run_tests() -> bool:
    all_ok = True
    print("--- levels and hierarchy ---")
    reg = LoggerRegistry(clock=lambda: 1.5)
    root_out = ListAppender(TextFormatter("{level} {name}: {message}"))
    reg.root.add_appender(root_out)
    db = reg.get_logger("app.db")
    all_ok &= _check("same name -> same logger; parents created",
                     reg.get_logger("app.db") is db and db.parent is reg.get_logger("app")
                     and db.parent.parent is reg.root)
    db.debug("hidden")
    db.info("pool size %d", 5)
    all_ok &= _check("root INFO: debug dropped, info kept, args formatted",
                     root_out.lines == ["INFO app.db: pool size 5"])
    reg.get_logger("app").set_level(Level.WARNING)
    db.info("now hidden")
    all_ok &= _check("app.db inherits WARNING from app", len(root_out.lines) == 1)
    db.set_level(Level.DEBUG)
    db.debug("visible")
    all_ok &= _check("own level overrides the ancestor", root_out.lines[-1] == "DEBUG app.db: visible")

    print("\n--- propagation and appender thresholds ---")
    app_out = ListAppender(TextFormatter("{message}"), level=Level.ERROR)
    reg.get_logger("app").add_appender(app_out)
    db.warning("w")
    db.error("e")
    all_ok &= _check("app appender (ERROR) sees only e; root sees both",
                     app_out.lines == ["e"] and root_out.lines[-2:] == ["WARNING app.db: w", "ERROR app.db: e"])
    reg.get_logger("app").propagate = False
    db.error("stop")
    all_ok &= _check("propagate=False on app stops before root",
                     app_out.lines[-1] == "stop" and root_out.lines[-1] != "ERROR app.db: stop")
    only_db = ListAppender(TextFormatter("{message}"), filters=(lambda r: "secret" not in r.template,))
    db.add_appender(only_db)
    db.error("secret token")
    db.error("fine")
    all_ok &= _check("filters reject records", only_db.lines == ["fine"])

    print("\n--- formatters, context, lazy formatting ---")
    reg = LoggerRegistry(clock=lambda: 2.0)
    out = ListAppender(JsonFormatter())
    reg.root.add_appender(out)
    reg.get_logger("api").bind(request_id="r-1").bind(user="ann").info("hello %s", "world")
    all_ok &= _check("JSON with bound context",
                     json.loads(out.lines[0]) == {"time": 2.0, "level": "INFO", "logger": "api",
                                                  "message": "hello world", "request_id": "r-1", "user": "ann"})
    calls = []

    class Expensive:
        def __str__(self) -> str:
            calls.append(1)
            return "big"

    reg.get_logger("api").debug("dump %s", Expensive())
    all_ok &= _check("disabled debug never calls __str__ on its args", calls == [])
    reg.get_logger("api").info("100% done")
    reg.get_logger("api").info("%d items", "not-a-number")
    all_ok &= _check("'%' without args printed literally; bad args don't raise",
                     json.loads(out.lines[1])["message"] == "100% done"
                     and "not-a-number" in json.loads(out.lines[2])["message"])

    print("\n--- failure isolation ---")
    reg = LoggerRegistry()
    good = ListAppender()
    reg.root.add_appender(Boom()).add_appender(good)
    reg.get_logger("x").error("still logged")
    all_ok &= _check("raising appender counted; the next appender still receives the record",
                     reg.appender_errors == 1 and len(good.lines) == 1)
    all_ok &= _check("two registries are isolated", LoggerRegistry().get_logger("x").appenders == []
                     and get_logger("x") is not reg.get_logger("x"))

    print("\n--- async appender ---")
    reg = LoggerRegistry()
    sink = ListAppender(TextFormatter("{message}"))
    async_app = AsyncAppender(sink)
    reg.root.add_appender(async_app)
    for i in range(500):
        reg.get_logger("a").info("line %d", i)
    async_app.flush()
    all_ok &= _check("flush delivers everything in order", sink.lines == [f"line {i}" for i in range(500)])
    async_app.close()
    reg.get_logger("a").info("after close")
    all_ok &= _check("log after close is dropped, not raised", async_app.dropped == 1)
    slow = SlowList(0.01, TextFormatter("{message}"))
    lossy = AsyncAppender(slow, capacity=5, block=False)
    reg2 = LoggerRegistry()
    reg2.root.add_appender(lossy)
    for i in range(50):
        reg2.root.info("m%d", i)
    lossy.close()
    all_ok &= _check(f"full queue with block=False drops ({lossy.dropped} dropped, {len(slow.lines)} written)",
                     lossy.dropped > 0 and lossy.dropped + len(slow.lines) == 50)
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
