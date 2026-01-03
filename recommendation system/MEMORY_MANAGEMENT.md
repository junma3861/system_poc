# Memory Management Documentation

## Overview

The chatbot system now includes comprehensive memory management with both **short-term (session)** and **long-term (persistent)** memory capabilities. This enables the chatbot to maintain conversation context and learn from user interactions over time.

## Architecture

### Two-Tier Memory System

1. **Short-Term Memory (Redis)**
   - Stores active conversation sessions
   - Fast, in-memory storage for real-time access
   - Automatic expiration after inactivity
   - Falls back to in-memory dict if Redis unavailable

2. **Long-Term Memory (MongoDB)**
   - Persistent storage of all conversations
   - Enables historical analysis and preference extraction
   - Indexed for efficient querying
   - Stores conversation metadata and context

## Database Setup

### Redis (Short-Term Memory)

Redis stores session-based conversations with automatic TTL (Time To Live).

**Installation:**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

**Configuration (.env):**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
SESSION_TTL=3600  # 1 hour in seconds
MAX_CONTEXT_MESSAGES=10
```

### MongoDB (Long-Term Memory)

MongoDB stores persistent conversation history in a dedicated collection.

**Collection: `conversation_history`**

Schema:
```javascript
{
  "_id": ObjectId,
  "user_id": int,           // User identifier
  "session_id": string,     // Session identifier
  "role": string,           // "user" or "assistant"
  "content": string,        // Message content
  "timestamp": datetime,    // Message timestamp
  "metadata": {             // Additional context
    "query_analysis": {},   // Extracted intent, categories, etc.
    "products_count": int,  // Number of products returned
    "intent": string        // Query intent
  }
}
```

**Indexes:**
- `{user_id: 1, timestamp: -1}` - For efficient user history queries
- `{session_id: 1}` - For session-based retrieval

The collection is automatically created with indexes when the memory service initializes.

## API Usage

### 1. Chat with Memory

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "query": "Show me affordable laptops",
  "user_id": 1,
  "session_id": "session_12345",  // NEW: Include for memory
  "n_results": 10,
  "use_recommendations": true
}
```

The chatbot will:
- Automatically store the user message
- Load previous conversation context
- Use context to better understand the query
- Store the assistant's response
- Remember preferences for future queries

### 2. Get Session Summary

**Endpoint:** `GET /memory/session/{session_id}`

**Query Parameters:**
- `user_id` (optional): User ID

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "session_12345",
    "user_id": 1,
    "message_count": 8,
    "started_at": "2025-11-30T10:00:00",
    "last_activity": "2025-11-30T10:15:00",
    "messages": [
      {
        "role": "user",
        "content": "Show me laptops",
        "timestamp": "2025-11-30T10:00:00",
        "metadata": {}
      },
      {
        "role": "assistant",
        "content": "I found 5 laptops for you...",
        "timestamp": "2025-11-30T10:00:05",
        "metadata": {
          "products_count": 5,
          "intent": "search"
        }
      }
    ]
  }
}
```

### 3. Clear Session

**Endpoint:** `DELETE /memory/session/{session_id}`

**Query Parameters:**
- `user_id` (optional): User ID

**Response:**
```json
{
  "success": true,
  "message": "Session session_12345 cleared successfully"
}
```

### 4. Get Conversation History

**Endpoint:** `GET /memory/history/{user_id}`

**Query Parameters:**
- `days` (default: 30): Number of days to look back
- `limit` (default: 100): Maximum number of messages

**Response:**
```json
{
  "success": true,
  "user_id": 1,
  "days": 30,
  "count": 45,
  "history": [
    {
      "_id": "...",
      "user_id": 1,
      "session_id": "session_12345",
      "role": "user",
      "content": "Show me laptops",
      "timestamp": "2025-11-30T10:00:00",
      "metadata": {}
    }
  ]
}
```

### 5. Extract User Preferences

**Endpoint:** `GET /memory/preferences/{user_id}`

Analyzes conversation history to extract user preferences.

**Response:**
```json
{
  "success": true,
  "user_id": 1,
  "preferences": {
    "categories": ["electronics", "clothing", "books"],
    "brands": ["Apple", "Nike", "Samsung"],
    "price_ranges": [[0, 100], [100, 500]],
    "keywords": ["affordable", "gaming", "wireless", "premium"]
  }
}
```

## Web Interface Integration

The `chatbot_demo.html` automatically handles sessions:

```javascript
// Session ID is generated and stored in localStorage
let sessionId = localStorage.getItem('chatSessionId');
if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('chatSessionId', sessionId);
}

// Included in every chat request
body: JSON.stringify({
    query: query,
    user_id: userId,
    session_id: sessionId,  // Enables memory
    n_results: 5,
    use_recommendations: true
})
```

## Memory Features

### Conversation Context

The LLM uses recent conversation history (up to 3-10 messages) to:
- Understand references ("show me more of those")
- Maintain topic continuity
- Provide contextually relevant responses
- Remember user preferences within the session

### Preference Learning

Over time, the system learns:
- **Favorite Categories:** Most frequently searched categories
- **Brand Preferences:** Brands the user asks about
- **Price Sensitivity:** Price ranges the user typically searches
- **Search Patterns:** Common keywords and interests

### Automatic Fallback

If Redis is unavailable:
- System falls back to in-memory storage
- Session memory still works (until server restart)
- Warning logged but functionality preserved

If MongoDB is unavailable:
- Long-term storage disabled
- Sessions still work with Redis/in-memory
- Warning logged

## Configuration

### Environment Variables

```env
# Redis Configuration
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Redis server port
REDIS_DB=0                   # Redis database number

# Session Configuration
SESSION_TTL=3600             # Session expiry (seconds) - default 1 hour
MAX_CONTEXT_MESSAGES=10      # Max messages in conversation context

# MongoDB (existing)
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=recommendation_db
```

### Memory Limits

- **Session TTL:** Sessions expire after inactivity (default: 1 hour)
- **Context Window:** Up to 10 messages kept in short-term memory
- **LLM Context:** Last 3-5 messages sent to LLM
- **History Retention:** No automatic deletion (manually manage if needed)

## Testing Memory

### Test Script

```python
import requests
import uuid

API_URL = "http://localhost:8000"
session_id = str(uuid.uuid4())
user_id = 1

# 1. Start conversation
response = requests.post(f"{API_URL}/chat", json={
    "query": "Show me affordable laptops",
    "user_id": user_id,
    "session_id": session_id,
    "n_results": 5
})
print("Response 1:", response.json()['response'])

# 2. Follow-up with context
response = requests.post(f"{API_URL}/chat", json={
    "query": "Show me more expensive ones",  # Contextual query
    "user_id": user_id,
    "session_id": session_id,
    "n_results": 5
})
print("Response 2:", response.json()['response'])

# 3. Get session summary
response = requests.get(f"{API_URL}/memory/session/{session_id}?user_id={user_id}")
print("Session:", response.json()['session'])

# 4. Get user preferences
response = requests.get(f"{API_URL}/memory/preferences/{user_id}")
print("Preferences:", response.json()['preferences'])

# 5. Clear session
response = requests.delete(f"{API_URL}/memory/session/{session_id}?user_id={user_id}")
print("Cleared:", response.json()['message'])
```

## Benefits

### For Users
- **Natural Conversations:** Reference previous messages without repeating context
- **Personalized Experience:** System remembers preferences and adapts
- **Continuity:** Pick up conversations where you left off
- **Better Understanding:** LLM uses context for more accurate responses

### For Developers
- **Analytics:** Analyze conversation patterns and user behavior
- **A/B Testing:** Track which queries and responses work best
- **Debugging:** Review conversation history to understand issues
- **Optimization:** Identify common queries to improve recommendations

## Performance Considerations

### Redis Performance
- **In-Memory:** Sub-millisecond read/write latency
- **Scalability:** Handles thousands of concurrent sessions
- **Memory Usage:** ~1-2KB per session (10 messages)

### MongoDB Performance
- **Indexed Queries:** Fast user history retrieval
- **Write Performance:** Async writes don't block responses
- **Storage:** ~100-500 bytes per message

### Optimization Tips
1. **Adjust SESSION_TTL:** Shorter TTL = less memory usage
2. **Limit MAX_CONTEXT_MESSAGES:** Fewer messages = faster context loading
3. **Archive Old History:** Periodically move old conversations to cold storage
4. **Use Redis Cluster:** Scale Redis for high-traffic deployments

## Troubleshooting

### Redis Connection Issues

**Error:** "Redis unavailable, using in-memory fallback"

**Solutions:**
1. Check if Redis is running: `redis-cli ping` (should return "PONG")
2. Verify REDIS_HOST and REDIS_PORT in .env
3. Check firewall settings
4. System falls back gracefully, so not critical

### MongoDB Connection Issues

**Error:** "MongoDB unavailable for conversation history"

**Solutions:**
1. Check if MongoDB is running: `mongosh` or `mongo`
2. Verify MONGO_URI in .env
3. Ensure database exists
4. Short-term memory still works with Redis

### Missing Context

**Issue:** LLM doesn't remember previous messages

**Check:**
1. Verify session_id is sent in requests
2. Session hasn't expired (check SESSION_TTL)
3. Redis is available (check logs)
4. MAX_CONTEXT_MESSAGES isn't set too low

## Next Steps

1. **Install Redis:** `brew install redis && brew services start redis`
2. **Update .env:** Add Redis configuration variables
3. **Install Python Package:** `pip install redis`
4. **Restart Server:** `uvicorn main:app --reload`
5. **Test Memory:** Use chatbot_demo.html or test script above
6. **Monitor:** Check logs for memory system status

## Advanced Features (Future)

Potential enhancements:
- **Multi-User Sessions:** Group conversations with multiple participants
- **Context Summarization:** Compress old messages to maintain longer context
- **Semantic Search:** Find similar past conversations
- **Export History:** Download conversation history as JSON/CSV
- **Privacy Controls:** User-initiated data deletion (GDPR compliance)
