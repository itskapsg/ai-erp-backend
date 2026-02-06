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

# --- NEW: Hybrid Chat/Upload Endpoint ---
from fastapi import UploadFile, File, Form, BackgroundTasks
from app.models.staging import StagingEntry, DocumentType, ProcessingStatus
import shutil
import os
import uuid
from app.services.ai_processor import process_document_task

UPLOAD_DIR = "/root/workspace/uploads"

@router.post("/message", response_model=ChatResponse)
async def post_chat_message(
    background_tasks: BackgroundTasks,
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handle generic chat messages with optional file attachments.
    - If file: Uploads and processes via AI (creates StagingEntry).
    - If text only: Uses ChatService/Gemini to reply.
    """
    try:
        response_text = ""
        data = []
        
        # 1. Handle File Upload
        if file:
            # Save File
            file_ext = os.path.splitext(file.filename)[1] or ".jpg"
            filename = f"{uuid.uuid4()}{file_ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create Staging Entry
            db_entry = StagingEntry(
                source_phone="web_upload", # Marker for internal upload
                media_url=filepath,
                raw_text=message or "Uploaded via Employee Chat",
                status=ProcessingStatus.PENDING_REVIEW,
                detected_type=DocumentType.UNKNOWN,
                manager_notes=f"Uploaded by {current_user.username}"
            )
            db.add(db_entry)
            db.commit()
            db.refresh(db_entry)
            
            # Trigger Processing
            background_tasks.add_task(process_document_task, db_entry.id)
            
            response_text = f"I've received your document '{file.filename}'. It is being processed by Gemini (ID: {db_entry.id}). You can view it in the Review Inbox shortly."
            data.append({"type": "file_upload", "id": str(db_entry.id), "status": "processing"})
        
        # 2. Handle Text (if no file, or as accompaniment)
        elif message:
            # Reuse existing chat service
            result = chat_service.process_message(db=db, user=current_user, text=message)
            response_text = result.get("response", "I heard you.")
            data = result.get("data", [])
        
        else:
             response_text = "Please provide a message or a file."

        return ChatResponse(
            response=response_text,
            data=data,
            user_role=current_user.role.value
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(response=f"Error: {str(e)}", error="processing_failed")