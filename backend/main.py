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

class Recording(Base):
    __tablename__ = 'recordings'
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    filename = Column(String, unique=True)
    recorded_at = Column(DateTime)

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
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    content = await file.read()
    lines = content.decode('utf-8').splitlines()
    reader = csv.reader(lines)
    prompts = [row[0] for row in reader if row]
    return {"prompts": prompts}

@app.post("/upload_audio/")
async def upload_audio(text: str = Form(...), audio: UploadFile = File(...)):
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
        else:
            rec = Recording(text=text, filename=filename, recorded_at=recorded_at)
            db.add(rec)
        db.commit()
        db.close()
    log_interaction("record", {"text": text, "filename": filename, "recorded_at": recorded_at.isoformat() + 'Z'})
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

# Update export_hf to use DB for metadata
@app.post("/export_hf/")
def export_hf(payload: dict = None):
    token = get_setting("huggingface_token", "")
    repo_id = get_setting("huggingface_repo", "")
    if not token or not repo_id:
        return {"status": "error", "detail": "Hugging Face token or repo not configured"}
    # Build dataset metadata (text, audio, recorded_at)
    with session_lock:
        db = SessionLocal()
        recs = db.query(Recording).all()
        dataset_rows = [{
            "audio": os.path.join(get_setting("storage_path", "recordings"), r.filename),
            "text": r.text,
            "recorded_at": r.recorded_at.isoformat() + 'Z' if r.recorded_at else None
        } for r in recs]
        db.close()
    if not dataset_rows:
        return {"status": "error", "detail": "No audio files found"}
    df = pd.DataFrame(dataset_rows)
    ds = Dataset.from_pandas(df)
    ds = ds.cast_column("audio", Audio())
    try:
        ds.push_to_hub(repo_id, token=token)
    except Exception as e:
        log_interaction("export_hf_error", {"error": str(e)})
        return {"status": "error", "detail": f"Failed to push dataset: {str(e)}"}
    log_interaction("export_hf", {"count": len(dataset_rows)})
    return {"status": "ok", "uploaded": [row["audio"] for row in dataset_rows]} 