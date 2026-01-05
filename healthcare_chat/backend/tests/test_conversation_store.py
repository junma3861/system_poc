import pytest
from app.services.conversation_store import ConversationStore


class TestConversationStore:
    """Tests for the ConversationStore service."""
    
    @pytest.fixture
    def store(self):
        return ConversationStore()
    
    def test_create_conversation(self, store):
        """Test creating a new conversation."""
        conversation_id = store.create_conversation()
        
        assert conversation_id is not None
        assert isinstance(conversation_id, str)
        assert len(conversation_id) > 0
    
    def test_create_multiple_conversations(self, store):
        """Test creating multiple conversations returns unique IDs."""
        id1 = store.create_conversation()
        id2 = store.create_conversation()
        id3 = store.create_conversation()
        
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
    
    def test_get_empty_history(self, store):
        """Test getting history for a new conversation."""
        conversation_id = store.create_conversation()
        history = store.get_history(conversation_id)
        
        assert history == []
    
    def test_get_history_nonexistent(self, store):
        """Test getting history for non-existent conversation."""
        history = store.get_history("nonexistent-id")
        
        assert history == []
    
    def test_add_message(self, store):
        """Test adding a message to conversation."""
        conversation_id = store.create_conversation()
        
        store.add_message(conversation_id, "user", "Hello")
        history = store.get_history(conversation_id)
        
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert "timestamp" in history[0]
    
    def test_add_multiple_messages(self, store):
        """Test adding multiple messages maintains order."""
        conversation_id = store.create_conversation()
        
        store.add_message(conversation_id, "user", "Hello")
        store.add_message(conversation_id, "assistant", "Hi there!")
        store.add_message(conversation_id, "user", "How are you?")
        
        history = store.get_history(conversation_id)
        
        assert len(history) == 3
        assert history[0]["content"] == "Hello"
        assert history[1]["content"] == "Hi there!"
        assert history[2]["content"] == "How are you?"
    
    def test_add_message_to_nonexistent_conversation(self, store):
        """Test adding message creates conversation if not exists."""
        store.add_message("new-id", "user", "Hello")
        history = store.get_history("new-id")
        
        assert len(history) == 1
        assert history[0]["content"] == "Hello"
    
    def test_delete_conversation(self, store):
        """Test deleting a conversation."""
        conversation_id = store.create_conversation()
        store.add_message(conversation_id, "user", "Hello")
        
        result = store.delete_conversation(conversation_id)
        
        assert result is True
        assert store.get_history(conversation_id) == []
    
    def test_delete_nonexistent_conversation(self, store):
        """Test deleting non-existent conversation returns False."""
        result = store.delete_conversation("nonexistent-id")
        
        assert result is False
    
    def test_list_conversations(self, store):
        """Test listing all conversations."""
        id1 = store.create_conversation()
        id2 = store.create_conversation()
        
        conversations = store.list_conversations()
        
        assert id1 in conversations
        assert id2 in conversations
        assert len(conversations) == 2
    
    def test_conversations_are_isolated(self, store):
        """Test that conversations don't interfere with each other."""
        id1 = store.create_conversation()
        id2 = store.create_conversation()
        
        store.add_message(id1, "user", "Message in conversation 1")
        store.add_message(id2, "user", "Message in conversation 2")
        
        history1 = store.get_history(id1)
        history2 = store.get_history(id2)
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]["content"] == "Message in conversation 1"
        assert history2[0]["content"] == "Message in conversation 2"
    
    def test_message_timestamp_format(self, store):
        """Test that message timestamps are in ISO format."""
        conversation_id = store.create_conversation()
        store.add_message(conversation_id, "user", "Hello")
        
        history = store.get_history(conversation_id)
        timestamp = history[0]["timestamp"]
        
        # Should be ISO format string
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format contains 'T' separator
