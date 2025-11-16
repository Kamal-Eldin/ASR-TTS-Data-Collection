import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import configuration
from core.config import AppConfig

# Import database components
from models.database import Base
from database.connection import engine
from database.migration import migrate_schema

# Import services
from services.settings_service import SettingsService

# Import API v1 routers
from api.v1 import auth, projects, recordings, settings, exports

# Create FastAPI app
app = FastAPI(
    title="ASR-TTS Data Collection API",
    version="1.0.0",
    description="Audio Recording Dataset Collection System with Authentication"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Run schema migration
migrate_schema()

# Ensure storage directory exists
SettingsService.ensure_storage_path()

# Include API v1 routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(recordings.router)
app.include_router(settings.router)
app.include_router(exports.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "api_version": "1.0.0"}

# API root
@app.get("/api")
async def api_root():
    return {
        "message": "ASR-TTS Data Collection API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "projects": "/api/v1/projects",
            "recordings": "/api/v1/recordings",
            "settings": "/api/v1/settings",
            "exports": "/api/v1/exports"
        }
    }

# Serve static files (React app)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)