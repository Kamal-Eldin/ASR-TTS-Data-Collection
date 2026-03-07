from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    year_of_birth = Column(String(10))
    gender = Column(String(20))
    country = Column(String(100))
    city = Column(String(100))
    education = Column(String(50))
    profession = Column(String(100))
    language_related = Column(String(10))
    native_language = Column(String(100))
    language_pairs = Column(JSON)  # [{"language": "...", "level": "..."}]
    system = Column(String(50))
    mic_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    value = Column(Text)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    is_rtl = Column(Integer, default=0)  # 0 for LTR, 1 for RTL
    created_at = Column(DateTime, default=datetime.utcnow)

class Prompt(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)  # To maintain order of prompts
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to Recordings
    recordings = relationship("Recording", back_populates="prompt")

class Recording(Base):
    __tablename__ = 'recordings'
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    filename = Column(String(255), unique=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(Integer)
    prompt_id = Column(Integer, ForeignKey('prompts.id'), index=True)  # Link to specific prompt
    
    # Relationship to Prompt
    prompt = relationship("Prompt", back_populates="recordings")

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255))
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0)  # 0 = unused, 1 = used
    created_at = Column(DateTime, default=datetime.utcnow)