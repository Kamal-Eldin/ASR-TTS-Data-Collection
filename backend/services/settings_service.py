import os
from sqlalchemy.orm import Session
from models.database import Setting
from database.connection import SessionLocal
from database.session import session_lock

class SettingsService:
    @staticmethod
    def get_setting(key: str, default: str = "") -> str:
        with session_lock:
            db = SessionLocal()
            try:
                setting = db.query(Setting).filter(Setting.key == key).first()
                return setting.value if setting else default
            finally:
                db.close()

    @staticmethod
    def set_setting(key: str, value: str):
        with session_lock:
            db = SessionLocal()
            try:
                setting = db.query(Setting).filter(Setting.key == key).first()
                if setting:
                    setting.value = value
                else:
                    setting = Setting(key=key, value=value)
                    db.add(setting)
                db.commit()
            finally:
                db.close()

    @staticmethod
    def ensure_storage_path():
        """Ensure storage directory exists"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        os.makedirs(storage_path, exist_ok=True)
        return storage_path

    # User-specific methods for multi-user support
    @staticmethod
    def get_user_setting(key: str, user_id: int, default: str, db: Session) -> str:
        """Get user-specific setting"""
        setting = db.query(Setting).filter(
            Setting.key == key,
            Setting.user_id == user_id
        ).first()
        return setting.value if setting else default

    @staticmethod
    def set_user_setting(key: str, value: str, user_id: int, db: Session):
        """Set user-specific setting"""
        setting = db.query(Setting).filter(
            Setting.key == key,
            Setting.user_id == user_id
        ).first()

        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value, user_id=user_id)
            db.add(setting)
        db.commit()

    @staticmethod
    def ensure_user_storage_path(user_id: int, db: Session):
        """Ensure user-specific storage directory exists"""
        storage_path = SettingsService.get_user_setting("storage_path", user_id, f"recordings/user_{user_id}", db)
        os.makedirs(storage_path, exist_ok=True)
        return storage_path 