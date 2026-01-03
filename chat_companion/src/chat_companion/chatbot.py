"""High-level chatbot orchestration."""

from __future__ import annotations

import json
from typing import Iterable, Sequence

from .llm.openrouter import OpenRouterClient
from .memory.manager import MemoryManager
from .prompts.templates import PromptLibrary, format_conversation


class Chatbot:
    """Connects prompts, LLM, and memory modules."""

    def __init__(
        self,
        llm: OpenRouterClient,
        prompts: PromptLibrary,
        memory: MemoryManager,
    ) -> None:
        self.llm = llm
        self.prompts = prompts
        self.memory = memory

    def _conversation_text(self) -> str:
        return format_conversation(self.memory.history())

    def suggest_queries(self, *, count: int = 3) -> list[str]:
        template = self.prompts.get("query_suggestion")
        user_prompt = template.render_user(
            conversation=self._conversation_text(),
            count=str(count),
        )
        raw = self.llm.complete(
            system_prompt=template.system,
            user_prompt=user_prompt,
        )
        try:
            payload = json.loads(raw)
            suggestions = payload.get("suggestions", [])
            if isinstance(suggestions, list):
                return [str(item) for item in suggestions][:count]
        except json.JSONDecodeError:
            pass
        return [line.strip("- ") for line in raw.splitlines() if line.strip()][:count]

    def respond(self, user_input: str) -> str:
        self.memory.record_user(user_input)
        template = self.prompts.get("response")
        user_prompt = template.render_user(
            conversation=self._conversation_text(),
            user_input=user_input,
        )
        assistant_message = self.llm.complete(
            system_prompt=template.system,
            user_prompt=user_prompt,
        )
        self.memory.record_assistant(assistant_message)
        return assistant_message

    def rank_responses(self, candidates: Sequence[dict[str, str]]) -> dict[str, str]:
        template = self.prompts.get("ranking")
        normalized = [
            {
                "id": candidate.get("id") or str(index),
                "content": candidate["content"],
            }
            for index, candidate in enumerate(candidates)
        ]
        candidate_block = "\n".join(
            f"- {item['id']}: {item['content']}" for item in normalized
        )
        user_prompt = template.render_user(
            conversation=self._conversation_text(),
            candidates=candidate_block,
        )
        raw = self.llm.complete(
            system_prompt=template.system,
            user_prompt=user_prompt,
        )
        try:
            payload = json.loads(raw)
            winner = payload.get("winner")
            reason = payload.get("reason", "")
            if winner is None:
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            winner = normalized[0]["id"]
            reason = raw.strip()
        return {"winner": str(winner), "reason": reason, "raw": raw}

    def force_summary(self, session_id: str) -> str:
        record = self.memory.summarize_and_store(session_id)
        return record.summary
