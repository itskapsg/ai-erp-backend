"""
Advanced Chat Service for Voice-First Assistant
Processes natural language commands with intent recognition and role-based security
Supports complex queries about Orders, Credit Limits, and Products
"""
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.core import User, UserRole
from app.models.masters import Partner
from app.models.orders import Order, OrderStatus
from app.models.products import Product, ProductVariant
from app.models.core import WorkflowStage
from app.services.finance_service import FinanceService
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """
    Voice-First Assistant Chat Service
    Processes natural language commands with security and intent recognition
    """
    
    def __init__(self):
        # Intent patterns for natural language processing
        # Order matters! More specific patterns should come first
        self.intent_patterns = {
            'order_status': [
                r'\b(order.*status|recent.*order|show.*order)\b',
                r'\b(my.*order|latest.*order|order.*list)\b',
                r'\b(order.*history|order.*details)\b',
                r'\b(show.*me.*recent.*order|show.*me.*order)\b',
                r'\b(show.*orders|recent.*orders)\b'
            ],
            'credit_check': [
                r'\b(credit.*limit|balance|limit.*for)\b',
                r'\b(credit.*check|check.*credit|available.*credit)\b',
                r'\b(outstanding|credit.*status)\b'
            ],
            'product_query': [
                r'\b(price.*of|cost.*of|rate.*of)\b',
                r'\b(variant.*of|variation.*of|option.*for)\b',
                r'\b(product.*detail|product.*info|tell.*about)\b'
            ],
            'approvals': [
                r'\b(pending.*approval|approval.*pending|need.*approval|waiting.*approval)\b',
                r'\b(pending.*partner|partner.*pending)\b',
                r'\b(approve.*partner|partner.*approve)\b'
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
    
    def handle_order_status_intent(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Handle order status queries - show recent orders with ID, Status, and Amount
        """
        try:
            # Get last 3 orders ordered by creation date
            query = db.query(Order).order_by(Order.created_at.desc()).limit(3)
            
            # Apply role-based filtering for security
            if user.role == UserRole.SALESMAN:
                # Salesmen might see limited orders (for demo purposes)
                query = query.limit(2)
            
            orders = query.all()
            count = len(orders)
            
            if count == 0:
                response = "No orders found in the system."
            elif count == 1:
                order = orders[0]
                response = f"Found 1 recent order: {order.order_number} - Status: {order.status.value} - Amount: ₹{order.total_amount}"
            else:
                response = f"Here are the {count} most recent orders:"
            
            # Prepare structured data
            data = []
            for order in orders:
                data.append({
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "status": order.status.value,
                    "total_amount": str(order.total_amount),
                    "buyer_name": order.buyer.name if order.buyer else "Unknown",
                    "seller_name": order.seller.name if order.seller else "Unknown",
                    "workflow_stage": order.workflow_stage.value,
                    "created_at": order.created_at.isoformat()
                })
            
            logger.info(f"Order status query: {count} results for user {user.username}")
            
            return {
                "response": response,
                "data": data,
                "count": count,
                "intent": "order_status"
            }
            
        except Exception as e:
            logger.error(f"Error handling order status intent: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while fetching orders. Please try again.",
                "data": [],
                "count": 0,
                "error": "database_error"
            }
    
    def extract_partner_name(self, message: str) -> Optional[str]:
        """
        Extract partner name from credit check queries using fuzzy matching patterns
        Handles patterns like "credit limit for ABC Company" or "balance of XYZ"
        """
        # Common patterns for extracting names
        patterns = [
            r'\b(?:for|of)\s+([A-Za-z\s]+?)(?:\s|$)',  # "for ABC Company" or "of XYZ"
            r'\blimit\s+([A-Za-z\s]+?)(?:\s|$)',       # "limit ABC Company"
            r'\bbalance\s+([A-Za-z\s]+?)(?:\s|$)',     # "balance ABC Company"
            r'\bcredit\s+([A-Za-z\s]+?)(?:\s|$)'       # "credit ABC Company"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common words that aren't names
                if name.lower() not in ['check', 'status', 'limit', 'balance', 'credit', 'for', 'of']:
                    return name
        
        return None
    
    def handle_credit_check_intent(self, db: Session, user: User, message: str) -> Dict[str, Any]:
        """
        Handle credit limit queries - search Partner by name and return credit info
        """
        try:
            # Extract partner name from the message
            partner_name = self.extract_partner_name(message)
            
            if not partner_name:
                return {
                    "response": "Please specify which partner you'd like to check. For example: 'Check credit limit for ABC Company'",
                    "data": [],
                    "count": 0,
                    "intent": "credit_check",
                    "error": "missing_partner_name"
                }
            
            # Fuzzy search for partner by name
            partners = db.query(Partner).filter(
                or_(
                    Partner.name.ilike(f"%{partner_name}%"),
                    Partner.name.ilike(f"{partner_name}%"),
                    Partner.name.ilike(f"%{partner_name}")
                )
            ).limit(5).all()
            
            if not partners:
                return {
                    "response": f"No partner found matching '{partner_name}'. Please check the name and try again.",
                    "data": [],
                    "count": 0,
                    "intent": "credit_check",
                    "searched_name": partner_name
                }
            
            # If multiple matches, show the best match (first one)
            partner = partners[0]
            
            # Use REAL financial math instead of mocked calculation
            finance_service = FinanceService(db)
            financial_summary = finance_service.get_partner_financial_summary(str(partner.id))
            
            response = f"Credit information for {partner.name}:\n" + \
                      f"• Credit Limit: ₹{financial_summary['credit_limit']:,.2f}\n" + \
                      f"• Outstanding: ₹{financial_summary['outstanding_balance']:,.2f} (REAL)\n" + \
                      f"• Available: ₹{financial_summary['available_credit']:,.2f}\n" + \
                      f"• Utilization: {financial_summary['credit_utilization_percent']:.1f}%"
            
            # Prepare structured data
            data = [{
                "id": str(partner.id),
                "name": partner.name,
                "type": partner.type.value,
                "credit_limit": str(financial_summary['credit_limit']),
                "outstanding_balance": f"{financial_summary['outstanding_balance']:.2f}",
                "available_credit": f"{financial_summary['available_credit']:.2f}",
                "credit_utilization_percent": f"{financial_summary['credit_utilization_percent']:.1f}",
                "gst_number": partner.gst_number,
                "workflow_stage": partner.workflow_stage.value,
                "total_orders": financial_summary['total_orders']
            }]
            
            # If multiple matches found, mention it
            if len(partners) > 1:
                response += f"\n\nNote: Found {len(partners)} matches, showing details for '{partner.name}'"
            
            logger.info(f"Credit check query for '{partner_name}' -> found {partner.name}")
            
            return {
                "response": response,
                "data": data,
                "count": 1,
                "intent": "credit_check",
                "searched_name": partner_name,
                "matches_found": len(partners)
            }
            
        except Exception as e:
            logger.error(f"Error handling credit check intent: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while checking credit information. Please try again.",
                "data": [],
                "count": 0,
                "error": "database_error"
            }
    
    def extract_product_name(self, message: str) -> Optional[str]:
        """
        Extract product name from product queries
        Handles patterns like "price of Banarasi Saree" or "variants of Silk Suit"
        """
        patterns = [
            r'\b(?:price|cost|rate)\s+of\s+([A-Za-z\s]+?)(?:\s|$)',      # "price of Product"
            r'\b(?:variant|variation|option)s?\s+of\s+([A-Za-z\s]+?)(?:\s|$)',  # "variants of Product"
            r'\btell.*about\s+([A-Za-z\s]+?)(?:\s|$)',                   # "tell me about Product"
            r'\bproduct.*info.*([A-Za-z\s]+?)(?:\s|$)'                   # "product info Product"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common words
                if name.lower() not in ['product', 'info', 'detail', 'about', 'price', 'cost']:
                    return name
        
        return None
    
    def handle_product_query_intent(self, db: Session, user: User, message: str) -> Dict[str, Any]:
        """
        Handle product queries - search Product table and return Base Price and Variant count
        """
        try:
            # Extract product name from the message
            product_name = self.extract_product_name(message)
            
            if not product_name:
                return {
                    "response": "Please specify which product you'd like to know about. For example: 'What is the price of Banarasi Saree?'",
                    "data": [],
                    "count": 0,
                    "intent": "product_query",
                    "error": "missing_product_name"
                }
            
            # Fuzzy search for product by name
            products = db.query(Product).filter(
                or_(
                    Product.name.ilike(f"%{product_name}%"),
                    Product.name.ilike(f"{product_name}%"),
                    Product.name.ilike(f"%{product_name}")
                )
            ).limit(5).all()
            
            if not products:
                return {
                    "response": f"No product found matching '{product_name}'. Please check the name and try again.",
                    "data": [],
                    "count": 0,
                    "intent": "product_query",
                    "searched_name": product_name
                }
            
            # If multiple matches, show the best match (first one)
            product = products[0]
            
            # Get variant count
            variant_count = db.query(ProductVariant).filter(ProductVariant.product_id == product.id).count()
            
            response = f"Product information for {product.name}:\n" + \
                      f"• Base Price: ₹{product.base_price:,.2f}\n" + \
                      f"• Category: {product.category}\n" + \
                      f"• Variants Available: {variant_count}\n" + \
                      f"• Status: {product.workflow_stage.value}"
            
            if product.description:
                response += f"\n• Description: {product.description[:100]}..."
            
            # Prepare structured data
            data = [{
                "id": str(product.id),
                "name": product.name,
                "base_price": str(product.base_price),
                "category": product.category,
                "variant_count": variant_count,
                "description": product.description,
                "workflow_stage": product.workflow_stage.value,
                "created_at": product.created_at.isoformat()
            }]
            
            # If multiple matches found, mention it
            if len(products) > 1:
                response += f"\n\nNote: Found {len(products)} matches, showing details for '{product.name}'"
            
            logger.info(f"Product query for '{product_name}' -> found {product.name}")
            
            return {
                "response": response,
                "data": data,
                "count": 1,
                "intent": "product_query",
                "searched_name": product_name,
                "matches_found": len(products)
            }
            
        except Exception as e:
            logger.error(f"Error handling product query intent: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while fetching product information. Please try again.",
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
            "Show recent orders",
            "Check credit limit for [Partner Name]",
            "What is the price of [Product Name]",
            "Show recent customers",
            "Display suppliers"
        ]
        
        role_specific = {
            UserRole.ADMIN: ["Approve partner requests", "View all system data", "Check any credit limits"],
            UserRole.MANAGER: ["Review team submissions", "Manage approvals", "View order history"],
            UserRole.ACCOUNTANT: ["Check financial data", "Review credit limits", "Monitor outstanding balances"],
            UserRole.SALESMAN: ["Create new partners", "Check your submissions", "View product prices"]
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
            elif intent == 'order_status':
                return self.handle_order_status_intent(db, user)
            elif intent == 'credit_check':
                return self.handle_credit_check_intent(db, user, normalized_message)
            elif intent == 'product_query':
                return self.handle_product_query_intent(db, user, normalized_message)
            elif intent == 'help':
                return self.handle_help_intent(user)
            else:
                # Unknown intent - provide helpful guidance
                return {
                    "response": "I'm not sure what you're asking for. You can say things like:\n" +
                              "• 'Show pending approvals'\n" +
                              "• 'List partners'\n" +
                              "• 'Show recent orders'\n" +
                              "• 'Check credit limit for [Partner Name]'\n" +
                              "• 'What is the price of [Product Name]'\n" +
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