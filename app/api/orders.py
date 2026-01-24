"""
Order API endpoints for Agency Business
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from decimal import Decimal
from io import BytesIO

from app.database import get_db
from app.models import User, Order, OrderStatus, WorkflowStage
from app.services.order_service import OrderService
from app.services.pdf_service import pdf_service
from app.api.auth import get_current_user


router = APIRouter(prefix="/orders", tags=["orders"])


# Pydantic models for request/response
class OrderItemCreate(BaseModel):
    variant_id: str = Field(..., description="Product variant UUID")
    quantity: int = Field(..., gt=0, description="Quantity to order")


class OrderCreate(BaseModel):
    buyer_id: str = Field(..., description="Buyer partner UUID")
    seller_id: str = Field(..., description="Seller partner UUID")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order items")


class OrderItemResponse(BaseModel):
    id: str
    product_variant_id: str
    quantity: int
    price: str
    line_total: str
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    order_number: str
    buyer_id: str
    seller_id: str
    total_amount: str
    status: OrderStatus
    workflow_stage: WorkflowStage
    rejection_reason: Optional[str] = None
    created_at: str
    updated_at: str
    
    # Nested relationships
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


class OrderApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, description="Required for rejection")


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new order with credit limit validation
    
    The system will:
    1. Calculate order total
    2. Check buyer's credit limit
    3. If exceeded -> Set to PENDING_APPROVAL
    4. Else -> Auto-approve and set to CONFIRMED
    """
    try:
        order_service = OrderService(db)
        
        # Convert items to dict format
        items_data = [
            {"variant_id": item.variant_id, "quantity": item.quantity}
            for item in order_data.items
        ]
        
        order = order_service.create_order(
            buyer_id=order_data.buyer_id,
            seller_id=order_data.seller_id,
            items=items_data,
            user=current_user
        )
        
        # Prepare response with additional data
        response_data = {
            "id": str(order.id),
            "order_number": order.order_number,
            "buyer_id": str(order.buyer_id),
            "seller_id": str(order.seller_id),
            "total_amount": str(order.total_amount),
            "status": order.status,
            "workflow_stage": order.workflow_stage,
            "rejection_reason": order.rejection_reason,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "buyer_name": order.buyer.name if order.buyer else None,
            "seller_name": order.seller.name if order.seller else None,
            "items": [
                {
                    "id": str(item.id),
                    "product_variant_id": str(item.product_variant_id),
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "line_total": str(item.line_total)
                }
                for item in order.items
            ]
        }
        
        return OrderResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    buyer_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all orders with optional filtering by buyer or seller
    """
    try:
        order_service = OrderService(db)
        orders = order_service.get_orders(buyer_id=buyer_id, seller_id=seller_id)
        
        response_data = []
        for order in orders:
            order_data = {
                "id": str(order.id),
                "order_number": order.order_number,
                "buyer_id": str(order.buyer_id),
                "seller_id": str(order.seller_id),
                "total_amount": str(order.total_amount),
                "status": order.status,
                "workflow_stage": order.workflow_stage,
                "rejection_reason": order.rejection_reason,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "buyer_name": order.buyer.name if order.buyer else None,
                "seller_name": order.seller.name if order.seller else None,
                "items": [
                    {
                        "id": str(item.id),
                        "product_variant_id": str(item.product_variant_id),
                        "quantity": item.quantity,
                        "price": str(item.price),
                        "line_total": str(item.line_total)
                    }
                    for item in order.items
                ]
            }
            response_data.append(OrderResponse(**order_data))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch orders: {str(e)}"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific order by ID
    """
    try:
        order_service = OrderService(db)
        order = order_service.get_order_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found"
            )
        
        response_data = {
            "id": str(order.id),
            "order_number": order.order_number,
            "buyer_id": str(order.buyer_id),
            "seller_id": str(order.seller_id),
            "total_amount": str(order.total_amount),
            "status": order.status,
            "workflow_stage": order.workflow_stage,
            "rejection_reason": order.rejection_reason,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "buyer_name": order.buyer.name if order.buyer else None,
            "seller_name": order.seller.name if order.seller else None,
            "items": [
                {
                    "id": str(item.id),
                    "product_variant_id": str(item.product_variant_id),
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "line_total": str(item.line_total)
                }
                for item in order.items
            ]
        }
        
        return OrderResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order: {str(e)}"
        )


@router.post("/{order_id}/approval", response_model=OrderResponse)
async def handle_order_approval(
    order_id: str,
    approval_data: OrderApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject an order (for credit limit exceeded cases)
    """
    try:
        order_service = OrderService(db)
        
        if approval_data.action == "approve":
            order = order_service.approve_order(order_id, current_user)
        elif approval_data.action == "reject":
            if not approval_data.reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required"
                )
            order = order_service.reject_order(order_id, current_user, approval_data.reason)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'approve' or 'reject'"
            )
        
        response_data = {
            "id": str(order.id),
            "order_number": order.order_number,
            "buyer_id": str(order.buyer_id),
            "seller_id": str(order.seller_id),
            "total_amount": str(order.total_amount),
            "status": order.status,
            "workflow_stage": order.workflow_stage,
            "rejection_reason": order.rejection_reason,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "buyer_name": order.buyer.name if order.buyer else None,
            "seller_name": order.seller.name if order.seller else None,
            "items": [
                {
                    "id": str(item.id),
                    "product_variant_id": str(item.product_variant_id),
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "line_total": str(item.line_total)
                }
                for item in order.items
            ]
        }
        
        return OrderResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process order approval: {str(e)}"
        )


@router.get("/pending/count")
async def get_pending_orders_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of orders pending approval
    """
    try:
        pending_count = db.query(Order).filter(
            Order.workflow_stage == WorkflowStage.PENDING_APPROVAL
        ).count()
        
        return {"pending_count": pending_count}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending orders count: {str(e)}"
        )


@router.get("/{order_id}/pdf")
async def download_order_pdf(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and download PDF for an order confirmation.
    
    Returns a PDF file with professional order confirmation format including:
    - Company header with branding
    - Order details and status
    - Buyer and seller information
    - Itemized order table
    - Order summary with totals
    - Signature section and footer
    """
    try:
        # Get order with all related data
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_order_pdf(order)
        
        # Create streaming response
        pdf_buffer = BytesIO(pdf_bytes)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Order_{order.order_number}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )