import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

class AppConfig:
    """Application configuration class"""
    
    # Storage Configuration
    STORAGE_PATH= os.getenv('STORAGE_PATH', default="/tmp/recordings")
    BUCKET: str = os.getenv('BUCKET', default="s3://speech-collector")
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv(key='CORS_ORIGINS',default= 'http://localhost:3000')
    CORS_REGEX: str = os.getenv(key="CORS_REGEX", default=r"^https?://(localhost:\d+|[\w-]+\.cloudfront\.net)$" )
    ROUTER_PREFIX: str = os.getenv('ROUTER_PREFIX', '')
    
    # Export Timeouts
    HF_EXPORT_TIMEOUT = int(os.getenv('HF_EXPORT_TIMEOUT', 300))
    S3_EXPORT_TIMEOUT = int(os.getenv('S3_EXPORT_TIMEOUT', 300))
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID_FILE = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY_FILE = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Hugging Face Configuration
    HUGGINGFACE_TOKEN_FILE: str = os.getenv('HUGGINGFACE_TOKEN_FILE', '/run/secrets/hf_token')
    HUGGINGFACE_REPO: str = os.getenv('HUGGINGFACE_REPO', '')      
    HUGGINGFACE_TOKEN: str = os.getenv('HUGGINGFACE_TOKEN', '')


    @staticmethod
    def get_secret(secret_path: str, env_key:str | None, default: str|None) -> str | None:

        try:
            assert os.path.exists(secret_path), f"No secret file found for {env_key} at path: {secret_path}"
            with open(secret_path, 'r') as file:
                return file.read() 
        except:
            print(f"Falling back to environment variable for key {env_key}")
            try:
                variable = os.getenv(env_key, "")
                assert variable, ValueError
                return variable
            except:
                print(f"failed to find user set variable, resorting to default value {default}")
                return default
   

    @classmethod
    def get_hf_token(cls) -> str:
       return cls.get_secret(secret_path=cls.HUGGINGFACE_TOKEN_FILE, env_key="HUGGINGFACE_TOKEN", default="")
        
    @classmethod
    def get_aws_access_id(cls):
       return cls.get_secret(secret_path=cls.AWS_ACCESS_KEY_ID_FILE, env_key="AWS_EXPORT_KEY_ID", default= "")
        
    @classmethod
    def get_aws_access_secret(cls):
       return cls.get_secret(secret_path=cls.AWS_SECRET_ACCESS_KEY_FILE, env_key="AWS_EXPORT_KEY_SECRET", default= "")

        
class DatabaseConfig:
    """Database configuration class"""
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD_FILE = os.getenv('MYSQL_PASSWORD_FILE', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'tts_dataset_generator')
    AWS_ACCESS_KEY_ID_FILE= os.getenv('AWS_ACCESS_KEY_ID_FILE', '')
    AWS_SECRET_ACCESS_KEY_FILE= os.getenv('AWS_SECRET_ACCESS_KEY_FILE', '')
    
    # SQLite Configuration (default)
    SQLITE_DATABASE = os.getenv('SQLITE_DATABASE', 'data/tts_dataset.db')

    config = AppConfig

    @classmethod
    def get_db_password(cls):
        return cls.config.get_secret(cls.MYSQL_PASSWORD_FILE, env_key="MYSQL_PASSWORD", default= "admin")
         
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