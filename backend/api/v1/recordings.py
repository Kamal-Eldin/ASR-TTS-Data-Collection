from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from services.recording_service import RecordingService
from core.dependencies import get_current_user
from models.database import User, Project, ProjectCollaborator
from database.session import get_db

router = APIRouter(prefix="/api/v1/recordings", tags=["Recordings"])


def can_access_project(project_id: int, user_id: int, db: Session) -> bool:
    """Check if user owns or is collaborator of project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    if project.user_id == user_id:
        return True
    # Check collaborator
    collab = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id,
        ProjectCollaborator.user_id == user_id
    ).first()
    return collab is not None


@router.post("/upload_audio/")
async def upload_audio(
    text: str = Form(...),
    audio: UploadFile = File(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project access (owner or collaborator)
    if not can_access_project(project_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    return RecordingService.upload_audio(text, audio, project_id, current_user.id, db)

@router.post("/delete_audio/")
async def delete_audio(
    text: str = Form(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project access (owner or collaborator)
    if not can_access_project(project_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    return RecordingService.delete_audio(text, project_id, current_user.id, db)

@router.get("/")
async def list_recordings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return RecordingService.list_recordings(current_user.id, db)

@router.get("/{filename}")
async def get_recording(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return RecordingService.get_recording(filename, current_user.id, db) 
