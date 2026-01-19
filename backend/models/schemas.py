from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str  # Can be email or username
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[dict] = None

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    is_rtl: bool = False

class ProjectCreate(ProjectBase):
    prompts_text: Optional[str] = None  # For text input method
    # user_id will be added automatically from JWT

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    is_owner: bool = True
    owner_username: Optional[str] = None
    collaborator_count: int = 0

    class Config:
        orm_mode = True

# Collaborator Schemas
class CollaboratorResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    added_at: datetime

    class Config:
        orm_mode = True

class ShareProjectRequest(BaseModel):
    email_or_username: str

# Recording Schemas
class RecordingCreate(BaseModel):
    project_id: int
    prompt_id: Optional[int] = None
    text: Optional[str] = None

class RecordingResponse(BaseModel):
    id: int
    filename: str
    text: Optional[str]
    recorded_at: datetime
    project_id: int
    prompt_id: Optional[int]
    user_id: int

    class Config:
        orm_mode = True

# Prompt Schemas
class PromptResponse(BaseModel):
    id: int
    text: str
    order_index: int
    project_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Settings Schemas
class Settings(BaseModel):
    storage_path: str
    s3_bucket: str = ""
    huggingface_token: str = ""
    huggingface_repo: str = "" 