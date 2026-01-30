import uuid
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, Enum as SQLEnum
from .utils import GUID
from sqlalchemy.orm import relationship
from .utils import GUID

from .core import Base, ApprovalMixin


class PartnerType(Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class PartnerStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"


class Partner(Base, ApprovalMixin):
    """
    Partner model representing customers and suppliers
    Inherits Base and ApprovalMixin for approval workflow capabilities
    """
    __tablename__ = "partners"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    type = Column(SQLEnum(PartnerType), nullable=False)
    gst_number = Column(String(15), nullable=True, unique=True, index=True)
    credit_limit = Column(Numeric(15, 2), nullable=True, default=Decimal('0.00'))
    
    # Textile Agency Specific Fields
    mobile = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)  # Using String for Text to be safe, or Text
    commission_rate = Column(Numeric(5, 2), nullable=True, default=Decimal('0.00'), comment="Commission percentage")
    outstanding_balance = Column(Numeric(15, 2), nullable=True, default=Decimal('0.00'), comment="Current money owed")
    status = Column(SQLEnum(PartnerStatus), nullable=False, default=PartnerStatus.ACTIVE)
    
    # Order relationships for Agency Business
    buyer_orders = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    seller_orders = relationship("Order", foreign_keys="Order.seller_id", back_populates="seller")
    
    def __repr__(self):
        return f"<Partner(name='{self.name}', type='{self.type.value}', status='{self.status.value}')>"