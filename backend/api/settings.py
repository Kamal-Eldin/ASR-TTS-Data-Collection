from fastapi import APIRouter, Depends
from api.dependencies import AuthenticatedUser, get_current_user
from models.schemas import Settings
from services.settings_service import SettingsService
from utils.logging import log_interaction
from config import AppConfig



router = APIRouter(tags=["settings"])

@router.get("/settings/")
def get_settings(current_user: AuthenticatedUser = Depends(get_current_user)):
    return {
        "storage_path": SettingsService.get_setting("storage_path", default=AppConfig.STORAGE_PATH, user_id=current_user.id),
        "s3_bucket": SettingsService.get_setting("s3_bucket", AppConfig.BUCKET, user_id=current_user.id),
        "huggingface_token": SettingsService.get_setting("huggingface_token", AppConfig.HUGGINGFACE_TOKEN, user_id=current_user.id),
        "huggingface_repo": SettingsService.get_setting("huggingface_repo", AppConfig.HUGGINGFACE_REPO, user_id=current_user.id)
    }

@router.post("/settings/")
def set_settings(settings: Settings, current_user: AuthenticatedUser = Depends(get_current_user)):
    payload = settings.model_dump(exclude_unset=True)
    for k, v in payload.items():
        SettingsService.set_setting(k, v, user_id=current_user.id)
    # Ensure storage path exists
    SettingsService.ensure_storage_path(current_user.id)
    log_interaction("update_settings", {"user_id": current_user.id, **payload})
    return get_settings(current_user)
