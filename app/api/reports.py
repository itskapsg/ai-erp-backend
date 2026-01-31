
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.orders import Order, OrderStatus
from app.models.accounting import PaymentReceipt, SupplierInvoice, InvoiceStatus

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/outstanding")
def get_outstanding_report(db: Session = Depends(get_db)):
    """
    List Buyers who have INVOICED orders but NO Payment linked (simplified).
    For MVP: Return Orders with Status INVOICED (meaning Bill raised) but not PAYMENT_RECEIVED.
    """
    # Find orders that are INVOICED but not fully paid
    # Since we track Payment on Partner level, precise linking is hard without "Payment <> Order" link.
    # We will list all INVOICED orders.
    
    outstanding_orders = db.query(Order).filter(
        Order.status == OrderStatus.INVOICED
    ).all()
    
    report = []
    for o in outstanding_orders:
        report.append({
            "order_number": o.order_number,
            "buyer": o.buyer.name,
            "amount": o.total_amount,
            "invoice_date": o.supplier_invoice[0].date if o.supplier_invoice else "N/A",
            "days_overdue": 0 # TODO: Calc based on Credit Days
        })
        
    return report

@router.get("/sales-register")
def get_sales_register(db: Session = Depends(get_db)):
    """
    Date-wise list of confirmed/invoiced orders.
    """
    orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.INVOICED])
    ).order_by(Order.created_at.desc()).all()
    
    return [
        {
            "date": o.created_at.date(),
            "order_no": o.order_number,
            "buyer": o.buyer.name,
            "seller": o.seller.name,
            "amount": o.total_amount,
            "status": o.status.value
        }
        for o in orders
    ]
