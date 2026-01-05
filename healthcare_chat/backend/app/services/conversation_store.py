import uuid
from typing import Dict, List, Optional
from datetime import datetime


class ConversationStore:
    """In-memory storage for conversation history."""
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict]] = {}
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = []
        return conversation_id
    
    def get_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history by ID."""
        return self._conversations.get(conversation_id, [])
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        self._conversations[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation. Returns True if successful."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs."""
        return list(self._conversations.keys())
