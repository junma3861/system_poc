import os
import httpx
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Service for interacting with OpenRouter LLM API."""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        
        self.system_prompt = """You are a helpful healthcare assistant. Your role is to:
1. Provide accurate, evidence-based health information
2. Help users understand medical conditions, symptoms, and treatments
3. Offer general wellness and preventive health advice
4. Always recommend consulting a healthcare professional for specific medical advice
5. Never diagnose conditions or prescribe treatments
6. Be empathetic and supportive in your responses

Important disclaimers to include when appropriate:
- This information is for educational purposes only
- Always consult a qualified healthcare provider for medical advice
- In case of emergency, call emergency services immediately"""

    def _load_api_key(self) -> str:
        """Load API key from file or environment variable."""
        # First try to load from file
        api_key_file = Path("/Users/junma/Desktop/openrouter-api-key")
        if api_key_file.exists():
            return api_key_file.read_text().strip()
        
        # Fall back to environment variable
        return os.getenv("OPENROUTER_API_KEY")

    async def get_response(self, message: str, history: List[Dict] = None) -> str:
        """Get a response from the LLM."""
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in file or environment variable")
        
        # Build messages array
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Make request to OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Healthcare Chatbot"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
