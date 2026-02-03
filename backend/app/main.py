from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_database, close_database
from app.auth import create_admin_user
from app.routers import auth, products, orders, reports, users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Initialize database connection
        get_database()
        logger.info("Connected to MongoDB")
        
        # Create admin user
        create_admin_user()
        logger.info("Admin user initialized")
        
        # Display startup information
        print("\n" + "="*70)
        print("🚀 INVENTORY & ORDER MANAGEMENT SYSTEM")
        print("   Complete Business Operations Platform")
        print("="*70)
        print("📊 MAIN DASHBOARD URL:")
        print("   👉 http://localhost:8000")
        print("")
        print("📚 ADDITIONAL URLs:")
        print("   📋 API Documentation: http://localhost:8000/docs")
        print("   🔍 Health Check:      http://localhost:8000/health")
        print("   🔐 Login Page:        http://localhost:8000/login")
        print("")
        print("🔐 LOGIN CREDENTIALS:")
        print("   Username: admin")
        print("   Password: admin123")
        print("")
        print("✨ FEATURES INCLUDED:")
        print("   • Professional Dashboard with Real-time Analytics")
        print("   • Advanced Product Management with Images")
        print("   • Multi-item Order Processing")
        print("   • Business Reports with Charts & Graphs")
        print("   • User Management with Role-based Access")
        print("   • Email Notifications & Low Stock Alerts")
        print("")
        print("🎯 OPEN YOUR BROWSER AND GO TO:")
        print("   http://localhost:8000")
        print("="*70)
        print("")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise e
    
    yield
    
    # Shutdown
    close_database()
    logger.info("Database connection closed")

import os
from pathlib import Path

# Get the correct path to frontend directory
current_dir = Path(__file__).parent
frontend_dir = current_dir.parent.parent / "frontend"

app = FastAPI(
    title="Inventory & Order Management System",
    description="A complete inventory and order management system with JWT authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# Mount uploads directory for product images
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(users.router, prefix="/api")

# Serve frontend at root - redirect to dashboard
@app.get("/")
async def serve_frontend():
    return FileResponse(str(frontend_dir / "dashboard.html"))

@app.get("/login")
async def serve_login():
    return FileResponse(str(frontend_dir / "login.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(frontend_dir / "dashboard.html"))

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        db = get_database()
        db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Inventory Management System is running"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# API info endpoint
@app.get("/api")
async def api_info():
    return {
        "message": "Inventory & Order Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "frontend": "/",
        "dashboard": "/dashboard"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)