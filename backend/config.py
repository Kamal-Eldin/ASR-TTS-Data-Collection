import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration class"""
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'tts_dataset_generator')
    
    # SQLite Configuration (default)
    SQLITE_DATABASE = os.getenv('SQLITE_DATABASE', 'tts_dataset.db')
    
    @classmethod
    def get_database_url(cls):
        """Get database URL - defaults to SQLite for easier setup"""
        # Check if MySQL is explicitly configured and available
        if (cls.MYSQL_HOST and cls.MYSQL_USER and cls.MYSQL_PASSWORD and 
            cls.MYSQL_DATABASE):
            return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        else:
            # Default to SQLite for easier setup
            return f"sqlite:///{cls.SQLITE_DATABASE}"
    
    @classmethod
    def validate_config(cls):
        """Validate database configuration"""
        if cls.get_database_url().startswith('mysql'):
            required_fields = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
            missing_fields = [field for field in required_fields if not getattr(cls, field)]
            if missing_fields:
                raise ValueError(f"Missing required MySQL configuration: {missing_fields}")
        return True

class AppConfig:
    """Application configuration class"""
    
    # Storage Configuration
    STORAGE_PATH = os.getenv('STORAGE_PATH', 'recordings')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174').split(',')
    
    # Export Timeouts
    HF_EXPORT_TIMEOUT = int(os.getenv('HF_EXPORT_TIMEOUT', 300))
    S3_EXPORT_TIMEOUT = int(os.getenv('S3_EXPORT_TIMEOUT', 300))
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Hugging Face Configuration
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '')
    HUGGINGFACE_REPO = os.getenv('HUGGINGFACE_REPO', '') 