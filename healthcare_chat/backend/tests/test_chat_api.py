import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


class TestChatAPI:
    """Tests for the Chat API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct status."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "Healthcare" in data["message"]
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_chat_non_healthcare_message(self, client):
        """Test that non-healthcare messages are rejected."""
        response = client.post(
            "/api/chat",
            json={"message": "What is the weather today?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_healthcare_related"] is False
        assert "healthcare-related" in data["response"].lower()
    
    def test_chat_healthcare_message(self, client):
        """Test that healthcare messages get LLM response."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = "Headaches can be caused by various factors..."
            
            response = client.post(
                "/api/chat",
                json={"message": "I have a headache, what should I do?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_healthcare_related"] is True
            assert "conversation_id" in data
            assert len(data["response"]) > 0
    
    def test_chat_with_conversation_id(self, client):
        """Test continuing an existing conversation."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = "Test response"
            
            # First message
            response1 = client.post(
                "/api/chat",
                json={"message": "What are symptoms of flu?"}
            )
            conversation_id = response1.json()["conversation_id"]
            
            # Second message with same conversation_id
            response2 = client.post(
                "/api/chat",
                json={
                    "message": "How can I treat it?",
                    "conversation_id": conversation_id
                }
            )
            
            assert response2.status_code == 200
            assert response2.json()["conversation_id"] == conversation_id
    
    def test_chat_llm_error(self, client):
        """Test handling of LLM service errors."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.side_effect = Exception("API Error")
            
            response = client.post(
                "/api/chat",
                json={"message": "What causes fever?"}
            )
            
            assert response.status_code == 500
    
    def test_get_conversation(self, client):
        """Test retrieving conversation history."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = "Response about headaches"
            
            # Create a conversation
            response = client.post(
                "/api/chat",
                json={"message": "I have a headache"}
            )
            conversation_id = response.json()["conversation_id"]
            
            # Get the conversation
            response = client.get(f"/api/conversations/{conversation_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == conversation_id
            assert len(data["messages"]) == 2  # user + assistant
    
    def test_get_nonexistent_conversation(self, client):
        """Test getting a non-existent conversation returns 404."""
        response = client.get("/api/conversations/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_delete_conversation(self, client):
        """Test deleting a conversation."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = "Test response"
            
            # Create a conversation
            response = client.post(
                "/api/chat",
                json={"message": "What is diabetes?"}
            )
            conversation_id = response.json()["conversation_id"]
            
            # Delete it
            response = client.delete(f"/api/conversations/{conversation_id}")
            
            assert response.status_code == 200
            assert "deleted" in response.json()["message"].lower()
            
            # Verify it's gone
            response = client.get(f"/api/conversations/{conversation_id}")
            assert response.status_code == 404
    
    def test_delete_nonexistent_conversation(self, client):
        """Test deleting a non-existent conversation returns 404."""
        response = client.delete("/api/conversations/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_chat_empty_message(self, client):
        """Test handling of empty message."""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )
        
        # Empty message should be treated as non-healthcare
        assert response.status_code == 200
        assert response.json()["is_healthcare_related"] is False
    
    def test_conversation_history_order(self, client):
        """Test that conversation history maintains correct order."""
        with patch('app.routers.chat.llm_service.get_response', new_callable=AsyncMock) as mock_get_response:
            mock_get_response.side_effect = [
                "First response about symptoms",
                "Second response about treatment"
            ]
            
            # First message
            response1 = client.post(
                "/api/chat",
                json={"message": "What are the symptoms of a cold?"}
            )
            conversation_id = response1.json()["conversation_id"]
            
            # Second message - include healthcare keyword
            client.post(
                "/api/chat",
                json={
                    "message": "What treatment options are available?",
                    "conversation_id": conversation_id
                }
            )
            
            # Get conversation
            response = client.get(f"/api/conversations/{conversation_id}")
            messages = response.json()["messages"]
            
            assert len(messages) == 4  # 2 user + 2 assistant
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"
            assert messages[2]["role"] == "user"
            assert messages[3]["role"] == "assistant"
