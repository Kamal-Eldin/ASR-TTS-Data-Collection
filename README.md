# Voice Dataset Collection Web App

This web application helps users generate high-quality voice datasets from CSV input. Each row in the CSV is a text prompt for which you can record audio samples, ideal for TTS or ASR dataset creation.

---

## Features
- **CSV Upload:** Upload a CSV file with one prompt per row.
- **Prompt Navigation:** See one prompt at a time, navigate with keyboard shortcuts.
- **Recording:** Record audio for each prompt, play back, delete, and skip.
- **Storage:** Recordings are saved on the server as md5(text).wav in a configurable folder.
- **Export (coming soon):** Upload to S3 or Hugging Face.

---

## Prerequisites
- **Backend:** Python 3.8+
- **Frontend:** Node.js (v16+ recommended), npm

---

## Setup & Run

### 1. Backend (FastAPI)

```bash
# Create and activate a virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn python-multipart boto3 huggingface_hub pydub

# Start the FastAPI server
uvicorn backend.main:app --reload
```
- The backend runs at: http://localhost:8000
- API docs: http://localhost:8000/docs

### 2. Frontend (React)

```bash
# Go to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the React development server
npm start
```
- The frontend runs at: http://localhost:3000

---

## Usage
1. Open http://localhost:3000 in your browser.
2. Upload a CSV file (one prompt per row).
3. Use keyboard shortcuts:
   - **Enter:** Start/Stop recording
   - **Left Arrow:** Next prompt
   - **Space:** Play/Stop audio
   - **Delete button:** Remove a recording
4. Recordings are saved in the `recordings/` folder on the backend.

---

## Troubleshooting
- If you see `Address already in use` for the backend, stop any previous `uvicorn` process or use a different port:
  ```bash
  uvicorn backend.main:app --reload --port 8001
  ```
- Make sure both servers are running at the same time in separate terminal windows/tabs.

---

## Coming Soon
- Export to Amazon S3
- Export to Hugging Face
- Settings screen for storage and export options 