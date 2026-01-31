import os
import json
import logging
from google import genai
from google.genai import types
from app.models.staging import StagingEntry, DocumentType, ProcessingStatus
from app.database import SessionLocal
from uuid import UUID

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY is not set!")
            raise ValueError("GEMINI_API_KEY is missing")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash" 

    def analyze_document(self, staging_id: UUID):
        session = SessionLocal()
        try:
            entry = session.query(StagingEntry).filter(StagingEntry.id == staging_id).first()
            if not entry:
                logger.error(f"StagingEntry {staging_id} not found.")
                return

            if not entry.media_url or not os.path.exists(entry.media_url):
                logger.error(f"Media file missing for {staging_id}: {entry.media_url}")
                entry.status = ProcessingStatus.REJECTED
                entry.manager_notes = "System Error: File not found."
                session.commit()
                return

            logger.info(f"Processing document {staging_id} with Gemini Vision...")

            # Prepare the prompt
            prompt = """
            Analyze this document image. 
            1. Identify the document type (options: INVOICE, ORDER_FORM, LR, TRAVEL_TICKET, PAYMENT_RECEIPT). 
            2. Extract all visible data into a strict JSON format.
            
            JSON Structure:
            {
                "document_type": "INVOICE",
                "extracted_data": {
                    "date": "YYYY-MM-DD",
                    "total_amount": 123.45,
                    "vendor_name": "Example Corp",
                    "items": [
                        {"description": "Item 1", "quantity": 1, "price": 10.0}
                    ],
                    "other_fields": {} 
                }
            }
            Return ONLY the JSON.
            """

            # Read image
            with open(entry.media_url, "rb") as f:
                image_bytes = f.read()

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), # Assuming JPEG/PNG, logic can be refined
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            try:
                result_json = json.loads(response.text)
                
                # Update Entry
                detected_type_str = result_json.get("document_type", "UNKNOWN")
                
                # Map string to Enum if possible
                if detected_type_str in DocumentType.__members__:
                     entry.detected_type = DocumentType[detected_type_str]
                else:
                     entry.detected_type = DocumentType.UNKNOWN

                entry.ai_extracted_json = result_json.get("extracted_data", {})
                entry.status = ProcessingStatus.PENDING_REVIEW # Ready for review
                logger.info(f"AI Processing complete for {staging_id}")

            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Gemini for {staging_id}")
                entry.status = ProcessingStatus.PENDING_REVIEW # Still let manager see it, but maybe warn?
                entry.manager_notes = "AI Extraction Failed: Invalid JSON"
            
            except Exception as e:
                logger.error(f"Error processing response for {staging_id}: {e}")
                entry.status = ProcessingStatus.PENDING_REVIEW
                entry.manager_notes = f"AI Error: {str(e)}"

            session.commit()

        except Exception as main_e:
            logger.error(f"Critical error in AIProcessor for {staging_id}: {main_e}")
            
            # MOCK FALLBACK FOR DEVELOPMENT (If API key fails/expires)
            logger.warning(f"Using MOCK data for {staging_id} due to API failure.")
            entry.detected_type = DocumentType.INVOICE
            entry.ai_extracted_json = {
                "date": "2026-01-30",
                "total_amount": 1234.56,
                "vendor_name": "Mock Vendor Corp",
                "items": [
                    {"description": "Mock Item 1", "quantity": 10, "price": 100.0},
                    {"description": "Tax", "quantity": 1, "price": 234.56}
                ],
                "note": "This is MOCK data generated because Gemini API failed."
            }
            entry.status = ProcessingStatus.PENDING_REVIEW
            entry.manager_notes = f"Auto-Mocked due to error: {str(main_e)}"
            session.commit()
        finally:
            session.close()

# Singleton instance
ai_processor = AIProcessor()

def process_document_task(staging_id: UUID):
    """Wrapper function for BackgroundTasks"""
    ai_processor.analyze_document(staging_id)
