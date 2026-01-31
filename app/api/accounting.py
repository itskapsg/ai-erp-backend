
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.accounting import SupplierInvoice, PaymentReceipt
from app.services.reconciliation_service import ReconciliationService
from app.services.accounting_service import AccountingService
from pydantic import BaseModel
from decimal import Decimal
from datetime import date

router = APIRouter(prefix="/accounting", tags=["Accounting"])

# Schemas
class InvoiceCreate(BaseModel):
    invoice_number: str
    supplier_id: str
    date: date
    total_amount: Decimal
    order_id: str

class PaymentCreate(BaseModel):
    payment_number: str
    from_partner_id: str
    to_partner_id: str
    amount: Decimal
    payment_date: date
    mode: str
    reference_number: str

# Endpoints

@router.post("/invoices")
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    db_inv = SupplierInvoice(**invoice.dict())
    db.add(db_inv)
    db.commit()
    return {"id": db_inv.id, "status": "created"}

@router.post("/invoices/{id}/reconcile")
def reconcile_invoice(id: str, db: Session = Depends(get_db)):
    try:
        result = ReconciliationService.reconcile_invoice(db, id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments")
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_pmt = PaymentReceipt(**payment.dict())
    db.add(db_pmt)
    db.commit()
    return {"id": db_pmt.id, "status": "created"}

@router.post("/payments/{id}/process")
def process_payment(id: str, db: Session = Depends(get_db)):
    try:
        result = AccountingService.process_payment(db, id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
