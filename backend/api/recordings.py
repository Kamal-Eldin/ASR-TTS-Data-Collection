from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from services.recording_service import RecordingService

router = APIRouter(tags=["recordings"])

@router.post("/upload_audio/")
async def upload_audio(text: str = Form(...), audio: UploadFile = File(...), project_id: int = Form(...)):
    return RecordingService.upload_audio(text, audio, project_id)

@router.post("/delete_audio/")
async def delete_audio(text: str = Form(...), project_id: int = Form(...)):
    return RecordingService.delete_audio(text, project_id)

@router.get("/list_recordings/")
def list_recordings():
    return RecordingService.list_recordings()

@router.get("/recordings/{filename}")
def get_recording(filename: str):
    return RecordingService.get_recording(filename) 