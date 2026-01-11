from pydantic import BaseModel

class Settings(BaseModel):
    storage_path: str
    s3_bucket: str = ""
    huggingface_token: str = ""
    huggingface_repo: str = "" 