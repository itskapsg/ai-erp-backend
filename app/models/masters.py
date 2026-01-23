import uuid
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from .core import Base, ApprovalMixin


class PartnerType(Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class Partner(Base, ApprovalMixin):
    """
    Partner model representing customers and suppliers
    Inherits Base and ApprovalMixin for approval workflow capabilities
    """
    __tablename__ = "partners"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    type = Column(SQLEnum(PartnerType), nullable=False)
    gst_number = Column(String(15), nullable=True, unique=True, index=True)
    credit_limit = Column(Numeric(15, 2), nullable=True, default=Decimal('0.00'))
    
    def __repr__(self):
        return f"<Partner(name='{self.name}', type='{self.type.value}', stage='{self.workflow_stage.value}')>"