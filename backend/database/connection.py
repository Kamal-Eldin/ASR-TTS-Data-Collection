import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DatabaseConfig

# Database configuration
DATABASE_URL = DatabaseConfig.get_database_url()
engine = None

# Check if we should use MySQL or SQLite
if DATABASE_URL.startswith('mysql'):
    print(f"Retrieved db url: {DATABASE_URL}")
    try:
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        print (f"Created db engine {engine}")
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).fetchone()
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"⚠️  MySQL connection failed: {e}")
        print("🔄 Falling back to SQLite for development...")
        # Fallback to SQLite
        engine = create_engine('sqlite:///tts_dataset.db', connect_args={"check_same_thread": False})
        print("✅ Connected to SQLite database")
else:
    # Use SQLite directly
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print("✅ Connected to SQLite database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 