import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL from app/database.py
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test_erp.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a session
db = SessionLocal()

try:
    # Execute SELECT 1
    result = db.execute(text('SELECT 1')).scalar()
    print(f'Database connection successful. Result: {result}')
except Exception as e:
    print(f'Database connection failed: {e}')
finally:
    db.close()