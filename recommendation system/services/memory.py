"""
Memory management for chatbot conversations.
Handles both short-term (session) and long-term (database) memory.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import redis
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


class ConversationMemory:
    """
    Manages conversation memory for the chatbot.
    
    - Short-term memory: Redis (session-based, expires after inactivity)
    - Long-term memory: MongoDB (persistent conversation history)
    """
    
    def __init__(self):
        """Initialize memory management with Redis and MongoDB."""
        # Redis for short-term memory (session cache)
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
            print("✓ Redis connected for short-term memory")
        except Exception as e:
            print(f"⚠️  Redis unavailable, using in-memory fallback: {e}")
            self.redis_available = False
            self.memory_fallback = defaultdict(list)
        
        # MongoDB for long-term memory (conversation history)
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        mongo_db_name = os.getenv('MONGO_DATABASE', 'recommendation_db')
        
        try:
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_db = self.mongo_client[mongo_db_name]
            self.conversations_collection = self.mongo_db['conversation_history']
            
            # Create indexes for efficient queries
            self.conversations_collection.create_index([("user_id", 1), ("timestamp", -1)])
            self.conversations_collection.create_index([("session_id", 1)])
            
            self.mongo_available = True
            print("✓ MongoDB connected for long-term memory")
        except Exception as e:
            print(f"⚠️  MongoDB unavailable for conversation history: {e}")
            self.mongo_available = False
        
        # Configuration
        self.session_ttl = int(os.getenv('SESSION_TTL', 3600))  # 1 hour default
        self.max_context_messages = int(os.getenv('MAX_CONTEXT_MESSAGES', 10))
    
    def get_session_key(self, user_id: Optional[int], session_id: str) -> str:
        """Generate Redis key for session."""
        return f"chat_session:{user_id or 'anonymous'}:{session_id}"
    
    def add_message(
        self,
        user_id: Optional[int],
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to conversation memory.
        
        Args:
            user_id: User ID (None for anonymous)
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata (query_analysis, products, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Short-term memory (Redis or fallback)
        self._add_to_short_term_memory(user_id, session_id, message)
        
        # Long-term memory (MongoDB)
        if self.mongo_available and user_id:
            self._add_to_long_term_memory(user_id, session_id, message)
    
    def _add_to_short_term_memory(
        self,
        user_id: Optional[int],
        session_id: str,
        message: Dict
    ) -> None:
        """Add message to Redis or in-memory fallback."""
        session_key = self.get_session_key(user_id, session_id)
        
        if self.redis_available:
            try:
                # Store as JSON list
                messages_json = self.redis_client.get(session_key)
                messages = json.loads(messages_json) if messages_json else []
                messages.append(message)
                
                # Keep only recent messages
                if len(messages) > self.max_context_messages:
                    messages = messages[-self.max_context_messages:]
                
                # Store with TTL
                self.redis_client.setex(
                    session_key,
                    self.session_ttl,
                    json.dumps(messages)
                )
            except Exception as e:
                print(f"Redis error: {e}")
                self.memory_fallback[session_key].append(message)
        else:
            # In-memory fallback
            self.memory_fallback[session_key].append(message)
            if len(self.memory_fallback[session_key]) > self.max_context_messages:
                self.memory_fallback[session_key] = self.memory_fallback[session_key][-self.max_context_messages:]
    
    def _add_to_long_term_memory(
        self,
        user_id: int,
        session_id: str,
        message: Dict
    ) -> None:
        """Store message in MongoDB for long-term history."""
        try:
            conversation_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "role": message["role"],
                "content": message["content"],
                "timestamp": datetime.utcnow(),
                "metadata": message["metadata"]
            }
            self.conversations_collection.insert_one(conversation_doc)
        except Exception as e:
            print(f"MongoDB error: {e}")
    
    def get_conversation_context(
        self,
        user_id: Optional[int],
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict]:
        """
        Get recent conversation context for the session.
        
        Args:
            user_id: User ID
            session_id: Session identifier
            max_messages: Max messages to return (default: self.max_context_messages)
            
        Returns:
            List of recent messages
        """
        max_messages = max_messages or self.max_context_messages
        session_key = self.get_session_key(user_id, session_id)
        
        if self.redis_available:
            try:
                messages_json = self.redis_client.get(session_key)
                if messages_json:
                    messages = json.loads(messages_json)
                    return messages[-max_messages:] if messages else []
            except Exception as e:
                print(f"Redis error: {e}")
        
        # Fallback to in-memory
        return self.memory_fallback.get(session_key, [])[-max_messages:]
    
    def get_conversation_history(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get user's conversation history from MongoDB.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of messages
            
        Returns:
            List of historical conversations
        """
        if not self.mongo_available:
            return []
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = self.conversations_collection.find(
                {
                    "user_id": user_id,
                    "timestamp": {"$gte": cutoff_date}
                }
            ).sort("timestamp", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"MongoDB error: {e}")
            return []
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """
        Extract user preferences from conversation history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user preferences (categories, brands, price ranges)
        """
        if not self.mongo_available:
            return {}
        
        try:
            # Get recent conversations
            history = self.get_conversation_history(user_id, days=90, limit=50)
            
            preferences = {
                "categories": [],
                "brands": [],
                "price_ranges": [],
                "keywords": []
            }
            
            # Extract preferences from metadata
            for conv in history:
                metadata = conv.get("metadata", {})
                query_analysis = metadata.get("query_analysis", {})
                
                if query_analysis.get("categories"):
                    preferences["categories"].extend(query_analysis["categories"])
                
                if query_analysis.get("brands"):
                    preferences["brands"].extend(query_analysis["brands"])
                
                if query_analysis.get("price_range"):
                    preferences["price_ranges"].append(query_analysis["price_range"])
                
                if query_analysis.get("keywords"):
                    preferences["keywords"].extend(query_analysis["keywords"])
            
            # Count frequencies
            from collections import Counter
            preferences["categories"] = [cat for cat, _ in Counter(preferences["categories"]).most_common(5)]
            preferences["brands"] = [brand for brand, _ in Counter(preferences["brands"]).most_common(5)]
            preferences["keywords"] = [kw for kw, _ in Counter(preferences["keywords"]).most_common(10)]
            
            return preferences
        except Exception as e:
            print(f"Error extracting preferences: {e}")
            return {}
    
    def clear_session(self, user_id: Optional[int], session_id: str) -> None:
        """Clear session memory."""
        session_key = self.get_session_key(user_id, session_id)
        
        if self.redis_available:
            try:
                self.redis_client.delete(session_key)
            except Exception as e:
                print(f"Redis error: {e}")
        
        if session_key in self.memory_fallback:
            del self.memory_fallback[session_key]
    
    def get_session_summary(self, user_id: Optional[int], session_id: str) -> Dict:
        """Get summary of current session."""
        context = self.get_conversation_context(user_id, session_id)
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "message_count": len(context),
            "started_at": context[0]["timestamp"] if context else None,
            "last_activity": context[-1]["timestamp"] if context else None,
            "messages": context
        }
    
    def format_context_for_llm(
        self,
        user_id: Optional[int],
        session_id: str,
        max_messages: int = 5
    ) -> List[Dict]:
        """
        Format conversation context for LLM input.
        
        Args:
            user_id: User ID
            session_id: Session identifier
            max_messages: Number of recent messages to include
            
        Returns:
            List of messages in OpenAI format [{"role": "user/assistant", "content": "..."}]
        """
        context = self.get_conversation_context(user_id, session_id, max_messages)
        
        # Format for OpenAI
        formatted = []
        for msg in context:
            formatted.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return formatted


# Global memory instance
conversation_memory = ConversationMemory()
