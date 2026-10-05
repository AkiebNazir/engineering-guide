"""
18 - Dependency injection & layering - Reference Solution
============================================================

See `18_dependency_injection_layering_explanation.py` for the full spec,
rationale, and acceptance criteria. Implements the `NotificationSender`
port, two adapters, the `NotificationService`, and the `build_service`
composition root exactly as specified there.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# The port: what NotificationService needs, described structurally.
# ---------------------------------------------------------------------------
@runtime_checkable
class NotificationSender(Protocol):
    """Structural port: anything with this method shape satisfies it.

    Neither adapter below subclasses this - mypy verifies conformance
    structurally (does the shape match?), not nominally (did you declare
    inheritance?). This is what lets `SmtpEmailSender` and `InMemorySender`
    be developed with zero coupling to this module beyond matching a
    method signature.
    """

    def send(self, recipient: str, message: str) -> None: ...


# ---------------------------------------------------------------------------
# Adapters - concrete implementations of the port.
# ---------------------------------------------------------------------------
class SmtpEmailSender:
    """A stand-in for a real SMTP-backed adapter.

    A production version would open a socket (`smtplib.SMTP(host, port)`)
    and issue `sendmail`; that's deliberately out of scope here so the
    exercise has no network dependency and no live SMTP server requirement
    to run the tests - `sent_log` lets tests assert on what *would* have
    been sent without any I/O.
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.sent_log: list[str] = []

    def send(self, recipient: str, message: str) -> None:
        self.sent_log.append(f"{self.host}:{self.port} -> {recipient}: {message}")


class InMemorySender:
    """A fake adapter for tests - records calls instead of doing I/O.

    A fake (as opposed to a `unittest.mock.Mock`) is a real, small,
    working implementation of the port: it has genuine behavior (it
    actually stores what it's told, and can answer queries about it), so
    tests read as assertions about observable behavior rather than
    assertions about which methods got called with which arguments.
    """

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.messages.append((recipient, message))

    def sent_to(self, recipient: str) -> list[str]:
        return [msg for (rcpt, msg) in self.messages if rcpt == recipient]


# ---------------------------------------------------------------------------
# The service - depends only on the port, injected via the constructor.
# ---------------------------------------------------------------------------
class NotificationService:
    """Business logic layer. Knows nothing about SMTP or fakes - only the
    `NotificationSender` protocol it was handed at construction time.
    """

    def __init__(self, sender: NotificationSender) -> None:
        self._sender = sender

    def notify(self, recipient: str, message: str) -> None:
        # Validate before delegating - the port shouldn't have to reject
        # empty input itself, and different adapters shouldn't each have
        # to reimplement this validation independently.
        if not recipient.strip():
            raise ValueError("recipient must not be empty or whitespace-only")
        if not message.strip():
            raise ValueError("message must not be empty or whitespace-only")
        self._sender.send(recipient, message)

    def notify_many(self, recipients: list[str], message: str) -> list[str]:
        # Partial-failure handling: one bad recipient (e.g. an empty
        # string that slipped into a batch) must not abort delivery to the
        # rest of the batch. Only ValueError - the documented failure mode
        # of `notify` - is caught; anything else (a broken adapter raising
        # e.g. TypeError) propagates, since silently swallowing it would
        # hide a real bug behind "just another failed recipient."
        failed: list[str] = []
        for recipient in recipients:
            try:
                self.notify(recipient, message)
            except ValueError:
                failed.append(recipient)
        return failed


# ---------------------------------------------------------------------------
# The composition root - the ONLY place that names concrete adapters.
# ---------------------------------------------------------------------------
def build_service(
    use_smtp: bool, host: str = "localhost", port: int = 25
) -> NotificationService:
    """Wire a `NotificationService` to a concrete adapter.

    Everything above this function (the service, and any code that calls
    it) only ever sees `NotificationSender`. In a real app this function
    would sit near `main()`/app startup and read `use_smtp`/`host`/`port`
    from config (see problem 08) rather than taking them as plain args.
    """
    sender: NotificationSender
    if use_smtp:
        sender = SmtpEmailSender(host, port)
    else:
        sender = InMemorySender()
    return NotificationService(sender)


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Let the *consumer* (NotificationService) own the port's shape, not the
#   producer (an adapter) - the Dependency Inversion Principle. If a new
#   adapter needs a method the port doesn't have, that's a service-level
#   design question ("does the business logic actually need this?"), not
#   an adapter-level one.
# - Keep exactly one composition root per logical "app" - scattering
#   `SmtpEmailSender(...)` constructor calls throughout the codebase
#   defeats the purpose; every concrete-adapter decision should be
#   traceable to one function (or one small set of them, per entry point).
# - Prefer a fake over a `Mock` when the double needs actual state/behavior
#   (here: "remembering what was sent, queryable by recipient") - see
#   problem 20 for exactly when a `Mock`/`patch` is the better tool instead.
# - Type the injected dependency as the Protocol in the constructor
#   signature, never as a concrete adapter class or `Any` - that's what
#   gives mypy the ability to catch a caller passing something that
#   doesn't actually implement `send`.
#
# Alternative approaches
# -----------------------
# - An abstract base class (`abc.ABC` + `@abstractmethod`) would also work
#   as a port, but forces every adapter to explicitly inherit from it -
#   fine for a first-party adapter, awkward for wrapping a third-party
#   object you don't control (you can't retroactively make `httpx.Client`
#   inherit from your ABC, but a Protocol matches it structurally for
#   free if the shape lines up).
# - A DI framework (e.g. `dependency-injector`, `punq`) becomes worth it
#   once you have dozens of services with deep, config-driven dependency
#   graphs and want declarative wiring - for a handful of services,
#   explicit constructor injection at one composition root is more
#   readable and fully static-type-checked with zero extra dependency.
# - `runtime_checkable` + `isinstance()` checks could replace mypy's
#   static verification for a plugin system that loads adapters
#   dynamically at runtime (where there's no static call site to check) -
#   not needed here since `build_service` is a fixed, static call site.
