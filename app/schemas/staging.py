from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "INVOICE"
    ORDER_FORM = "ORDER_FORM"
    LR = "LR"
    TRAVEL_TICKET = "TRAVEL_TICKET"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"
    UNKNOWN = "UNKNOWN"

class ProcessingStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class StagingEntryBase(BaseModel):
    source_phone: Optional[str] = None
    media_url: Optional[str] = None
    raw_text: Optional[str] = None
    detected_type: DocumentType = DocumentType.UNKNOWN
    status: ProcessingStatus = ProcessingStatus.PENDING_REVIEW
    manager_notes: Optional[str] = None
    ai_extracted_json: Optional[Dict[str, Any]] = None

class StagingEntryCreate(StagingEntryBase):
    pass

class StagingEntryResponse(StagingEntryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
