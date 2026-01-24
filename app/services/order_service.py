"""
Order Service with Credit Limit Approval Logic

This service implements the Agency Business order creation logic:
1. Calculate Order Total
2. Check Buyer's Credit Limit
3. If Credit Limit Exceeded -> Require Approval
4. Else -> Auto-Approve
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Partner, ProductVariant, User, OrderStatus, WorkflowStage
from app.services.approval_service import ApprovalService
from app.services.finance_service import FinanceService


class OrderService:
    """
    Order Service for Agency Business with Credit Limit Logic
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.approval_service = ApprovalService(db_session)
        self.finance_service = FinanceService(db_session)
    
    def create_order(
        self, 
        buyer_id: str, 
        seller_id: str, 
        items: List[Dict[str, Any]], 
        user: User
    ) -> Order:
        """
        Create a new order with credit limit validation
        
        Args:
            buyer_id: UUID of the buyer partner
            seller_id: UUID of the seller partner
            items: List of items [{"variant_id": "...", "quantity": 10}]
            user: User creating the order
            
        Returns:
            Order: The created order with appropriate status
            
        Raises:
            ValueError: If buyer/seller not found or invalid data
        """
        # Validate buyer and seller
        buyer = self.db.query(Partner).filter_by(id=buyer_id).first()
        if not buyer:
            raise ValueError(f"Buyer with ID {buyer_id} not found")
        
        seller = self.db.query(Partner).filter_by(id=seller_id).first()
        if not seller:
            raise ValueError(f"Seller with ID {seller_id} not found")
        
        # Calculate order total
        total_amount, order_items_data = self._calculate_order_total(items)
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Create order
        order = Order(
            order_number=order_number,
            buyer_id=buyer_id,
            seller_id=seller_id,
            total_amount=total_amount,
            status=OrderStatus.DRAFT
        )
        
        # Check credit limit using REAL financial math (prevents split-order loophole)
        credit_check_result = self.finance_service.check_credit_limit_with_new_order(buyer_id, total_amount)
        
        if credit_check_result["requires_approval"]:
            # Credit limit exceeded -> Require approval
            order.workflow_stage = WorkflowStage.PENDING_APPROVAL
            order.rejection_reason = credit_check_result["reason"]
        else:
            # Within credit limit -> Auto-approve
            order.workflow_stage = WorkflowStage.APPROVED
            order.status = OrderStatus.CONFIRMED
        
        # Save order to get ID
        self.db.add(order)
        self.db.flush()
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_variant_id=item_data["variant_id"],
                quantity=item_data["quantity"],
                price=item_data["price"]
            )
            self.db.add(order_item)
        
        self.db.commit()
        return order
    
    def _calculate_order_total(self, items: List[Dict[str, Any]]) -> tuple[Decimal, List[Dict[str, Any]]]:
        """
        Calculate order total and prepare order items data
        
        Args:
            items: List of items [{"variant_id": "...", "quantity": 10}]
            
        Returns:
            tuple: (total_amount, order_items_data)
        """
        total_amount = Decimal('0.00')
        order_items_data = []
        
        for item in items:
            variant_id = item.get("variant_id")
            quantity = item.get("quantity", 1)
            
            # Get product variant
            variant = self.db.query(ProductVariant).filter_by(id=variant_id).first()
            if not variant:
                raise ValueError(f"Product variant with ID {variant_id} not found")
            
            # Use variant final price (base price + adjustment)
            price = variant.final_price
            line_total = Decimal(str(quantity)) * price
            total_amount += line_total
            
            order_items_data.append({
                "variant_id": variant_id,
                "quantity": quantity,
                "price": price
            })
        
        return total_amount, order_items_data
    
    # NOTE: _check_credit_limit and _get_outstanding_balance methods removed
    # Now using FinanceService.check_credit_limit_with_new_order() for REAL financial math
    
    def _generate_order_number(self) -> str:
        """
        Generate a unique order number
        Format: ORD-001, ORD-002, etc.
        
        Returns:
            str: Generated order number
        """
        # Get the highest order number
        last_order = self.db.query(Order).order_by(Order.order_number.desc()).first()
        
        if last_order and last_order.order_number.startswith('ORD-'):
            try:
                last_number = int(last_order.order_number.split('-')[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                next_number = 1
        else:
            next_number = 1
        
        return f"ORD-{next_number:03d}"
    
    def get_orders(self, buyer_id: Optional[str] = None, seller_id: Optional[str] = None) -> List[Order]:
        """
        Get orders with optional filtering
        
        Args:
            buyer_id: Optional buyer ID filter
            seller_id: Optional seller ID filter
            
        Returns:
            List[Order]: List of orders
        """
        query = self.db.query(Order)
        
        if buyer_id:
            query = query.filter(Order.buyer_id == buyer_id)
        
        if seller_id:
            query = query.filter(Order.seller_id == seller_id)
        
        return query.order_by(Order.created_at.desc()).all()
    
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID
        
        Args:
            order_id: Order UUID
            
        Returns:
            Order or None if not found
        """
        return self.db.query(Order).filter_by(id=order_id).first()
    
    def approve_order(self, order_id: str, approved_by: User) -> Order:
        """
        Approve an order (for credit limit exceeded cases)
        
        Args:
            order_id: Order UUID
            approved_by: User approving the order
            
        Returns:
            Order: The approved order
            
        Raises:
            ValueError: If order not found or not in pending state
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        if order.workflow_stage != WorkflowStage.PENDING_APPROVAL:
            raise ValueError(f"Order {order.order_number} is not pending approval")
        
        # Approve the order
        order.approve(approved_by)
        order.status = OrderStatus.CONFIRMED
        
        self.db.commit()
        return order
    
    def reject_order(self, order_id: str, rejected_by: User, reason: str) -> Order:
        """
        Reject an order
        
        Args:
            order_id: Order UUID
            rejected_by: User rejecting the order
            reason: Rejection reason
            
        Returns:
            Order: The rejected order
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        # Reject the order
        order.reject(rejected_by, reason)
        order.status = OrderStatus.CANCELLED
        
        self.db.commit()
        return order