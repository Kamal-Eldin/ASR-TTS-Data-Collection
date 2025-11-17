from fastapi import APIRouter, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from services.export_service import ExportService
from core.dependencies import get_current_user
from models.database import User, Project
from database.session import get_db

router = APIRouter(tags=["exports"])

@router.post("/export_s3/")
async def export_s3(
    payload: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If exporting a specific file, verify ownership
    if payload and payload.get("filename"):
        from models.database import Recording
        recording = db.query(Recording).filter(
            Recording.filename == payload["filename"],
            Recording.user_id == current_user.id
        ).first()

        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found or access denied"
            )

    return ExportService.export_to_s3(payload, current_user.id, db)

@router.post("/export_hf/")
async def export_hf(
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    return ExportService.export_to_huggingface(project_id, current_user.id)

@router.post("/clear_user_data/")
async def clear_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all data for the current user only (safer than clearing entire database)"""
    return ExportService.clear_user_data(current_user.id, db) 