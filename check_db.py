import sys
import os
sys.path.append(os.getcwd())
try:
    from sqlalchemy import text
    from app.database import engine
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def check_db():
    print("Checking Database Connectivity...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database Connection: OK (SELECT 1 returned successfully)")
            return True
    except Exception as e:
        print(f"Database Connection: FAILED - {e}")
        return False

if __name__ == "__main__":
    success = check_db()
    sys.exit(0 if success else 1)