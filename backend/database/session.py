import threading
from sqlalchemy.orm import Session
from .connection import SessionLocal

# Session lock for thread safety
session_lock = threading.Lock()

def get_db() -> Session:
    """Get database session with thread safety"""
    with session_lock:
        db = SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise 