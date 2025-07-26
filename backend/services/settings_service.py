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