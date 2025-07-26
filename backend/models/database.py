from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

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