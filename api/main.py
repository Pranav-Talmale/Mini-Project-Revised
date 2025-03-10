from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import the app configuration and endpoints
from api.routes.students import router as students_router
from api.routes.subjects import router as subjects_router
from api.routes.enrollments import router as enrollments_router
from api.routes.batches import router as batches_router
from api.routes.analytics import router as analytics_router
from api.routes.query import router as query_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DocGene API",
    description="API for DocGene application to enable mobile integration",
    version="1.0.0"
)

# Configure CORS for mobile app integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
@app.middleware("http")
async def log_and_handle_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Request to {request.url} failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

# Root endpoint
@app.get("/")
def read_root():
    return {
        "name": "DocGene API", 
        "version": "1.0.0",
        "description": "API for DocGene educational management system",
        "documentation": "/docs",
        "server_time": datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Include all routers
app.include_router(students_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(enrollments_router, prefix="/api")
app.include_router(batches_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(query_router, prefix="/api")

# Run the application with Uvicorn if executed directly
if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting DocGene API server on {host}:{port}")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)