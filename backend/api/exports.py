from fastapi import APIRouter, Depends, Form
from api.dependencies import AuthenticatedUser, get_current_user
from services.export_service import ExportService

router = APIRouter(tags=["exports"])

@router.post("/export_s3/")
def export_s3(payload: dict = None, current_user: AuthenticatedUser = Depends(get_current_user)):
    return ExportService.export_to_s3(current_user.id, payload)

@router.post("/export_hf/")
def export_hf(project_id: int = Form(...), current_user: AuthenticatedUser = Depends(get_current_user)):
    return ExportService.export_to_huggingface(project_id, current_user.id)

@router.post("/clear_database/")
def clear_database(current_user: AuthenticatedUser = Depends(get_current_user)):
    return ExportService.clear_database(current_user.id)
