from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

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

@app.get("/")
async def root():
    """Root endpoint with basic system information"""
    return {
        "message": "Welcome to the Scalable ERP System",
        "status": "active",
        "version": "dynamic"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "active",
        "version": "dynamic",
        "service": "erp-backend",
        "port": os.getenv("APP_PORT", "8000")
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint with detailed information"""
    return {
        "api_version": "v1",
        "status": "active",
        "version": "dynamic",
        "database_status": "connected",  # This would be actual DB check in production
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)