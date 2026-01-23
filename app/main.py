from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import argparse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://erp_admin:db_password_123@localhost/erp_dev_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# System Logs Model
class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    instance_name = Column(String, nullable=True)

app = FastAPI(
    title="Scalable ERP System",
    description="A robust ERP system with dynamic versioning and parallel deployment support",
    version="1.0.0"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and log startup"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully: {DATABASE_URL}")
        
        # Log startup
        db = SessionLocal()
        try:
            startup_log = SystemLog(
                message="Phase 1 Initialized",
                instance_name=os.getenv("INSTANCE_NAME", "unknown")
            )
            db.add(startup_log)
            db.commit()
            logger.info("Startup log created successfully")
        except Exception as e:
            logger.error(f"Failed to create startup log: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with basic system information"""
    return {
        "message": "Welcome to the Scalable ERP System",
        "status": "active",
        "version": "dynamic",
        "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "unknown"  # Hide credentials
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "active",
        "version": "dynamic",
        "service": "erp-backend",
        "port": str(getattr(app.state, 'port', os.getenv("APP_PORT", "8000"))),
        "database_status": db_status
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint with detailed information"""
    return {
        "api_version": "v1",
        "status": "active",
        "version": "dynamic",
        "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "unknown",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/v1/logs")
async def get_system_logs():
    """Get all system logs"""
    try:
        db = SessionLocal()
        logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(50).all()
        db.close()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "message": log.message,
                    "created_at": log.created_at.isoformat(),
                    "instance_name": log.instance_name
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")

@app.post("/api/v1/logs")
async def create_log(message: str):
    """Create a new system log entry"""
    try:
        db = SessionLocal()
        new_log = SystemLog(
            message=message,
            instance_name=os.getenv("INSTANCE_NAME", "unknown")
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        db.close()
        
        return {
            "id": new_log.id,
            "message": new_log.message,
            "created_at": new_log.created_at.isoformat(),
            "instance_name": new_log.instance_name
        }
    except Exception as e:
        logger.error(f"Failed to create log: {e}")
        raise HTTPException(status_code=500, detail="Failed to create log")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ERP System')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    args = parser.parse_args()
    
    # Also check environment variable for backward compatibility
    port = args.port or int(os.getenv("APP_PORT", 8000))
    
    # Store port in app state for health endpoint
    app.state.port = port
    
    uvicorn.run(app, host=args.host, port=port)