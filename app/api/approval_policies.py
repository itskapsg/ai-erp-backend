"""
Approval Policies API

Provides endpoints to manage dynamic approval policies.
Allows toggling approval rules without code changes.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApprovalPolicy, UserRole


router = APIRouter()


# Pydantic Models
class ApprovalPolicyResponse(BaseModel):
    id: UUID
    resource: str
    action: str
    is_active: bool
    required_role: UserRole
    
    class Config:
        from_attributes = True


class ApprovalPolicyCreate(BaseModel):
    resource: str
    action: str
    is_active: bool = True
    required_role: UserRole


class ApprovalPolicyUpdate(BaseModel):
    is_active: Optional[bool] = None
    required_role: Optional[UserRole] = None


class PolicyCheckRequest(BaseModel):
    resource: str
    action: str


class PolicyCheckResponse(BaseModel):
    requires_approval: bool
    required_role: Optional[UserRole] = None
    policy_id: Optional[UUID] = None


@router.get("/", response_model=List[ApprovalPolicyResponse])
def get_approval_policies(
    resource: Optional[str] = None,
    action: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all approval policies with optional filtering."""
    query = db.query(ApprovalPolicy)
    
    if resource:
        query = query.filter(ApprovalPolicy.resource == resource)
    if action:
        query = query.filter(ApprovalPolicy.action == action)
    if is_active is not None:
        query = query.filter(ApprovalPolicy.is_active == is_active)
    
    policies = query.order_by(ApprovalPolicy.resource, ApprovalPolicy.action).all()
    return policies


@router.post("/", response_model=ApprovalPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_approval_policy(
    policy_data: ApprovalPolicyCreate,
    db: Session = Depends(get_db)
):
    """Create a new approval policy."""
    # Check if policy already exists
    existing = db.query(ApprovalPolicy).filter_by(
        resource=policy_data.resource,
        action=policy_data.action
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy for {policy_data.resource}.{policy_data.action} already exists"
        )
    
    policy = ApprovalPolicy(**policy_data.dict())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy


@router.get("/{policy_id}", response_model=ApprovalPolicyResponse)
def get_approval_policy(policy_id: UUID, db: Session = Depends(get_db)):
    """Get a specific approval policy by ID."""
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval policy not found"
        )
    
    return policy


@router.patch("/{policy_id}", response_model=ApprovalPolicyResponse)
def update_approval_policy(
    policy_id: UUID,
    policy_update: ApprovalPolicyUpdate,
    db: Session = Depends(get_db)
):
    """Update an approval policy (typically to toggle is_active)."""
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval policy not found"
        )
    
    # Update fields
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    db.commit()
    db.refresh(policy)
    
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval_policy(policy_id: UUID, db: Session = Depends(get_db)):
    """Delete an approval policy."""
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval policy not found"
        )
    
    db.delete(policy)
    db.commit()


@router.post("/check", response_model=PolicyCheckResponse)
def check_approval_required(
    check_request: PolicyCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if approval is required for a specific resource/action combination.
    
    This is the core API that implements the logic:
    'Check Rulebook → If Rule exists, Require Approval → Else Auto-Approve'
    """
    result = ApprovalPolicy.requires_approval(
        db, 
        check_request.resource, 
        check_request.action
    )
    
    return PolicyCheckResponse(
        requires_approval=result['requires_approval'],
        required_role=result['required_role'],
        policy_id=result['policy'].id if result['policy'] else None
    )


@router.post("/{policy_id}/toggle", response_model=ApprovalPolicyResponse)
def toggle_approval_policy(policy_id: UUID, db: Session = Depends(get_db)):
    """Toggle the is_active status of an approval policy."""
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval policy not found"
        )
    
    # Toggle the active status
    policy.is_active = not policy.is_active
    db.commit()
    db.refresh(policy)
    
    return policy