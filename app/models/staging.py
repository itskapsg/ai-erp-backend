import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.core import Base
import enum

class DocumentType(str, enum.Enum):
    INVOICE = "INVOICE"
    ORDER_FORM = "ORDER_FORM"
    LR = "LR"
    TRAVEL_TICKET = "TRAVEL_TICKET"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"
    UNKNOWN = "UNKNOWN"

class ProcessingStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class StagingEntry(Base):
    __tablename__ = "staging_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_phone = Column(String, nullable=True)
    media_url = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    
    detected_type = Column(Enum(DocumentType), default=DocumentType.UNKNOWN)
    
    # Store the massive JSON from Gemini here
    ai_extracted_json = Column(JSONB, nullable=True)
    
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING_REVIEW)
    manager_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StagingEntry {self.id} ({self.status})>"
