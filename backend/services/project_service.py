from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.database import Project, Prompt
from database.connection import SessionLocal
from database.session import session_lock
from utils.logging import logger


class ProjectService:
    @staticmethod
    def create_project_with_prompts(project_name: str, prompts: list, is_rtl: bool = False):
        """Create a project with given prompts"""
        with session_lock:
            db = SessionLocal()
            logger.debug(f"Retrieved db session: {SessionLocal.kw}")
            try:
                # Check if project name already exists
                existing_project = db.query(Project).filter(Project.name == project_name).first()
                if existing_project:
                    raise HTTPException(status_code=400, detail="Project name already exists")
                
                # Create project
                project = Project(name=project_name, is_rtl=1 if is_rtl else 0)
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
                logger.debug(f"project_id: {project.id}, prompt_count: {len(prompts)}, is_rtl: {is_rtl}")
                return {"project_id": project.id, "prompt_count": len(prompts), "is_rtl": is_rtl}
                
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
            finally:
                db.close()

    @staticmethod
    def list_projects():
        """List all projects with their statistics"""
        with session_lock:
            db = SessionLocal()
            try:
                projects = db.query(Project).all()
                result = []
                for p in projects:
                    # Get total prompts for this project
                    total_prompts = db.query(Prompt).filter(Prompt.project_id == p.id).count()
                    
                    # Get recordings for this project
                    from models.database import Recording
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
                        "is_rtl": bool(p.is_rtl),
                        "created_at": p.created_at.isoformat() + 'Z' if p.created_at else None,
                        "total_prompts": total_prompts,
                        "recorded_count": recorded_count,
                        "last_recorded_index": last_recorded_index
                    })
                return {"projects": result}
            finally:
                db.close()

    @staticmethod
    def get_project(project_id: int):
        """Get a specific project with its prompts"""
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
                from models.database import Recording
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
                    "is_rtl": bool(project.is_rtl),
                    "created_at": project.created_at.isoformat() + 'Z' if project.created_at else None,
                    "prompts": [p.text for p in prompts],
                    "total_prompts": len(prompts),
                    "recorded_count": recorded_count,
                    "last_recorded_index": last_recorded_index
                }
            finally:
                db.close()

    @staticmethod
    def delete_project(project_id: int):
        """Delete a project and all its associated data"""
        from services.settings_service import SettingsService
        from models.database import Recording
        from utils.file_utils import delete_audio_file
        
        storage_path = SettingsService.get_setting("storage_path", "recordings")
        
        with session_lock:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                
                # Delete all recordings for this project
                recordings = db.query(Recording).filter(Recording.project_id == project_id).all()
                
                for recording in recordings:
                    delete_audio_file(recording.filename, storage_path)
                
                # Delete recordings from database
                db.query(Recording).filter(Recording.project_id == project_id).delete()
                
                # Delete prompts from database
                db.query(Prompt).filter(Prompt.project_id == project_id).delete()
                
                # Delete project
                db.delete(project)
                db.commit()
                
                from utils.logging import log_interaction
                log_interaction("delete_project", {"project_id": project_id, "name": project.name})
                
                return {"status": "ok", "message": f"Project '{project.name}' deleted successfully"}
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
            finally:
                db.close() 