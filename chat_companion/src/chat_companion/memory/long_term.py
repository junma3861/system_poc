"""Long-term memory that stores summaries of prior conversations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from time import time
from typing import Any, Callable, Iterable, Optional, Sequence

Message = dict[str, str]


@dataclass
class SummaryRecord:
    session_id: str
    summary: str
    created_at: float = field(default_factory=time)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def default_summarizer(messages: Sequence[Message]) -> str:
    if not messages:
        return "No conversation to summarize."
    opening = messages[0]["content"].strip()
    closing = messages[-1]["content"].strip()
    bullet_points = [opening]
    if len(messages) > 1:
        bullet_points.append(closing)
    condensed = " | ".join(point[:160] for point in bullet_points)
    return f"Session recap: {condensed}"


class LongTermMemory:
    """Stores session summaries on disk for future retrieval."""

    def __init__(
        self,
        store_path: Path,
        *,
        summarizer: Callable[[Sequence[Message]], str] = default_summarizer,
    ) -> None:
        self.store_path = store_path
        self.summarizer = summarizer
        self._records: list[SummaryRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        with self.store_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            self._records = [SummaryRecord(**item) for item in data]

    def _persist(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("w", encoding="utf-8") as handle:
            json.dump([asdict(record) for record in self._records], handle, indent=2)

    def add_summary(
        self,
        session_id: str,
        summary: str,
        *,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SummaryRecord:
        record = SummaryRecord(
            session_id=session_id,
            summary=summary,
            tags=list(tags or []),
            metadata=metadata or {},
        )
        self._records.append(record)
        self._persist()
        return record

    def summarize_and_store(
        self,
        session_id: str,
        conversation: Sequence[Message],
        *,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SummaryRecord:
        summary = self.summarizer(conversation)
        return self.add_summary(session_id, summary, tags=tags, metadata=metadata)

    def latest(self, limit: int = 5) -> list[SummaryRecord]:
        return list(self._records[-limit:])

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"LongTermMemory(records={len(self)})"
