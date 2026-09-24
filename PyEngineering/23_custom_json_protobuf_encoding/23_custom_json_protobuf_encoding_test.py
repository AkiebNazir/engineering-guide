"""Tests for `23_custom_json_protobuf_encoding_solution.py`.

Run: .venv/bin/pytest 23_custom_json_protobuf_encoding/ -v
"""

from __future__ import annotations

import inspect
import io
import json
from importlib import import_module
from typing import Any

import pytest

_solution = import_module("23_custom_json_protobuf_encoding_solution")
Event = _solution.Event
encode_event = _solution.encode_event
decode_event = _solution.decode_event
event_object_hook = _solution.event_object_hook
write_events_jsonl = _solution.write_events_jsonl
read_events_jsonl = _solution.read_events_jsonl
event_to_proto = _solution.event_to_proto
proto_to_event = _solution.proto_to_event
encode_event_proto = _solution.encode_event_proto
decode_event_proto = _solution.decode_event_proto


def _sample_events() -> list[Any]:
    return [
        Event("evt-1", "order.created", 1_700_000_000.0, {"amount": 42}, priority=1),
        Event("evt-2", "order.cancelled", 1_700_000_100.5, {}, priority=0),
        Event(
            "evt-3",
            "user.updated",
            1_700_000_200.25,
            {"nested": {"a": 1, "b": [1, 2, 3]}},
            priority=5,
        ),
    ]


# ---------------------------------------------------------------------------
# JSON encode/decode round trip.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("event", _sample_events())
def test_json_round_trip(event: Any) -> None:
    assert decode_event(encode_event(event)) == event


def test_encoded_json_is_plain_text() -> None:
    event = _sample_events()[0]
    encoded = encode_event(event)
    assert isinstance(encoded, str)
    # Sanity: it's real JSON, not some opaque encoding.
    parsed = json.loads(encoded)
    assert parsed["__type__"] == "Event"
    assert parsed["event_id"] == "evt-1"


# ---------------------------------------------------------------------------
# Schema evolution: missing "priority" key still decodes.
# ---------------------------------------------------------------------------
def test_schema_evolution_missing_priority_defaults_to_zero() -> None:
    legacy_json = json.dumps(
        {
            "__type__": "Event",
            "event_id": "evt-old",
            "event_type": "legacy.event",
            "timestamp": 1_600_000_000.0,
            "payload": {"note": "written before priority existed"},
            # no "priority" key at all
        }
    )
    event = json.loads(legacy_json, object_hook=event_object_hook)
    assert isinstance(event, Event)
    assert event.priority == 0
    assert event.event_id == "evt-old"


def test_object_hook_ignores_plain_nested_dicts() -> None:
    # A dict without the "__type__" marker must pass through unchanged,
    # even though it has some overlapping key names.
    plain = {"event_id": "not-an-event", "amount": 10}
    assert event_object_hook(plain) is plain


# ---------------------------------------------------------------------------
# Streaming JSON Lines encode/decode.
# ---------------------------------------------------------------------------
def test_jsonl_round_trip() -> None:
    events = _sample_events()
    buffer = io.StringIO()
    write_events_jsonl(events, buffer)

    buffer.seek(0)
    decoded = list(read_events_jsonl(buffer))
    assert decoded == events


def test_jsonl_write_is_one_line_per_event() -> None:
    events = _sample_events()
    buffer = io.StringIO()
    write_events_jsonl(events, buffer)
    lines = [line for line in buffer.getvalue().split("\n") if line]
    assert len(lines) == len(events)


def test_read_events_jsonl_is_a_generator() -> None:
    buffer = io.StringIO()
    write_events_jsonl(_sample_events(), buffer)
    buffer.seek(0)
    result = read_events_jsonl(buffer)
    assert inspect.isgenerator(result)


def test_read_events_jsonl_streams_incrementally() -> None:
    # Consume one event, then append and read more without the reader
    # having pre-materialized everything up front. A single io.StringIO
    # can't easily simulate append-while-reading, so instead this checks
    # that only as many lines as consumed have been parsed by advancing
    # the generator manually and confirming partial consumption works
    # (a plain `list`-returning implementation would also pass a full
    # consumption test, but this confirms laziness via next()).
    events = _sample_events()
    buffer = io.StringIO()
    write_events_jsonl(events, buffer)
    buffer.seek(0)

    gen = read_events_jsonl(buffer)
    first = next(gen)
    assert first == events[0]
    rest = list(gen)
    assert rest == events[1:]


def test_jsonl_skips_blank_lines() -> None:
    events = _sample_events()
    buffer = io.StringIO()
    write_events_jsonl(events, buffer)
    raw = buffer.getvalue()
    with_blanks = raw.replace("\n", "\n\n")
    decoded = list(read_events_jsonl(io.StringIO(with_blanks)))
    assert decoded == events


# ---------------------------------------------------------------------------
# Protobuf round trip.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("event", _sample_events())
def test_proto_round_trip(event: Any) -> None:
    assert decode_event_proto(encode_event_proto(event)) == event


def test_proto_to_event_and_back_are_inverse() -> None:
    event = _sample_events()[2]
    message = event_to_proto(event)
    assert proto_to_event(message) == event


def test_proto_empty_payload_round_trips() -> None:
    event = Event("evt-empty", "noop", 0.0, {}, priority=0)
    assert decode_event_proto(encode_event_proto(event)) == event


# ---------------------------------------------------------------------------
# Size comparison (measured, not assumed).
# ---------------------------------------------------------------------------
def test_protobuf_not_larger_than_json_for_realistic_payload() -> None:
    event = Event(
        "evt-large",
        "order.created",
        1_700_000_000.123,
        {"sku": "ABC-123", "quantity": 7, "warehouse": "eu-west-1"},
        priority=3,
    )
    json_size = len(encode_event(event).encode("utf-8"))
    proto_size = len(encode_event_proto(event))
    assert proto_size <= json_size
