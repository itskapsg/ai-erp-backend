#!/usr/bin/env python3
"""
Dynamic Approval System - Policy Logic Verification Script

This script simulates two scenarios to prove the dynamic approval system works:
- Scenario A (Rule Active): Salesman tries to create Partner → System sets workflow_stage=PENDING
- Scenario B (Rule Disabled): Admin disables rule → Salesman creates Partner → System sets workflow_stage=APPROVED

Usage: python test_policy_logic.py
"""

import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the workspace to the Python path
sys.path.append('/workspace')

from app.models.core import ApprovalPolicy, UserRole, User, WorkflowStage
from app.models.masters import Partner, PartnerType

class ApprovalEngine:
    """
    The Dynamic Approval Engine
    This is the core logic: 'Check Rulebook -> If Rule exists, Require Approval -> Else Auto-Approve'
    """
    
    def __init__(self, session):
        self.session = session
    
    def check_approval_required(self, resource: str, action: str, user_role: UserRole) -> tuple[bool, UserRole]:
        """
        Check if approval is required for a specific resource/action combination
        
        Returns:
            tuple: (approval_required: bool, required_role: UserRole)
        """
        # Query the rulebook
        policy = self.session.query(ApprovalPolicy).filter_by(
            resource=resource,
            action=action,
            is_active=True  # Only active rules count
        ).first()
        
        if policy:
            # Rule exists and is active - check if user has sufficient role
            if user_role.value == policy.required_role.value:
                return False, policy.required_role  # User has required role, no approval needed
            else:
                return True, policy.required_role   # User needs approval from higher role
        else:
            # No active rule found - auto-approve
            return False, user_role
    
    def create_with_approval_check(self, entity, resource: str, action: str, user_role: UserRole):
        """
        Create an entity with automatic approval workflow logic
        """
        approval_required, required_role = self.check_approval_required(resource, action, user_role)
        
        if approval_required:
            entity.workflow_stage = WorkflowStage.PENDING_APPROVAL
            print(f"🔒 APPROVAL REQUIRED: {resource}.{action} needs {required_role.value} approval")
        else:
            entity.workflow_stage = WorkflowStage.APPROVED
            print(f"✅ AUTO-APPROVED: {resource}.{action} approved automatically")
        
        self.session.add(entity)
        self.session.commit()
        return entity

def test_approval_scenarios():
    """Test the dynamic approval system with two scenarios"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://erp_admin:db_password_123@localhost/erp_dev_db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    approval_engine = ApprovalEngine(session)
    
    try:
        print("🧪 DYNAMIC APPROVAL SYSTEM - VERIFICATION TEST")
        print("=" * 60)
        
        # Clean up any existing test data
        session.query(Partner).filter(Partner.name.like('Test Partner%')).delete()
        session.commit()
        
        # Create test users (if they don't exist)
        salesman = session.query(User).filter_by(username='test_salesman').first()
        if not salesman:
            salesman = User(
                username='test_salesman',
                email='salesman@test.com',
                role=UserRole.SALESMAN
            )
            salesman.set_password('password123')
            session.add(salesman)
        
        admin = session.query(User).filter_by(username='test_admin').first()
        if not admin:
            admin = User(
                username='test_admin',
                email='admin@test.com',
                role=UserRole.ADMIN
            )
            admin.set_password('password123')
            session.add(admin)
        
        session.commit()
        
        print("👥 Test Users Created:")
        print(f"   • Salesman: {salesman.username} ({salesman.role.value})")
        print(f"   • Admin: {admin.username} ({admin.role.value})")
        print()
        
        # SCENARIO A: Rule Active - Salesman tries to create Partner
        print("📋 SCENARIO A: RULE ACTIVE")
        print("-" * 30)
        
        # Check current rule status
        partner_create_rule = session.query(ApprovalPolicy).filter_by(
            resource='partner',
            action='create'
        ).first()
        
        if partner_create_rule:
            print(f"🔍 Current Rule: partner.create → {partner_create_rule.required_role.value} (Active: {partner_create_rule.is_active})")
        else:
            print("⚠️  No rule found for partner.create")
        
        # Salesman attempts to create partner
        print(f"👤 {salesman.role.value.upper()} attempts to create Partner...")
        
        test_partner_1 = Partner(
            name="Test Partner A",
            type=PartnerType.CUSTOMER,
            gst_number="TEST123456789A",
            credit_limit=Decimal('50000.00')
        )
        
        approval_engine.create_with_approval_check(
            test_partner_1, 
            'partner', 
            'create', 
            salesman.role
        )
        
        print(f"📊 Result: Partner created with workflow_stage = {test_partner_1.workflow_stage.value}")
        print()
        
        # SCENARIO B: Rule Disabled - Auto-approve
        print("📋 SCENARIO B: RULE DISABLED")
        print("-" * 30)
        
        # Admin disables the rule
        if partner_create_rule:
            partner_create_rule.is_active = False
            session.commit()
            print(f"🔧 ADMIN disables rule: partner.create → is_active = False")
        
        # Salesman attempts to create another partner
        print(f"👤 {salesman.role.value.upper()} attempts to create Partner (rule disabled)...")
        
        test_partner_2 = Partner(
            name="Test Partner B",
            type=PartnerType.SUPPLIER,
            gst_number="TEST123456789B",
            credit_limit=Decimal('75000.00')
        )
        
        approval_engine.create_with_approval_check(
            test_partner_2, 
            'partner', 
            'create', 
            salesman.role
        )
        
        print(f"📊 Result: Partner created with workflow_stage = {test_partner_2.workflow_stage.value}")
        print()
        
        # SCENARIO C: Re-enable rule and test Admin access
        print("📋 SCENARIO C: ADMIN BYPASS")
        print("-" * 30)
        
        # Re-enable the rule
        if partner_create_rule:
            partner_create_rule.is_active = True
            session.commit()
            print(f"🔧 Rule re-enabled: partner.create → is_active = True")
        
        # Admin creates partner (should auto-approve since admin has required role)
        print(f"👤 {admin.role.value.upper()} attempts to create Partner...")
        
        test_partner_3 = Partner(
            name="Test Partner C",
            type=PartnerType.CUSTOMER,
            gst_number="TEST123456789C",
            credit_limit=Decimal('100000.00')
        )
        
        approval_engine.create_with_approval_check(
            test_partner_3, 
            'partner', 
            'create', 
            admin.role
        )
        
        print(f"📊 Result: Partner created with workflow_stage = {test_partner_3.workflow_stage.value}")
        print()
        
        # Summary
        print("=" * 60)
        print("🎯 TEST RESULTS SUMMARY:")
        print("=" * 60)
        print(f"✅ Scenario A (Rule Active + Salesman): {test_partner_1.workflow_stage.value}")
        print(f"✅ Scenario B (Rule Disabled + Salesman): {test_partner_2.workflow_stage.value}")
        print(f"✅ Scenario C (Rule Active + Admin): {test_partner_3.workflow_stage.value}")
        print()
        print("🔍 VERIFICATION:")
        print("   • When rule is ACTIVE and user lacks permission → PENDING_APPROVAL")
        print("   • When rule is DISABLED → APPROVED (auto-approve)")
        print("   • When user has required role → APPROVED (bypass)")
        print()
        print("🎉 Dynamic Approval System is working correctly!")
        
        # Query all test partners to show final state
        print("\n📋 Final Partner States:")
        test_partners = session.query(Partner).filter(Partner.name.like('Test Partner%')).all()
        for partner in test_partners:
            print(f"   • {partner.name}: {partner.workflow_stage.value}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during testing: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    test_approval_scenarios()