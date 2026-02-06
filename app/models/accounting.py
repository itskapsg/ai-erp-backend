
import uuid
from enum import Enum
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Enum as SQLEnum, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship

from .core import Base
from .utils import GUID

# Enums
class TransactionType(Enum):
    PAYMENT = "payment"
    INVOICE = "invoice"
    GOODS_RETURN = "goods_return"
    COMMISSION = "commission"
    OPENING_BALANCE = "opening_balance"

class InvoiceStatus(Enum):
    DRAFT = "draft"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"

class PaymentMode(Enum):
    CHEQUE = "cheque"
    RTGS = "rtgs"
    CASH = "cash"
    NEFT = "neft"

class PaymentStatus(Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    BOUNCED = "bounced"

class GRStatus(Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"

# Models

class Ledger(Base):
    """
    Double-entry ledger for Partners (Customer/Supplier).
    Tracks all financial movements using Debit/Credit principle.
    """
    __tablename__ = "ledgers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    partner_id = Column(GUID(), ForeignKey('partners.id'), nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Financials
    debit = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False, comment="Money leaving the agency / Decrease Liability")
    credit = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False, comment="Money coming to agency / Increase Liability")
    balance = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False, comment="Running Balance")
    
    reference_id = Column(String(100), nullable=True, comment="Cheque No, Invoice No, etc.")
    related_document_id = Column(GUID(), nullable=True, comment="Link to Payment/Invoice ID if applicable")

    partner = relationship("Partner", backref="ledger_entries")

    def __repr__(self):
        return f"<Ledger(partner='{self.partner_id}', type='{self.transaction_type.value}', bal={self.balance})>"


class SupplierInvoice(Base):
    """
    Tracks the actual bill received from the Supplier.
    Must be reconciled against an internal Order.
    """
    __tablename__ = "supplier_invoices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), nullable=False, index=True)
    supplier_id = Column(GUID(), ForeignKey('partners.id'), nullable=False)
    
    date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    scanned_copy_url = Column(String(500), nullable=True)
    
    # Strict Linking for Reconciliation
    order_id = Column(GUID(), ForeignKey('orders.id'), nullable=False, unique=True)
    
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Relationships
    supplier = relationship("Partner")
    order = relationship("Order", backref="supplier_invoice")

    def __repr__(self):
        return f"<SupplierInvoice(no='{self.invoice_number}', amount={self.total_amount}, status='{self.status.value}')>"


class PaymentReceipt(Base):
    """
    Tracks money flow between Buyer and Supplier.
    The Agency tracks this to know when to charge Commission.
    """
    __tablename__ = "payment_receipts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    payment_number = Column(String(50), unique=True, nullable=False)
    
    from_partner_id = Column(GUID(), ForeignKey('partners.id'), nullable=False, comment="Buyer")
    to_partner_id = Column(GUID(), ForeignKey('partners.id'), nullable=False, comment="Supplier")
    
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    mode = Column(SQLEnum(PaymentMode), nullable=False)
    reference_number = Column(String(100), nullable=True, comment="Cheque/UTR No")
    
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    cleared_date = Column(Date, nullable=True, comment="Date when payment actually hit the bank")

    # Relationships
    buyer = relationship("Partner", foreign_keys=[from_partner_id])
    supplier = relationship("Partner", foreign_keys=[to_partner_id])

    def __repr__(self):
        return f"<Payment(no='{self.payment_number}', amount={self.amount}, status='{self.status.value}')>"


class GoodsReturn(Base):
    """
    Tracks returned goods to reduce Commissionable Value.
    """
    __tablename__ = "goods_returns"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID(), ForeignKey('orders.id'), nullable=False)
    
    return_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    value = Column(Numeric(15, 2), nullable=False, comment="Value to deduct from Commission Calculation")
    
    status = Column(SQLEnum(GRStatus), default=GRStatus.REQUESTED, nullable=False)
    
    order = relationship("Order", backref="returns")

    def __repr__(self):
        return f"<GR(order='{self.order_id}', value={self.value})>"


class CommissionInvoice(Base):
    """
    The Agency's bill to the Supplier (Service Invoice).
    Generated ONLY when a PaymentReceipt is CLEARED.
    """
    __tablename__ = "commission_invoices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False)
    
    supplier_id = Column(GUID(), ForeignKey('partners.id'), nullable=False)
    payment_id = Column(GUID(), ForeignKey('payment_receipts.id'), nullable=False, unique=True)
    
    base_amount = Column(Numeric(15, 2), nullable=False, comment="Commission Amount before Tax")
    tax_amount = Column(Numeric(15, 2), nullable=False, comment="GST")
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    supplier = relationship("Partner")
    payment = relationship("PaymentReceipt", backref="commission_invoice")

    def __repr__(self):
        return f"<CommissionInv(no='{self.invoice_number}', total={self.total_amount})>"
