import csv
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from api.dependencies import AuthenticatedUser, get_current_user
from services.project_service import ProjectService
from utils.logging import logger

router = APIRouter(tags=["projects"])

@router.post("/upload_csv/")
async def upload_csv(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    is_rtl: bool = Form(False),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV content
    content = await file.read()
    text = content.decode('utf-8')
    logger.debug(f"decoded csv content: {text[:13]}")
    
    # Parse CSV
    prompts = []
    csv_reader = csv.reader(text.splitlines())
    for row in csv_reader:
        if row and row[0].strip():  # Skip empty rows
            prompts.append(row[0].strip())
    
    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found in CSV")
    
    return ProjectService.create_project_with_prompts(current_user.id, project_name, prompts, is_rtl)

@router.post("/create_project/")
async def create_project_with_text(
    project_name: str = Form(...),
    prompts_text: str = Form(...),
    is_rtl: bool = Form(False),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a project with prompts from multi-line text input"""
    if not prompts_text.strip():
        logger.error(f"no prompts provided")
        raise HTTPException(status_code=400, detail="No prompts provided")
    
    # Split by lines and filter empty lines
    # Handle both \n and \r\n line endings
    prompts = [line.strip() for line in prompts_text.replace('\r\n', '\n').split('\n') if line.strip()]
    
    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found in text")
    
    return ProjectService.create_project_with_prompts(current_user.id, project_name, prompts, is_rtl)

@router.get("/projects/")
def list_projects(current_user: AuthenticatedUser = Depends(get_current_user)):
    return ProjectService.list_projects(current_user.id)

@router.get("/projects/{project_id}")
def get_project(project_id: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    return ProjectService.get_project(project_id, current_user.id)

@router.get("/projects/{project_id}/recordings")
def get_project_recordings(project_id: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    from services.recording_service import RecordingService
    return RecordingService.get_project_recordings(project_id, current_user.id)

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    return ProjectService.delete_project(project_id, current_user.id)
