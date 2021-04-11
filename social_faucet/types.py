from dataclasses import dataclass, field


@dataclass
class Message:
    source: str
    id: str
    user_id: str
    text: str
    extra: dict = field(default_factory=dict)
