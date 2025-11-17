import os
import boto3
from boto3 import client
import pandas as pd
from datasets import Dataset, Audio
from sqlalchemy.orm import Session, joinedload
from models.database import Project, Recording, Prompt, Setting, Interaction
from database.connection import SessionLocal
from database.session import session_lock
from services.settings_service import SettingsService
from utils.logging import log_interaction
from core.config import AppConfig

'''
export services offers 2 export methods to S3 and to huggingface
'''


class ExportService:
    @staticmethod
    def get_s3_client()-> client:
        s3:client = client("s3", 
                        aws_access_key_id= AppConfig.get_aws_access_id(),
                        aws_secret_access_key= AppConfig.get_aws_access_secret()
                        )
        return s3
    @classmethod
    def export_to_s3(cls, payload: dict = None, user_id: int = None, db: Session = None):
        """Export recordings to Amazon S3"""
        from services.settings_service import SettingsService

        # Get user-specific settings if user_id provided
        if user_id and db:
            bucket = SettingsService.get_user_setting("s3_bucket", user_id, "", db)
            storage_path = SettingsService.get_user_setting("storage_path", user_id, "recordings", db)
        else:
            bucket = SettingsService.get_setting("s3_bucket", "")
            storage_path = SettingsService.get_setting("storage_path", "recordings")

        s3:client = cls.get_s3_client()
        print(s3)

        if not bucket:
            return {"status": "error", "detail": "S3 bucket not configured"}
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
        
        # fallback: upload all user's recordings
        uploaded = []

        # If user_id is provided, only upload user's files
        if user_id and db:
            from models.database import Recording
            user_recordings = db.query(Recording).filter(Recording.user_id == user_id).all()

            for rec in user_recordings:
                fpath = os.path.join(storage_path, rec.filename)
                if os.path.isfile(fpath):
                    try:
                        print(f"uploading file {rec.filename} to {bucket} at {fpath}")
                        s3.upload_file(fpath, bucket, rec.filename)
                        uploaded.append(rec.filename)
                    except Exception as e:
                        continue
        else:
            # Legacy behavior - upload all files (not recommended)
            for fname in os.listdir(storage_path):
                fpath = os.path.join(storage_path, fname)
                if os.path.isfile(fpath):
                    try:
                        print(f"uploading file {fname} to {bucket} at {fpath}")
                        s3.upload_file(fpath, bucket, fname)
                        uploaded.append(fname)
                    except Exception as e:
                        continue

        return {"status": "ok", "uploaded": uploaded}

    @staticmethod
    def export_to_huggingface(project_id: int, user_id: int):
        """Export project recordings to Hugging Face"""
        # Get user-specific settings
        with session_lock:
            db_temp = SessionLocal()
            try:
                token = SettingsService.get_user_setting("huggingface_token", user_id, AppConfig.get_hf_token(), db_temp)
                repo_id = SettingsService.get_user_setting("huggingface_repo", user_id, AppConfig.HUGGINGFACE_REPO, db_temp)
                storage_path = SettingsService.get_user_setting("storage_path", user_id, "recordings", db_temp)
            finally:
                db_temp.close()
        
        if not token or not repo_id:
            return {"status": "error", "detail": "Hugging Face token or repo not configured"}

        # Get project info and verify ownership
        with session_lock:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id
                ).first()
                if not project:
                    return {"status": "error", "detail": "Project not found or access denied"}
                
                # Get recordings for this project with prompt information (already filtered by user via project)
                recordings = db.query(Recording).join(Prompt, Recording.prompt_id == Prompt.id).filter(
                    Recording.project_id == project_id,
                    Recording.user_id == user_id
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
    def clear_user_data(user_id: int, db: Session):
        """Clear all data for a specific user"""
        storage_path = SettingsService.get_user_setting("storage_path", user_id, f"recordings/user_{user_id}", db)
        
        try:
            # Get user's recordings
            user_recordings = db.query(Recording).filter(Recording.user_id == user_id).all()

            # Delete audio files for user's recordings
            deleted_files = 0
            for rec in user_recordings:
                file_path = os.path.join(storage_path, rec.filename)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except Exception as e:
                        print(f"Failed to delete file {rec.filename}: {e}")

            # Clear user's database data in reverse dependency order
            # Interactions (if they have user_id)
            db.query(Interaction).filter(Interaction.user_id == user_id).delete()

            # Recordings
            db.query(Recording).filter(Recording.user_id == user_id).delete()

            # Prompts
            db.query(Prompt).filter(Prompt.user_id == user_id).delete()

            # Projects
            db.query(Project).filter(Project.user_id == user_id).delete()

            # Settings
            db.query(Setting).filter(Setting.user_id == user_id).delete()

            db.commit()

            log_interaction("clear_user_data", {"user_id": user_id, "deleted_files": deleted_files})
            return {"status": "ok", "message": f"User data cleared successfully. Deleted {deleted_files} audio files."}

        except Exception as e:
            db.rollback()
            return {"status": "error", "detail": f"Failed to clear user data: {str(e)}"}

    @staticmethod
    def clear_database():
        """
        DEPRECATED: Clear all data from the database and delete all audio files
        WARNING: This is dangerous and should only be used by admins
        Use clear_user_data() instead for user-specific cleanup
        """
        # This method is kept for backward compatibility but should not be exposed via API
        # without proper admin authentication
        return {"status": "error", "detail": "This operation is deprecated. Use clear_user_data instead."} 