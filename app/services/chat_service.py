"""
Chat Service for Voice-First Assistant
Processes natural language commands with intent recognition and role-based security
"""
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.core import User, UserRole
from app.models.masters import Partner
from app.models.core import WorkflowStage
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """
    Voice-First Assistant Chat Service
    Processes natural language commands with security and intent recognition
    """
    
    def __init__(self):
        # Intent patterns for natural language processing
        self.intent_patterns = {
            'approvals': [
                r'\b(pending|approval|approve|status)\b',
                r'\b(need.*approval|waiting.*approval)\b',
                r'\b(pending.*partner|partner.*pending)\b'
            ],
            'list_partners': [
                r'\b(list|show|display)\b.*\b(partner|customer|supplier)s?\b',
                r'\b(partner|customer|supplier)s?\b.*\b(list|show|display)\b',
                r'\b(all.*partner|recent.*partner)\b',
                r'\b(list.*all|show.*all|display.*all)\b'
            ],
            'help': [
                r'\b(help|what.*can|how.*use)\b',
                r'\b(command|option|available)\b'
            ]
        }
    
    def normalize_message(self, text: str) -> str:
        """
        Normalize voice input text
        - Convert to lowercase
        - Strip whitespace
        - Remove extra spaces
        """
        if not text:
            return ""
        
        # Convert to lowercase and strip
        normalized = text.lower().strip()
        
        # Remove extra whitespace (common in voice input)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common voice artifacts
        normalized = re.sub(r'\b(um|uh|er|ah)\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        logger.info(f"Normalized message: '{text}' -> '{normalized}'")
        return normalized
    
    def detect_intent(self, message: str) -> str:
        """
        Detect user intent from normalized message
        Returns: 'approvals', 'list_partners', 'help', or 'unknown'
        """
        message = message.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    logger.info(f"Detected intent: {intent} for message: '{message}'")
                    return intent
        
        logger.info(f"Unknown intent for message: '{message}'")
        return 'unknown'
    
    def handle_approvals_intent(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Handle approvals-related queries with role-based security
        """
        try:
            # Base query for pending approvals
            query = db.query(Partner).filter(
                Partner.workflow_stage == WorkflowStage.PENDING_APPROVAL
            )
            
            # Apply role-based filtering for security
            if user.role == UserRole.SALESMAN:
                # For demo: Salesmen see limited results (simulating their own submissions)
                query = query.limit(1)  # Simulate showing only their own
                context = "your pending"
            elif user.role in [UserRole.MANAGER, UserRole.ADMIN, UserRole.ACCOUNTANT]:
                # Managers and above can see all pending approvals
                context = "all pending"
            else:
                return {
                    "response": "You don't have permission to view approval information.",
                    "data": [],
                    "count": 0
                }
            
            # Execute query
            pending_partners = query.all()
            count = len(pending_partners)
            
            # Format response
            if count == 0:
                response = f"No {context} approvals found. All partners are up to date!"
            elif count == 1:
                partner = pending_partners[0]
                response = f"Found 1 {context} approval: {partner.name} ({partner.type}) awaiting review."
            else:
                response = f"Found {count} {context} approvals requiring attention."
            
            # Prepare structured data for frontend
            data = []
            for partner in pending_partners:
                data.append({
                    "id": str(partner.id),
                    "name": partner.name,
                    "type": partner.type.value,
                    "gst_number": partner.gst_number,
                    "credit_limit": str(partner.credit_limit),
                    "created_at": partner.created_at.isoformat(),
                    "workflow_stage": partner.workflow_stage.value
                })
            
            logger.info(f"Approvals query: {count} results for user {user.username} (role: {user.role.value})")
            
            return {
                "response": response,
                "data": data,
                "count": count,
                "intent": "approvals"
            }
            
        except Exception as e:
            logger.error(f"Error handling approvals intent: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while checking approvals. Please try again.",
                "data": [],
                "count": 0,
                "error": "database_error"
            }
    
    def handle_list_partners_intent(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Handle list/show partners queries
        """
        try:
            # Get last 5 created partners
            query = db.query(Partner).order_by(Partner.created_at.desc()).limit(5)
            
            # Apply role-based filtering if needed
            if user.role == UserRole.SALESMAN:
                # For demo: Salesmen see approved partners only
                query = db.query(Partner).filter(
                    Partner.workflow_stage == WorkflowStage.APPROVED
                ).order_by(Partner.created_at.desc()).limit(3)
            
            partners = query.all()
            count = len(partners)
            
            if count == 0:
                response = "No partners found in the system."
            elif count == 1:
                response = f"Found 1 partner: {partners[0].name}"
            else:
                response = f"Here are the {count} most recent partners:"
            
            # Prepare structured data
            data = []
            for partner in partners:
                data.append({
                    "id": str(partner.id),
                    "name": partner.name,
                    "type": partner.type.value,
                    "gst_number": partner.gst_number,
                    "credit_limit": str(partner.credit_limit),
                    "workflow_stage": partner.workflow_stage.value,
                    "created_at": partner.created_at.isoformat()
                })
            
            logger.info(f"Partners list query: {count} results for user {user.username}")
            
            return {
                "response": response,
                "data": data,
                "count": count,
                "intent": "list_partners"
            }
            
        except Exception as e:
            logger.error(f"Error handling list partners intent: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while fetching partners. Please try again.",
                "data": [],
                "count": 0,
                "error": "database_error"
            }
    
    def handle_help_intent(self, user: User) -> Dict[str, Any]:
        """
        Handle help queries with role-specific guidance
        """
        base_commands = [
            "Show pending approvals",
            "List partners",
            "Show recent customers",
            "Display suppliers"
        ]
        
        role_specific = {
            UserRole.ADMIN: ["Approve partner requests", "View all system data"],
            UserRole.MANAGER: ["Review team submissions", "Manage approvals"],
            UserRole.ACCOUNTANT: ["Check financial data", "Review credit limits"],
            UserRole.SALESMAN: ["Create new partners", "Check your submissions"]
        }
        
        commands = base_commands + role_specific.get(user.role, [])
        
        response = f"Hi {user.username}! As a {user.role.value}, you can say:\n" + \
                  "\n".join([f"• {cmd}" for cmd in commands])
        
        # Convert commands to dictionary format for API consistency
        data = [{"command": cmd, "description": f"Voice command: {cmd}"} for cmd in commands]
        
        return {
            "response": response,
            "data": data,
            "count": len(commands),
            "intent": "help",
            "user_role": user.role.value
        }
    
    def process_message(self, db: Session, user: User, text: str) -> Dict[str, Any]:
        """
        Main entry point for processing voice/text messages
        
        Args:
            db: Database session
            user: Authenticated user
            text: Raw input text (potentially from voice recognition)
            
        Returns:
            Dict with response, data, and metadata
        """
        # Input validation and security
        if not text or not text.strip():
            return {
                "response": "I didn't catch that. Could you please repeat your request?",
                "data": [],
                "count": 0,
                "error": "empty_input"
            }
        
        # Normalize the input (important for voice input)
        normalized_message = self.normalize_message(text)
        
        if not normalized_message:
            return {
                "response": "I didn't understand that. Try saying 'help' to see what I can do.",
                "data": [],
                "count": 0,
                "error": "invalid_input"
            }
        
        # Detect intent
        intent = self.detect_intent(normalized_message)
        
        # Route to appropriate handler
        try:
            if intent == 'approvals':
                return self.handle_approvals_intent(db, user)
            elif intent == 'list_partners':
                return self.handle_list_partners_intent(db, user)
            elif intent == 'help':
                return self.handle_help_intent(user)
            else:
                # Unknown intent - provide helpful guidance
                return {
                    "response": "I'm not sure what you're asking for. You can say things like:\n" +
                              "• 'Show pending approvals'\n" +
                              "• 'List partners'\n" +
                              "• 'Help' for more options",
                    "data": [],
                    "count": 0,
                    "intent": "unknown",
                    "original_message": text,
                    "normalized_message": normalized_message
                }
                
        except Exception as e:
            logger.error(f"Error processing message '{text}' for user {user.username}: {str(e)}")
            return {
                "response": "I'm experiencing technical difficulties. Please try again in a moment.",
                "data": [],
                "count": 0,
                "error": "processing_error"
            }

# Global instance
chat_service = ChatService()