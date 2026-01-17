import os
import shutil
import hashlib
import time

def save_audio_file(audio_file, text: str, storage_path: str, user_id: int = None, project_id: int = None) -> str:
    """Save audio file and return filename"""
    # Generate unique filename from text + user + project + timestamp
    unique_string = f"{text}_{user_id}_{project_id}_{time.time()}"
    filename = hashlib.md5(unique_string.encode()).hexdigest() + '.wav'
    file_path = os.path.join(storage_path, filename)
    
    # Save the audio file
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