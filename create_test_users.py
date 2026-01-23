#!/usr/bin/env python3
"""
Create Test Users for API Testing

Creates users with different roles for testing the API endpoints.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import User, UserRole


def create_test_users():
    """Create test users with different roles"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        # Test users data
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@erp.com',
                'role': UserRole.ADMIN,
                'password': 'admin123'
            },
            {
                'username': 'manager',
                'email': 'manager@erp.com',
                'role': UserRole.MANAGER,
                'password': 'manager123'
            },
            {
                'username': 'accountant',
                'email': 'accountant@erp.com',
                'role': UserRole.ACCOUNTANT,
                'password': 'accountant123'
            },
            {
                'username': 'salesman',
                'email': 'salesman@erp.com',
                'role': UserRole.SALESMAN,
                'password': 'salesman123'
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = session.query(User).filter_by(username=user_data['username']).first()
            
            if existing_user:
                print(f"✅ User '{user_data['username']}' already exists")
                created_users.append(existing_user)
                continue
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            
            session.add(user)
            created_users.append(user)
            print(f"➕ Created user '{user_data['username']}' with role '{user_data['role'].value}'")
        
        session.commit()
        
        print("\n🎉 Test users setup complete!")
        print("\n👥 Available Test Users:")
        print("=" * 50)
        
        for user_data in test_users:
            print(f"Username: {user_data['username']}")
            print(f"Password: {user_data['password']}")
            print(f"Role: {user_data['role'].value}")
            print(f"Email: {user_data['email']}")
            print("-" * 30)
        
        print("\n💡 Usage:")
        print("1. Start the API server: python app/main.py --port 54279")
        print("2. Login to get JWT token: POST /api/v1/auth/token")
        print("3. Use token in Authorization header: Bearer <token>")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating test users: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Creating Test Users for API...")
    create_test_users()
    print("✨ Done!")