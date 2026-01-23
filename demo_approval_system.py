#!/usr/bin/env python3
"""
Dynamic Approval System Demo

This script demonstrates the complete Dynamic Approval System functionality:
1. Configurable approval policies
2. Role-based approval logic
3. Dynamic policy toggling
4. Workflow stage management
"""

import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import User, Partner, PartnerType, UserRole, WorkflowStage, ApprovalPolicy
from app.services.approval_service import ApprovalService


def create_test_users(session):
    """Create test users with different roles"""
    users = {}
    
    user_data = [
        ('admin_user', 'admin@test.com', UserRole.ADMIN),
        ('manager_user', 'manager@test.com', UserRole.MANAGER),
        ('accountant_user', 'accountant@test.com', UserRole.ACCOUNTANT),
        ('salesman_user', 'salesman@test.com', UserRole.SALESMAN),
    ]
    
    for username, email, role in user_data:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, role=role)
            user.set_password('password123')
            session.add(user)
        users[role] = user
    
    session.commit()
    return users


def demo_role_hierarchy(approval_service, users):
    """Demonstrate role hierarchy in approval decisions"""
    print("\n🏆 ROLE HIERARCHY DEMONSTRATION")
    print("=" * 60)
    
    # Test each user role against partner creation (requires ADMIN)
    for role, user in users.items():
        requires_approval, required_role = approval_service.check_approval_required('partner', 'create', user)
        workflow_stage = approval_service.determine_workflow_stage('partner', 'create', user)
        
        print(f"👤 {user.username} ({role.value}):")
        print(f"   📋 Requires Approval: {requires_approval}")
        print(f"   ⚡ Workflow Stage: {workflow_stage.value}")
        
        if role == UserRole.ADMIN:
            print("   ✅ Admin can auto-approve (sufficient privileges)")
        else:
            print("   🔄 Requires admin approval (insufficient privileges)")
        print()


def demo_policy_management(session, approval_service):
    """Demonstrate dynamic policy management"""
    print("\n🔧 POLICY MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    
    # Show current policies
    print("📋 Current Active Policies:")
    policies = approval_service.get_active_policies()
    for policy in policies:
        print(f"   • {policy.resource}.{policy.action} -> {policy.required_role.value} (Active: {policy.is_active})")
    
    # Create a new policy
    print("\n➕ Creating new policy: partner.delete -> MANAGER")
    new_policy = ApprovalPolicy(
        resource='partner',
        action='delete',
        is_active=True,
        required_role=UserRole.MANAGER
    )
    session.add(new_policy)
    session.commit()
    
    # Toggle existing policy
    print("🔄 Toggling partner.create policy OFF")
    approval_service.toggle_policy('partner', 'create', False)
    
    print("📋 Updated Policies:")
    policies = approval_service.get_active_policies()
    for policy in policies:
        print(f"   • {policy.resource}.{policy.action} -> {policy.required_role.value} (Active: {policy.is_active})")
    
    # Toggle back
    print("\n🔄 Toggling partner.create policy back ON")
    approval_service.toggle_policy('partner', 'create', True)


def demo_partner_creation_scenarios(session, approval_service, users):
    """Demonstrate partner creation with different scenarios"""
    print("\n🏢 PARTNER CREATION SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        ("Admin creates partner", users[UserRole.ADMIN]),
        ("Manager creates partner", users[UserRole.MANAGER]),
        ("Salesman creates partner", users[UserRole.SALESMAN]),
    ]
    
    partners_created = []
    
    for scenario_name, user in scenarios:
        print(f"\n📝 {scenario_name}:")
        
        # Check approval requirements
        requires_approval, required_role = approval_service.check_approval_required('partner', 'create', user)
        workflow_stage = approval_service.determine_workflow_stage('partner', 'create', user)
        
        print(f"   👤 User: {user.username} ({user.role.value})")
        print(f"   📋 Requires Approval: {requires_approval}")
        print(f"   ⚡ Initial Stage: {workflow_stage.value}")
        
        # Create partner
        partner_name = f"Partner by {user.role.value}"
        partner = Partner(
            name=partner_name,
            type=PartnerType.CUSTOMER,
            gst_number=f"27DEMO{len(partners_created):04d}F1Z5",
            credit_limit=Decimal('100000.00'),
            workflow_stage=workflow_stage
        )
        
        session.add(partner)
        session.commit()
        partners_created.append(partner)
        
        print(f"   ✅ Partner '{partner.name}' created with status: {partner.workflow_stage.value}")
    
    return partners_created


def demo_approval_workflow(session, partners, users):
    """Demonstrate the approval workflow"""
    print("\n✅ APPROVAL WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    # Find a partner that needs approval
    pending_partner = None
    for partner in partners:
        if partner.workflow_stage == WorkflowStage.PENDING_APPROVAL:
            pending_partner = partner
            break
    
    if not pending_partner:
        print("No partners pending approval found.")
        return
    
    admin_user = users[UserRole.ADMIN]
    
    print(f"📋 Partner '{pending_partner.name}' is pending approval")
    print(f"   Current Stage: {pending_partner.workflow_stage.value}")
    
    # Approve the partner
    print(f"\n✅ Admin '{admin_user.username}' approves the partner")
    pending_partner.approve(admin_user)
    session.commit()
    
    print(f"   New Stage: {pending_partner.workflow_stage.value}")
    print(f"   Approved By: {pending_partner.approved_by.username}")
    
    # Demonstrate rejection
    print(f"\n❌ Demonstrating rejection workflow...")
    
    # Create another partner for rejection demo
    reject_partner = Partner(
        name="Partner for Rejection Demo",
        type=PartnerType.SUPPLIER,
        gst_number="27REJECT001F1Z5",
        credit_limit=Decimal('50000.00'),
        workflow_stage=WorkflowStage.PENDING_APPROVAL
    )
    session.add(reject_partner)
    session.commit()
    
    print(f"📋 Partner '{reject_partner.name}' created for rejection demo")
    
    # Reject the partner
    reject_partner.reject(admin_user, "Incomplete documentation")
    session.commit()
    
    print(f"   Status: {reject_partner.workflow_stage.value}")
    print(f"   Rejected By: {reject_partner.approved_by.username}")
    print(f"   Reason: {reject_partner.rejection_reason}")


def main():
    """Run the complete demonstration"""
    print("🚀 DYNAMIC APPROVAL SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Database setup
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        # Create test users
        print("🔧 Setting up test users...")
        users = create_test_users(session)
        
        # Initialize approval service
        approval_service = ApprovalService(session)
        
        # Run demonstrations
        demo_role_hierarchy(approval_service, users)
        demo_policy_management(session, approval_service)
        partners = demo_partner_creation_scenarios(session, approval_service, users)
        demo_approval_workflow(session, partners, users)
        
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("✅ Dynamic Approval System Features Demonstrated:")
        print("   • Configurable approval policies (The Rulebook)")
        print("   • Role-based approval logic")
        print("   • Dynamic policy toggling")
        print("   • Automatic workflow stage determination")
        print("   • Complete approval/rejection workflow")
        print("\n💡 Key Benefits:")
        print("   • No code changes needed to modify approval rules")
        print("   • Flexible role hierarchy")
        print("   • Complete audit trail")
        print("   • Easy policy management")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during demonstration: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()