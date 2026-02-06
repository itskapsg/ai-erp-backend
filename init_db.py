#!/usr/bin/env python3
"""
Database Initialization Script
Creates a Super Admin user if the User table is empty
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.core import Base, User, UserRole

def init_database():
    """Initialize database with Super Admin user"""
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    
    if '@' in database_url:
        print(f"🔗 Connecting to database: {database_url.split('@')[1]}")
    else:
        print(f"🔗 Connecting to database: {database_url}")
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as session:
            # Check if User table is empty
            user_count = session.query(User).count()
            
            if user_count == 0:
                print("👤 User table is empty. Creating Super Admin...")
                
                # Create Super Admin
                admin_user = User(
                    username='admin',
                    email='admin@erp-system.com',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin_user.set_password('admin123')
                
                session.add(admin_user)
                session.commit()
                
                print("✅ Super Admin created successfully!")
                print("   Username: admin")
                print("   Password: admin123")
                print("   Role: ADMIN")
                print("   Email: admin@erp-system.com")
                
            else:
                print(f"👥 User table already contains {user_count} users. Skipping admin creation.")
                
                # Show existing users
                users = session.query(User).all()
                print("\n📋 Existing users:")
                for user in users:
                    print(f"   - {user.username} ({user.role.value}) - Active: {user.is_active}")
    
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    
    print("🎉 Database initialization complete!")

if __name__ == "__main__":
    init_database()