import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
    allow_origin_regex=AppConfig.CORS_REGEX,
    # allow_origins=AppConfig.CORS_ORIGINS.split(','),
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

# Include API routers with optional ROUTER_PREFIX (for CloudFront/ALB routing)
app.include_router(auth.router, prefix=AppConfig.ROUTER_PREFIX)
app.include_router(projects.router, prefix=AppConfig.ROUTER_PREFIX)
app.include_router(recordings.router, prefix=AppConfig.ROUTER_PREFIX)
app.include_router(settings.router, prefix=AppConfig.ROUTER_PREFIX)
app.include_router(exports.router, prefix=AppConfig.ROUTER_PREFIX)

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

# Serve static assets (JS, CSS, images from Vite build)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

# Serve index.html for root path
@app.get("/")
async def serve_root():
    return FileResponse("static/index.html")

# Catch-all route for SPA - serves index.html for client-side routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Check if it's an actual file in static directory
    file_path = os.path.join("static", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    # Otherwise return index.html for SPA routing
    return FileResponse("static/index.html")



if __name__ == "__main__":
    import uvicorn
    print(f"Set CORS_ORIGINS: {AppConfig.CORS_ORIGINS}")
    uvicorn.run(app, host="0.0.0.0", port=8500) 
