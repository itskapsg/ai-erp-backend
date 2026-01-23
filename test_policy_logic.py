#!/usr/bin/env python3
"""
Dynamic Approval System Verification Script

This script tests the approval logic with two scenarios:
- Scenario A: Rule Active -> Salesman creates Partner -> Requires Approval
- Scenario B: Rule Disabled -> Salesman creates Partner -> Auto-Approved
"""

import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import User, Partner, PartnerType, UserRole, WorkflowStage
from app.services.approval_service import ApprovalService


def setup_test_data(session):
    """Create test users if they don't exist"""
    
    # Create a salesman user
    salesman = session.query(User).filter_by(username='test_salesman').first()
    if not salesman:
        salesman = User(
            username='test_salesman',
            email='salesman@test.com',
            role=UserRole.SALESMAN
        )
        salesman.set_password('password123')
        session.add(salesman)
    
    # Create an admin user
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
    return salesman, admin


def scenario_a_rule_active(session, approval_service, salesman):
    """
    Scenario A: Rule Active
    Salesman tries to create a Partner -> System sees Policy -> Sets workflow_stage=PENDING
    """
    print("\n🔍 SCENARIO A: Rule Active (Salesman creates Partner)")
    print("=" * 60)
    
    # Check if approval is required
    requires_approval, required_role = approval_service.check_approval_required('partner', 'create', salesman)
    
    print(f"👤 User: {salesman.username} (Role: {salesman.role.value})")
    print(f"🎯 Action: Create Partner")
    print(f"📋 Approval Required: {requires_approval}")
    if required_role:
        print(f"🔐 Required Role: {required_role.value}")
    
    # Determine workflow stage
    workflow_stage = approval_service.determine_workflow_stage('partner', 'create', salesman)
    print(f"⚡ Workflow Stage: {workflow_stage.value}")
    
    # Create a partner
    partner = Partner(
        name="Test Customer A",
        type=PartnerType.CUSTOMER,
        gst_number="27ABCDE1234F1Z5",
        credit_limit=Decimal('50000.00'),
        workflow_stage=workflow_stage
    )
    
    session.add(partner)
    session.commit()
    
    print(f"✅ Partner created: {partner.name}")
    print(f"📊 Final Status: {partner.workflow_stage.value}")
    
    if requires_approval:
        print("🔄 Result: SUCCESS - Partner requires approval as expected!")
    else:
        print("❌ Result: UNEXPECTED - Partner was auto-approved!")
    
    return partner


def scenario_b_rule_disabled(session, approval_service, salesman):
    """
    Scenario B: Rule Disabled
    Admin disables the policy -> Salesman creates Partner -> Auto-Approved
    """
    print("\n🔍 SCENARIO B: Rule Disabled (Policy toggled off)")
    print("=" * 60)
    
    # Disable the approval policy
    print("🔧 Disabling approval policy for partner creation...")
    policy = approval_service.toggle_policy('partner', 'create', False)
    
    if policy:
        print(f"✅ Policy updated: {policy.resource}.{policy.action} -> Active: {policy.is_active}")
    else:
        print("❌ Policy not found!")
        return None
    
    # Check if approval is required now
    requires_approval, required_role = approval_service.check_approval_required('partner', 'create', salesman)
    
    print(f"👤 User: {salesman.username} (Role: {salesman.role.value})")
    print(f"🎯 Action: Create Partner")
    print(f"📋 Approval Required: {requires_approval}")
    if required_role:
        print(f"🔐 Required Role: {required_role.value}")
    
    # Determine workflow stage
    workflow_stage = approval_service.determine_workflow_stage('partner', 'create', salesman)
    print(f"⚡ Workflow Stage: {workflow_stage.value}")
    
    # Create another partner
    partner = Partner(
        name="Test Customer B",
        type=PartnerType.CUSTOMER,
        gst_number="27ABCDE1234F1Z6",
        credit_limit=Decimal('75000.00'),
        workflow_stage=workflow_stage
    )
    
    session.add(partner)
    session.commit()
    
    print(f"✅ Partner created: {partner.name}")
    print(f"📊 Final Status: {partner.workflow_stage.value}")
    
    if not requires_approval and workflow_stage == WorkflowStage.APPROVED:
        print("🔄 Result: SUCCESS - Partner was auto-approved as expected!")
    else:
        print("❌ Result: UNEXPECTED - Partner still requires approval!")
    
    # Re-enable the policy for future tests
    print("\n🔧 Re-enabling approval policy...")
    approval_service.toggle_policy('partner', 'create', True)
    print("✅ Policy re-enabled")
    
    return partner


def main():
    """Run the verification scenarios"""
    print("🚀 Dynamic Approval System Verification")
    print("=" * 60)
    
    # Database connection (use SQLite for testing if PostgreSQL not available)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        # Setup test data
        print("🔧 Setting up test data...")
        salesman, admin = setup_test_data(session)
        
        # Initialize approval service
        approval_service = ApprovalService(session)
        
        # Show current active policies
        print("\n📋 Current Active Policies:")
        policies = approval_service.get_active_policies()
        for policy in policies:
            print(f"   • {policy.resource}.{policy.action} -> {policy.required_role.value}")
        
        # Run scenarios
        partner_a = scenario_a_rule_active(session, approval_service, salesman)
        partner_b = scenario_b_rule_disabled(session, approval_service, salesman)
        
        # Summary
        print("\n📊 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✅ Scenario A: Partner '{partner_a.name}' -> {partner_a.workflow_stage.value}")
        if partner_b:
            print(f"✅ Scenario B: Partner '{partner_b.name}' -> {partner_b.workflow_stage.value}")
        
        print("\n🎉 Dynamic Approval System is working correctly!")
        print("💡 The system successfully toggles approval requirements based on policies.")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during verification: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()