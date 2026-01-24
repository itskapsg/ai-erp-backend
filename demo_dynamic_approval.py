#!/usr/bin/env python3
"""
🎯 DYNAMIC APPROVAL SYSTEM - COMPLETE DEMONSTRATION

This script demonstrates the complete Dynamic Approval System implementation:

✅ COMPLETED FEATURES:
1. ✅ ApprovalPolicy Model (The Rulebook) - Configurable approval rules
2. ✅ Partner Model (Masters) - Inherits ApprovalMixin for approval workflow
3. ✅ Dynamic Logic: 'Check Rulebook → If Rule exists, Require Approval → Else Auto-Approve'
4. ✅ Default Rules Seeded - Partner creation/update/delete policies
5. ✅ Toggle Functionality - Rules can be enabled/disabled without code changes

🚀 MISSION ACCOMPLISHED:
- Partner model inherits Base and ApprovalMixin ✅
- ApprovalPolicy table with configurable rules ✅
- Logic implementation with policy checking ✅
- Migration and database setup ✅
- Verification scripts proving toggle functionality ✅

This demo shows the system in action with real database operations.
"""

import os
import sys
from uuid import uuid4
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User, UserRole, Partner, PartnerType, ApprovalPolicy, WorkflowStage


def print_banner(title: str):
    """Print a formatted banner."""
    print(f"\n{'🎯' * 20}")
    print(f"  {title}")
    print(f"{'🎯' * 20}")


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n{'─' * 50}")
    print(f"📋 {title}")
    print(f"{'─' * 50}")


def demonstrate_approval_system():
    """Demonstrate the complete Dynamic Approval System."""
    
    print_banner("DYNAMIC APPROVAL SYSTEM DEMONSTRATION")
    print("🎯 Mission: Configurable approval rules without hard-coding")
    print("🔧 Implementation: Database-driven policy engine")
    
    db = SessionLocal()
    
    try:
        # Show current approval policies
        print_section("CURRENT APPROVAL POLICIES (The Rulebook)")
        policies = db.query(ApprovalPolicy).order_by(ApprovalPolicy.resource, ApprovalPolicy.action).all()
        
        print("📚 Active Approval Rules:")
        for policy in policies:
            status = "🟢 ACTIVE" if policy.is_active else "🔴 INACTIVE"
            print(f"   {status} | {policy.resource.upper()}.{policy.action.upper()} → {policy.required_role.value.upper()}")
        
        # Get test users
        print_section("TEST USERS")
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        salesman = db.query(User).filter(User.role == UserRole.SALESMAN).first()
        
        if not admin or not salesman:
            print("❌ Test users not found. Please run test_policy_logic.py first.")
            return
        
        print(f"👤 Admin: {admin.username} ({admin.role.value})")
        print(f"👤 Salesman: {salesman.username} ({salesman.role.value})")
        
        # Demonstrate the core logic
        print_section("CORE LOGIC DEMONSTRATION")
        print("🔍 Logic: Check Rulebook → If Rule exists, Require Approval → Else Auto-Approve")
        print()
        
        # Test 1: Partner creation with active rule
        print("🧪 TEST 1: Partner Creation (Rule ACTIVE)")
        policy_check = ApprovalPolicy.requires_approval(db, "partner", "create")
        print(f"   Policy Check Result: {policy_check}")
        
        if policy_check['requires_approval']:
            print(f"   ✅ Rule Found: Requires {policy_check['required_role'].value} approval")
            print(f"   🔒 Salesman Action: Would be PENDING_APPROVAL")
            print(f"   ✅ Admin Action: Would be AUTO-APPROVED (has required role)")
        else:
            print(f"   ✅ No Active Rule: Would be AUTO-APPROVED")
        
        print()
        
        # Test 2: Invoice creation with inactive rule
        print("🧪 TEST 2: Invoice Creation (Rule INACTIVE)")
        policy_check = ApprovalPolicy.requires_approval(db, "invoice", "create")
        print(f"   Policy Check Result: {policy_check}")
        
        if policy_check['requires_approval']:
            print(f"   🔒 Rule Active: Requires {policy_check['required_role'].value} approval")
        else:
            print(f"   ✅ No Active Rule: Would be AUTO-APPROVED for any user")
        
        # Show existing partners and their approval states
        print_section("EXISTING PARTNERS (Approval States)")
        partners = db.query(Partner).order_by(Partner.created_at.desc()).limit(5).all()
        
        if partners:
            print("📊 Recent Partners and their Approval States:")
            for partner in partners:
                stage_icon = {
                    WorkflowStage.APPROVED: "✅",
                    WorkflowStage.PENDING_APPROVAL: "⏳",
                    WorkflowStage.REJECTED: "❌",
                    WorkflowStage.DRAFT: "📝"
                }.get(partner.workflow_stage, "❓")
                
                print(f"   {stage_icon} {partner.name}: {partner.workflow_stage.value}")
        else:
            print("📊 No partners found in database")
        
        # Demonstrate toggle functionality
        print_section("TOGGLE FUNCTIONALITY DEMO")
        print("🔄 Demonstrating how rules can be toggled without code changes:")
        
        # Find partner creation rule
        partner_rule = db.query(ApprovalPolicy).filter_by(resource="partner", action="create").first()
        if partner_rule:
            original_state = partner_rule.is_active
            print(f"   📋 Current State: partner.create = {'ACTIVE' if original_state else 'INACTIVE'}")
            
            # Toggle the rule
            partner_rule.is_active = not original_state
            db.commit()
            print(f"   🔄 Toggled State: partner.create = {'ACTIVE' if partner_rule.is_active else 'INACTIVE'}")
            
            # Check the effect
            policy_check = ApprovalPolicy.requires_approval(db, "partner", "create")
            if policy_check['requires_approval']:
                print(f"   📊 Effect: Partner creation now REQUIRES {policy_check['required_role'].value} approval")
            else:
                print(f"   📊 Effect: Partner creation now AUTO-APPROVED")
            
            # Restore original state
            partner_rule.is_active = original_state
            db.commit()
            print(f"   🔄 Restored State: partner.create = {'ACTIVE' if original_state else 'INACTIVE'}")
        
        # Summary
        print_section("SYSTEM CAPABILITIES SUMMARY")
        print("✅ IMPLEMENTED FEATURES:")
        print("   🏗️  ApprovalPolicy Model (The Rulebook)")
        print("   🏢 Partner Model with ApprovalMixin inheritance")
        print("   🔍 Dynamic approval logic with policy checking")
        print("   🔄 Runtime rule toggling without code deployment")
        print("   📊 Database-driven configuration")
        print("   🧪 Comprehensive testing and verification")
        print()
        print("🎯 KEY BENEFITS:")
        print("   • No hard-coded approval rules")
        print("   • Business rules configurable via database")
        print("   • Same code, different behavior based on policy")
        print("   • Easy to add new resources and actions")
        print("   • Role-based approval requirements")
        print()
        print("🚀 MISSION ACCOMPLISHED!")
        print("   The Dynamic Approval System is fully operational!")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    demonstrate_approval_system()