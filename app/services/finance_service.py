"""
Finance Service for Real Financial Math

This service implements real financial calculations to prevent the split-order loophole:
1. Calculate actual outstanding balance from database orders
2. Prevent credit limit bypass through multiple small orders
3. Provide accurate financial reporting
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.orders import Order, OrderStatus
from app.models.masters import Partner


class FinanceService:
    """
    Finance Service for Real Financial Math
    Calculates actual outstanding balances to prevent credit limit bypass
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_outstanding_balance(self, partner_id: str) -> Decimal:
        """
        Calculate the actual outstanding balance for a partner from database orders
        
        This is the CRITICAL function that prevents the split-order loophole.
        It sums all orders that contribute to the partner's outstanding balance.
        
        Args:
            partner_id: UUID of the partner (buyer)
            
        Returns:
            Decimal: Total outstanding balance
            
        Business Logic:
            - Include orders with status: CONFIRMED (orders that are active/outstanding)
            - Exclude orders with status: DRAFT (not yet confirmed), CANCELLED (cancelled orders)
            - For future: Could include APPROVED, DELIVERED if those statuses are added
        """
        # Query orders for this buyer with statuses that contribute to outstanding balance
        # Currently using CONFIRMED as the main status for outstanding orders
        # In a real system, this might include additional statuses like APPROVED, DELIVERED, INVOICED
        outstanding_statuses = [OrderStatus.CONFIRMED]
        
        # Calculate sum of total_amount for all outstanding orders
        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.buyer_id == partner_id,
            Order.status.in_(outstanding_statuses)
        ).scalar()
        
        # Handle case where no orders exist (sum returns None)
        outstanding_balance = result or Decimal('0.00')
        
        return outstanding_balance
    
    def get_partner_financial_summary(self, partner_id: str) -> dict:
        """
        Get comprehensive financial summary for a partner
        
        Args:
            partner_id: UUID of the partner
            
        Returns:
            Dict with financial details including credit limit, outstanding, available credit
        """
        # Get partner details
        partner = self.db.query(Partner).filter_by(id=partner_id).first()
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")
        
        # Calculate outstanding balance
        outstanding_balance = self.calculate_outstanding_balance(partner_id)
        
        # Calculate available credit
        credit_limit = partner.credit_limit or Decimal('0.00')
        available_credit = credit_limit - outstanding_balance
        
        # Get order counts by status (only for existing database enum values)
        order_counts = {}
        existing_statuses = [OrderStatus.DRAFT, OrderStatus.CONFIRMED, OrderStatus.CANCELLED]
        for status in existing_statuses:
            count = self.db.query(Order).filter(
                Order.buyer_id == partner_id,
                Order.status == status
            ).count()
            order_counts[status.value] = count
        
        return {
            "partner_id": str(partner.id),
            "partner_name": partner.name,
            "credit_limit": float(credit_limit),
            "outstanding_balance": float(outstanding_balance),
            "available_credit": float(available_credit),
            "credit_utilization_percent": float((outstanding_balance / credit_limit * 100) if credit_limit > 0 else 0),
            "order_counts": order_counts,
            "total_orders": sum(order_counts.values())
        }
    
    def check_credit_limit_with_new_order(self, partner_id: str, new_order_amount: Decimal) -> dict:
        """
        Check if a new order would exceed the partner's credit limit
        
        This is the CORE LOGIC that prevents the split-order loophole:
        Outstanding Balance + New Order Amount > Credit Limit = Requires Approval
        
        Args:
            partner_id: UUID of the partner (buyer)
            new_order_amount: Amount of the new order being created
            
        Returns:
            Dict with approval decision and details
        """
        # Get partner
        partner = self.db.query(Partner).filter_by(id=partner_id).first()
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")
        
        # Get current outstanding balance (REAL calculation from database)
        outstanding_balance = self.calculate_outstanding_balance(partner_id)
        
        # Calculate total exposure with new order
        total_exposure = outstanding_balance + new_order_amount
        credit_limit = partner.credit_limit or Decimal('0.00')
        
        # Determine if approval is required
        requires_approval = total_exposure > credit_limit
        
        return {
            "requires_approval": requires_approval,
            "partner_name": partner.name,
            "credit_limit": float(credit_limit),
            "current_outstanding": float(outstanding_balance),
            "new_order_amount": float(new_order_amount),
            "total_exposure": float(total_exposure),
            "available_credit_before": float(credit_limit - outstanding_balance),
            "available_credit_after": float(credit_limit - total_exposure),
            "reason": self._generate_credit_check_reason(
                requires_approval, partner.name, outstanding_balance, 
                new_order_amount, total_exposure, credit_limit
            )
        }
    
    def _generate_credit_check_reason(
        self, 
        requires_approval: bool, 
        partner_name: str,
        outstanding: Decimal, 
        new_amount: Decimal, 
        total_exposure: Decimal, 
        credit_limit: Decimal
    ) -> str:
        """Generate human-readable reason for credit check decision"""
        
        if requires_approval:
            return (
                f"Credit Limit Exceeded: {partner_name} has outstanding balance ₹{outstanding:,.2f} + "
                f"new order ₹{new_amount:,.2f} = ₹{total_exposure:,.2f} which exceeds "
                f"credit limit ₹{credit_limit:,.2f}"
            )
        else:
            return (
                f"Within Credit Limit: {partner_name} total exposure ₹{total_exposure:,.2f} "
                f"is within credit limit ₹{credit_limit:,.2f}"
            )
    
    def get_all_partners_credit_summary(self) -> list:
        """
        Get credit summary for all partners (useful for reporting)
        
        Returns:
            List of financial summaries for all partners
        """
        partners = self.db.query(Partner).all()
        summaries = []
        
        for partner in partners:
            try:
                summary = self.get_partner_financial_summary(str(partner.id))
                summaries.append(summary)
            except Exception as e:
                # Log error but continue with other partners
                summaries.append({
                    "partner_id": str(partner.id),
                    "partner_name": partner.name,
                    "error": str(e)
                })
        
        return summaries