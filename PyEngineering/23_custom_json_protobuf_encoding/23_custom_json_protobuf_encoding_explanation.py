"""
23 - Custom JSON & protobuf encoding
=======================================

WHAT WE'RE BUILDING
--------------------
An `Event` envelope (`event_id`, `event_type`, `timestamp`, `payload`,
`priority`) encoded two different ways:

1. **Custom JSON** via `json.JSONEncoder` (encode) and `object_hook`
   (decode), plus a *streaming* JSON Lines reader/writer that works over
   any file-like object instead of building one giant string in memory.
2. **Protobuf**, using a small `.proto` contract compiled to real Python
   bindings with `grpcio-tools` (see `event.proto` in this directory for
   the exact generation command - it's also repeated below).

Both paths round-trip the same `Event` dataclass, so the exercise is a
direct, measurable comparison of two serialization strategies you'll
choose between constantly in production Python: "JSON because it's
debuggable and the ecosystem already speaks it" vs "protobuf because it's
smaller on the wire and the schema is enforced."

WHY THIS MATTERS IN REAL SYSTEMS
-----------------------------------
1. **`JSONEncoder`/`object_hook` are how you teach `json` your domain
   types.** `json.dumps` has no idea what an `Event` (or a `datetime`, or
   a `Decimal`) is - `default=`/subclassing `JSONEncoder` on the encode
   side and `object_hook=` on the decode side are the two extension
   points that let `json.dumps`/`json.loads` round-trip domain objects
   without every caller hand-rolling `.to_dict()`/`from_dict()` calls.
2. **Streaming vs "one giant string" is a real memory/latency decision.**
   `json.dumps(huge_list)` builds the *entire* serialized string in
   memory before you can write a single byte of it anywhere, and
   `json.load(fp)` needs the entire file's bytes parsed before you see
   the first record. For a log/event stream that's unbounded or just
   large, JSON Lines (one JSON object per line, written/read
   incrementally) keeps memory bounded to one record at a time and lets
   a consumer start processing before the producer finishes - the same
   trade-off `csv.DictWriter`/`DictReader` make for tabular data.
3. **Schema evolution is where JSON and protobuf diverge sharply.** JSON
   has no schema at all - an old consumer reading a new field just
   ignores it, and a new consumer reading an old record missing a field
   must defend itself explicitly (`dict.get(key, default)` in the decode
   hook, exactly like a migration `ALTER TABLE ... DEFAULT`). Protobuf
   bakes this into the wire format: every field is optional on the wire
   by field number, an old message decoded by a new schema silently gets
   the type's zero-value for fields it never set, and *removing* a field
   number is the one operation you must never redo (reusing a retired
   field number can misinterpret old bytes) - a discipline JSON gives you
   no help enforcing.
4. **Protobuf is smaller and schema-checked; JSON is human-debuggable and
   universally supported.** Neither wins outright - `curl | jq` works on
   JSON out of the box and breaks nothing new engineers need to learn;
   protobuf needs the `.proto` compiled and shared, but produces
   meaningfully smaller messages and rejects a field of the wrong type at
   encode time instead of at some downstream consumer's runtime.

CONCEPTS COVERED
------------------
- `json.JSONEncoder` subclassing (`default()`) vs the `cls=` parameter
- `object_hook` for decode-side custom type reconstruction
- Streaming encode/decode over file-like objects (JSON Lines) vs
  `json.dumps`/`json.load` building one string/consuming one blob
- Schema evolution via `dict.get(key, default)` on the JSON side
- A hand-written `.proto` file compiled with
  `python -m grpc_tools.protoc` into real `_pb2.py` bindings
- Converting between a plain dataclass and generated protobuf message
  classes; `SerializeToString()`/`ParseFromString()`

THE SPEC
---------
`Event` (dataclass): `event_id: str`, `event_type: str`,
    `timestamp: float`, `payload: dict[str, Any]`, `priority: int = 0`.

`EventJSONEncoder(json.JSONEncoder)`
    Overrides `default()` to serialize an `Event` as a JSON object with a
    `"__type__": "Event"` marker plus its fields (needed so the decode
    side's `object_hook` can tell an `Event` dict apart from a plain
    nested dict, e.g. inside `payload`).

`event_object_hook(obj: dict[str, Any]) -> Event | dict[str, Any]`
    `json.loads(..., object_hook=...)` callback: if `obj` carries
    `"__type__": "Event"`, reconstruct an `Event`, reading `priority` via
    `obj.get("priority", 0)` so a JSON blob written *before* `priority`
    existed still decodes cleanly. Otherwise return `obj` unchanged (it's
    a nested plain dict, e.g. `payload`, not an `Event`).

`encode_event(event: Event) -> str`
    `json.dumps(event, cls=EventJSONEncoder)`.

`decode_event(data: str) -> Event`
    `json.loads(data, object_hook=event_object_hook)`.

`write_events_jsonl(events: Iterable[Event], fp: TextIO) -> None`
    Streaming encode: write one `encode_event(event)` per line to `fp`,
    one event at a time - never builds a string containing more than one
    event at once, regardless of how many events there are.

`read_events_jsonl(fp: TextIO) -> Iterator[Event]`
    Streaming decode: a *generator* that reads `fp` line by line and
    yields one decoded `Event` per non-blank line - never materializes
    the whole file's events in memory at once.

Protobuf half (`event_pb2`, generated - see `event.proto`):
`event_to_proto(event: Event) -> event_pb2.Event`
    Maps the dataclass to the generated message type, JSON-encoding
    `payload` into the message's `payload_json` string field (the
    envelope-is-protobuf/payload-is-JSON hybrid described above).

`proto_to_event(message: "event_pb2.Event") -> Event`
    Inverse of `event_to_proto`.

`encode_event_proto(event: Event) -> bytes`
    `event_to_proto(event).SerializeToString()`.

`decode_event_proto(data: bytes) -> Event`
    Parse bytes into `event_pb2.Event()` then `proto_to_event(...)`.

ACCEPTANCE CRITERIA
---------------------
1. `decode_event(encode_event(e)) == e` for a variety of `Event`s
   (including empty/nested `payload` dicts).
2. A JSON string built *without* a `"priority"` key still decodes via
   `event_object_hook` to an `Event` with `priority == 0` (schema
   evolution on the JSON side).
3. `write_events_jsonl` followed by `read_events_jsonl` round-trips a
   list of `Event`s through an `io.StringIO`, and `read_events_jsonl`
   is a generator (doesn't eagerly return a `list`) - it must be possible
   to consume one event, mutate/close nothing yet, and still consume the
   rest.
4. `decode_event_proto(encode_event_proto(e)) == e` for the same set of
   events used in (1).
5. Encoding the same `Event` both ways demonstrates the protobuf encoding
   is not larger than the JSON encoding for a realistic payload (measured,
   not assumed - see the module's tests).
6. mypy-clean, black-formatted, ruff-clean. The generated `event_pb2.py`
   (and `.pyi`) are excluded from the "written from scratch" files but
   must still type-check when imported (a narrowly-scoped `# type:
   ignore` on the generated-module import is fine; do not disable mypy
   broadly).

Regenerate the protobuf bindings any time `event.proto` changes, from the
`PyEngineering/` directory:

    .venv/bin/python -m grpc_tools.protoc \\
        -I23_custom_json_protobuf_encoding \\
        --python_out=23_custom_json_protobuf_encoding \\
        --pyi_out=23_custom_json_protobuf_encoding \\
        23_custom_json_protobuf_encoding/event.proto
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import IO, Any


@dataclass
class Event:
    """Domain object mirrored by both the JSON encoding and `event.proto`."""

    event_id: str
    event_type: str
    timestamp: float
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


# ---------------------------------------------------------------------------
# Custom JSON encode/decode.
# ---------------------------------------------------------------------------
class EventJSONEncoder(json.JSONEncoder):
    """`json.JSONEncoder` subclass that knows how to serialize `Event`.

    TODO: override `default(self, o: Any) -> Any`. If `o` is an `Event`,
    return a plain dict with a `"__type__": "Event"` marker plus its
    fields (`event_id`, `event_type`, `timestamp`, `payload`, `priority`).
    Otherwise call `super().default(o)` (raises `TypeError` for anything
    else `json` doesn't know how to encode - do not swallow that).
    """

    def default(self, o: Any) -> Any:
        raise NotImplementedError("TODO: implement EventJSONEncoder.default")


def event_object_hook(obj: dict[str, Any]) -> Event | dict[str, Any]:
    """`json.loads(..., object_hook=...)` callback.

    TODO: if `obj.get("__type__") == "Event"`, build and return an
    `Event` from `obj`'s fields, reading `priority` via
    `obj.get("priority", 0)` (schema evolution: old JSON without a
    `priority` key must still decode). Otherwise return `obj` unchanged -
    `object_hook` is called for *every* JSON object decoded, including
    nested ones like `payload`, and only the `Event` marker distinguishes
    the outer object from a plain nested dict.
    """
    raise NotImplementedError("TODO: implement event_object_hook")


def encode_event(event: Event) -> str:
    """TODO: `json.dumps(event, cls=EventJSONEncoder)`."""
    raise NotImplementedError("TODO: implement encode_event")


def decode_event(data: str) -> Event:
    """TODO: `json.loads(data, object_hook=event_object_hook)`.

    The result of `json.loads` is typed `Any`; the caller of this
    function gets the narrower `Event` return type back.
    """
    raise NotImplementedError("TODO: implement decode_event")


# ---------------------------------------------------------------------------
# Streaming encode/decode over file-like objects (JSON Lines).
# ---------------------------------------------------------------------------
def write_events_jsonl(events: Iterable[Event], fp: IO[str]) -> None:
    """Streaming encode: one `encode_event(event)` per line, written as
    each event is produced - never holds more than one event's JSON in
    memory at a time, regardless of how many events `events` yields.

    TODO: for event in events: fp.write(encode_event(event) + "\\n")
    """
    raise NotImplementedError("TODO: implement write_events_jsonl")


def read_events_jsonl(fp: IO[str]) -> Iterator[Event]:
    """Streaming decode: a generator yielding one `Event` per non-blank
    line of `fp`.

    TODO: iterate `fp` line by line (file objects are already line
    iterators - do not call `fp.read()` or `fp.readlines()`, that would
    defeat the point). For each line, `line.strip()`; skip if empty;
    otherwise `yield decode_event(line)`.
    """
    raise NotImplementedError("TODO: implement read_events_jsonl")
    yield  # pragma: no cover - makes this a generator function for mypy


# ---------------------------------------------------------------------------
# Protobuf half. See event.proto for the schema and the exact `protoc`
# generation command (repeated in the module docstring above).
# ---------------------------------------------------------------------------
# TODO: import the generated module. mypy has no type information for
# generated protobuf code, so scope the ignore to this one import:
#
# from . import event_pb2  # type: ignore[import-untyped]
#
# (This file is run/imported directly - not as a package - so a bare
# `import event_pb2` also works when this directory is on `sys.path`,
# which is how the test file imports it. Pick whichever import form the
# solution file uses and keep it consistent with the test.)


def event_to_proto(event: Event) -> Any:
    """TODO: build and return an `event_pb2.Event`, JSON-encoding
    `event.payload` into the message's `payload_json` field via
    `json.dumps(event.payload)`.
    """
    raise NotImplementedError("TODO: implement event_to_proto")


def proto_to_event(message: Any) -> Event:
    """TODO: inverse of `event_to_proto` - read `message`'s fields back
    into an `Event`, `json.loads`-ing `payload_json` back into a dict.
    """
    raise NotImplementedError("TODO: implement proto_to_event")


def encode_event_proto(event: Event) -> bytes:
    """TODO: `event_to_proto(event).SerializeToString()`."""
    raise NotImplementedError("TODO: implement encode_event_proto")


def decode_event_proto(data: bytes) -> Event:
    """TODO: parse `data` into an `event_pb2.Event()` (`.ParseFromString`)
    then `proto_to_event(...)`.
    """
    raise NotImplementedError("TODO: implement decode_event_proto")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `JSONEncoder.default` is only called for objects `json` doesn't
#   already know how to serialize (not str/int/float/bool/None/list/dict)
#   - you never call it yourself, `json.dumps` calls it internally when it
#     hits an `Event`.
# - `object_hook` fires for *every* JSON object as it's parsed, bottom-up
#   (innermost objects first) - a nested `payload` dict is seen by the
#   hook before the outer `Event` dict is, which is exactly why the
#   `"__type__"` marker is needed to tell them apart.
# - `IO[str]` (from `typing`) is the right parameter type for "a
#   file-like object opened in text mode" - it matches both a real open
#   file and `io.StringIO`, which is what the tests use to avoid touching
#   the filesystem.
# - Regenerate `event_pb2.py`/`event_pb2.pyi` with the `protoc` command in
#   the module docstring any time `event.proto` changes - they're
#   generated artifacts, never hand-edit them.
#
# COMMON PITFALLS
# ----------------
# - Forgetting the `"__type__"` marker (or checking for it) and having
#   `event_object_hook` try to build an `Event` out of every dict it
#   sees, including `payload` - `Event(**payload)` blows up the moment
#   `payload`'s keys don't happen to match `Event`'s fields.
# - Using `dict[key]` instead of `dict.get(key, default)` for `priority`
#   in the decode hook - that's the one line that makes schema evolution
#   actually work; a plain subscript reintroduces a `KeyError` on old data.
# - Calling `fp.read()` inside `read_events_jsonl` "to be safe" - that
#   silently turns the streaming reader back into a load-everything
#   reader and defeats acceptance criterion 3.
# - Round-tripping `payload` through the protobuf path without
#   `json.dumps`/`json.loads` - `payload_json` is a `str` field; assigning
#   a `dict` to it directly is a `TypeError` from the generated message
#   class, not a silent bug, but it's the fix people reach for wrong first.
#
# STRETCH GOALS
# --------------
# - Add a `payload_schema_version` field to `Event` and demonstrate
#   decoding a v1 JSON blob (no `payload_schema_version` key) and a v2
#   blob side by side, both handled by the same `event_object_hook`.
# - Compress the JSON Lines stream with `gzip.open` (text mode) and show
#   `read_events_jsonl`/`write_events_jsonl` work unmodified - they only
#   need "a text file-like object," which a gzip text-mode handle is.
# - Extend `event.proto` with an `enum EventType` instead of a free `str`
#   `event_type`, and discuss why that's a schema-evolution-riskier move
#   than adding a new field (reordering/removing enum values shifts
#   meaning for old wire bytes in a way appending never does).
