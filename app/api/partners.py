"""
Partner API Endpoints

Implements CRUD operations for partners with integrated approval workflow.
Uses ApprovalService to determine workflow stages based on configurable policies.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import Partner, PartnerType, User, UserRole, WorkflowStage
from app.services.approval_service import ApprovalService
from app.database import get_db
from app.api.auth import get_current_active_user, require_role


# Router
router = APIRouter(prefix="/api/v1/partners", tags=["partners"])


# Pydantic Models
class PartnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Partner name")
    type: PartnerType = Field(..., description="Partner type: CUSTOMER or SUPPLIER")
    gst_number: Optional[str] = Field(None, max_length=15, description="GST registration number")
    credit_limit: Optional[Decimal] = Field(None, ge=0, description="Credit limit amount")


class PartnerResponse(BaseModel):
    id: str
    name: str
    type: str
    gst_number: Optional[str]
    credit_limit: Optional[Decimal]
    workflow_stage: str
    approved_by_id: Optional[str]
    rejection_reason: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PartnerApproval(BaseModel):
    action: str = Field(..., description="Action: 'approve' or 'reject'")
    reason: Optional[str] = Field(None, description="Reason for rejection (required if action is 'reject')")


class ApprovalResponse(BaseModel):
    message: str
    partner_id: str
    new_status: str
    approved_by: str


# API Endpoints
@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner_data: PartnerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new partner
    
    CRITICAL: Uses ApprovalService to determine workflow stage based on policies!
    - If approval required: Creates partner with PENDING_APPROVAL status
    - If auto-approved: Creates partner with APPROVED status
    """
    
    # Initialize approval service
    approval_service = ApprovalService(db)
    
    # CRITICAL: Check approval policy and determine workflow stage
    workflow_stage = approval_service.determine_workflow_stage('partner', 'create', current_user)
    
    # Check for duplicate GST number
    if partner_data.gst_number:
        existing_partner = db.query(Partner).filter(Partner.gst_number == partner_data.gst_number).first()
        if existing_partner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Partner with GST number {partner_data.gst_number} already exists"
            )
    
    # Create partner with determined workflow stage
    partner = Partner(
        name=partner_data.name,
        type=partner_data.type,
        gst_number=partner_data.gst_number,
        credit_limit=partner_data.credit_limit or Decimal('0.00'),
        workflow_stage=workflow_stage  # Set by ApprovalService!
    )
    
    # If auto-approved, set the approver
    if workflow_stage == WorkflowStage.APPROVED:
        partner.approved_by_id = current_user.id
    
    db.add(partner)
    db.commit()
    db.refresh(partner)
    
    return PartnerResponse(
        id=str(partner.id),
        name=partner.name,
        type=partner.type.value,
        gst_number=partner.gst_number,
        credit_limit=partner.credit_limit,
        workflow_stage=partner.workflow_stage.value,
        approved_by_id=str(partner.approved_by_id) if partner.approved_by_id else None,
        rejection_reason=partner.rejection_reason,
        created_at=partner.created_at.isoformat(),
        updated_at=partner.updated_at.isoformat()
    )


@router.get("/", response_model=List[PartnerResponse])
async def list_partners(
    skip: int = 0,
    limit: int = 100,
    workflow_stage: Optional[WorkflowStage] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all partners with optional filtering
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - workflow_stage: Filter by workflow stage (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
    """
    
    query = db.query(Partner)
    
    # Filter by workflow stage if provided
    if workflow_stage:
        query = query.filter(Partner.workflow_stage == workflow_stage)
    
    # Apply pagination
    partners = query.offset(skip).limit(limit).all()
    
    return [
        PartnerResponse(
            id=str(partner.id),
            name=partner.name,
            type=partner.type.value,
            gst_number=partner.gst_number,
            credit_limit=partner.credit_limit,
            workflow_stage=partner.workflow_stage.value,
            approved_by_id=str(partner.approved_by_id) if partner.approved_by_id else None,
            rejection_reason=partner.rejection_reason,
            created_at=partner.created_at.isoformat(),
            updated_at=partner.updated_at.isoformat()
        )
        for partner in partners
    ]


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific partner by ID"""
    
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    return PartnerResponse(
        id=str(partner.id),
        name=partner.name,
        type=partner.type.value,
        gst_number=partner.gst_number,
        credit_limit=partner.credit_limit,
        workflow_stage=partner.workflow_stage.value,
        approved_by_id=str(partner.approved_by_id) if partner.approved_by_id else None,
        rejection_reason=partner.rejection_reason,
        created_at=partner.created_at.isoformat(),
        updated_at=partner.updated_at.isoformat()
    )


@router.put("/{partner_id}/approve", response_model=ApprovalResponse)
async def approve_or_reject_partner(
    partner_id: UUID,
    approval_data: PartnerApproval,
    current_user: User = Depends(require_role(UserRole.MANAGER)),  # Requires MANAGER or higher
    db: Session = Depends(get_db)
):
    """
    Approve or reject a partner (MANAGER+ only)
    
    Actions:
    - approve: Set status to APPROVED
    - reject: Set status to REJECTED with reason
    """
    
    # Find the partner
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    # Check if partner is in a state that can be approved/rejected
    if partner.workflow_stage not in [WorkflowStage.PENDING_APPROVAL, WorkflowStage.DRAFT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Partner is already {partner.workflow_stage.value}. Cannot change status."
        )
    
    # Process the approval action
    if approval_data.action.lower() == "approve":
        partner.approve(current_user)
        message = f"Partner '{partner.name}' has been approved"
        
    elif approval_data.action.lower() == "reject":
        if not approval_data.reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required when rejecting a partner"
            )
        partner.reject(current_user, approval_data.reason)
        message = f"Partner '{partner.name}' has been rejected"
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'approve' or 'reject'"
        )
    
    db.commit()
    db.refresh(partner)
    
    return ApprovalResponse(
        message=message,
        partner_id=str(partner.id),
        new_status=partner.workflow_stage.value,
        approved_by=current_user.username
    )


@router.get("/pending/count")
async def get_pending_approvals_count(
    current_user: User = Depends(require_role(UserRole.MANAGER)),  # Requires MANAGER or higher
    db: Session = Depends(get_db)
):
    """Get count of partners pending approval (MANAGER+ only)"""
    
    count = db.query(Partner).filter(Partner.workflow_stage == WorkflowStage.PENDING_APPROVAL).count()
    
    return {
        "pending_approvals": count,
        "message": f"There are {count} partners pending approval"
    }