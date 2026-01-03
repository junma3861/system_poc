import pytest

from chat_companion.config import load_settings
from chat_companion.llm.openrouter import OpenRouterClient


@pytest.fixture
def real_settings():
    """Fixture providing real settings with API key from file."""
    return load_settings(require_api_key=True)


def test_openrouter_client_real_call(real_settings) -> None:
    """Test that OpenRouterClient can make a real API call."""

    client = OpenRouterClient(real_settings)

    try:
        result = client.complete(
            system_prompt="You are a helpful assistant. Be concise.",
            user_prompt="Say 'Hello' in one word.",
        )

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
    finally:
        client.close()
