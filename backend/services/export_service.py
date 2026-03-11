import os

from boto3 import client
from datasets import Audio, Dataset

from config import AppConfig
from database.connection import SessionLocal
from database.session import session_lock
from models.database import Project, Prompt, Recording, Setting
from services.settings_service import SettingsService
from utils.file_utils import delete_audio_file
from utils.logging import log_interaction


class ExportService:
    @staticmethod
    def get_s3_client() -> client:
        return client(
            "s3",
            aws_access_key_id=AppConfig.get_aws_access_id(),
            aws_secret_access_key=AppConfig.get_aws_access_secret(),
        )

    @classmethod
    def export_to_s3(cls, user_id: int, payload: dict = None):
        """Export only the current user's recordings to Amazon S3."""
        bucket = SettingsService.get_setting("s3_bucket", AppConfig.BUCKET, user_id=user_id)
        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)
        if not bucket:
            return {"status": "error", "detail": "S3 bucket not configured"}

        with session_lock:
            db = SessionLocal()
            try:
                query = db.query(Recording.filename).join(
                    Project, Recording.project_id == Project.id
                ).filter(Project.user_id == user_id)

                if payload and payload.get("filename"):
                    query = query.filter(Recording.filename == payload["filename"])

                filenames = [filename for (filename,) in query.all()]
            finally:
                db.close()

        s3 = cls.get_s3_client()
        uploaded = []
        for filename in filenames:
            file_path = os.path.join(storage_path, filename)
            if not os.path.isfile(file_path):
                continue
            try:
                s3.upload_file(file_path, bucket, filename)
                uploaded.append(filename)
            except Exception:
                continue

        return {"status": "ok", "uploaded": uploaded}

    @staticmethod
    def export_to_huggingface(project_id: int, user_id: int):
        """Export a user-owned project to Hugging Face."""
        token = SettingsService.get_setting("huggingface_token", AppConfig.get_hf_token(), user_id=user_id)
        repo_id = SettingsService.get_setting("huggingface_repo", AppConfig.HUGGINGFACE_REPO, user_id=user_id)
        if not token or not repo_id:
            return {"status": "error", "detail": "Hugging Face token or repo not configured"}

        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)

        with session_lock:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id,
                ).first()
                if not project:
                    return {"status": "error", "detail": "Project not found"}

                recordings = db.query(Recording).join(
                    Prompt, Recording.prompt_id == Prompt.id
                ).filter(
                    Recording.project_id == project_id
                ).order_by(Prompt.order_index).all()

                dataset_rows = []
                for recording in recordings:
                    dataset_rows.append({
                        "audio": os.path.join(storage_path, recording.filename),
                        "text": recording.text,
                        "prompt_id": recording.prompt_id,
                        "order_index": recording.prompt.order_index,
                        "recorded_at": recording.recorded_at.isoformat() + 'Z' if recording.recorded_at else None,
                    })

                if not dataset_rows:
                    return {"status": "error", "detail": "No audio files found for this project"}

                dataset_name = f"{repo_id}-{project.name.lower().replace(' ', '-')}"
                ds = Dataset.from_list(dataset_rows)
                ds = ds.cast_column("audio", Audio(sampling_rate=16000, decode=False, mono=False))
                ds.push_to_hub(dataset_name, token=token, private=True)

                log_interaction("export_hf", {"user_id": user_id, "project_id": project_id, "dataset_name": dataset_name})
                return {"status": "ok", "uploaded": [row["audio"] for row in dataset_rows], "dataset_name": dataset_name}
            except TimeoutError:
                log_interaction("export_hf_timeout", {"user_id": user_id, "project_id": project_id})
                return {"status": "error", "detail": "Upload timed out. Please try again."}
            except Exception as exc:
                log_interaction("export_hf_error", {"user_id": user_id, "project_id": project_id, "error": str(exc)})
                return {"status": "error", "detail": f"Failed to export project: {exc}"}
            finally:
                db.close()

    @staticmethod
    def clear_database(user_id: int):
        """Clear only the current user's projects, recordings, prompts, and settings."""
        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)

        with session_lock:
            db = SessionLocal()
            try:
                projects = db.query(Project).filter(Project.user_id == user_id).all()
                project_ids = [project.id for project in projects]
                recordings = db.query(Recording).filter(Recording.project_id.in_(project_ids)).all() if project_ids else []

                for recording in recordings:
                    delete_audio_file(recording.filename, storage_path)

                if project_ids:
                    db.query(Recording).filter(Recording.project_id.in_(project_ids)).delete(synchronize_session=False)
                    db.query(Prompt).filter(Prompt.project_id.in_(project_ids)).delete(synchronize_session=False)
                    db.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)

                db.query(Setting).filter(Setting.user_id == user_id).delete(synchronize_session=False)
                db.commit()

                log_interaction("clear_user_data", {"user_id": user_id, "project_count": len(project_ids)})
                return {"status": "ok", "message": "Your data was cleared successfully"}
            except Exception as exc:
                db.rollback()
                return {"status": "error", "detail": f"Failed to clear your data: {exc}"}
            finally:
                db.close()
