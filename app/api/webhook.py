from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.staging import StagingEntry, DocumentType, ProcessingStatus
from app.schemas.staging import StagingEntryCreate, StagingEntryResponse
import shutil
import os
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "/root/workspace/uploads"

from app.services.ai_processor import process_document_task

# Stub removed, importing actual task


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    
    # Extract fields (support both generic and Twilio casing)
    raw_text = form_data.get('body') or form_data.get('Body')
    source_phone = form_data.get('from_number') or form_data.get('From')
    media_url_external = form_data.get('MediaUrl0')
    file = form_data.get('file') # UploadFile object if present
    
    logger.info(f"Received WhatsApp message from: {source_phone}")

    media_local_path = None

    # Handle Media
    if file and isinstance(file, UploadFile):
        # Direct File Upload (Legacy/Testing)
        file_ext = os.path.splitext(file.filename)[1] or ".jpg"
        filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        try:
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            media_local_path = filepath
            logger.info(f"File saved to: {media_local_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")
            
    elif media_url_external:
        # Twilio Media URL
        try:
            filename = f"{uuid.uuid4()}.jpg" # Default to jpg, can assume from headers
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(media_url_external)
                if resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    media_local_path = filepath
                    logger.info(f"Downloaded Twilio media to: {media_local_path}")
                else:
                    logger.error(f"Failed to download media: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error downloading Twilio media: {e}")
            # Continue without media? Or fail? Let's continue with text only.

    # Create Staging Entry
    db_entry = StagingEntry(
        source_phone=source_phone,
        media_url=media_local_path,
        raw_text=raw_text,
        status=ProcessingStatus.PENDING_REVIEW,
        detected_type=DocumentType.UNKNOWN 
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    background_tasks.add_task(process_document_task, db_entry.id)

    # Return TwiML (Empty Response tells Twilio we received it but have no immediate reply)
    return Response(content="<Response></Response>", media_type="application/xml")

@router.get("/staging/pending", response_model=list[StagingEntryResponse])
def get_pending_entries(db: Session = Depends(get_db)):
    """Fetch all entries with status PENDING_REVIEW"""
    return db.query(StagingEntry).filter(StagingEntry.status == ProcessingStatus.PENDING_REVIEW).order_by(StagingEntry.created_at.desc()).all()
@router.put("/staging/{entry_id}")
def update_staging_entry(entry_id: uuid.UUID, update_data: dict, db: Session = Depends(get_db)):
    """Update status or JSON data of a staging entry"""
    entry = db.query(StagingEntry).filter(StagingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if "status" in update_data:
        entry.status = update_data["status"]
    
    if "ai_extracted_json" in update_data:
        entry.ai_extracted_json = update_data["ai_extracted_json"]
        
    if "manager_notes" in update_data:
        entry.manager_notes = update_data["manager_notes"]

    db.commit()
    return {"status": "updated"}
