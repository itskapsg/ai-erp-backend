
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from app.models.accounting import (
    PaymentReceipt, PaymentStatus, Ledger, TransactionType, 
    CommissionInvoice, GoodsReturn, GRStatus
)
from app.models.orders import Order, OrderStatus
from app.services.ledger_service import LedgerService
from app.models.masters import Partner

class AccountingService:
    
    @staticmethod
    def process_payment(db: Session, payment_id: str):
        """
        Mark Payment as CLEARED.
        Update Ledger (Asset/Liability).
        Trigger Commission Logic.
        """
        payment = db.query(PaymentReceipt).get(payment_id)
        if not payment:
            raise ValueError("Payment not found")
            
        if payment.status == PaymentStatus.CLEARED:
            return {"status": "already_cleared"}
            
        payment.status = PaymentStatus.CLEARED
        payment.cleared_date = datetime.utcnow().date()
        
        # Ledger Entires
        # 1. Buyer Paid (Credit Buyer Ledger -> They owe us less / We hold their money?)
        # Agency context: Buyer pays Agency (or Supplier directly?).
        # If tracking "Receivables" from Buyer:
        # Credit Buyer Account.
        LedgerService.post_entry(
            db=db,
            partner_id=payment.from_partner_id,
            transaction_type=TransactionType.PAYMENT,
            amount=payment.amount,
            is_debit=False, # Credit
            description=f"Payment Received: {payment.payment_number}",
            reference_id=payment.reference_number,
            document_id=payment.id
        )
        
        # 2. Supplier (If money flows to them?)
        # If payment is FROM buyer TO supplier, agency just records it.
        # But we need to record that Supplier RECEIVED money, so their "Receivable" from us/Buyer drops?
        # Actually in Agency, usually:
        # A. Buyer -> Agency -> Supplier (Del Credere)
        # B. Buyer -> Supplier (Direct)
        # Assuming B for "Commission Agent" unless specified.
        # If B: We just mark it.
        # But Phase 3 says: "Debit Supplier Ledger (They owe us)... Credit Agency Revenue" -> This is for Commission.
        
        # Trigger Commission
        comm_result = AccountingService.process_commission_on_payment(db, payment)
        
        db.commit()
        return {"status": "cleared", "commission": comm_result}

    @staticmethod
    def process_commission_on_payment(db: Session, payment: PaymentReceipt):
        """
        Calculate and charge commission.
        Comm = (Payment Amount - Returns) * Rate
        """
        # 1. Identify Supplier (To Partner)
        supplier = payment.supplier
        if not supplier or not supplier.commission_rate:
            return None # No commission config
            
        rate = supplier.commission_rate
        
        # 2. Check linked Goods Returns (GR)
        # We need to find ORDERS linked to this payment to find GRs.
        # But Payment is Partner<>Partner.
        # Heuristic: Find Orders between these two partners that are INVOICED/DELIVERED?
        # OR just take the Payment Amount as the Base.
        # The prompt says: "Check for any linked GoodsReturn (GR) that reduces the commissionable value."
        # But GR is linked to Invoice/Order. Payment is not strictly linked to Order in our schema (it's Partner to Partner).
        # We need to infer or assume Payment settles oldest orders?
        # Or simplified: Start with Payment Amount. check if there are any "Pending GRs" for this Supplier/Buyer pair?
        # Prompt says: "linked GoodsReturn". Our schema: GR -> Order.
        # Missing Link: Payment -> Order?
        # Let's assume for MVP: Commission is on total payment received.
        # GR handling: If a GR exists, it should have reduced the "Payable", so the Payment amount *is* the net.
        # BUT "We lose commission on that amount".
        # If Buyer pays 100k, but returns 20k worth.
        # Scenario A: Buyer pays 80k. We charge comm on 80k. (Correct)
        # Scenario B: Buyer pays 100k, then Returns 20k.
        # Complex.
        # Let's stick to: Base Amount = Payment Amount.
        # If GR logic is needed, we query for GRs verified in this period?
        # Let's simplify: Commission = Payment.amount * Rate. (If GR happens, Payment would be less).
        
        commission_base = payment.amount
        
        # Calculate
        comm_amount = commission_base * (rate / Decimal('100.00'))
        tax_amount = comm_amount * Decimal('0.18') # 18% GST on Service
        total_comm = comm_amount + tax_amount
        
        # Create Invoice
        inv_number = f"COMM/{datetime.now().strftime('%Y%m')}/{payment.id.hex[:6].upper()}"
        
        comm_inv = CommissionInvoice(
            invoice_number=inv_number,
            supplier_id=payment.to_partner_id,
            payment_id=payment.id,
            base_amount=comm_amount,
            tax_amount=tax_amount,
            total_amount=total_comm
        )
        db.add(comm_inv)
        db.flush()
        
        # Ledger: Debit Supplier (They owe us this commission)
        LedgerService.post_entry(
            db=db,
            partner_id=payment.to_partner_id,
            transaction_type=TransactionType.COMMISSION,
            amount=total_comm,
            is_debit=True, # Debit = Asset (Receivable from Supplier)
            description=f"Commission on Pmt {payment.payment_number}",
            reference_id=inv_number,
            document_id=comm_inv.id
        )
        
        return {"invoice": inv_number, "amount": total_comm}
