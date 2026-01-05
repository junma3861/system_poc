## Plan: Healthcare Chatbot System

Build a healthcare-focused chatbot with a UI, using OpenRouter for LLM calls, persistent conversation history, and strict domain filtering for healthcare questions.

### Steps
1. Set up backend service to handle chat requests and responses.
2. Integrate OpenRouter API for LLM calls in the backend.
3. Implement conversation history storage (in-memory, file, or database).
4. Add healthcare domain filtering to only answer relevant questions.
5. Develop a frontend UI for user interaction with the chatbot.
6. Connect frontend to backend via API endpoints for chat and history.

### Further Considerations
1. Should conversation history be persistent (database) or session-based (in-memory)?
2. What tech stack for the UI? (React, Vue, plain HTML/JS, etc.)
3. How strict should healthcare filtering be? (keyword match, classifier, etc.)