#!/usr/bin/env python3
"""
Dynamic Approval System - Rule Initialization Script

This script seeds the ApprovalPolicy table with default rules.
It demonstrates how approval rules can be configured without changing code.

Usage: python init_rules.py
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the workspace to the Python path
sys.path.append('/workspace')

from app.models.core import ApprovalPolicy, UserRole


def init_default_rules():
    """Initialize default approval rules in the database"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://erp_admin:db_password_123@localhost/erp_dev_db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        print("🔧 Initializing Dynamic Approval System Rules...")
        print("=" * 50)
        
        # Check if rules already exist
        existing_rules = session.query(ApprovalPolicy).count()
        if existing_rules > 0:
            print(f"⚠️  Found {existing_rules} existing rules. Clearing old rules...")
            session.query(ApprovalPolicy).delete()
            session.commit()
        
        # Default Rules to Insert
        default_rules = [
            {
                "resource": "partner",
                "action": "create",
                "is_active": True,
                "required_role": UserRole.ADMIN,
                "description": "Creating a new Partner requires Admin approval"
            },
            {
                "resource": "partner", 
                "action": "update",
                "is_active": True,
                "required_role": UserRole.MANAGER,
                "description": "Updating Partner details requires Manager approval"
            },
            {
                "resource": "partner",
                "action": "delete", 
                "is_active": True,
                "required_role": UserRole.ADMIN,
                "description": "Deleting a Partner requires Admin approval"
            },
            {
                "resource": "invoice",
                "action": "create",
                "is_active": False,  # Disabled by default
                "required_role": UserRole.ACCOUNTANT,
                "description": "Invoice creation approval (currently disabled)"
            },
            {
                "resource": "order",
                "action": "create", 
                "is_active": False,  # Disabled by default
                "required_role": UserRole.MANAGER,
                "description": "Order creation approval (currently disabled)"
            }
        ]
        
        # Insert rules
        rules_created = 0
        for rule_data in default_rules:
            rule = ApprovalPolicy(
                resource=rule_data["resource"],
                action=rule_data["action"],
                is_active=rule_data["is_active"],
                required_role=rule_data["required_role"]
            )
            session.add(rule)
            rules_created += 1
            
            status = "🟢 ACTIVE" if rule_data["is_active"] else "🔴 INACTIVE"
            print(f"✅ {status} | {rule_data['resource'].upper()}.{rule_data['action'].upper()} → {rule_data['required_role'].value.upper()}")
            print(f"   📝 {rule_data['description']}")
            print()
        
        # Commit all rules
        session.commit()
        
        print("=" * 50)
        print(f"🎉 Successfully created {rules_created} approval rules!")
        print()
        print("📋 Rule Summary:")
        print("   • Partner Creation: REQUIRES ADMIN APPROVAL")
        print("   • Partner Updates: REQUIRES MANAGER APPROVAL") 
        print("   • Partner Deletion: REQUIRES ADMIN APPROVAL")
        print("   • Invoice Creation: AUTO-APPROVED (rule disabled)")
        print("   • Order Creation: AUTO-APPROVED (rule disabled)")
        print()
        print("🔧 To toggle rules: Update 'is_active' field in approval_policies table")
        print("🧪 Test with: python test_policy_logic.py")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating default rules: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Initializing Dynamic Approval System...")
    init_default_rules()
    print("✨ Done!")