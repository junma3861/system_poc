"""OpenRouter client used to reach hosted LLMs."""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

import httpx
from pydantic import BaseModel, Field

from ..config import Settings

# Type alias for chat messages with role and content fields
Message = dict[str, str]


class ChoiceMessage(BaseModel):
    """Represents a message within a choice returned by the API."""
    role: str
    content: str


class Choice(BaseModel):
    """Represents a single completion choice from the API response."""
    index: int = 0
    message: ChoiceMessage
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    """Schema for OpenRouter's chat completion API response."""
    id: str
    choices: list[Choice] = Field(default_factory=list)
    created: Optional[int] = None
    model: Optional[str] = None


class OpenRouterClient:
    """Thin wrapper around the OpenRouter chat completions endpoint."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: Optional[httpx.Client] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        """Initialize the OpenRouter client.
        
        Args:
            settings: Configuration settings including API key and model.
            http_client: Optional custom HTTP client. If None, creates a new client.
            transport: Optional custom transport for testing (e.g., MockTransport).
        """
        self.settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=settings.openrouter_base_url,
            timeout=settings.openrouter_timeout,
            transport=transport,
        )

    def _request(self, payload: dict[str, Any]) -> ChatCompletionResponse:
        """Send a chat completion request to OpenRouter API.
        
        Args:
            payload: JSON payload containing model, messages, and parameters.
            
        Returns:
            Parsed ChatCompletionResponse from the API.
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status.
        """
        response = self._client.post(
            "/chat/completions",
            headers=self.settings.headers,
            json=payload,
        )
        response.raise_for_status()
        return ChatCompletionResponse.model_validate(response.json())

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> str:
        """Send a chat request with a sequence of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Controls randomness (0.0-2.0). Lower is more deterministic.
            top_p: Nucleus sampling parameter. Lower values make output more focused.
            max_tokens: Maximum number of tokens to generate.
            extra: Additional parameters to include in the API request.
            
        Returns:
            The assistant's response content as a string.
            
        Raises:
            RuntimeError: If the API returns no choices.
        """
        payload = {
            "model": self.settings.openrouter_model,
            "messages": list(messages),
            "temperature": temperature,
            "top_p": top_p,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        completion = self._request(payload)
        if not completion.choices:
            raise RuntimeError("OpenRouter returned no choices.")
        return completion.choices[0].message.content.strip()

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context_messages: Optional[Iterable[Message]] = None,
        **kwargs: Any,
    ) -> str:
        """Complete a chat interaction with system and user prompts.
        
        This is a convenience method that builds the message list from components.
        
        Args:
            system_prompt: The system instruction defining assistant behavior.
            user_prompt: The user's query or input.
            context_messages: Optional conversation history to include.
            **kwargs: Additional parameters passed to chat().
            
        Returns:
            The assistant's response content as a string.
        """
        messages: list[Message] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context_messages:
            messages.extend(context_messages)
        messages.append({"role": "user", "content": user_prompt})
        return self.chat(messages, **kwargs)

    def close(self) -> None:
        """Close the HTTP client if owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OpenRouterClient":
        """Context manager entry."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Context manager exit - ensures client is closed."""
        self.close()
