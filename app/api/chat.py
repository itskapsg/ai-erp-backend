"""
Chat API for Voice-First Assistant
Handles natural language processing and voice command interpretation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from app.database import get_db
from app.api.auth import get_current_user
from app.models.core import User
from app.services.chat_service import chat_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Voice or text message to process",
        example="show me pending approvals"
    )

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str = Field(description="Natural language response")
    data: List[Dict[str, Any]] = Field(default=[], description="Structured data for frontend")
    count: int = Field(default=0, description="Number of items in data")
    intent: Optional[str] = Field(default=None, description="Detected user intent")
    user_role: Optional[str] = Field(default=None, description="User's role for context")
    error: Optional[str] = Field(default=None, description="Error code if any")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

@router.post("/", response_model=ChatResponse)
async def process_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Process voice or text chat messages
    
    This endpoint receives transcribed text from frontend voice recognition
    and processes it using natural language understanding.
    
    Security Features:
    - JWT authentication required
    - Role-based data filtering
    - Input validation and sanitization
    - Rate limiting ready (can be added via middleware)
    """
    try:
        # Log the interaction for monitoring
        logger.info(f"Chat request from user {current_user.username} (role: {current_user.role.value}): '{request.message}'")
        
        # Process the message through chat service
        result = chat_service.process_message(
            db=db,
            user=current_user,
            text=request.message
        )
        
        # Add user context to response
        result["user_role"] = current_user.role.value
        result["metadata"] = {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "timestamp": "2026-01-23T19:35:00Z"  # In production, use datetime.utcnow()
        }
        
        # Log successful processing
        logger.info(f"Chat response for {current_user.username}: intent={result.get('intent', 'unknown')}, count={result.get('count', 0)}")
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat processing error for user {current_user.username}: {str(e)}")
        
        # Return user-friendly error without exposing internal details
        return ChatResponse(
            response="I'm having trouble processing your request right now. Please try again.",
            data=[],
            count=0,
            error="processing_error",
            user_role=current_user.role.value
        )

@router.get("/help", response_model=ChatResponse)
async def get_chat_help(
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Get help information for chat commands
    Returns role-specific guidance
    """
    try:
        result = chat_service.handle_help_intent(current_user)
        result["user_role"] = current_user.role.value
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting chat help for user {current_user.username}: {str(e)}")
        
        return ChatResponse(
            response="Help information is temporarily unavailable.",
            data=[],
            count=0,
            error="help_error",
            user_role=current_user.role.value
        )

@router.get("/intents")
async def get_available_intents(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available intents and example phrases for development/debugging
    """
    intents = {
        "approvals": {
            "description": "Check pending approvals",
            "examples": [
                "show pending approvals",
                "what needs approval",
                "approval status",
                "pending partners"
            ],
            "available_to": ["all roles"]
        },
        "list_partners": {
            "description": "List recent partners",
            "examples": [
                "list partners",
                "show customers",
                "display suppliers",
                "recent partners"
            ],
            "available_to": ["all roles"]
        },
        "help": {
            "description": "Get help and available commands",
            "examples": [
                "help",
                "what can you do",
                "available commands"
            ],
            "available_to": ["all roles"]
        }
    }
    
    return {
        "intents": intents,
        "user_role": current_user.role.value,
        "total_intents": len(intents)
    }