"""Prompt templates used by the chatbot for different tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

Message = dict[str, str]


def format_conversation(messages: Sequence[Message]) -> str:
    """Render a conversation into a readable transcript."""

    lines = [f"{m['role'].title()}: {m['content'].strip()}" for m in messages]
    return "\n".join(lines)


@dataclass
class PromptTemplate:
    """Simple template with system and user segments."""

    name: str
    system: str
    user_template: str

    def render_user(self, **kwargs: str) -> str:
        return self.user_template.format(**kwargs)


class PromptLibrary:
    """Collection of prompt templates keyed by human-friendly names."""

    def __init__(self, templates: Iterable[PromptTemplate]):
        self._templates = {template.name: template for template in templates}

    def get(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise KeyError(f"Prompt '{name}' is not registered.")
        return self._templates[name]

    @property
    def names(self) -> list[str]:
        return sorted(self._templates)


QUERY_SUGGESTION = PromptTemplate(
    name="query_suggestion",
    system=(
        "You generate short follow-up queries that help the user keep a helpful"
        " conversation moving. Suggestions must be concrete and reference the"
        " conversation context when possible. Return JSON with a 'suggestions'"
        " array of plain strings."
    ),
    user_template=(
        "Here is the recent conversation:\n{conversation}\n\n"
        "Suggest up to {count} follow-up questions the user could ask next."
    ),
)

RESPONSE_PROMPT = PromptTemplate(
    name="response",
    system=(
        "You are an empathetic and detail-oriented companion chatbot. Respond"
        " with actionable, concise guidance and cite what you remember from"
        " previous turns when relevant."
    ),
    user_template=(
        "Conversation so far:\n{conversation}\n\n"
        "Latest user request:\n{user_input}\n\n"
        "Draft a response that is grounded in the conversation."
    ),
)

RANKING_PROMPT = PromptTemplate(
    name="ranking",
    system=(
        "You are ranking candidate chatbot messages. Output JSON with a"
        " 'winner' key matching the id of the best response and provide"
        " rationale in a 'reason' field."
    ),
    user_template=(
        "Conversation:\n{conversation}\n\n"
        "Candidates:\n{candidates}\n\n"
        "Identify the most helpful candidate."
    ),
)


def build_default_library() -> PromptLibrary:
    """Pre-register the built-in prompt templates."""

    return PromptLibrary([QUERY_SUGGESTION, RESPONSE_PROMPT, RANKING_PROMPT])
