"""Short-term conversational memory as a bounded buffer."""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterable

Message = dict[str, str]


class ShortTermMemory:
    """Maintains the latest conversation turns for quick recall."""

    def __init__(self, *, capacity: int = 24) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._messages: Deque[Message] = deque(maxlen=capacity)

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def extend(self, messages: Iterable[Message]) -> None:
        for message in messages:
            self._messages.append(message)

    def history(self) -> list[Message]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"ShortTermMemory(capacity={self.capacity}, messages={list(self._messages)})"
