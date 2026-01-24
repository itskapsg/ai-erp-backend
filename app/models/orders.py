import uuid
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Enum as SQLEnum, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .core import Base, ApprovalMixin


class OrderStatus(Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PENDING_APPROVAL = "pending_approval"


class Order(Base, ApprovalMixin):
    """
    Order model for Agency Business (Buyer + Seller)
    Inherits ApprovalMixin for Credit Limit approval workflow
    """
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(20), nullable=False, unique=True, index=True)
    
    # Agency Business: Buyer and Seller relationships
    buyer_id = Column(UUID(as_uuid=True), ForeignKey('partners.id'), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey('partners.id'), nullable=False)
    
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.DRAFT)
    
    # Relationships
    buyer = relationship("Partner", foreign_keys=[buyer_id], back_populates="buyer_orders")
    seller = relationship("Partner", foreign_keys=[seller_id], back_populates="seller_orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(number='{self.order_number}', total={self.total_amount}, status='{self.status.value}')>"


class OrderItem(Base):
    """
    Order Item model linking orders to product variants
    """
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey('product_variants.id'), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(15, 2), nullable=False)  # Price at time of booking
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product_variant = relationship("ProductVariant")
    
    @property
    def line_total(self) -> Decimal:
        """Calculate line total (quantity * price)"""
        return Decimal(str(self.quantity)) * self.price
    
    def __repr__(self):
        return f"<OrderItem(order='{self.order.order_number}', qty={self.quantity}, price={self.price})>"