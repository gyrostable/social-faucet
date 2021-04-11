from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Message:
    source: str
    id: str
    user_id: str
    text: str
    extra: dict = field(default_factory=dict)


class Status(Enum):
    SUCCESS = 0
    INVALID = 1
    RATE_LIMITED = 2
    ERROR = 3
