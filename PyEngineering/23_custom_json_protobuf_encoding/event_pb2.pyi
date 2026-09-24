# ruff: noqa
# mypy: ignore-errors
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Event(_message.Message):
    __slots__ = ("event_id", "event_type", "timestamp", "payload_json", "priority")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_JSON_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    event_type: str
    timestamp: float
    payload_json: str
    priority: int
    def __init__(
        self,
        event_id: _Optional[str] = ...,
        event_type: _Optional[str] = ...,
        timestamp: _Optional[float] = ...,
        payload_json: _Optional[str] = ...,
        priority: _Optional[int] = ...,
    ) -> None: ...
