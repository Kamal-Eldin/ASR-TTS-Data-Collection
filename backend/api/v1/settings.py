from fastapi import APIRouter, HTTPException
from models.schemas import Settings
from services.settings_service import SettingsService
from utils.logging import log_interaction

router = APIRouter(tags=["settings"])

@router.get("/settings/")
def get_settings():
    return {
        "storage_path": SettingsService.get_setting("storage_path", "recordings"),
        "s3_bucket": SettingsService.get_setting("s3_bucket", ""),
        "huggingface_token": SettingsService.get_setting("huggingface_token", ""),
        "huggingface_repo": SettingsService.get_setting("huggingface_repo", "")
    }

@router.post("/settings/")
def set_settings(settings: Settings):
    for k, v in settings.dict(exclude_unset=True).items():
        SettingsService.set_setting(k, v)
    # Ensure storage path exists
    SettingsService.ensure_storage_path()
    log_interaction("update_settings", settings.dict(exclude_unset=True))
    return get_settings() 