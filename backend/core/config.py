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
    MYSQL_PASSWORD_FILE = os.getenv('MYSQL_PASSWORD_FILE', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'tts_dataset_generator')
    
    # SQLite Configuration (default)
    SQLITE_DATABASE = os.getenv('SQLITE_DATABASE', 'data/tts_dataset.db')
    
    @classmethod
    def get_db_password(cls):
        valid_filepath = os.path.exists(cls.MYSQL_PASSWORD_FILE)
        assert valid_filepath, f"MYSQL_PASSWORD_FILE cannot be found neither at {cls.MYSQL_PASSWORD_FILE} nor defaults"
        with open(cls.MYSQL_PASSWORD_FILE, 'r') as file:
            return file.read() 
         
    @classmethod
    def get_database_url(cls):
        """Get database URL - defaults to SQLite for easier setup"""
        # Check if MySQL is explicitly configured and available
        MYSQL_PASSWORD= cls.get_db_password()
        if (cls.MYSQL_HOST and cls.MYSQL_USER and MYSQL_PASSWORD and 
            cls.MYSQL_DATABASE):
            print(f"successfully retrieved mysql connection creds and db url...")
            return f"mysql+pymysql://{cls.MYSQL_USER}:{MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        else:
            # Default to SQLite for easier setup
            print(f"failed to retrieve mysql creds, defaulting to sqlite connection creds...")
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
    STORAGE_PATH = os.getenv('STORAGE_PATH', 'data/recordings')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174').split(',')
    
    # Export Timeouts
    HF_EXPORT_TIMEOUT = int(os.getenv('HF_EXPORT_TIMEOUT', 300))
    S3_EXPORT_TIMEOUT = int(os.getenv('S3_EXPORT_TIMEOUT', 300))
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID_FILE = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY_FILE = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Hugging Face Configuration
    HUGGINGFACE_TOKEN_FILE = os.getenv('HUGGINGFACE_TOKEN_FILE', '/run/secrets/hf_token')
    HUGGINGFACE_REPO = os.getenv('HUGGINGFACE_REPO', '')       

    @classmethod
    def get_hf_token(cls):
        with open(cls.HUGGINGFACE_TOKEN_FILE, 'r') as file:
            return file.read()
        
    @classmethod
    def get_aws_access_id(cls):
        with open(cls.AWS_ACCESS_KEY_ID_FILE, 'r') as file:
            return file.read()
        
    @classmethod
    def get_aws_access_secret(cls):
        with open(cls.AWS_SECRET_ACCESS_KEY_FILE, 'r') as file:
            return file.read()
