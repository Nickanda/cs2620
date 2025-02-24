from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UserSignup(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class SearchPattern(_message.Message):
    __slots__ = ("pattern",)
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    def __init__(self, pattern: _Optional[str] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, users: _Optional[_Iterable[str]] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("sender", "receiver", "message")
    SENDER_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    sender: str
    receiver: str
    message: str
    def __init__(self, sender: _Optional[str] = ..., receiver: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class GetMessages(_message.Message):
    __slots__ = ("username", "num_messages")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    NUM_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    username: str
    num_messages: int
    def __init__(self, username: _Optional[str] = ..., num_messages: _Optional[int] = ...) -> None: ...

class RetrievedMessage(_message.Message):
    __slots__ = ("id", "sender", "message")
    ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    id: int
    sender: str
    message: str
    def __init__(self, id: _Optional[int] = ..., sender: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class MessageList(_message.Message):
    __slots__ = ("messages",)
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[RetrievedMessage]
    def __init__(self, messages: _Optional[_Iterable[_Union[RetrievedMessage, _Mapping]]] = ...) -> None: ...

class DeleteMessage(_message.Message):
    __slots__ = ("username", "ids")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    username: str
    ids: str
    def __init__(self, username: _Optional[str] = ..., ids: _Optional[str] = ...) -> None: ...

class UpdateHome(_message.Message):
    __slots__ = ("username", "undeliv_messages")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    UNDELIV_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    username: str
    undeliv_messages: int
    def __init__(self, username: _Optional[str] = ..., undeliv_messages: _Optional[int] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
