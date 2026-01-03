"""Coordinates short-term and long-term memories."""

from __future__ import annotations

from typing import Iterable, Optional

from .long_term import LongTermMemory, SummaryRecord
from .short_term import Message, ShortTermMemory


class MemoryManager:
    """High-level facade for managing conversation state."""

    def __init__(self, short_term: ShortTermMemory, long_term: LongTermMemory) -> None:
        self.short_term = short_term
        self.long_term = long_term

    def record_user(self, content: str) -> None:
        self.short_term.add("user", content)

    def record_assistant(self, content: str) -> None:
        self.short_term.add("assistant", content)

    def history(self) -> list[Message]:
        return self.short_term.history()

    def summarize_and_store(
        self,
        session_id: str,
        *,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> SummaryRecord:
        return self.long_term.summarize_and_store(
            session_id,
            self.short_term.history(),
            tags=tags,
            metadata=metadata,
        )

    def load_recent_summaries(self, limit: int = 5) -> list[SummaryRecord]:
        return self.long_term.latest(limit)

    def clear_short_term(self) -> None:
        self.short_term.clear()
