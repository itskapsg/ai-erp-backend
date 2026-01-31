from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
import uvicorn
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our API routers
from app.api.auth import router as auth_router
from app.api.partners import router as partners_router
from app.api.products import router as products_router
from app.api.orders import router as orders_router
from app.api.approval_policies import router as approval_policies_router
from app.api.chat import router as chat_router
from app.api.namaste import router as namaste_router
from app.api.users import router as users_router
from app.api.webhook import router as webhook_router
from app.api.accounting import router as accounting_router
from app.api.reports import router as reports_router
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
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(approval_policies_router, prefix="/api/v1/approval-policies", tags=["Approval Policies"])
app.include_router(chat_router, prefix="/api/v1")
app.include_router(namaste_router, prefix="/api/v1/namaste", tags=["Project Namaste"])
app.include_router(users_router)
app.include_router(webhook_router, prefix="/api/v1", tags=["WhatsApp Webhook"])
app.include_router(accounting_router, prefix="/api/v1", tags=["Accounting"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])

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
            "Dynamic Approval Policies with API Management",
            "Partner Management",
            "Product Management with JSONB Variants",
            "Order Management with Credit Limit Approval",
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
            "product_management",
            "order_management"
        ]
    }

# Mount static files for frontend
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist_path):
    # Mount /static for explicit static access if needed
    app.mount("/static", StaticFiles(directory=frontend_dist_path), name="static")
    
    # Mount /assets which Vite uses by default
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        
    logger.info(f"Mounted static files from: {frontend_dist_path}")

# Mount uploads directory for serving images
UPLOAD_DIR = "/root/workspace/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CATCH-ALL ROUTE FOR SPA (Fixes 404 on Refresh)
# This must be the LAST route defined
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    Catch-all route for SPA (Single Page Application) support.
    Returns index.html for non-API routes to let React handle routing.
    """
    # If API request (starts with api/), let it fail normally (404)
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API Endpoint not found")
    
    # Serve index.html (React handles the routing)
    index_path = os.path.join(frontend_dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback if index.html doesn't exist
    raise HTTPException(status_code=404, detail="Frontend not built")


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