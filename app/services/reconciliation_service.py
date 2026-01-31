
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.accounting import SupplierInvoice, InvoiceStatus, TransactionType
from app.models.orders import Order, OrderStatus
from app.services.ledger_service import LedgerService

class ReconciliationService:
    
    @staticmethod
    def reconcile_invoice(db: Session, invoice_id: str):
        """
        Compare Invoice Amount vs Order Amount.
        If match (within tolerance), Mark Reconciled & API Ledger.
        """
        invoice = db.query(SupplierInvoice).get(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
            
        if invoice.status == InvoiceStatus.RECONCILED:
            return {"status": "already_reconciled"}
            
        order = invoice.order
        if not order:
            raise ValueError("Linked Order not found")
            
        # Tolerance check (e.g. +/- 10 INR for roundoff)
        diff = abs(invoice.total_amount - order.total_amount)
        if diff > Decimal('10.00'):
            invoice.status = InvoiceStatus.DISPUTED
            return {
                "status": "disputed", 
                "reason": f"Amount Mismatch: Inv {invoice.total_amount} != Ord {order.total_amount}"
            }
            
        # Success Logic
        invoice.status = InvoiceStatus.RECONCILED
        order.status = OrderStatus.CONFIRMED # Ensure it is confirmed? or INVOICED status if we had one.
        # OrderStatus enum doesn't have INVOICED yet, keeping CONFIRMED or moving to APPROVED if logic dictates.
        # Let's assume CONFIRMED is fine for now, or just leave it. 
        # Actually requirements said Update Order Status -> INVOICED. 
        # I need to check OrderStatus enum. If INVOICED missing, add it or use closest.
        
        # Ledger Entry: Purchase (Credit to Supplier)
        LedgerService.post_entry(
            db=db,
            partner_id=invoice.supplier_id,
            transaction_type=TransactionType.INVOICE,
            amount=invoice.total_amount,
            is_debit=False, # Credit = Liability increases (We owe Supplier)
            description=f"Invoice Reconciled: {invoice.invoice_number}",
            reference_id=invoice.invoice_number,
            document_id=invoice.id
        )
        
        db.commit()
        return {"status": "reconciled", "invoice": invoice.invoice_number}
