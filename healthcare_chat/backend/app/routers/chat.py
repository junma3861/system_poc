from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.conversation_store import ConversationStore
from app.services.healthcare_filter import HealthcareFilter

router = APIRouter()

# Initialize services
llm_service = LLMService()
conversation_store = ConversationStore()
healthcare_filter = HealthcareFilter()


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    is_healthcare_related: bool


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages and return AI responses."""
    
    # Check if the message is healthcare-related
    is_healthcare = healthcare_filter.is_healthcare_related(request.message)
    
    if not is_healthcare:
        return ChatResponse(
            response="I'm sorry, but I can only assist with healthcare-related questions. Please ask me about health, medical conditions, symptoms, treatments, wellness, or other healthcare topics.",
            conversation_id=request.conversation_id or conversation_store.create_conversation(),
            is_healthcare_related=False
        )
    
    # Get or create conversation
    conversation_id = request.conversation_id or conversation_store.create_conversation()
    
    # Get conversation history
    history = conversation_store.get_history(conversation_id)
    
    # Add user message to history
    conversation_store.add_message(conversation_id, "user", request.message)
    
    try:
        # Get response from LLM
        response = await llm_service.get_response(request.message, history)
        
        # Add assistant response to history
        conversation_store.add_message(conversation_id, "assistant", response)
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            is_healthcare_related=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history by ID."""
    history = conversation_store.get_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": history}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = conversation_store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}
