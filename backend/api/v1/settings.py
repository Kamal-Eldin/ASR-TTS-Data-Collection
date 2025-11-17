from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.schemas import Settings
from services.settings_service import SettingsService
from utils.logging import log_interaction
from core.dependencies import get_current_user
from models.database import User
from database.session import get_db

router = APIRouter(tags=["settings"])

@router.get("/settings/")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "storage_path": SettingsService.get_user_setting("storage_path", current_user.id, "recordings", db),
        "s3_bucket": SettingsService.get_user_setting("s3_bucket", current_user.id, "", db),
        "huggingface_token": SettingsService.get_user_setting("huggingface_token", current_user.id, "", db),
        "huggingface_repo": SettingsService.get_user_setting("huggingface_repo", current_user.id, "", db)
    }

@router.post("/settings/")
async def set_settings(
    settings: Settings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for k, v in settings.dict(exclude_unset=True).items():
        SettingsService.set_user_setting(k, v, current_user.id, db)
    # Ensure storage path exists for this user
    SettingsService.ensure_user_storage_path(current_user.id, db)
    log_interaction("update_settings", {
        "user_id": current_user.id,
        "settings": settings.dict(exclude_unset=True)
    })
    return await get_settings(current_user, db) 