import os
from models.database import Setting
from database.connection import SessionLocal
from database.session import session_lock
from config import AppConfig

class SettingsService:
    @staticmethod
    def get_setting(key: str, default: str = "", user_id: int | None = None) -> str:
        with session_lock:
            db = SessionLocal()
            try:
                if user_id is not None:
                    setting = db.query(Setting).filter(
                        Setting.user_id == user_id,
                        Setting.key == key
                    ).first()
                    if setting and setting.value is not None:
                        return setting.value

                shared_setting = db.query(Setting).filter(
                    Setting.user_id.is_(None),
                    Setting.key == key
                ).first()
                if shared_setting and shared_setting.value is not None:
                    return shared_setting.value

                return default
            finally:
                db.close()

    @staticmethod
    def set_setting(key: str, value: str, user_id: int | None = None):
        with session_lock:
            db = SessionLocal()
            try:
                setting = db.query(Setting).filter(
                    Setting.user_id == user_id,
                    Setting.key == key
                ).first()
                if setting:
                    setting.value = value
                else:
                    setting = Setting(user_id=user_id, key=key, value=value)
                    db.add(setting)
                db.commit()
            finally:
                db.close()

    @staticmethod
    def ensure_storage_path(user_id: int | None = None):
        """Ensure storage directory exists"""
        storage_path = SettingsService.get_setting(
            "storage_path",
            default=AppConfig.STORAGE_PATH,
            user_id=user_id,
        )
        os.makedirs(storage_path, exist_ok=True)
        return storage_path
