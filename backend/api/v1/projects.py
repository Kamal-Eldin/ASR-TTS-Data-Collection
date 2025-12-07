import csv
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from models.database import Project, Prompt, User
from models.schemas import ProjectCreate, ProjectResponse, PromptResponse
from core.dependencies import get_current_user
from utils.logging import logger

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])

@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_name: str = Form(...),
    prompts_text: str = Form(None),
    is_rtl: bool = Form(False),
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project with prompts from CSV or text input"""

    # Check if user already has a project with this name
    existing = db.query(Project).filter(
        Project.name == project_name,
        Project.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a project with this name"
        )

    # Process prompts from either CSV file or text input
    prompts = []

    if file and file.filename:
        # Process CSV file
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        content = await file.read()
        text = content.decode('utf-8')

        csv_reader = csv.reader(text.splitlines())
        for row in csv_reader:
            if row and row[0].strip():  # Skip empty rows
                prompts.append(row[0].strip())

    elif prompts_text:
        # Process text input
        prompts = [line.strip() for line in prompts_text.replace('\r\n', '\n').split('\n') if line.strip()]

    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found")

    # Create project
    db_project = Project(
        name=project_name,
        is_rtl=is_rtl,
        user_id=current_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Create prompts
    for index, prompt_text in enumerate(prompts):
        db_prompt = Prompt(
            project_id=db_project.id,
            user_id=current_user.id,
            text=prompt_text,
            order_index=index
        )
        db.add(db_prompt)

    db.commit()

    logger.info(f"Created project '{project_name}' with {len(prompts)} prompts for user {current_user.username}")

    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project (only if owned by current user)"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project

@router.get("/{project_id}/prompts", response_model=List[PromptResponse])
async def get_project_prompts(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all prompts for a project"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    prompts = db.query(Prompt).filter(
        Prompt.project_id == project_id
    ).order_by(Prompt.order_index).all()

    return prompts

@router.get("/{project_id}/recordings")
async def get_project_recordings(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all recordings for a project"""
    from models.database import Recording

    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    recordings = db.query(Recording).filter(
        Recording.project_id == project_id
    ).all()

    return recordings

@router.post("/{project_id}/prompts")
async def add_prompts_to_project(
    project_id: int,
    prompts_text: str = Form(None),
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add more prompts to an existing project"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Get current max order_index
    max_index = db.query(Prompt).filter(
        Prompt.project_id == project_id
    ).count()

    # Process prompts from either CSV file or text input
    prompts = []

    if file and file.filename:
        # Process CSV file
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        content = await file.read()
        text = content.decode('utf-8')

        csv_reader = csv.reader(text.splitlines())
        for row in csv_reader:
            if row and row[0].strip():
                prompts.append(row[0].strip())

    elif prompts_text:
        # Process text input
        prompts = [line.strip() for line in prompts_text.replace('\r\n', '\n').split('\n') if line.strip()]

    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found")

    # Create new prompts
    for index, prompt_text in enumerate(prompts):
        db_prompt = Prompt(
            project_id=project_id,
            user_id=current_user.id,
            text=prompt_text,
            order_index=max_index + index
        )
        db.add(db_prompt)

    db.commit()

    logger.info(f"Added {len(prompts)} prompts to project '{project.name}' for user {current_user.username}")

    return {"message": f"Added {len(prompts)} prompts", "count": len(prompts)}


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project (only if owned by current user)"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    logger.info(f"Deleted project '{project.name}' for user {current_user.username}")

    return {"message": "Project deleted successfully"}