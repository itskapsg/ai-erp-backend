import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship
import bcrypt

Base = declarative_base()

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    SALESMAN = "salesman"

class WorkflowStage(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SALESMAN)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def set_password(self, password: str):
        """Hash and set the password"""
        # Ensure password is not longer than 72 bytes for bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash"""
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        return bcrypt.checkpw(password_bytes, self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}')>"

class ApprovalMixin:
    """
    The Maker-Checker Engine: Abstract Mixin for approval workflow
    Any table that inherits this will have approval capabilities
    """
    
    @declared_attr
    def workflow_stage(cls):
        return Column(SQLEnum(WorkflowStage), default=WorkflowStage.DRAFT, nullable=False)
    
    @declared_attr
    def approved_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    @declared_attr
    def approved_by(cls):
        return relationship("User", foreign_keys=[cls.approved_by_id])
    
    @declared_attr
    def rejection_reason(cls):
        return Column(Text, nullable=True)
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def approve(self, approved_by_user: User):
        """Approve this record"""
        self.workflow_stage = WorkflowStage.APPROVED
        self.approved_by_id = approved_by_user.id
        self.rejection_reason = None
        self.updated_at = datetime.utcnow()
    
    def reject(self, rejected_by_user: User, reason: str):
        """Reject this record with a reason"""
        self.workflow_stage = WorkflowStage.REJECTED
        self.approved_by_id = rejected_by_user.id
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
    
    def submit_for_approval(self):
        """Submit for approval (move from DRAFT to PENDING_APPROVAL)"""
        self.workflow_stage = WorkflowStage.PENDING_APPROVAL
        self.updated_at = datetime.utcnow()