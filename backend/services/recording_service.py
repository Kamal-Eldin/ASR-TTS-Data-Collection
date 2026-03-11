import os

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import joinedload

from config import AppConfig
from database.connection import SessionLocal
from database.session import session_lock
from models.database import Project, Prompt, Recording
from services.settings_service import SettingsService
from utils.file_utils import delete_audio_file, save_audio_file
from utils.logging import log_interaction


class RecordingService:
    @staticmethod
    def _get_owned_project(db, project_id: int, user_id: int) -> Project:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @staticmethod
    def upload_audio(text: str, audio_file, project_id: int, user_id: int):
        """Upload audio for a prompt in a user-owned project."""
        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)

        with session_lock:
            db = SessionLocal()
            try:
                project = RecordingService._get_owned_project(db, project_id, user_id)
                prompt = db.query(Prompt).filter(
                    Prompt.project_id == project.id,
                    Prompt.text == text,
                ).first()
                if not prompt:
                    raise HTTPException(status_code=404, detail="Prompt not found for this project")

                existing = db.query(Recording).filter(
                    Recording.project_id == project.id,
                    Recording.prompt_id == prompt.id,
                ).first()
                if existing:
                    return {"status": "ok", "filename": existing.filename, "message": "Recording already exists"}

                filename = f"user_{user_id}_project_{project.id}_prompt_{prompt.id}.wav"
                save_audio_file(audio_file, storage_path, filename)

                recording = Recording(
                    text=text,
                    filename=filename,
                    project_id=project.id,
                    prompt_id=prompt.id,
                )
                db.add(recording)
                db.commit()

                log_interaction("upload_audio", {
                    "user_id": user_id,
                    "filename": filename,
                    "project_id": project.id,
                    "prompt_id": prompt.id,
                })
                return {"status": "ok", "filename": filename}
            except HTTPException:
                db.rollback()
                raise
            except Exception as exc:
                db.rollback()
                if "filename" in locals():
                    delete_audio_file(filename, storage_path)
                raise HTTPException(status_code=500, detail=f"Failed to save recording: {exc}") from exc
            finally:
                db.close()

    @staticmethod
    def delete_audio(text: str, project_id: int, user_id: int):
        """Delete a recording from a user-owned project."""
        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)

        with session_lock:
            db = SessionLocal()
            try:
                project = RecordingService._get_owned_project(db, project_id, user_id)
                prompt = db.query(Prompt).filter(
                    Prompt.project_id == project.id,
                    Prompt.text == text,
                ).first()
                if not prompt:
                    raise HTTPException(status_code=404, detail="Prompt not found for this project")

                recording = db.query(Recording).filter(
                    Recording.project_id == project.id,
                    Recording.prompt_id == prompt.id,
                ).first()
                if not recording:
                    raise HTTPException(status_code=404, detail="Recording not found")

                delete_audio_file(recording.filename, storage_path)
                db.delete(recording)
                db.commit()

                log_interaction("delete_audio", {
                    "user_id": user_id,
                    "filename": recording.filename,
                    "project_id": project.id,
                    "prompt_id": prompt.id,
                })
                return {"status": "ok", "message": "Recording deleted"}
            except HTTPException:
                db.rollback()
                raise
            except Exception as exc:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to delete recording: {exc}") from exc
            finally:
                db.close()

    @staticmethod
    def get_project_recordings(project_id: int, user_id: int):
        """Get recordings for a user-owned project."""
        with session_lock:
            db = SessionLocal()
            try:
                RecordingService._get_owned_project(db, project_id, user_id)
                recordings = db.query(Recording).join(
                    Prompt, Recording.prompt_id == Prompt.id
                ).options(
                    joinedload(Recording.prompt)
                ).filter(
                    Recording.project_id == project_id
                ).order_by(Prompt.order_index).all()

                return {
                    "recordings": [
                        {
                            "text": recording.text,
                            "filename": recording.filename,
                            "prompt_id": recording.prompt_id,
                            "order_index": recording.prompt.order_index,
                            "recorded_at": recording.recorded_at.isoformat() + 'Z' if recording.recorded_at else None,
                        }
                        for recording in recordings
                    ]
                }
            finally:
                db.close()

    @staticmethod
    def list_recordings(user_id: int):
        """List recording filenames owned by the current user."""
        with session_lock:
            db = SessionLocal()
            try:
                recordings = db.query(Recording.filename).join(
                    Project, Recording.project_id == Project.id
                ).filter(Project.user_id == user_id).all()
                return {"recordings": [filename for (filename,) in recordings]}
            finally:
                db.close()

    @staticmethod
    def get_recording(filename: str, user_id: int):
        """Return a recording file only if it belongs to the current user."""
        with session_lock:
            db = SessionLocal()
            try:
                recording = db.query(Recording).join(
                    Project, Recording.project_id == Project.id
                ).filter(
                    Recording.filename == filename,
                    Project.user_id == user_id,
                ).first()
                if not recording:
                    raise HTTPException(status_code=404, detail="Recording not found")
            finally:
                db.close()

        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)
        file_path = os.path.join(storage_path, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Recording file not found")

        return FileResponse(file_path, media_type="audio/wav")
