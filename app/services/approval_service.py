"""
Dynamic Approval Service

This service implements the core logic:
'Check Rulebook -> If Rule exists, Require Approval -> Else Auto-Approve'
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models import ApprovalPolicy, User, UserRole, WorkflowStage


class ApprovalService:
    """
    The Dynamic Approval Engine
    
    This service checks the approval policies (rulebook) and determines
    whether a specific action requires approval or can be auto-approved.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_approval_required(self, resource: str, action: str, user: User) -> tuple[bool, Optional[UserRole]]:
        """
        Check if approval is required for a specific resource and action
        
        Args:
            resource: The resource type (e.g., 'partner')
            action: The action being performed (e.g., 'create')
            user: The user performing the action
            
        Returns:
            tuple: (requires_approval: bool, required_role: Optional[UserRole])
        """
        # Query the approval policy for this resource and action
        policy = self.db.query(ApprovalPolicy).filter_by(
            resource=resource,
            action=action,
            is_active=True
        ).first()
        
        if not policy:
            # No policy found -> Auto-approve
            return False, None
        
        # Policy exists and is active -> Check if user has required role
        if self._user_has_required_role(user, policy.required_role):
            # User has sufficient privileges -> Auto-approve
            return False, None
        else:
            # User doesn't have required role -> Requires approval
            return True, policy.required_role
    
    def determine_workflow_stage(self, resource: str, action: str, user: User) -> WorkflowStage:
        """
        Determine the initial workflow stage for a new record
        
        Args:
            resource: The resource type (e.g., 'partner')
            action: The action being performed (e.g., 'create')
            user: The user performing the action
            
        Returns:
            WorkflowStage: The initial workflow stage
        """
        requires_approval, _ = self.check_approval_required(resource, action, user)
        
        if requires_approval:
            return WorkflowStage.PENDING_APPROVAL
        else:
            return WorkflowStage.APPROVED
    
    def _user_has_required_role(self, user: User, required_role: UserRole) -> bool:
        """
        Check if user has the required role or higher privileges
        
        Role hierarchy (highest to lowest):
        ADMIN > MANAGER > ACCOUNTANT > SALESMAN
        """
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.ACCOUNTANT: 2,
            UserRole.SALESMAN: 1
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def get_active_policies(self) -> list[ApprovalPolicy]:
        """Get all active approval policies"""
        return self.db.query(ApprovalPolicy).filter_by(is_active=True).all()
    
    def toggle_policy(self, resource: str, action: str, is_active: bool) -> Optional[ApprovalPolicy]:
        """
        Toggle an approval policy on/off
        
        Args:
            resource: The resource type
            action: The action type
            is_active: Whether to activate or deactivate the policy
            
        Returns:
            The updated policy or None if not found
        """
        policy = self.db.query(ApprovalPolicy).filter_by(
            resource=resource,
            action=action
        ).first()
        
        if policy:
            policy.is_active = is_active
            self.db.commit()
            return policy
        
        return None