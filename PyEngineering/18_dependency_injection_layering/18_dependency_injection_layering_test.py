"""Tests for `18_dependency_injection_layering_solution.py`.

Run: .venv/bin/pytest 18_dependency_injection_layering/ -v
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest

# The module under test is named "18_..." which is not a valid Python
# identifier, so it can't be reached with a normal `import` statement -
# `importlib.import_module` takes an arbitrary string and works fine for a
# file-based module. mypy can't statically resolve these as *types*, only
# as runtime values, hence the `Any` annotations below.
_solution = import_module("18_dependency_injection_layering_solution")
NotificationSender = _solution.NotificationSender
SmtpEmailSender = _solution.SmtpEmailSender
InMemorySender = _solution.InMemorySender
NotificationService = _solution.NotificationService
build_service = _solution.build_service


# ---------------------------------------------------------------------------
# The fake adapter satisfies the protocol structurally.
# ---------------------------------------------------------------------------
def test_in_memory_sender_is_a_notification_sender() -> None:
    sender: Any = InMemorySender()
    assert isinstance(sender, NotificationSender)


def test_smtp_email_sender_is_a_notification_sender() -> None:
    sender: Any = SmtpEmailSender(host="smtp.example.com", port=587)
    assert isinstance(sender, NotificationSender)


def test_neither_adapter_subclasses_the_protocol() -> None:
    # Structural, not nominal, typing: neither adapter names the Protocol
    # as a base class.
    assert NotificationSender not in InMemorySender.__mro__
    assert NotificationSender not in SmtpEmailSender.__mro__


# ---------------------------------------------------------------------------
# InMemorySender fake behavior
# ---------------------------------------------------------------------------
def test_in_memory_sender_records_messages() -> None:
    sender: Any = InMemorySender()
    sender.send("alice@example.com", "hello")
    sender.send("bob@example.com", "hi")
    sender.send("alice@example.com", "again")

    assert sender.messages == [
        ("alice@example.com", "hello"),
        ("bob@example.com", "hi"),
        ("alice@example.com", "again"),
    ]
    assert sender.sent_to("alice@example.com") == ["hello", "again"]
    assert sender.sent_to("bob@example.com") == ["hi"]
    assert sender.sent_to("carol@example.com") == []


# ---------------------------------------------------------------------------
# SmtpEmailSender adapter behavior
# ---------------------------------------------------------------------------
def test_smtp_email_sender_logs_formatted_line() -> None:
    sender: Any = SmtpEmailSender(host="smtp.example.com", port=587)
    sender.send("alice@example.com", "hello")

    assert len(sender.sent_log) == 1
    assert "smtp.example.com:587" in sender.sent_log[0]
    assert "alice@example.com" in sender.sent_log[0]
    assert "hello" in sender.sent_log[0]


# ---------------------------------------------------------------------------
# NotificationService: depends only on the port, exercised via the fake.
# ---------------------------------------------------------------------------
def test_notify_delegates_to_sender() -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    service.notify("alice@example.com", "hello")

    assert fake.sent_to("alice@example.com") == ["hello"]


@pytest.mark.parametrize("recipient", ["", "   ", "\t\n"])
def test_notify_rejects_blank_recipient(recipient: str) -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    with pytest.raises(ValueError):
        service.notify(recipient, "hello")
    assert fake.messages == []


@pytest.mark.parametrize("message", ["", "   ", "\t\n"])
def test_notify_rejects_blank_message(message: str) -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    with pytest.raises(ValueError):
        service.notify("alice@example.com", message)
    assert fake.messages == []


def test_notify_many_delivers_to_all_valid_recipients() -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    failed = service.notify_many(
        ["alice@example.com", "bob@example.com"], "announcement"
    )

    assert failed == []
    assert fake.sent_to("alice@example.com") == ["announcement"]
    assert fake.sent_to("bob@example.com") == ["announcement"]


def test_notify_many_reports_failed_recipients_without_aborting_batch() -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    failed = service.notify_many(
        ["alice@example.com", "", "bob@example.com", "   "], "announcement"
    )

    assert failed == ["", "   "]
    # The valid recipients still got the message despite the failures.
    assert fake.sent_to("alice@example.com") == ["announcement"]
    assert fake.sent_to("bob@example.com") == ["announcement"]


def test_notify_many_preserves_order_of_failures() -> None:
    fake: Any = InMemorySender()
    service = NotificationService(fake)

    failed = service.notify_many(["", "alice@example.com", "  "], "hi")

    assert failed == ["", "  "]


# ---------------------------------------------------------------------------
# Composition root wiring
# ---------------------------------------------------------------------------
def test_build_service_wires_in_memory_sender_by_default() -> None:
    service: Any = build_service(use_smtp=False)

    assert isinstance(service._sender, InMemorySender)


def test_build_service_wires_smtp_sender_when_requested() -> None:
    service: Any = build_service(use_smtp=True, host="mail.example.com", port=2525)

    assert isinstance(service._sender, SmtpEmailSender)
    assert service._sender.host == "mail.example.com"
    assert service._sender.port == 2525


def test_build_service_returns_a_working_service() -> None:
    service: Any = build_service(use_smtp=False)
    service.notify("alice@example.com", "hello")

    assert service._sender.sent_to("alice@example.com") == ["hello"]
