# TTS Dataset Generator

A web application for collecting high-quality voice datasets from CSV input with support for multiple projects and export to Amazon S3 and Hugging Face.

## Features

- 📁 **Multi-Project Support**: Upload multiple CSV files, each as a separate project
- 🎤 **Audio Recording**: Record audio for each prompt with keyboard controls
- 🗂️ **Project Management**: Create, delete, and manage projects independently
- 📊 **Progress Tracking**: Track recording progress and resume from last position
- 🎵 **Audio Playback**: Play previous recordings within projects
- ☁️ **Export Options**: Export datasets to Amazon S3 or Hugging Face
- ⚙️ **Settings Management**: Configure storage paths and API credentials
- 🗄️ **Database Management**: Clear entire database when needed

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: MySQL
- **Storage**: Local filesystem + Amazon S3 + Hugging Face Datasets

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tts-dataset-generator
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Database Setup

The application supports both MySQL and SQLite:

**Option A: MySQL (Recommended for Production)**
```bash
# 1. Install MySQL (if not already installed)
# macOS: brew install mysql
# Ubuntu/Debian: sudo apt install mysql-server
# Windows: Download from https://dev.mysql.com/downloads/mysql/

# 2. Configure database settings
cp env.example .env
# Edit .env with your MySQL credentials

# 3. Start MySQL and setup database
python start_mysql.py

# 4. Start the application
uvicorn main:app --reload
```

**Option B: SQLite (Development/Testing)**
```bash
# The application will automatically fall back to SQLite if MySQL is not available
# No additional setup required
uvicorn main:app --reload
```

#### Environment Variables (Optional)

Create a `.env` file in the backend directory:
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=tts_dataset_generator
STORAGE_PATH=recordings
HF_EXPORT_TIMEOUT=300
S3_EXPORT_TIMEOUT=300
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### 2. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:3000`

## Usage

### Creating a Project

1. Click "New Project" on the main page
2. Enter a project name
3. Select a CSV file with prompts (one prompt per row)
4. Click "Create Project"

### Recording Audio

1. Navigate to a project
2. Use keyboard controls:
   - **Enter**: Start/Stop recording
   - **Left Arrow**: Skip to next prompt
   - **Right Arrow**: Go to previous prompt
   - **Space**: Play/Stop current recording

### Exporting Datasets

1. **Hugging Face Export**:
   - Configure your Hugging Face token in Settings
   - Set your repository name
   - Click "Export to Hugging Face"

2. **Amazon S3 Export**:
   - Configure your AWS credentials in Settings
   - Set your S3 bucket name
   - Click "Export to S3"

## Database Schema

### Tables

- **settings**: Application configuration
- **projects**: Project information and prompts
- **recordings**: Audio recordings metadata
- **interactions**: User interaction logs

### Key Features

- **Project Isolation**: Each project has its own recordings
- **Progress Tracking**: Resume recording from last position
- **Metadata Storage**: Recording timestamps and file information
- **Audit Trail**: Log all user interactions

## Configuration

### Storage Path

Configure where audio files are stored:
- Default: `recordings/` directory
- Can be changed in Settings

### Export Settings

- **Hugging Face**: Token and repository configuration
- **Amazon S3**: Bucket name and credentials
- **Timeouts**: Configurable export timeouts

## Troubleshooting

### Database Issues

**MySQL Connection Problems:**
```bash
# Check if MySQL is running
# macOS
brew services list | grep mysql

# Linux
sudo systemctl status mysql

# Test MySQL connection
python start_mysql.py
```

**Automatic Fallback to SQLite:**
- If MySQL is not available, the application automatically falls back to SQLite
- This is perfect for development and testing
- You'll see a message: "⚠️ MySQL connection failed, falling back to SQLite for development..."

**Migration from SQLite to MySQL:**
```bash
# If you have existing data in SQLite and want to migrate to MySQL
python migrate_sqlite_to_mysql.py
```

### Port Conflicts

If ports are already in use:
```bash
# Kill processes on specific ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### Permission Issues

Ensure proper file permissions:
```bash
chmod +x backend/setup_database.py
chmod +x backend/start_mysql.py
chmod +x backend/migrate_sqlite_to_mysql.py
mkdir -p recordings
chmod 755 recordings
```

## Development

### Project Structure

```
tts-dataset-generator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── setup_database.py    # Database setup script
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.tsx         # Main application
│   │   └── main.tsx        # Entry point
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
└── recordings/             # Audio storage directory
```

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Create new components in `src/components/`
3. **Database**: Update models and run migrations

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 