from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="user", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="creator", cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="user", cascade="all, delete-orphan")
    shared_projects = relationship("ProjectCollaborator", back_populates="user", cascade="all, delete-orphan")

class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), index=True)
    value = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationship
    user = relationship("User", back_populates="settings")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)  # Removed unique constraint - unique per user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_rtl = Column(Integer, default=0)  # 0 for LTR, 1 for RTL
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")

class Prompt(Base):
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)  # To maintain order of prompts
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="prompts")
    project = relationship("Project", back_populates="prompts")
    recordings = relationship("Recording", back_populates="prompt", cascade="all, delete-orphan")

class Recording(Base):
    __tablename__ = 'recordings'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    filename = Column(String(255), unique=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    prompt_id = Column(Integer, ForeignKey('prompts.id'), index=True)  # Link to specific prompt
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="recordings")
    project = relationship("Project", back_populates="recordings")
    prompt = relationship("Prompt", back_populates="recordings")

class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255))
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))

class ProjectCollaborator(Base):
    __tablename__ = 'project_collaborators'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="collaborators")
    user = relationship("User", back_populates="shared_projects")

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_collaborator'),
    )