from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import shutil
import csv
import json
import hashlib
import boto3
import pandas as pd
from datetime import datetime
from huggingface_hub import HfApi
from datasets import Dataset, Audio
import threading
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
import pymysql
from pydantic import BaseModel

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DatabaseConfig, AppConfig

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Settings(BaseModel):
    storage_path: str
    s3_bucket: str = ""
    huggingface_token: str = ""
    huggingface_repo: str = ""

# Database configuration
DATABASE_URL = DatabaseConfig.get_database_url()
engine = None

# Check if we should use MySQL or SQLite
if DATABASE_URL.startswith('mysql'):
    try:
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).fetchone()
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"⚠️  MySQL connection failed: {e}")
        print("🔄 Falling back to SQLite for development...")
        # Fallback to SQLite
        engine = create_engine('sqlite:///tts_dataset.db', connect_args={"check_same_thread": False})
        print("✅ Connected to SQLite database")
else:
    # Use SQLite directly
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print("✅ Connected to SQLite database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    value = Column(Text)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
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

# Create tables
Base.metadata.create_all(bind=engine)

# Session lock for thread safety
session_lock = threading.Lock()

# Handle schema migrations for existing databases
def migrate_schema():
    """Handle schema migrations for existing databases"""
    with session_lock:
        db = SessionLocal()
        try:
            # Check if we're using SQLite
            if 'sqlite' in str(engine.url):
                print("🔄 Checking SQLite database schema...")
                
                # Check if prompt_id column exists in recordings table
                try:
                    db.execute(text("SELECT prompt_id FROM recordings LIMIT 1"))
                    print("✅ Database schema is up to date")
                except Exception:
                    print("🔄 Migrating SQLite database schema...")
                    
                    # Add prompt_id column to recordings table
                    try:
                        db.execute(text("ALTER TABLE recordings ADD COLUMN prompt_id INTEGER"))
                        print("✅ Added prompt_id column to recordings table")
                    except Exception as e:
                        print(f"⚠️  Could not add prompt_id column: {e}")
                    
                    # Check if prompts table exists
                    try:
                        db.execute(text("SELECT COUNT(*) FROM prompts"))
                        print("✅ Prompts table exists")
                    except Exception:
                        print("🔄 Creating prompts table...")
                        # Create prompts table manually for SQLite
                        db.execute(text("""
                            CREATE TABLE prompts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                project_id INTEGER NOT NULL,
                                text TEXT NOT NULL,
                                order_index INTEGER NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        print("✅ Created prompts table")
                    
                    db.commit()
                    print("✅ Schema migration completed")
            
            # For MySQL, the schema should be created automatically
            else:
                print("✅ MySQL database schema is up to date")
                
        except Exception as e:
            print(f"⚠️  Schema migration check failed: {e}")
        finally:
            db.close()

# Run schema migration
migrate_schema()

# Helper functions
def get_setting(key: str, default: str = "") -> str:
    with session_lock:
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == key).first()
            return setting.value if setting else default
        finally:
            db.close()

def set_setting(key: str, value: str):
    with session_lock:
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.add(setting)
            db.commit()
        finally:
            db.close()

def log_interaction(action: str, data: dict):
    # with session_lock:
    #     db = SessionLocal()
    #     try:
    #         interaction = Interaction(action=action, data=data)
    #         db.add(interaction)
    #         db.commit()
    #     finally:
    #         db.close()
    print(f"🔄 Logging interaction: {action} with data: {data}")

# Ensure storage directory exists
storage_path = get_setting("storage_path", "recordings")
os.makedirs(storage_path, exist_ok=True)

@app.post("/upload_csv/")
async def upload_csv(file: UploadFile = File(...), project_name: str = Form(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV content
    content = await file.read()
    text = content.decode('utf-8')
    
    # Parse CSV
    prompts = []
    csv_reader = csv.reader(text.splitlines())
    for row in csv_reader:
        if row and row[0].strip():  # Skip empty rows
            prompts.append(row[0].strip())
    
    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found in CSV")
    
    return await create_project_with_prompts(project_name, prompts)

@app.post("/create_project/")
async def create_project_with_text(project_name: str = Form(...), prompts_text: str = Form(...)):
    """Create a project with prompts from multi-line text input"""
    if not prompts_text.strip():
        raise HTTPException(status_code=400, detail="No prompts provided")
    
    # Split by lines and filter empty lines
    # Handle both \n and \r\n line endings
    prompts = [line.strip() for line in prompts_text.replace('\r\n', '\n').split('\n') if line.strip()]
    
    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found in text")
    
    return await create_project_with_prompts(project_name, prompts)

async def create_project_with_prompts(project_name: str, prompts: list):
    """Helper function to create a project with given prompts"""
    with session_lock:
        db = SessionLocal()
        try:
            # Check if project name already exists
            existing_project = db.query(Project).filter(Project.name == project_name).first()
            if existing_project:
                db.close()
                raise HTTPException(status_code=400, detail="Project name already exists")
            
            # Create project
            project = Project(name=project_name)
            db.add(project)
            db.flush()  # Get the project ID
            
            # Create prompt records
            for index, prompt_text in enumerate(prompts):
                prompt = Prompt(
                    project_id=project.id,
                    text=prompt_text,
                    order_index=index
                )
                db.add(prompt)
            
            db.commit()
            
            return {"project_id": project.id, "prompt_count": len(prompts)}
            
        except Exception as e:
            db.rollback()
            db.close()
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
        finally:
            db.close()

@app.get("/projects/")
def list_projects():
    with session_lock:
        db = SessionLocal()
        try:
            projects = db.query(Project).all()
            result = []
            for p in projects:
                # Get total prompts for this project
                total_prompts = db.query(Prompt).filter(Prompt.project_id == p.id).count()
                
                # Get recordings for this project
                recordings = db.query(Recording).filter(Recording.project_id == p.id).all()
                recorded_count = len(recordings)
                
                # Find last recorded index
                last_recorded_index = -1
                if recordings:
                    # Get the highest order_index from recorded prompts
                    recorded_prompts = db.query(Prompt).join(Recording, Prompt.id == Recording.prompt_id).filter(
                        Prompt.project_id == p.id
                    ).all()
                    if recorded_prompts:
                        last_recorded_index = max(p.order_index for p in recorded_prompts)
                
                result.append({
                    "id": p.id, 
                    "name": p.name, 
                    "created_at": p.created_at.isoformat() + 'Z' if p.created_at else None,
                    "total_prompts": total_prompts,
                    "recorded_count": recorded_count,
                    "last_recorded_index": last_recorded_index
                })
            return {"projects": result}
        finally:
            db.close()

@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    storage_path = get_setting("storage_path", "recordings")
    with session_lock:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Delete all recordings for this project
            recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
            
            for recording in recordings:
                try:
                    file_path = os.path.join(storage_path, recording.filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Failed to delete file {recording.filename}: {e}")
            
            # Delete recordings from database
            db.query(Recording).filter(Recording.project_id == project_id).delete()
            
            # Delete prompts from database
            db.query(Prompt).filter(Prompt.project_id == project_id).delete()
            
            # Delete project
            db.delete(project)
            db.commit()
            
            log_interaction("delete_project", {"project_id": project_id, "name": project.name})
            return {"status": "ok", "message": f"Project '{project.name}' deleted successfully"}
        except Exception as e:
            db.rollback()
            db.close()
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
        finally:
            db.close()

@app.get("/projects/{project_id}")
def get_project(project_id: int):
    with session_lock:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Get prompts for this project
            prompts = db.query(Prompt).filter(
                Prompt.project_id == project_id
            ).order_by(Prompt.order_index).all()
            
            # Get recordings for this project
            recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
            recorded_count = len(recordings)
            
            # Find last recorded index
            last_recorded_index = -1
            if recordings:
                # Get the highest order_index from recorded prompts
                recorded_prompts = db.query(Prompt).join(Recording, Prompt.id == Recording.prompt_id).filter(
                    Prompt.project_id == project_id
                ).all()
                if recorded_prompts:
                    last_recorded_index = max(p.order_index for p in recorded_prompts)
            
            return {
                "id": project.id,
                "name": project.name,
                "created_at": project.created_at.isoformat() + 'Z' if project.created_at else None,
                "prompts": [p.text for p in prompts],
                "total_prompts": len(prompts),
                "recorded_count": recorded_count,
                "last_recorded_index": last_recorded_index
            }
        finally:
            db.close()

@app.get("/projects/{project_id}/recordings")
def get_project_recordings(project_id: int):
    with session_lock:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Get all recordings for this project with prompt information
            recordings = db.query(Recording).join(Prompt, Recording.prompt_id == Prompt.id).options(
                joinedload(Recording.prompt)
            ).filter(
                Recording.project_id == project_id
            ).order_by(Prompt.order_index).all()
            
            result = []
            for rec in recordings:
                result.append({
                    "text": rec.text,
                    "filename": rec.filename,
                    "prompt_id": rec.prompt_id,
                    "order_index": rec.prompt.order_index,
                    "recorded_at": rec.recorded_at.isoformat() + 'Z' if rec.recorded_at else None
                })
            
            return {"recordings": result}
        finally:
            db.close()

@app.post("/upload_audio/")
async def upload_audio(text: str = Form(...), audio: UploadFile = File(...), project_id: int = Form(...)):
    # Generate filename from text
    filename = hashlib.md5(text.encode()).hexdigest() + '.wav'
    
    # Save audio file
    storage_path = get_setting("storage_path", "recordings")
    file_path = os.path.join(storage_path, filename)
    
    with session_lock:
        db = SessionLocal()
        try:
            # Find the prompt for this text and project
            prompt = db.query(Prompt).filter(
                Prompt.project_id == project_id,
                Prompt.text == text
            ).first()
            
            if not prompt:
                db.close()
                raise HTTPException(status_code=404, detail="Prompt not found for this project")
            
            # Check if recording already exists (more comprehensive check)
            existing = db.query(Recording).filter(
                Recording.filename == filename,
                Recording.project_id == project_id,
                Recording.prompt_id == prompt.id
            ).first()
            
            if existing:
                # If recording already exists, just return success (idempotent behavior)
                db.close()
                return {"status": "ok", "filename": filename, "message": "Recording already exists"}
            
            # Save the audio file first
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
            
            # Save recording
            recording = Recording(
                text=text,
                filename=filename,
                project_id=project_id,
                prompt_id=prompt.id
            )
            db.add(recording)
            db.commit()
            
            log_interaction("upload_audio", {
                "filename": filename, 
                "project_id": project_id,
                "prompt_id": prompt.id,
                "text": text
            })
            
            return {"status": "ok", "filename": filename}
        except Exception as e:
            db.rollback()
            # Clean up the file if it was created but database save failed
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            db.close()
            raise HTTPException(status_code=500, detail=f"Failed to save recording: {str(e)}")
        finally:
            db.close()

@app.post("/delete_audio/")
async def delete_audio(text: str = Form(...), project_id: int = Form(...)):
    filename = hashlib.md5(text.encode()).hexdigest() + '.wav'
            # Delete file from storage
    storage_path = get_setting("storage_path", "recordings")    
    with session_lock:
        db = SessionLocal()
        try:
            # Find the prompt for this text and project
            prompt = db.query(Prompt).filter(
                Prompt.project_id == project_id,
                Prompt.text == text
            ).first()
            
            if not prompt:
                db.close()
                raise HTTPException(status_code=404, detail="Prompt not found for this project")
            
            # Find and delete recording
            recording = db.query(Recording).filter(
                Recording.filename == filename,
                Recording.project_id == project_id,
                Recording.prompt_id == prompt.id
            ).first()
            
            if not recording:
                db.close()
                raise HTTPException(status_code=404, detail="Recording not found")
            

            file_path = os.path.join(storage_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database
            db.delete(recording)
            db.commit()
            
            log_interaction("delete_audio", {
                "filename": filename, 
                "project_id": project_id,
                "prompt_id": prompt.id,
                "text": text
            })
            
            return {"status": "ok", "message": "Recording deleted"}
        except Exception as e:
            db.rollback()
            db.close()
            raise HTTPException(status_code=500, detail=f"Failed to delete recording: {str(e)}")
        finally:
            db.close()

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
    storage_path = get_setting("storage_path", "recordings")
    files = [f for f in os.listdir(storage_path) if os.path.isfile(os.path.join(storage_path, f))]
    return {"recordings": files}

# Placeholder for export endpoints
@app.post("/export_s3/")
def export_s3(payload: dict = None):
    bucket = get_setting("s3_bucket", "")
    storage_path = get_setting("storage_path", "recordings")
    if not bucket:
        return {"status": "error", "detail": "S3 bucket not configured"}
    s3 = boto3.client("s3")
    if payload and payload.get("filename"):
        fname = payload["filename"]
        fpath = os.path.join(storage_path, fname)
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
    for fname in os.listdir(storage_path):
        fpath = os.path.join(storage_path, fname)
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
    
    storage_path = get_setting("storage_path", "recordings")


    # Get project info
    with session_lock:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "detail": "Project not found"}
            
            # Get recordings for this project with prompt information
            recordings = db.query(Recording).join(Prompt, Recording.prompt_id == Prompt.id).filter(
                Recording.project_id == project_id
            ).order_by(Prompt.order_index).all()
            
            dataset_rows = []
            for rec in recordings:
                dataset_rows.append({
                    "audio": os.path.join(storage_path, rec.filename),
                    "text": rec.text,
                    "prompt_id": rec.prompt_id,
                    "order_index": rec.prompt.order_index,
                    "recorded_at": rec.recorded_at.isoformat() + 'Z' if rec.recorded_at else None
                })
            
            if not dataset_rows:
                return {"status": "error", "detail": "No audio files found for this project"}
            
            # Create dataset with project name
            dataset_name = f"{repo_id}-{project.name.lower().replace(' ', '-')}"
            
            try:
                # Create dataset
                df = pd.DataFrame(dataset_rows)
                ds = Dataset.from_pandas(df)
                ds = ds.cast_column("audio", Audio())
                

                
                try:
                    # Push to hub with timeout
                    ds.push_to_hub(dataset_name, token=token, private=True)
                except TimeoutError:
                    log_interaction("export_hf_timeout", {"project_id": project_id, "dataset_name": dataset_name})
                    return {"status": "error", "detail": "Upload timed out. Please try again or check your internet connection."}
                except Exception as e:
                    log_interaction("export_hf_error", {"error": str(e), "project_id": project_id})
                    return {"status": "error", "detail": f"Failed to push dataset: {str(e)}"}
                
            except Exception as e:
                log_interaction("export_hf_error", {"error": str(e), "project_id": project_id})
                return {"status": "error", "detail": f"Failed to create dataset: {str(e)}"}
            
            log_interaction("export_hf", {"count": len(dataset_rows), "project_id": project_id, "dataset_name": dataset_name})
            return {"status": "ok", "uploaded": [row["audio"] for row in dataset_rows], "dataset_name": dataset_name}
        finally:
            db.close()

@app.post("/clear_database/")
def clear_database():
    """Clear all data from the database and delete all audio files"""
    storage_path = get_setting("storage_path", "recordings")
    
    # Delete all audio files
    if os.path.exists(storage_path):
        for filename in os.listdir(storage_path):
            file_path = os.path.join(storage_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete file {filename}: {e}")
    
    # Clear all database tables
    with session_lock:
        db = SessionLocal()
        try:
            # Clear all tables in reverse dependency order
            db.query(Interaction).delete()
            db.query(Recording).delete()
            db.query(Prompt).delete()
            db.query(Project).delete()
            db.query(Setting).delete()
            db.commit()
            
            log_interaction("clear_database", {"message": "All data cleared"})
            return {"status": "ok", "message": "All data cleared successfully"}
        except Exception as e:
            db.rollback()
            db.close()
            return {"status": "error", "detail": f"Failed to clear database: {str(e)}"}
        finally:
            db.close()

@app.get("/recordings/{filename}")
def get_recording(filename: str):
    """Serve audio files from the recordings directory"""
    storage_path = get_setting("storage_path", "recordings")
    file_path = os.path.join(storage_path, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return FileResponse(file_path, media_type="audio/wav") 