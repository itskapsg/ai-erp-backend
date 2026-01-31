
from app.database import engine
from app.models import Base
# Import all models to ensure they are registered
import app.models

def create_financial_tables():
    print("Creating Financial Schema Tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Financial Tables Created Successfully.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_financial_tables()
