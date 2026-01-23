#!/usr/bin/env python3
"""
Seed Default Approval Rules Script

This script inserts default approval policies into the database.
It demonstrates how to configure approval rules without changing code.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import ApprovalPolicy, UserRole


def init_default_rules():
    """Initialize default approval rules in the database"""
    
    # Database connection (use SQLite for testing if PostgreSQL not available)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        # Check if rules already exist
        existing_rule = session.query(ApprovalPolicy).filter_by(
            resource='partner', 
            action='create'
        ).first()
        
        if existing_rule:
            print("✅ Default approval rules already exist!")
            print(f"   Partner creation rule: {existing_rule}")
            return
        
        # Create default approval policies
        default_policies = [
            ApprovalPolicy(
                resource='partner',
                action='create',
                is_active=True,
                required_role=UserRole.ADMIN
            ),
            ApprovalPolicy(
                resource='partner',
                action='update',
                is_active=True,
                required_role=UserRole.MANAGER
            ),
            ApprovalPolicy(
                resource='partner',
                action='delete',
                is_active=True,
                required_role=UserRole.ADMIN
            )
        ]
        
        # Add policies to session
        for policy in default_policies:
            session.add(policy)
        
        # Commit changes
        session.commit()
        
        print("🎉 Default approval rules created successfully!")
        print("\n📋 Created Rules:")
        for policy in default_policies:
            print(f"   • {policy.resource}.{policy.action} -> Requires {policy.required_role.value} approval")
        
        print("\n💡 Meaning:")
        print("   • Creating a new Partner requires Admin approval")
        print("   • Updating a Partner requires Manager approval") 
        print("   • Deleting a Partner requires Admin approval")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating default rules: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Initializing Default Approval Rules...")
    init_default_rules()
    print("✨ Done!")