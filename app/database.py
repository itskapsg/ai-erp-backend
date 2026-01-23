"""
Database Connection and Session Management

Provides database session dependency for FastAPI endpoints.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base

# Database URL - use SQLite for testing, PostgreSQL for production
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Database session dependency for FastAPI
    
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)