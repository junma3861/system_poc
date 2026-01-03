import pytest

from chat_companion.prompts import templates


@pytest.fixture
def sample_messages():
    """Fixture providing sample conversation messages."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]


@pytest.fixture
def prompt_library():
    """Fixture providing the default prompt library."""
    return templates.build_default_library()


def test_format_conversation_builds_transcript(sample_messages) -> None:
    """Test that format_conversation creates a proper transcript."""
    transcript = templates.format_conversation(sample_messages)
    assert "User" in transcript
    assert "Assistant" in transcript


def test_prompt_library_lookup(prompt_library) -> None:
    """Test that prompt library can lookup and render prompts."""
    prompt = prompt_library.get("response")
    rendered = prompt.render_user(conversation="test", user_input="ping")
    assert "test" in rendered
    assert "ping" in rendered
