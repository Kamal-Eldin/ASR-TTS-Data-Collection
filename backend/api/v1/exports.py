from fastapi import APIRouter, Form
from services.export_service import ExportService

router = APIRouter(tags=["exports"])

@router.post("/export_s3/")
def export_s3(payload: dict = None):
    return ExportService.export_to_s3(payload)

@router.post("/export_hf/")
def export_hf(project_id: int = Form(...)):
    return ExportService.export_to_huggingface(project_id)

@router.post("/clear_database/")
def clear_database():
    return ExportService.clear_database() 