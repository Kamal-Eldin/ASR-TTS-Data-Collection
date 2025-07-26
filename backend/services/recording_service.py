from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.database import Recording, Prompt
from database.connection import SessionLocal
from database.session import session_lock
from services.settings_service import SettingsService
from utils.file_utils import save_audio_file, delete_audio_file
from utils.logging import log_interaction
import os
from fastapi.responses import FileResponse

class RecordingService:
    @staticmethod
    def upload_audio(text: str, audio_file, project_id: int):
        """Upload audio recording for a specific prompt"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
        with session_lock:
            db = SessionLocal()
            try:
                # Find the prompt for this text and project
                prompt = db.query(Prompt).filter(
                    Prompt.project_id == project_id,
                    Prompt.text == text
                ).first()
                
                if not prompt:
                    raise HTTPException(status_code=404, detail="Prompt not found for this project")
                
                # Generate filename and save audio
                filename = save_audio_file(audio_file, text, storage_path)
                
                # Check if recording already exists
                existing = db.query(Recording).filter(
                    Recording.filename == filename,
                    Recording.project_id == project_id,
                    Recording.prompt_id == prompt.id
                ).first()
                
                if existing:
                    # If recording already exists, just return success (idempotent behavior)
                    return {"status": "ok", "filename": filename, "message": "Recording already exists"}
                
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
                # Clean up the file if it was created but database save failed
                if 'filename' in locals():
                    delete_audio_file(filename, storage_path)
                raise HTTPException(status_code=500, detail=f"Failed to save recording: {str(e)}")
            finally:
                db.close()

    @staticmethod
    def delete_audio(text: str, project_id: int):
        """Delete audio recording for a specific prompt"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
        with session_lock:
            db = SessionLocal()
            try:
                # Find the prompt for this text and project
                prompt = db.query(Prompt).filter(
                    Prompt.project_id == project_id,
                    Prompt.text == text
                ).first()
                
                if not prompt:
                    raise HTTPException(status_code=404, detail="Prompt not found for this project")
                
                # Find and delete recording
                recording = db.query(Recording).filter(
                    Recording.text == text,
                    Recording.project_id == project_id,
                    Recording.prompt_id == prompt.id
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
                    "text": text
                })
                
                return {"status": "ok", "message": "Recording deleted"}
                
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to delete recording: {str(e)}")
            finally:
                db.close()

    @staticmethod
    def get_project_recordings(project_id: int):
        """Get all recordings for a specific project"""
        with session_lock:
            db = SessionLocal()
            try:
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

    @staticmethod
    def list_recordings():
        """List all recording files"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        files = [f for f in os.listdir(storage_path) if os.path.isfile(os.path.join(storage_path, f))]
        return {"recordings": files}

    @staticmethod
    def get_recording(filename: str):
        """Get a specific recording file"""
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        file_path = os.path.join(storage_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        return FileResponse(file_path, media_type="audio/wav") 