
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from app.models.accounting import Ledger, TransactionType, InvoiceStatus
from app.models.masters import Partner

class LedgerService:
    @staticmethod
    def post_entry(db: Session, partner_id: str, transaction_type: TransactionType, 
                   amount: Decimal, is_debit: bool, description: str, 
                   reference_id: str = None, document_id: str = None):
        """
        Post a single entry to the ledger.
        Updates the running balance.
        """
        # Get last balance
        last_entry = db.query(Ledger).filter(
            Ledger.partner_id == partner_id
        ).order_by(Ledger.transaction_date.desc(), Ledger.id.desc()).first()
        
        current_balance = last_entry.balance if last_entry else Decimal('0.00')
        
        debit = amount if is_debit else Decimal('0.00')
        credit = amount if not is_debit else Decimal('0.00')
        
        # Balance Logic:
        # Asset/Expense (Debit +) ?? No, this is Partner Ledger.
        # Supplier (Liability): Credit increases Balance (They owe us? No, We owe them).
        # Let's standardize:
        # Creditor (Supplier): Credit = We owe them more. Debit = We paid them / They owe us.
        # Debtor (Customer): Debit = They owe us more. Credit = They paid us.
        
        # Simplified Math for Partner Balance (positive = we owe them / they are in credit? or positive = they owe us?)
        # Let's stick to standard Accounting Convention for "Party Ledger":
        # Credit (+): Liability/Income (Party gave us value)
        # Debit (-): Asset/Expense (We gave party value)
        # So Balance = Previous + Credit - Debit
        
        new_balance = current_balance + credit - debit
        
        entry = Ledger(
            partner_id=partner_id,
            transaction_type=transaction_type,
            transaction_date=datetime.utcnow(),
            description=description,
            debit=debit,
            credit=credit,
            balance=new_balance,
            reference_id=reference_id,
            related_document_id=document_id
        )
        
        db.add(entry)
        db.flush() # Generate ID
        
        # Update Partner's cached balance
        partner = db.query(Partner).get(partner_id)
        if partner:
            partner.outstanding_balance = new_balance
            
        return entry
