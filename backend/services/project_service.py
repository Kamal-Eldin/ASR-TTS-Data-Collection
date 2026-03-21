from fastapi import HTTPException

from config import AppConfig
from database.connection import SessionLocal
from database.session import session_lock
from models.database import Project, Prompt, Recording
from services.settings_service import SettingsService
from utils.file_utils import delete_audio_file
from utils.logging import log_interaction, logger


class ProjectService:
    @staticmethod
    def create_project_with_prompts(user_id: int, project_name: str, prompts: list[str], is_rtl: bool = False):
        """Create a project with prompts for a specific user."""
        with session_lock:
            db = SessionLocal()
            try:
                existing_project = db.query(Project).filter(
                    Project.user_id == user_id,
                    Project.name == project_name,
                ).first()
                if existing_project:
                    raise HTTPException(status_code=400, detail="Project name already exists")

                project = Project(
                    user_id=user_id,
                    name=project_name,
                    is_rtl=1 if is_rtl else 0,
                )
                db.add(project)
                db.flush()

                for index, prompt_text in enumerate(prompts):
                    db.add(Prompt(
                        project_id=project.id,
                        text=prompt_text,
                        order_index=index,
                    ))

                db.commit()
                logger.debug("Created project %s for user %s", project.id, user_id)
                return {"project_id": project.id, "prompt_count": len(prompts), "is_rtl": is_rtl}
            except HTTPException:
                db.rollback()
                raise
            except Exception as exc:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to create project: {exc}") from exc
            finally:
                db.close()

    @staticmethod
    def _project_stats(db, project_id: int) -> tuple[int, int, int]:
        total_prompts = db.query(Prompt).filter(Prompt.project_id == project_id).count()
        recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
        recorded_count = len(recordings)

        last_recorded_index = -1
        if recordings:
            recorded_prompts = db.query(Prompt).join(
                Recording, Prompt.id == Recording.prompt_id
            ).filter(Prompt.project_id == project_id).all()
            if recorded_prompts:
                last_recorded_index = max(prompt.order_index for prompt in recorded_prompts)

        return total_prompts, recorded_count, last_recorded_index

    @staticmethod
    def list_projects(user_id: int):
        """List projects owned by the current user."""
        with session_lock:
            db = SessionLocal()
            try:
                projects = db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()
                result = []
                for project in projects:
                    total_prompts, recorded_count, last_recorded_index = ProjectService._project_stats(db, project.id)
                    result.append({
                        "id": project.id,
                        "name": project.name,
                        "is_rtl": bool(project.is_rtl),
                        "created_at": project.created_at.isoformat() + 'Z' if project.created_at else None,
                        "total_prompts": total_prompts,
                        "recorded_count": recorded_count,
                        "last_recorded_index": last_recorded_index,
                    })
                return {"projects": result}
            finally:
                db.close()

    @staticmethod
    def get_project(project_id: int, user_id: int):
        """Get a user-owned project with prompts and progress."""
        with session_lock:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id,
                ).first()
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")

                prompts = db.query(Prompt).filter(
                    Prompt.project_id == project_id
                ).order_by(Prompt.order_index).all()
                total_prompts, recorded_count, last_recorded_index = ProjectService._project_stats(db, project_id)

                return {
                    "id": project.id,
                    "name": project.name,
                    "is_rtl": bool(project.is_rtl),
                    "created_at": project.created_at.isoformat() + 'Z' if project.created_at else None,
                    "prompts": [prompt.text for prompt in prompts],
                    "total_prompts": total_prompts,
                    "recorded_count": recorded_count,
                    "last_recorded_index": last_recorded_index,
                }
            finally:
                db.close()

    @staticmethod
    def delete_project(project_id: int, user_id: int):
        """Delete a user-owned project and its recordings."""
        storage_path = SettingsService.get_setting("storage_path", AppConfig.STORAGE_PATH, user_id=user_id)

        with session_lock:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id,
                ).first()
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")

                recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
                for recording in recordings:
                    delete_audio_file(recording.filename, storage_path)

                db.query(Recording).filter(Recording.project_id == project_id).delete()
                db.query(Prompt).filter(Prompt.project_id == project_id).delete()
                db.delete(project)
                db.commit()

                log_interaction("delete_project", {"user_id": user_id, "project_id": project_id, "name": project.name})
                return {"status": "ok", "message": f"Project '{project.name}' deleted successfully"}
            except HTTPException:
                db.rollback()
                raise
            except Exception as exc:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to delete project: {exc}") from exc
            finally:
                db.close()
