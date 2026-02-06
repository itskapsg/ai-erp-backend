
import sys
import os
import logging
from sqlalchemy import text

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_product_data():
    """
    Backfill missing mandatory fields in Product table to satisfy strict Pydantic schema.
    Fields: design_number, quality, category.
    """
    db = SessionLocal()
    try:
        logger.info("Starting Product Data Repair...")
        
        # 0. Check and Fix Schema (Add missing columns)
        # We use raw connection for schema changes to avoid transaction issues with ALTER TABLE
        connection = db.connection().connection
        cursor = connection.cursor()
        
        # Get existing columns (Generic way or Postgres specific)
        if 'postgresql' in str(db.get_bind().url):
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'products'")
            columns = [row[0] for row in cursor.fetchall()]
        else:
            # SQLite fallback
            cursor.execute("PRAGMA table_info(products)")
            columns = [info[1] for info in cursor.fetchall()]
        logger.info(f"Existing columns: {columns}")
        
        # Add design_number if missing
        if 'design_number' not in columns:
            logger.info("Adding missing column: design_number")
            cursor.execute("ALTER TABLE products ADD COLUMN design_number VARCHAR(100)")
            
        # Add quality if missing
        if 'quality' not in columns:
            logger.info("Adding missing column: quality")
            cursor.execute("ALTER TABLE products ADD COLUMN quality VARCHAR(100)")
            
        # Add category if missing
        if 'category' not in columns:
            logger.info("Adding missing column: category")
            cursor.execute("ALTER TABLE products ADD COLUMN category VARCHAR(100)")

        connection.commit() # Commit schema changes
        
        # 1. Fix NULL design_number
        result = db.execute(text("UPDATE products SET design_number = 'MISSING-DN' WHERE design_number IS NULL"))
        logger.info(f"Updated {result.rowcount} products with missing design_number.")
        
        # 2. Fix NULL quality
        result = db.execute(text("UPDATE products SET quality = 'MISSING-QUALITY' WHERE quality IS NULL"))
        logger.info(f"Updated {result.rowcount} products with missing quality.")
        
        # 3. Fix NULL category
        result = db.execute(text("UPDATE products SET category = 'Uncategorized' WHERE category IS NULL"))
        logger.info(f"Updated {result.rowcount} products with missing category.")
        
        db.commit()
        logger.info("Data Repair Completed Successfully.")
        
    except Exception as e:
        logger.error(f"Error during data repair: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_product_data()
