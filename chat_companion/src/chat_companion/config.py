"""Configuration helpers for the Chat Companion project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Container for configuration values loaded from environment variables."""

    openrouter_api_key: str
    openrouter_model: str = "openrouter/auto"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: float = 60.0
    app_name: str = "chat-companion-dev"
    app_url: str = "https://github.com/example/chat-companion"
    short_term_limit: int = 24
    memory_store_path: Path = Path("var/memory_store.json")

    @property
    def headers(self) -> dict[str, str]:
        """Default HTTP headers required by OpenRouter."""

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }
        return headers


def load_settings(*, require_api_key: bool = False) -> Settings:
    """Load settings from environment variables and optional overrides."""

    env = os.environ
    api_key = env.get("OPENROUTER_API_KEY", "")
    
    # Load API key from file if not set in environment
    if not api_key:
        api_key_file = Path("/Users/junma/Desktop/openrouter-api-key")
        if api_key_file.exists():
            api_key = api_key_file.read_text().strip()

    if require_api_key and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY must be set before running the chatbot.")

    model = env.get("OPENROUTER_MODEL", "openrouter/auto")
    base_url = env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    timeout = float(env.get("OPENROUTER_TIMEOUT", "60"))
    app_name = env.get("CHAT_COMPANION_APP_NAME", "chat-companion-dev")
    app_url = env.get("CHAT_COMPANION_APP_URL", "https://github.com/example/chat-companion")
    short_term_limit = int(env.get("CHAT_COMPANION_SHORT_TERM_LIMIT", "24"))
    memory_path = Path(env.get("CHAT_COMPANION_MEMORY_PATH", "var/memory_store.json"))

    return Settings(
        openrouter_api_key=api_key,
        openrouter_model=model,
        openrouter_base_url=base_url,
        openrouter_timeout=timeout,
        app_name=app_name,
        app_url=app_url,
        short_term_limit=short_term_limit,
        memory_store_path=memory_path,
    )
