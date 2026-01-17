import csv
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from database.session import get_db
from models.database import Project, Prompt, User, ProjectCollaborator
from models.schemas import ProjectCreate, ProjectResponse, PromptResponse, CollaboratorResponse
from core.dependencies import get_current_user
from utils.logging import logger

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


def get_accessible_project(project_id: int, user_id: int, db: Session, owner_only: bool = False) -> Optional[Project]:
    """Get project if user owns it or is a collaborator"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    if project.user_id == user_id:
        return project
    if owner_only:
        return None
    # Check if user is a collaborator
    collab = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id,
        ProjectCollaborator.user_id == user_id
    ).first()
    return project if collab else None


def enrich_project_response(project: Project, current_user_id: int, db: Session) -> dict:
    """Add is_owner, owner_username, and collaborator_count to project response"""
    collaborator_count = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project.id
    ).count()

    return {
        "id": project.id,
        "name": project.name,
        "is_rtl": bool(project.is_rtl),
        "user_id": project.user_id,
        "created_at": project.created_at,
        "is_owner": project.user_id == current_user_id,
        "owner_username": project.owner.username if project.owner else None,
        "collaborator_count": collaborator_count
    }

@router.get("/")
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user (owned and shared)"""
    # Get owned projects
    owned_projects = db.query(Project).filter(Project.user_id == current_user.id).all()

    # Get shared projects
    shared_project_ids = db.query(ProjectCollaborator.project_id).filter(
        ProjectCollaborator.user_id == current_user.id
    ).all()
    shared_projects = db.query(Project).filter(
        Project.id.in_([p[0] for p in shared_project_ids])
    ).all() if shared_project_ids else []

    # Combine and enrich with ownership info
    all_projects = owned_projects + shared_projects
    return [enrich_project_response(p, current_user.id, db) for p in all_projects]

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

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project (owner or collaborator)"""
    project = get_accessible_project(project_id, current_user.id, db)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return enrich_project_response(project, current_user.id, db)

@router.get("/{project_id}/prompts", response_model=List[PromptResponse])
async def get_project_prompts(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all prompts for a project (owner or collaborator)"""
    project = get_accessible_project(project_id, current_user.id, db)

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
    """Get all recordings for a project (owner or collaborator)"""
    from models.database import Recording

    project = get_accessible_project(project_id, current_user.id, db)

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


# ============== Sharing Endpoints ==============

@router.post("/{project_id}/share")
async def share_project(
    project_id: int,
    email_or_username: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a project with another user by email or username (owner only)"""
    # Verify ownership (only owner can share)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you don't have permission to share it"
        )

    # Find user by email or username
    target_user = db.query(User).filter(
        or_(User.email == email_or_username, User.username == email_or_username)
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent sharing with self
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot share a project with yourself"
        )

    # Check if already shared
    existing = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id,
        ProjectCollaborator.user_id == target_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already shared with this user"
        )

    # Create collaborator entry
    collaborator = ProjectCollaborator(
        project_id=project_id,
        user_id=target_user.id
    )
    db.add(collaborator)
    db.commit()

    logger.info(f"Project '{project.name}' shared with user '{target_user.username}' by {current_user.username}")

    return {
        "message": f"Project shared with {target_user.username}",
        "collaborator": {
            "id": collaborator.id,
            "user_id": target_user.id,
            "username": target_user.username,
            "email": target_user.email,
            "added_at": collaborator.added_at.isoformat() + 'Z'
        }
    }


@router.get("/{project_id}/collaborators")
async def get_project_collaborators(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all collaborators for a project (owner or collaborator can view)"""
    project = get_accessible_project(project_id, current_user.id, db)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    collaborators = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id
    ).all()

    result = []
    for collab in collaborators:
        user = db.query(User).filter(User.id == collab.user_id).first()
        if user:
            result.append({
                "id": collab.id,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "added_at": collab.added_at.isoformat() + 'Z' if collab.added_at else None
            })

    return {"collaborators": result, "is_owner": project.user_id == current_user.id}


@router.delete("/{project_id}/collaborators/{user_id}")
async def remove_collaborator(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a collaborator from a project (owner only)"""
    # Verify ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you don't have permission"
        )

    # Find and delete collaborator
    collaborator = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id,
        ProjectCollaborator.user_id == user_id
    ).first()

    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    db.delete(collaborator)
    db.commit()

    logger.info(f"Removed collaborator {user_id} from project '{project.name}'")

    return {"message": "Collaborator removed successfully"}