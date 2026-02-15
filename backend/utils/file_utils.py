import os
import shutil
import hashlib

def save_audio_file(audio_file, text: str, storage_path: str) -> str:
    """Save audio file and return filename"""
    # Generate filename from text
    filename = hashlib.md5(text.encode()).hexdigest() + '.wav'
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