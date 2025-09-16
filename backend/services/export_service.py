import os
import boto3
import pandas as pd
from datasets import Dataset, Audio
from sqlalchemy.orm import Session, joinedload
from models.database import Project, Recording, Prompt, Setting, Interaction
from database.connection import SessionLocal
from database.session import session_lock
from services.settings_service import SettingsService
from utils.logging import log_interaction
from config import AppConfig

'''
export services offers 2 export methods to S3 and to huggingface
'''


class ExportService:
    @staticmethod
    def export_to_s3(payload: dict = None):
        """Export recordings to Amazon S3"""
        bucket = SettingsService.get_setting("s3_bucket", "")
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
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

    @staticmethod
    def export_to_huggingface(project_id: int):
        """Export project recordings to Hugging Face"""
        token = SettingsService.get_setting("huggingface_token", default=AppConfig.HUGGINGFACE_TOKEN)
        repo_id = SettingsService.get_setting("huggingface_repo", default=AppConfig.HUGGINGFACE_REPO)
        
        if not token or not repo_id:
            return {"status": "error", "detail": "Hugging Face token or repo not configured"}
        
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
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
                    
                    ds = Dataset.from_list(dataset_rows)
                    ds = ds.cast_column("audio", Audio(sampling_rate=16000, decode=False, mono=False))
                    
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

    @staticmethod
    def clear_database():
        """Clear all data from the database and delete all audio files"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
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
                return {"status": "error", "detail": f"Failed to clear database: {str(e)}"}
            finally:
                db.close() 