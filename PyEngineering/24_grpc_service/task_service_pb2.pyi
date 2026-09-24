# ruff: noqa
# mypy: ignore-errors
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Task(_message.Message):
    __slots__ = ("id", "title", "done")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    done: bool
    def __init__(
        self,
        id: _Optional[str] = ...,
        title: _Optional[str] = ...,
        done: _Optional[bool] = ...,
    ) -> None: ...

class CreateTaskRequest(_message.Message):
    __slots__ = ("title",)
    TITLE_FIELD_NUMBER: _ClassVar[int]
    title: str
    def __init__(self, title: _Optional[str] = ...) -> None: ...

class GetTaskRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListTasksRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SlowRequest(_message.Message):
    __slots__ = ("delay_seconds",)
    DELAY_SECONDS_FIELD_NUMBER: _ClassVar[int]
    delay_seconds: float
    def __init__(self, delay_seconds: _Optional[float] = ...) -> None: ...

class SlowResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
