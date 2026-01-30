import sys
import os
from sqlalchemy import text

# Set env var for app.database to pick up
os.environ["DATABASE_URL"] = "postgresql://erp_admin:db_password_123@localhost/erp_dev_db"

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine

def check_schema():
    print(f"Connecting via engine: {engine.url}")
    with engine.connect() as conn:
        for table in ['partners', 'orders']:
            print(f"\nScanning table: {table}")
            try:
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                columns = [row[0] for row in result]
                if 'created_by_id' in columns:
                    print(f"✅ {table} has 'created_by_id'")
                else:
                    print(f"❌ {table} MISSING 'created_by_id'")
            except Exception as e:
                print(f"Error scanning {table}: {e}")

if __name__ == "__main__":
    check_schema()
