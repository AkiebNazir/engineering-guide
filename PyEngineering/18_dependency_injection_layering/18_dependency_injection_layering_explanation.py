"""
18 - Dependency injection & layering
======================================

WHAT WE'RE BUILDING
--------------------
A tiny "user notification" service split into three layers:

1. A **port** - `NotificationSender`, a `typing.Protocol` describing "send a
   message to a recipient" with no reference to any concrete transport.
2. Two **adapters** implementing that port: `SmtpEmailSender` (a real-ish
   adapter that would talk to an SMTP server, stubbed here so the exercise
   has no network dependency) and `InMemorySender` (a fake used in tests -
   it records every call it received instead of doing I/O).
3. A **service** (`NotificationService`) that depends only on the
   `NotificationSender` *protocol*, never on a concrete class - it doesn't
   know or care whether it's wired to SMTP or to the fake.
4. A **composition root** (`build_service`) - the one function in the whole
   program that knows about concrete adapter classes and wires them into
   the service. Everything above it only ever sees protocols.

WHY THIS MATTERS IN REAL SYSTEMS
----------------------------------
Python has no built-in DI container culture like Java/C# - and it doesn't
need one for most services. `typing.Protocol` gives you **structural
typing**: `NotificationService` can declare "I need something with a
`send(recipient, message) -> None` method" without importing a base class,
without runtime registration, and without any adapter having to know the
protocol exists (`SmtpEmailSender` never subclasses `NotificationSender` -
it just happens to have a matching method, and mypy verifies the match
statically). This is "ports and adapters" (hexagonal architecture) done
with nothing but the type system and ordinary constructor arguments:

- The **port** (`NotificationSender`) is owned by the business logic layer
  (`NotificationService`) - it describes what the service *needs*, not
  what any particular adapter *provides*. This is the Dependency Inversion
  Principle: the high-level module defines the interface; low-level
  modules (adapters) depend on it, not the other way around.
- **Explicit wiring at a composition root** means there is exactly one
  place in the program where "which concrete adapter goes where" is
  decided - typically near `main()` / app startup. Everything else is
  testable in isolation by passing a different adapter to the constructor.
  There's no hidden global registry, no magic `@inject` decorator scanning
  the call stack, no runtime reflection - just a function call with
  explicit arguments, which is easy to read, easy to step through in a
  debugger, and gives mypy full static checking of the wiring.
- A **fake adapter** (`InMemorySender`) that implements the same protocol
  is what makes the service unit-testable without spinning up SMTP,
  hitting the network, or mocking library internals - see problem 20 for
  the fuller table-driven-tests treatment of this exact pattern.

CONCEPTS COVERED
------------------
- `typing.Protocol` (structural subtyping / duck typing with static checks)
- `runtime_checkable` protocols and `isinstance()` against a Protocol
- Ports-and-adapters layering: port -> adapters -> service -> composition
  root, with dependencies pointing *inward* toward the port
- Constructor injection (passing the port implementation into
  `NotificationService.__init__`) vs a DI framework - and why Python
  rarely needs the latter
- A fake (not a mock) as a first-class test double

THE SPEC
---------
`NotificationSender` (Protocol):
    `send(self, recipient: str, message: str) -> None`

`SmtpEmailSender` (adapter):
    - Constructed with `host: str`, `port: int`.
    - `send(recipient, message)` - here, simulate "sending" by formatting
      a line and appending it to `self.sent_log: list[str]` (a real
      implementation would open a socket; that's out of scope and would
      require a live SMTP server to test against, which is exactly what
      the fake/port split lets us avoid).

`InMemorySender` (fake adapter):
    - `send(recipient, message)` records `(recipient, message)` into
      `self.messages: list[tuple[str, str]]`.
    - `sent_to(recipient: str) -> list[str]` - convenience accessor
      returning all messages sent to a given recipient, in order.

`NotificationService`:
    - Constructed with a single `sender: NotificationSender` dependency
      (constructor injection - nothing else, no service locator).
    - `notify(recipient: str, message: str) -> None`:
        - Raises `ValueError` if `recipient` is empty/whitespace-only or
          `message` is empty/whitespace-only.
        - Otherwise delegates to `self._sender.send(recipient, message)`.
    - `notify_many(recipients: list[str], message: str) -> list[str]`:
        - Calls `notify` for each recipient; collects and returns the
          recipients that raised `ValueError` (e.g. empty strings in the
          list) instead of letting the whole batch fail - partial-failure
          handling a real bulk-notify endpoint needs.

`build_service(...) -> NotificationService` (composition root):
    - Takes a `use_smtp: bool` flag (stands in for "read from config/env"
      in a real app) plus `host`/`port` for the SMTP case.
    - Returns a `NotificationService` wired to `SmtpEmailSender` when
      `use_smtp` is True, else `InMemorySender` - this is the *only*
      function in the module allowed to construct a concrete adapter.

ACCEPTANCE CRITERIA
---------------------
1. `NotificationService` never imports or references `SmtpEmailSender` or
   `InMemorySender` by name - only `NotificationSender`.
2. `SmtpEmailSender` and `InMemorySender` do not inherit from
   `NotificationSender` - protocol conformance is structural.
3. `mypy` statically accepts passing either adapter wherever
   `NotificationSender` is expected, and rejects (were you to try it) an
   object missing `send`.
4. `notify_many` correctly separates recipients that failed validation
   from those that succeeded, without stopping the whole batch.
5. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# The port: what NotificationService needs, described structurally.
# ---------------------------------------------------------------------------
@runtime_checkable
class NotificationSender(Protocol):
    """Structural port: anything with this method shape satisfies it.

    `@runtime_checkable` lets `isinstance(obj, NotificationSender)` work at
    runtime (checking only method *presence*, not signatures - mypy is
    still what enforces signature correctness statically). Adapters below
    deliberately do NOT subclass this - that's the point of structural
    typing.
    """

    def send(self, recipient: str, message: str) -> None: ...


# ---------------------------------------------------------------------------
# Adapters - concrete implementations of the port.
# ---------------------------------------------------------------------------
class SmtpEmailSender:
    """A stand-in for a real SMTP-backed adapter.

    TODO:
    - __init__(self, host: str, port: int) -> None: store host/port, and
      initialize self.sent_log: list[str] = [].
    - send(self, recipient: str, message: str) -> None: append a formatted
      line like f"{self.host}:{self.port} -> {recipient}: {message}" to
      self.sent_log (simulating "sent an email" without real I/O).
    """

    def __init__(self, host: str, port: int) -> None:
        raise NotImplementedError("TODO: implement SmtpEmailSender.__init__")

    def send(self, recipient: str, message: str) -> None:
        raise NotImplementedError("TODO: implement SmtpEmailSender.send")


class InMemorySender:
    """A fake adapter for tests - records calls instead of doing I/O.

    TODO:
    - __init__(self) -> None: self.messages: list[tuple[str, str]] = [].
    - send(self, recipient: str, message: str) -> None: append
      (recipient, message) to self.messages.
    - sent_to(self, recipient: str) -> list[str]: return the `message`
      values (in order) of every recorded call whose recipient matches.
    """

    def __init__(self) -> None:
        raise NotImplementedError("TODO: implement InMemorySender.__init__")

    def send(self, recipient: str, message: str) -> None:
        raise NotImplementedError("TODO: implement InMemorySender.send")

    def sent_to(self, recipient: str) -> list[str]:
        raise NotImplementedError("TODO: implement InMemorySender.sent_to")


# ---------------------------------------------------------------------------
# The service - depends only on the port, injected via the constructor.
# ---------------------------------------------------------------------------
class NotificationService:
    """Business logic layer. Knows nothing about SMTP or fakes - only the
    `NotificationSender` protocol it was handed.

    TODO:
    - __init__(self, sender: NotificationSender) -> None: store it as
      self._sender.
    - notify(self, recipient: str, message: str) -> None: raise
      ValueError if recipient.strip() or message.strip() is empty;
      otherwise self._sender.send(recipient, message).
    - notify_many(self, recipients: list[str], message: str) -> list[str]:
      call self.notify for each recipient, catching ValueError per-item;
      return the list of recipients that failed (in original order),
      without letting one bad recipient abort the whole batch.
    """

    def __init__(self, sender: NotificationSender) -> None:
        raise NotImplementedError("TODO: implement NotificationService.__init__")

    def notify(self, recipient: str, message: str) -> None:
        raise NotImplementedError("TODO: implement NotificationService.notify")

    def notify_many(self, recipients: list[str], message: str) -> list[str]:
        raise NotImplementedError("TODO: implement NotificationService.notify_many")


# ---------------------------------------------------------------------------
# The composition root - the ONLY place that names concrete adapters.
# ---------------------------------------------------------------------------
def build_service(
    use_smtp: bool, host: str = "localhost", port: int = 25
) -> NotificationService:
    """Wire a `NotificationService` to a concrete adapter.

    TODO: if use_smtp: sender = SmtpEmailSender(host, port); else:
    sender = InMemorySender(). Return NotificationService(sender).
    """
    raise NotImplementedError("TODO: implement build_service")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `Protocol` classes are matched structurally: any class with a matching
#   `send(self, recipient: str, message: str) -> None` method satisfies
#   `NotificationSender`, whether or not it inherits from it. Try removing
#   `send` from `InMemorySender` and running mypy to see the rejection.
# - `@runtime_checkable` only makes `isinstance()` check method *names*
#   exist, not that their signatures match - don't rely on it for the
#   correctness mypy already gives you statically; it's useful for the
#   rarer case of a runtime dispatch decision (e.g. "did the caller pass
#   something that looks like a sender at all?").
# - Constructor injection (`NotificationService(sender)`) is normally all
#   the "DI" a Python service needs - no framework, no container, no
#   decorator-based registration. Reach for one only when you have dozens
#   of services with deep, config-driven dependency graphs.
#
# COMMON PITFALLS
# ---------------
# - Having `NotificationService` import `SmtpEmailSender` "just to type
#   hint the parameter" - that reintroduces the coupling the Protocol was
#   meant to remove. The parameter type must be the Protocol.
# - Making the adapters *inherit* from `NotificationSender` - harmless
#   here, but it defeats the purpose of the exercise (structural, not
#   nominal, typing) and creates an import dependency from adapters back
#   to the port module that isn't actually required.
# - Swallowing all exceptions (not just ValueError) in `notify_many` -
#   that would hide real bugs (e.g. a `TypeError` from a broken adapter)
#   behind "just another failed recipient."
#
# STRETCH GOALS
# --------------
# - Add a second port (e.g. `AuditLogger`) and show `NotificationService`
#   depending on two protocols at once, both wired at `build_service`.
# - Make `build_service` read `use_smtp`/`host`/`port` from an `os.environ`
#   mapping argument instead of plain parameters (foreshadows problem 08's
#   config loader).
# - Add an `AsyncNotificationSender` Protocol with an `async def send(...)`
#   method and an adapter using `httpx.AsyncClient`, to show the pattern
#   extends to async ports unchanged.
