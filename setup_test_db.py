#!/usr/bin/env python3
"""
Test Database Setup Script

This script creates tables and initializes the database for testing
the Dynamic Approval System without requiring a full PostgreSQL setup.
"""

import os
import sys
from sqlalchemy import create_engine

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import Base


def setup_test_database():
    """Create all tables in the database"""
    
    # Use SQLite for testing if PostgreSQL is not available
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')
    
    print(f"🔧 Setting up database: {database_url}")
    
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print("\n📋 Created Tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"   • {table_name}")


if __name__ == "__main__":
    setup_test_database()