from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import uvicorn
import argparse
import logging

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our API routers
from app.api.auth import router as auth_router
from app.api.partners import router as partners_router
from app.api.products import router as products_router
from app.api.chat import router as chat_router
from app.database import create_tables, get_db, SessionLocal
from app.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dynamic ERP System with Approval Workflow",
    description="A robust ERP system with JWT authentication and configurable approval policies",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(partners_router)
app.include_router(products_router)
app.include_router(chat_router, prefix="/api/v1")

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
        logger.info("🚀 Dynamic ERP System with Approval Workflow started!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "🚀 Dynamic ERP System with Approval Workflow",
        "status": "active",
        "version": "2.0.0",
        "features": [
            "JWT Authentication",
            "Dynamic Approval Policies",
            "Partner Management",
            "Product Management with JSONB Variants",
            "Role-based Access Control"
        ],
        "api_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "dynamic-erp-backend",
        "database_status": db_status,
        "features_enabled": [
            "authentication",
            "approval_workflow",
            "partner_management",
            "product_management"
        ]
    }



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