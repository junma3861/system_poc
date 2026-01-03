from pathlib import Path

import pytest

from chat_companion.memory import LongTermMemory, MemoryManager, ShortTermMemory


@pytest.fixture
def short_term_memory():
    """Fixture providing a ShortTermMemory instance with capacity of 2."""
    return ShortTermMemory(capacity=2)


@pytest.fixture
def sample_conversation():
    """Fixture providing a sample conversation."""
    return [
        {"role": "user", "content": "How was the day?"},
        {"role": "assistant", "content": "It went well."},
    ]


def test_short_term_capacity(short_term_memory) -> None:
    """Test that ShortTermMemory respects capacity limits."""
    short_term_memory.add("user", "hi")
    short_term_memory.add("assistant", "hello")
    short_term_memory.add("user", "again")

    history = short_term_memory.history()
    assert len(history) == 2
    assert history[0]["role"] == "assistant"


def test_long_term_persist(tmp_path, sample_conversation) -> None:
    """Test that LongTermMemory persists conversations to disk."""
    store = tmp_path / "memory.json"
    long_term = LongTermMemory(store)
    
    record = long_term.summarize_and_store("session-1", sample_conversation)

    assert store.exists()
    assert "Session recap" in record.summary

    # Test recovery from disk
    recovered = LongTermMemory(store)
    assert len(recovered.latest()) == 1


def test_memory_manager_summary(tmp_path) -> None:
    """Test that MemoryManager correctly summarizes and stores conversations."""
    store = tmp_path / "mem.json"
    manager = MemoryManager(ShortTermMemory(capacity=3), LongTermMemory(store))
    manager.record_user("hello")
    manager.record_assistant("hi there")
    summary = manager.summarize_and_store("session-test")

    assert store.exists()
    assert "hello" in summary.summary or "hi there" in summary.summary
    assert len(manager.load_recent_summaries()) == 1
