import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import AppConfig
from models.database import Base
from database.connection import engine
from database.migration import migrate_schema
from services.settings_service import SettingsService
from api import projects_router, recordings_router, settings_router, exports_router

# Create FastAPI app
app = FastAPI(title="TTS Dataset Generator", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.CORS_ORIGINS,
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

# Include API routers
app.include_router(projects_router)
app.include_router(recordings_router)
app.include_router(settings_router)
app.include_router(exports_router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 