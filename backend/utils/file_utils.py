import os
import shutil

def save_audio_file(audio_file, storage_path: str, filename: str) -> str:
    """Save audio file using an explicit filename and return it."""
    os.makedirs(storage_path, exist_ok=True)
    file_path = os.path.join(storage_path, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    return filename

def delete_audio_file(filename: str, storage_path: str):
    """Delete audio file from storage"""
    file_path = os.path.join(storage_path, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete file {filename}: {e}") 
