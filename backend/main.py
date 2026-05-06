import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException


class SPAStaticFiles(StaticFiles):
    """StaticFiles that falls back to index.html on 404 so client-side routes load directly.

    /api/* paths bypass the fallback so missing API endpoints still return real 404s.
    """

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.lstrip("/").startswith("api/"):
                return await super().get_response("index.html", scope)
            raise

from config import AppConfig
from models.database import Base
from database.connection import engine
from database.migration import migrate_schema
from services.settings_service import SettingsService
from api import projects_router, recordings_router, settings_router, exports_router, password_reset_router, auth_router, profile_router

# Create FastAPI app
app = FastAPI(title="TTS Dataset Generator", version="1.0.0")

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

# Include API routers with ROUTER_PREFIX        # for cloudfront ALB routing
app.include_router(projects_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(recordings_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(settings_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(exports_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(password_reset_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(auth_router, prefix= AppConfig.ROUTER_PREFIX )
app.include_router(profile_router, prefix= AppConfig.ROUTER_PREFIX )

# Health check endpoint (must be before static mount)
@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.mount("/", SPAStaticFiles(directory="static", html=True), name="static")



if __name__ == "__main__":
    import uvicorn
    print(f"Set CORS_ORIGINS: {AppConfig.CORS_ORIGINS}")
    uvicorn.run(app, host="0.0.0.0", port=8500) 
