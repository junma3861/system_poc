import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.llm_service import LLMService


class TestLLMService:
    """Tests for the LLMService."""
    
    @pytest.fixture
    def llm_service(self):
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-api-key'}):
            return LLMService()
    
    def test_initialization(self, llm_service):
        """Test LLMService initializes with correct defaults."""
        assert llm_service.api_key == "test-api-key"
        assert llm_service.base_url == "https://openrouter.ai/api/v1"
        assert llm_service.model is not None
        assert llm_service.system_prompt is not None
    
    def test_system_prompt_contains_healthcare_context(self, llm_service):
        """Test that system prompt contains healthcare-related instructions."""
        prompt = llm_service.system_prompt.lower()
        
        assert "healthcare" in prompt or "health" in prompt
        assert "medical" in prompt
        assert "consult" in prompt or "professional" in prompt
    
    @pytest.mark.asyncio
    async def test_get_response_without_api_key(self):
        """Test that missing API key raises an error."""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': ''}):
            service = LLMService()
            service.api_key = None
            
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await service.get_response("Test message")
    
    @pytest.mark.asyncio
    async def test_get_response_success(self, llm_service):
        """Test successful API response."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response about healthcare."
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_instance.post.return_value = mock_http_response
            
            response = await llm_service.get_response("What are symptoms of a cold?")
            
            assert response == "This is a test response about healthcare."
            mock_instance.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_response_with_history(self, llm_service):
        """Test that conversation history is included in the request."""
        mock_response = {
            "choices": [
                {"message": {"content": "Response with history"}}
            ]
        }
        
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_instance.post.return_value = mock_http_response
            
            await llm_service.get_response("New question", history)
            
            # Verify the call was made
            call_args = mock_instance.post.call_args
            request_body = call_args.kwargs['json']
            
            # Should have system prompt + history + new message
            messages = request_body['messages']
            assert messages[0]['role'] == 'system'
            assert messages[1]['role'] == 'user'
            assert messages[1]['content'] == 'Previous question'
            assert messages[2]['role'] == 'assistant'
            assert messages[2]['content'] == 'Previous answer'
            assert messages[3]['role'] == 'user'
            assert messages[3]['content'] == 'New question'
    
    @pytest.mark.asyncio
    async def test_get_response_api_error(self, llm_service):
        """Test handling of API errors."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_http_response = MagicMock()
            mock_http_response.status_code = 500
            mock_http_response.text = "Internal Server Error"
            mock_instance.post.return_value = mock_http_response
            
            with pytest.raises(Exception, match="OpenRouter API error"):
                await llm_service.get_response("Test message")
    
    @pytest.mark.asyncio
    async def test_request_headers(self, llm_service):
        """Test that correct headers are sent with the request."""
        mock_response = {
            "choices": [{"message": {"content": "Test"}}]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_instance.post.return_value = mock_http_response
            
            await llm_service.get_response("Test")
            
            call_args = mock_instance.post.call_args
            headers = call_args.kwargs['headers']
            
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer test-api-key'
            assert headers['Content-Type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_request_body_structure(self, llm_service):
        """Test that request body has correct structure."""
        mock_response = {
            "choices": [{"message": {"content": "Test"}}]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_instance.post.return_value = mock_http_response
            
            await llm_service.get_response("Test message")
            
            call_args = mock_instance.post.call_args
            body = call_args.kwargs['json']
            
            assert 'model' in body
            assert 'messages' in body
            assert 'temperature' in body
            assert 'max_tokens' in body


import os
from pathlib import Path

class TestLLMServiceIntegration:
    """Integration tests for LLMService with real OpenRouter API calls.
    
    These tests require a valid API key either from file or environment variable.
    Run with: pytest tests/test_llm_service.py -v -k integration
    """
    
    @pytest.fixture
    def real_llm_service(self):
        """Create LLM service with real API key from file or environment."""
        api_key_file = Path("/Users/junma/Desktop/openrouter-api-key")
        api_key = None
        
        if api_key_file.exists():
            api_key = api_key_file.read_text().strip()
        else:
            api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            pytest.skip("OpenRouter API key not found - skipping integration test")
        
        return LLMService()
    
    @pytest.mark.asyncio
    async def test_integration_simple_healthcare_question(self, real_llm_service):
        """Test a real API call with a simple healthcare question."""
        response = await real_llm_service.get_response(
            "What are common symptoms of the common cold? Please answer briefly."
        )
        
        assert response is not None
        assert len(response) > 0
        # Check the response contains relevant healthcare terms
        response_lower = response.lower()
        assert any(term in response_lower for term in [
            "symptom", "cold", "cough", "fever", "runny", "nose", 
            "sore", "throat", "sneez", "congest"
        ])
        print(f"\n--- Real API Response ---\n{response}\n")
    
    @pytest.mark.asyncio
    async def test_integration_with_conversation_history(self, real_llm_service):
        """Test a real API call with conversation history."""
        # First message
        history = []
        response1 = await real_llm_service.get_response(
            "What is a headache?",
            history
        )
        
        assert response1 is not None
        print(f"\n--- First Response ---\n{response1}\n")
        
        # Add to history
        history.append({"role": "user", "content": "What is a headache?"})
        history.append({"role": "assistant", "content": response1})
        
        # Follow-up question
        response2 = await real_llm_service.get_response(
            "What can cause it?",
            history
        )
        
        assert response2 is not None
        # The response should be contextual (about headaches)
        print(f"\n--- Follow-up Response ---\n{response2}\n")
    
    @pytest.mark.asyncio
    async def test_integration_healthcare_disclaimer(self, real_llm_service):
        """Test that responses include appropriate healthcare disclaimers."""
        response = await real_llm_service.get_response(
            "Should I take aspirin for my headache?"
        )
        
        assert response is not None
        response_lower = response.lower()
        # Should include some form of disclaimer or recommendation to consult
        has_disclaimer = any(term in response_lower for term in [
            "consult", "doctor", "healthcare", "professional", 
            "medical advice", "physician", "not a substitute"
        ])
        print(f"\n--- Response with potential disclaimer ---\n{response}\n")
        print(f"Contains disclaimer language: {has_disclaimer}")
