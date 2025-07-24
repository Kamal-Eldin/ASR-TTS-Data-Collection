from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import hashlib
import shutil
import csv
from typing import List
from pydantic import BaseModel
import boto3
from huggingface_hub import HfApi, HfFolder
from datasets import Dataset, Audio
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default config
CONFIG = {
    "storage_path": "recordings"
}

# Ensure storage path exists
os.makedirs(CONFIG["storage_path"], exist_ok=True)

class Settings(BaseModel):
    storage_path: str
    s3_bucket: str = ""
    huggingface_token: str = ""
    huggingface_repo: str = ""

# SQLite setup
engine = create_engine('sqlite:///tts_dataset.db', connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session_lock = threading.Lock()

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    prompts = Column(JSON)  # Store prompts as JSON array
    created_at = Column(DateTime)

class Recording(Base):
    __tablename__ = 'recordings'
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    filename = Column(String, unique=True)
    recorded_at = Column(DateTime)
    project_id = Column(Integer)  # Link to project

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime)

Base.metadata.create_all(bind=engine)

# Helper functions

def get_setting(key, default=None):
    with session_lock:
        db = SessionLocal()
        s = db.query(Setting).filter(Setting.key == key).first()
        db.close()
        return s.value if s else default

def set_setting(key, value):
    with session_lock:
        db = SessionLocal()
        s = db.query(Setting).filter(Setting.key == key).first()
        if s:
            s.value = value
        else:
            s = Setting(key=key, value=value)
            db.add(s)
        db.commit()
        db.close()

def log_interaction(action, details):
    from datetime import datetime
    with session_lock:
        db = SessionLocal()
        db.add(Interaction(action=action, details=details, timestamp=datetime.utcnow()))
        db.commit()
        db.close()

@app.post("/upload_csv/")
async def upload_csv(file: UploadFile = File(...), project_name: str = Form(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    content = await file.read()
    lines = content.decode('utf-8').splitlines()
    reader = csv.reader(lines)
    prompts = [row[0] for row in reader if row]
    print(prompts)
    # Save project to database
    from datetime import datetime
    with session_lock:
        db = SessionLocal()
        # Check if project exists
        existing = db.query(Project).filter(Project.name == project_name).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Project name already exists")
        
        project = Project(name=project_name, prompts=prompts, created_at=datetime.utcnow())
        db.add(project)
        db.commit()
        db.refresh(project)
        db.close()
    
    log_interaction("create_project", {"name": project_name, "prompt_count": len(prompts)})
    return {"project_id": project.id, "name": project_name, "prompts": prompts}

@app.get("/projects/")
def list_projects():
    with session_lock:
        db = SessionLocal()
        projects = db.query(Project).all()
        result = [{"id": p.id, "name": p.name, "created_at": p.created_at.isoformat() + 'Z' if p.created_at else None} for p in projects]
        db.close()
    return {"projects": result}

@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    with session_lock:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            db.close()
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete all recordings for this project
        recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
        storage_path = get_setting("storage_path", "recordings")
        for recording in recordings:
            try:
                file_path = os.path.join(storage_path, recording.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete file {recording.filename}: {e}")
        
        # Delete recordings from database
        db.query(Recording).filter(Recording.project_id == project_id).delete()
        
        # Delete project
        db.delete(project)
        db.commit()
        db.close()
    
    log_interaction("delete_project", {"project_id": project_id, "name": project.name})
    return {"status": "ok", "message": f"Project '{project.name}' deleted successfully"}

@app.get("/projects/{project_id}")
def get_project(project_id: int):
    with session_lock:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            db.close()
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get recording progress
        recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
        recorded_texts = [r.text for r in recordings]
        last_recorded_index = -1
        for i, prompt in enumerate(project.prompts):
            if prompt in recorded_texts:
                last_recorded_index = i
        
        result = {
            "id": project.id, 
            "name": project.name, 
            "prompts": project.prompts, 
            "created_at": project.created_at.isoformat() + 'Z' if project.created_at else None,
            "total_prompts": len(project.prompts),
            "recorded_count": len(recordings),
            "last_recorded_index": last_recorded_index
        }
        db.close()
    return result

@app.post("/upload_audio/")
async def upload_audio(text: str = Form(...), audio: UploadFile = File(...), project_id: int = Form(...)):
    from datetime import datetime
    md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
    ext = os.path.splitext(audio.filename)[-1] or '.wav'
    filename = f"{md5}{ext}"
    storage_path = get_setting("storage_path", "recordings")
    save_path = os.path.join(storage_path, filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    recorded_at = datetime.utcnow()
    with session_lock:
        db = SessionLocal()
        rec = db.query(Recording).filter(Recording.filename == filename).first()
        if rec:
            rec.text = text
            rec.recorded_at = recorded_at
            rec.project_id = project_id
        else:
            rec = Recording(text=text, filename=filename, recorded_at=recorded_at, project_id=project_id)
            db.add(rec)
        db.commit()
        db.close()
    log_interaction("record", {"text": text, "filename": filename, "project_id": project_id, "recorded_at": recorded_at.isoformat() + 'Z'})
    return {"filename": filename}

@app.post("/delete_audio/")
async def delete_audio(text: str = Form(...)):
    md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
    storage_path = get_setting("storage_path", "recordings")
    deleted = False
    with session_lock:
        db = SessionLocal()
        for ext in ['.wav', '.mp3', '.ogg']:
            filename = f"{md5}{ext}"
            path = os.path.join(storage_path, filename)
            if os.path.exists(path):
                os.remove(path)
                rec = db.query(Recording).filter(Recording.filename == filename).first()
                if rec:
                    db.delete(rec)
                deleted = True
        db.commit()
        db.close()
    log_interaction("delete", {"text": text, "md5": md5, "deleted": deleted})
    return {"deleted": deleted}

# Update settings endpoints to use DB
@app.get("/settings/")
def get_settings():
    return {
        "storage_path": get_setting("storage_path", "recordings"),
        "s3_bucket": get_setting("s3_bucket", ""),
        "huggingface_token": get_setting("huggingface_token", ""),
        "huggingface_repo": get_setting("huggingface_repo", "")
    }

@app.post("/settings/")
def set_settings(settings: Settings):
    for k, v in settings.dict(exclude_unset=True).items():
        set_setting(k, v)
    # Ensure storage path exists
    os.makedirs(get_setting("storage_path", "recordings"), exist_ok=True)
    log_interaction("update_settings", settings.dict(exclude_unset=True))
    return get_settings()

@app.get("/list_recordings/")
def list_recordings():
    files = [f for f in os.listdir(CONFIG["storage_path"]) if os.path.isfile(os.path.join(CONFIG["storage_path"], f))]
    return {"recordings": files}

# Placeholder for export endpoints
@app.post("/export_s3/")
def export_s3(payload: dict = None):
    bucket = CONFIG.get("s3_bucket")
    if not bucket:
        return {"status": "error", "detail": "S3 bucket not configured"}
    s3 = boto3.client("s3")
    if payload and payload.get("filename"):
        fname = payload["filename"]
        fpath = os.path.join(CONFIG["storage_path"], fname)
        if os.path.isfile(fpath):
            try:
                s3.upload_file(fpath, bucket, fname)
                return {"status": "ok", "uploaded": [fname]}
            except Exception as e:
                return {"status": "error", "detail": str(e)}
        else:
            return {"status": "error", "detail": "File not found"}
    # fallback: upload all
    uploaded = []
    for fname in os.listdir(CONFIG["storage_path"]):
        fpath = os.path.join(CONFIG["storage_path"], fname)
        if os.path.isfile(fpath):
            try:
                s3.upload_file(fpath, bucket, fname)
                uploaded.append(fname)
            except Exception as e:
                continue
    return {"status": "ok", "uploaded": uploaded}

# Update export_hf to work with specific project
@app.post("/export_hf/")
def export_hf(project_id: int = Form(...)):
    token = get_setting("huggingface_token", "")
    repo_id = get_setting("huggingface_repo", "")
    if not token or not repo_id:
        return {"status": "error", "detail": "Hugging Face token or repo not configured"}
    
    # Get project info
    with session_lock:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            db.close()
            return {"status": "error", "detail": "Project not found"}
        
        # Get recordings for this project
        recs = db.query(Recording).filter(Recording.project_id == project_id).all()
        dataset_rows = [{
            "audio": os.path.join(get_setting("storage_path", "recordings"), r.filename),
            "text": r.text,
            "recorded_at": r.recorded_at.isoformat() + 'Z' if r.recorded_at else None
        } for r in recs]
        db.close()
    
    if not dataset_rows:
        return {"status": "error", "detail": "No audio files found for this project"}
    
    # Create dataset with project name
    dataset_name = f"{repo_id}-{project.name.lower().replace(' ', '-')}"
    
    df = pd.DataFrame(dataset_rows)
    ds = Dataset.from_pandas(df)
    ds = ds.cast_column("audio", Audio())
    try:
        ds.push_to_hub(dataset_name, token=token)
    except Exception as e:
        log_interaction("export_hf_error", {"error": str(e), "project_id": project_id})
        return {"status": "error", "detail": f"Failed to push dataset: {str(e)}"}
    log_interaction("export_hf", {"count": len(dataset_rows), "project_id": project_id, "dataset_name": dataset_name})
    return {"status": "ok", "uploaded": [row["audio"] for row in dataset_rows], "dataset_name": dataset_name} 

@app.post("/clear_database/")
def clear_database():
    """Clear all data from the database and delete all audio files"""
    try:
        with session_lock:
            db = SessionLocal()
            
            # Get all recordings to delete their files
            recordings = db.query(Recording).all()
            storage_path = get_setting("storage_path", "recordings")
            
            # Delete all audio files
            for recording in recordings:
                try:
                    file_path = os.path.join(storage_path, recording.filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Failed to delete file {recording.filename}: {e}")
            
            # Clear all tables
            db.query(Interaction).delete()
            db.query(Recording).delete()
            db.query(Project).delete()
            db.query(Setting).delete()
            
            db.commit()
            db.close()
        
        log_interaction("clear_database", {"message": "Database cleared successfully"})
        return {"status": "ok", "message": "Database cleared successfully. All projects, recordings, and settings have been removed."}
    
    except Exception as e:
        return {"status": "error", "detail": f"Failed to clear database: {str(e)}"} 