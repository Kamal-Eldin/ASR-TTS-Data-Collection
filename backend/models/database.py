from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
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
    projects = relationship("Project", back_populates="user")
    settings = relationship("Setting", back_populates="user")

class Setting(Base):
    __tablename__ = 'settings'
    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uq_settings_user_key'),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    key = Column(String(255), index=True, nullable=False)
    value = Column(Text)
    user = relationship("User", back_populates="settings")

class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_projects_user_name'),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    name = Column(String(255), index=True, nullable=False)
    is_rtl = Column(Integer, default=0)  # 0 for LTR, 1 for RTL
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project")

class Prompt(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), index=True)
    text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)  # To maintain order of prompts
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="prompts")
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
