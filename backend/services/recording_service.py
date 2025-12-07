from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.database import Recording, Prompt
from services.settings_service import SettingsService
from utils.file_utils import save_audio_file, delete_audio_file
from utils.logging import log_interaction
from core.config import AppConfig
import os
from fastapi.responses import FileResponse

class RecordingService:
    @staticmethod
    def upload_audio(text: str, audio_file, project_id: int, user_id: int, db: Session):
        """Upload audio recording for a specific prompt"""
        storage_path = SettingsService.get_user_setting(
            "storage_path",
            user_id,
            f"{AppConfig.STORAGE_PATH}/user_{user_id}",
            db
        )
        os.makedirs(storage_path, exist_ok=True)

        try:
            # Find the prompt for this text and project (verify user ownership through prompt)
            prompt = db.query(Prompt).filter(
                Prompt.project_id == project_id,
                Prompt.text == text,
                Prompt.user_id == user_id
            ).first()
            
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt not found for this project")
            
            # Generate filename and save audio
            filename = save_audio_file(audio_file, text, storage_path)
            
            # Check if recording already exists for this user/project/prompt
            existing = db.query(Recording).filter(
                Recording.filename == filename,
                Recording.project_id == project_id,
                Recording.prompt_id == prompt.id,
                Recording.user_id == user_id
            ).first()
            
            if existing:
                return {"status": "ok", "filename": filename, "message": "Recording already exists"}
            
            # Save recording
            recording = Recording(
                text=text,
                filename=filename,
                project_id=project_id,
                prompt_id=prompt.id,
                user_id=user_id
            )
            db.add(recording)
            db.commit()
            
            log_interaction("upload_audio", {
                "filename": filename, 
                "project_id": project_id,
                "prompt_id": prompt.id,
                "text": text,
                "user_id": user_id
            })
            
            return {"status": "ok", "filename": filename}
            
        except Exception as e:
            db.rollback()
            # Clean up the file if it was created but database save failed
            if 'filename' in locals():
                delete_audio_file(filename, storage_path)
            raise HTTPException(status_code=500, detail=f"Failed to save recording: {str(e)}")

    @staticmethod
    def delete_audio(text: str, project_id: int, user_id: int, db: Session):
        """Delete audio recording for a specific prompt"""
        storage_path = SettingsService.get_user_setting(
            "storage_path",
            user_id,
            f"{AppConfig.STORAGE_PATH}/user_{user_id}",
            db
        )
        
        try:
            # Find the prompt for this text and project (verify user ownership)
            prompt = db.query(Prompt).filter(
                Prompt.project_id == project_id,
                Prompt.text == text,
                Prompt.user_id == user_id
            ).first()
            
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt not found for this project")
            
            # Find and delete recording (ensure it belongs to the user)
            recording = db.query(Recording).filter(
                Recording.text == text,
                Recording.project_id == project_id,
                Recording.prompt_id == prompt.id,
                Recording.user_id == user_id
            ).first()
            
            if not recording:
                raise HTTPException(status_code=404, detail="Recording not found")
            
            # Delete file from storage
            delete_audio_file(recording.filename, storage_path)
            
            # Delete from database
            db.delete(recording)
            db.commit()
            
            log_interaction("delete_audio", {
                "filename": recording.filename, 
                "project_id": project_id,
                "prompt_id": prompt.id,
                "text": text,
                "user_id": user_id
            })
            
            return {"status": "ok", "message": "Recording deleted"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete recording: {str(e)}")

    @staticmethod
    def get_project_recordings(project_id: int, user_id: int, db: Session):
        """Get all recordings for a specific project"""
        recordings = db.query(Recording).join(Prompt, Recording.prompt_id == Prompt.id).options(
            joinedload(Recording.prompt)
        ).filter(
            Recording.project_id == project_id,
            Recording.user_id == user_id
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

    @staticmethod
    def list_recordings(user_id: int, db: Session):
        """List all recordings belonging to the current user"""
        recordings = db.query(Recording).filter(Recording.user_id == user_id).all()
        return {
            "recordings": [
                {
                    "filename": rec.filename,
                    "text": rec.text,
                    "project_id": rec.project_id,
                    "prompt_id": rec.prompt_id,
                    "recorded_at": rec.recorded_at.isoformat() + 'Z' if rec.recorded_at else None
                }
                for rec in recordings
            ]
        }

    @staticmethod
    def get_recording(filename: str, user_id: int, db: Session):
        """Get a specific recording file if it belongs to the user"""
        recording = db.query(Recording).filter(
            Recording.filename == filename,
            Recording.user_id == user_id
        ).first()

        if not recording:
            raise HTTPException(status_code=404, detail="Recording not found")

        storage_path = SettingsService.get_user_setting(
            "storage_path",
            user_id,
            f"{AppConfig.STORAGE_PATH}/user_{user_id}",
            db
        )
        file_path = os.path.join(storage_path, recording.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Recording file not found on disk")

        return FileResponse(file_path, media_type="audio/wav") 
