
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load env before importing database
load_dotenv()

from app.database import engine

def fix_enums():
    with engine.connect() as conn:
        print("Fixing Enums...")
        try:
            # Fix OrderStatus
            # Try adding Uppercase INVOICED
            conn.execute(text("ALTER TYPE orderstatus ADD VALUE 'INVOICED'"))
            print("✅ Added 'INVOICED' to orderstatus.")
        except Exception as e:
            print(f"⚠️ Could not add 'invoiced' (might exist): {e}")
            
        conn.commit()

if __name__ == "__main__":
    fix_enums()
