"""
================================================================================
SOLUTION · LLD 007 · Logging Framework                             [Tier 1]
================================================================================

THE CORE IDEA
--------------
A logging library separates four questions that beginners put in one class:

    1. SHOULD this be logged?      Logger level (inherited through a dotted
                                   hierarchy: "app.db.pool" -> "app.db" -> "app"
                                   -> root) + appender level + filters.
    2. WHAT does the line say?     Formatter (text, JSON) — a strategy.
    3. WHERE does it go?           Appender (memory, stream, file, network) —
                                   several per logger; records PROPAGATE up to
                                   ancestors' appenders.
    4. WHEN is it written?         Synchronously, or via an AsyncAppender that
                                   DECORATES another appender with a bounded
                                   queue and a worker thread.

Two performance rules interviewers probe:
    * Check the level BEFORE doing any work. The message is a template plus
      args, formatted only if some appender will actually write it (demo 2:
      an f-string on a disabled debug line still pays for building the string).
    * Logging must never take the application down: an appender that raises is
      counted and skipped, and a full async queue drops (and counts) instead of
      blocking the request thread if configured that way.

And the singleton question: a module-level default registry is fine, but the
registry is an ordinary class, so tests create their own isolated one.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Levels DEBUG < INFO < WARNING < ERROR < CRITICAL.
  2. get_logger(name) returns the same Logger for the same dotted name.
     Unset levels inherit from the nearest ancestor; root defaults to INFO.
  3. A record goes to the logger's appenders, then its parent's, up to root,
     unless a logger on the way has propagate=False.
  4. Appenders have their own minimum level, filters, and formatter.
  5. Formatters: text and JSON. Context key/values can be bound to a logger.
  6. Lazy message formatting ("%s" args).
  7. Thread safe: lines never interleave.
  8. Async appender with bounded queue; flush() and close().
  9. A failing appender never raises into application code.
  Out of scope: config files, rotation, remote shipping.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Level               IntEnum (ordering is the whole point)
    LogRecord           immutable: name, level, template, args, time, thread, context
    Logger              name, level (None = inherit), appenders, propagate, parent
    LoggerRegistry      INVARIANT: one Logger per name; every logger's parent
                        exists; owns the clock and the error counter
    BoundLogger         Logger + fixed context (request_id=...)
    Appender            level, filters, formatter, lock; emit(line) abstract
       ListAppender / StreamAppender / AsyncAppender (decorator)
    Formatter           TextFormatter, JsonFormatter


================================================================================
CLASS DIAGRAM
================================================================================
    LoggerRegistry ◆──▶ Logger("") root
                           ▲ parent
                        Logger("app") ──────◆ appenders ──▶ «abstract» Appender
                           ▲ parent                         ├ level, filters
                        Logger("app.db")                    ├ formatter ──▶ «protocol» Formatter
                                                            │                 ▲ TextFormatter
                                                            │                 ▲ JsonFormatter
                                                            ▲ ListAppender
                                                            ▲ StreamAppender
                                                            ▲ AsyncAppender ──wraps──▶ Appender


================================================================================
KEY FLOW · logger("app.db").info("pool size %d", 5)
================================================================================
    effective level of app.db  (own or nearest ancestor)   INFO < level? -> return
    record = LogRecord(template, args)                      (no string built yet)
    for logger in app.db, app, root:
        for appender in logger.appenders:
            record.level < appender.level? skip
            any filter rejects?            skip
            line = formatter.format(record)   <- message % args happens here
            with appender.lock: emit(line)
            exception? registry.appender_errors += 1 and continue
        if not logger.propagate: stop


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Hierarchy by dotted name gives per-module control ("app.db" at DEBUG while
    the rest of "app" stays at WARNING) without configuring every logger.
  * Appender x Formatter composition instead of JsonFileAppender,
    TextFileAppender, JsonStreamAppender... (M x N subclasses).
  * AsyncAppender is a DECORATOR around any appender. Bounded queue, and the
    caller picks block (never lose logs) or drop (never slow requests).
  * Per-appender lock, held only for the emit, so one slow sink doesn't block
    writes to another.
  * Registry is injectable; the process default is a convenience, not a
    Singleton the code depends on.
  * Level checks read the effective level by walking parents (depth is tiny);
    production libraries cache it and invalidate on set_level.


================================================================================
COMPLEXITY
================================================================================
    disabled log call        O(depth of name)        no allocation of the message
    enabled log call         O(depth + appenders)
    async enqueue            O(1)


================================================================================
EDGE CASES
================================================================================
  * "%" in a message with no args -> printed literally (no formatting).
  * Wrong number of args -> the line still logs with the raw template + args
    (a broken log line must not crash the caller).
  * Appender raises -> counted, other appenders still receive the record.
  * Async queue full with block=False -> record dropped, dropped counter +1.
  * close() twice / log after close -> ignored, counted as dropped.
  * Two registries -> fully isolated (tests don't leak into each other).


================================================================================
COMMON MISTAKES
================================================================================
  1. `class Logger` as a Singleton with global state; tests interfere.
  2. Building the message before checking the level.
  3. FileJsonAppender-style subclass explosion instead of composition.
  4. Letting an appender exception propagate to business code.
  5. Unbounded async queue (memory blow-up when the sink stalls).
  6. Writing message and newline in separate unlocked writes (demo 1).
  7. No flush()/close() — lost logs at shutdown.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * File rotation            -> RotatingFileAppender (size/time policy strategy).
  * Sampling noisy logs      -> Filter that passes 1 in N or token-bucket per key.
  * Structured logging/tracing -> context from contextvars (request id, span id)
                                  merged into every record automatically.
  * Remote shipping          -> AsyncAppender(HttpBatchAppender) with batching,
                                retries with backoff, disk spill on outage.
  * Change levels at runtime -> registry.set_level(name) + cached effective levels.
  * Multi-process            -> each process writes locally; a shipper agent
                                tails files (don't share a file lock).


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §6 Singleton, §10 Decorator,
                                                    §11 Chain of Responsibility, §7 Observer
  PyEngineering (logging, contextvars, queues)
  lld/012_rate_limiter (sampling filter follow-up)
"""

from __future__ import annotations

import io
import json
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Protocol, TextIO

Clock = Callable[[], float]


# ----------------------------------------------------------------------------
# Value objects
# ----------------------------------------------------------------------------
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

    @property
    def message(self) -> str:
        if not self.args:
            return self.template
        try:
            return self.template % self.args
        except (TypeError, ValueError):
            return f"{self.template} {self.args!r}"


# ----------------------------------------------------------------------------
# Formatters
# ----------------------------------------------------------------------------
class Formatter(Protocol):
    def format(self, record: LogRecord) -> str: ...


class TextFormatter:
    def __init__(self, pattern: str = "{time:.3f} {level:<8} {name}: {message}") -> None:
        self._pattern = pattern

    def format(self, record):
        line = self._pattern.format(time=record.time, level=record.level.name,
                                    name=record.name or "root", message=record.message,
                                    thread=record.thread)
        if record.context:
            line += " " + " ".join(f"{k}={v}" for k, v in sorted(record.context.items()))
        return line


class JsonFormatter:
    def format(self, record):
        return json.dumps({"time": record.time, "level": record.level.name,
                           "logger": record.name or "root", "message": record.message,
                           **record.context}, sort_keys=True, default=str)


# ----------------------------------------------------------------------------
# Appenders
# ----------------------------------------------------------------------------
Filter = Callable[[LogRecord], bool]


class Appender:
    def __init__(self, formatter: Formatter | None = None, level: Level = Level.DEBUG,
                 filters: tuple[Filter, ...] = ()) -> None:
        self.formatter = formatter or TextFormatter()
        self.level = level
        self.filters = list(filters)
        self._lock = threading.Lock()

    def handle(self, record: LogRecord) -> None:
        if record.level < self.level or not all(f(record) for f in self.filters):
            return
        line = self.formatter.format(record)
        with self._lock:
            self.emit(line)

    def emit(self, line: str) -> None:
        raise NotImplementedError

    def flush(self) -> None: ...
    def close(self) -> None: ...


class ListAppender(Appender):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.lines: list[str] = []

    def emit(self, line):
        self.lines.append(line)


class StreamAppender(Appender):
    def __init__(self, stream: TextIO, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stream = stream

    def emit(self, line):
        self._stream.write(line + "\n")            # one write call, under the lock

    def flush(self):
        with self._lock:
            self._stream.flush()


class AsyncAppender(Appender):
    """Decorator: hands records to `inner` on a worker thread through a bounded queue."""

    _STOP = object()

    def __init__(self, inner: Appender, capacity: int = 10_000, block: bool = True) -> None:
        super().__init__()
        self._inner = inner
        self._queue: queue.Queue = queue.Queue(maxsize=capacity)
        self._block = block
        self._closed = False
        self.dropped = 0
        self.errors = 0
        self._worker = threading.Thread(target=self._run, name="log-writer", daemon=True)
        self._worker.start()

    def handle(self, record):
        if self._closed:
            self.dropped += 1
            return
        try:
            self._queue.put(record, block=self._block)
        except queue.Full:
            self.dropped += 1

    def _run(self) -> None:
        while True:
            record = self._queue.get()
            try:
                if record is self._STOP:
                    return
                self._inner.handle(record)
            except Exception:
                self.errors += 1
            finally:
                self._queue.task_done()

    def flush(self):
        self._queue.join()
        self._inner.flush()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._queue.put(self._STOP)
        self._worker.join()
        self._inner.flush()


# ----------------------------------------------------------------------------
# Loggers and registry
# ----------------------------------------------------------------------------
class Logger:
    def __init__(self, name: str, registry: LoggerRegistry, parent: Logger | None) -> None:
        self.name = name
        self.parent = parent
        self.level: Level | None = None
        self.propagate = True
        self.appenders: list[Appender] = []
        self._registry = registry

    def set_level(self, level: Level | None) -> Logger:
        self.level = level
        return self

    def add_appender(self, appender: Appender) -> Logger:
        self.appenders.append(appender)
        return self

    def effective_level(self) -> Level:
        logger: Logger | None = self
        while logger is not None:
            if logger.level is not None:
                return logger.level
            logger = logger.parent
        return Level.INFO

    def is_enabled_for(self, level: Level) -> bool:
        return level >= self.effective_level()

    def log(self, level: Level, template: str, *args, _context: dict | None = None) -> None:
        if not self.is_enabled_for(level):
            return
        record = LogRecord(self.name, level, template, args, self._registry.clock(),
                           threading.current_thread().name, _context or {})
        logger: Logger | None = self
        while logger is not None:
            for appender in logger.appenders:
                try:
                    appender.handle(record)
                except Exception:
                    self._registry.appender_errors += 1
            if not logger.propagate:
                break
            logger = logger.parent

    def debug(self, t: str, *a) -> None: self.log(Level.DEBUG, t, *a)
    def info(self, t: str, *a) -> None: self.log(Level.INFO, t, *a)
    def warning(self, t: str, *a) -> None: self.log(Level.WARNING, t, *a)
    def error(self, t: str, *a) -> None: self.log(Level.ERROR, t, *a)
    def critical(self, t: str, *a) -> None: self.log(Level.CRITICAL, t, *a)

    def bind(self, **context) -> BoundLogger:
        return BoundLogger(self, context)


class BoundLogger:
    """A logger with fixed context merged into every record."""

    def __init__(self, logger: Logger, context: dict) -> None:
        self._logger, self._context = logger, dict(context)

    def bind(self, **more) -> BoundLogger:
        return BoundLogger(self._logger, {**self._context, **more})

    def log(self, level: Level, t: str, *a) -> None:
        self._logger.log(level, t, *a, _context=self._context)

    def debug(self, t: str, *a) -> None: self.log(Level.DEBUG, t, *a)
    def info(self, t: str, *a) -> None: self.log(Level.INFO, t, *a)
    def warning(self, t: str, *a) -> None: self.log(Level.WARNING, t, *a)
    def error(self, t: str, *a) -> None: self.log(Level.ERROR, t, *a)


class LoggerRegistry:
    def __init__(self, clock: Clock = time.time) -> None:
        self.clock = clock
        self.appender_errors = 0
        self._lock = threading.Lock()
        self.root = Logger("", self, None).set_level(Level.INFO)
        self._loggers: dict[str, Logger] = {"": self.root}

    def get_logger(self, name: str = "") -> Logger:
        with self._lock:
            if name in self._loggers:
                return self._loggers[name]
            parent_name = name.rpartition(".")[0]
        parent = self.get_logger(parent_name)          # outside the lock: recursion
        with self._lock:
            return self._loggers.setdefault(name, Logger(name, self, parent))


default_registry = LoggerRegistry()                    # convenience, not a singleton


def get_logger(name: str = "") -> Logger:
    return default_registry.get_logger(name)


# ===================================================================== TESTS ==
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


class TornStreamAppender(StreamAppender):
    """The bug: message and newline written separately, no lock."""

    def handle(self, record):
        line = self.formatter.format(record)
        self._stream.write(line)
        time.sleep(0)
        self._stream.write("\n")


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 8 threads x 3,000 lines into one stream ---")

    def hammer(appender_cls) -> tuple[int, int]:
        buf = io.StringIO()
        reg = LoggerRegistry(clock=lambda: 0.0)
        reg.root.add_appender(appender_cls(buf, TextFormatter("{thread}|{message}|end")))

        def worker(t: int) -> None:
            log = reg.get_logger(f"w{t}")
            for i in range(3000):
                log.info("payload-%d", i)

        threads = [threading.Thread(target=worker, args=(t,), name=f"T{t}") for t in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        lines = buf.getvalue().splitlines()
        bad = sum(1 for ln in lines if not (ln.startswith("T") and ln.endswith("|end") and ln.count("|") == 2))
        return len(lines), bad

    torn_total, torn_bad = hammer(TornStreamAppender)
    ok_total, ok_bad = hammer(StreamAppender)
    print(f"      two unlocked writes : {torn_total} lines, {torn_bad} corrupted")
    print(f"      one locked write    : {ok_total} lines, {ok_bad} corrupted")
    all_ok &= _check("locked appender never corrupts a line", ok_total == 24_000 and ok_bad == 0)
    all_ok &= _check("the torn version corrupts lines", torn_bad > 0)

    print("\n--- DEMO 2: what a DISABLED debug line costs (200,000 calls) ---")
    reg = LoggerRegistry()
    log = reg.get_logger("hot.path")
    payload = {"user": 42, "items": list(range(20))}
    n = 200_000
    start = time.perf_counter()
    for _ in range(n):
        log.debug(f"state {payload}")
    eager = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(n):
        log.debug("state %s", payload)
    lazy = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(n):
        if log.is_enabled_for(Level.DEBUG):
            log.debug("state %s", payload)
    guarded = time.perf_counter() - start
    print(f"      f-string: {eager * 1000:.0f} ms   lazy args: {lazy * 1000:.0f} ms   "
          f"explicit guard: {guarded * 1000:.0f} ms")
    all_ok &= _check("lazy formatting beats the eager f-string", lazy < eager)

    print("\n--- DEMO 3: request thread latency, sync vs async sink (1 ms per write) ---")
    for name, make in (("sync ", lambda s: s), ("async", lambda s: AsyncAppender(s))):
        sink = SlowList(0.001)
        app = make(sink)
        reg = LoggerRegistry()
        reg.root.add_appender(app)
        start = time.perf_counter()
        for i in range(200):
            reg.root.info("req %d", i)
        caller = time.perf_counter() - start
        app.flush()
        if isinstance(app, AsyncAppender):
            app.close()
            async_caller = caller
        else:
            sync_caller = caller
        print(f"      {name}: caller spent {caller * 1000:6.1f} ms for 200 lines; written {len(sink.lines)}")
    all_ok &= _check("async appender takes the slow sink off the request path", async_caller * 5 < sync_caller)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
