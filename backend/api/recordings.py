from fastapi import APIRouter, Depends, File, UploadFile, Form
from api.dependencies import AuthenticatedUser, get_current_user
from services.recording_service import RecordingService

router = APIRouter(tags=["recordings"])

@router.post("/upload_audio/")
async def upload_audio(
    text: str = Form(...),
    audio: UploadFile = File(...),
    project_id: int = Form(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return RecordingService.upload_audio(text, audio, project_id, current_user.id)

@router.post("/delete_audio/")
async def delete_audio(
    text: str = Form(...),
    project_id: int = Form(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return RecordingService.delete_audio(text, project_id, current_user.id)

@router.get("/list_recordings/")
def list_recordings(current_user: AuthenticatedUser = Depends(get_current_user)):
    return RecordingService.list_recordings(current_user.id)

@router.get("/recordings/{filename}")
def get_recording(filename: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    return RecordingService.get_recording(filename, current_user.id)
