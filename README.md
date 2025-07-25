# TTS Dataset Generator

A web application for collecting high-quality voice datasets with support for CSV upload and multi-line text input, multiple projects, RTL language support, and export to Amazon S3 and Hugging Face.

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd tts-dataset-generator

# Backend (SQLite for quick start)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5174` to start creating voice datasets!

## Features

- 📁 **Multi-Project Support**: Upload multiple CSV files, each as a separate project
- 🎤 **Audio Recording**: Record audio for each prompt with keyboard controls
- 🗂️ **Project Management**: Create, delete, and manage projects independently
- 📊 **Progress Tracking**: Track recording progress and resume from last position
- 🎵 **Audio Playback**: Play previous recordings within projects
- ☁️ **Export Options**: Export datasets to Amazon S3 or Hugging Face
- ⚙️ **Settings Management**: Configure storage paths and API credentials
- 🗄️ **Database Management**: Clear entire database when needed
- 🌐 **RTL Language Support**: Full support for Right-to-Left languages (Arabic, Hebrew, Persian)
- 📝 **Flexible Input Methods**: CSV upload or multi-line text input
- 🎯 **Smart UI**: RTL text display with English interface

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python + SQLAlchemy
- **Database**: MySQL (with SQLite fallback for development)
- **Storage**: Local filesystem + Amazon S3 + Hugging Face Datasets

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL 8.0+ (optional - SQLite fallback available)
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

The application will be available at `http://localhost:5174` (or the next available port)

## Usage

### Creating a Project

1. Click "New Project" on the main page
2. Enter a project name
3. Choose input method:
   - **CSV Upload**: Select a CSV file with prompts (one prompt per row)
   - **Multi-line Text**: Type or paste prompts directly (one per line)
4. **Optional**: Check "Right-to-Left (RTL) Language" for Arabic, Hebrew, Persian, etc.
5. Click "Create Project"

#### RTL Language Support

When creating projects for RTL languages:
- Check the "Right-to-Left (RTL) Language" checkbox
- The text input area will display in RTL format
- Prompts will be properly formatted in the recording interface
- UI labels remain in English for consistency

### Recording Audio

1. Navigate to a project
2. Use keyboard controls:
   - **Enter**: Start/Stop recording
   - **Left Arrow**: Skip to next prompt
   - **Right Arrow**: Go to previous prompt
   - **Space**: Play/Stop current recording

#### RTL Text Display

For RTL projects, prompts are automatically displayed with proper RTL formatting:
- Text flows from right to left
- Proper text alignment for Arabic, Hebrew, Persian, etc.
- Maintains readability in the recording interface

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
- **projects**: Project information, prompts, and RTL settings
- **prompts**: Individual prompts with order and project association
- **recordings**: Audio recordings metadata with prompt association
- **interactions**: User interaction logs

### Key Features

- **Project Isolation**: Each project has its own recordings
- **Progress Tracking**: Resume recording from last position
- **Metadata Storage**: Recording timestamps and file information
- **Audit Trail**: Log all user interactions
- **RTL Support**: Projects can be marked as RTL for proper text display
- **Prompt Management**: Prompts are stored separately with order preservation

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
lsof -ti:5173 | xargs kill -9  # Frontend (Vite default)
lsof -ti:5174 | xargs kill -9  # Frontend (Vite fallback)
```

**Note**: Vite automatically finds the next available port if 5173 is in use.

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
│   ├── migrate_sqlite_to_mysql.py  # Database migration script
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Projects.tsx # Project management
│   │   │   ├── Recording.tsx # Audio recording interface
│   │   │   └── Settings.tsx # Settings management
│   │   ├── App.tsx         # Main application
│   │   └── main.tsx        # Entry point
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
└── recordings/             # Audio storage directory
```

### RTL Implementation

The application includes comprehensive RTL language support:

- **Database**: Projects have an `is_rtl` field to mark RTL languages
- **Frontend**: Text inputs display in RTL format when RTL is selected
- **Recording Interface**: Prompts are displayed with proper RTL styling
- **UI Consistency**: Interface labels remain in English for consistency

### Input Methods

Two flexible input methods are supported:

1. **CSV Upload**: Traditional CSV file upload with one prompt per row
2. **Multi-line Text**: Direct text input with one prompt per line
   - Supports RTL text input when RTL checkbox is selected
   - Real-time prompt counting
   - Automatic empty line filtering

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Create new components in `src/components/`
3. **Database**: Update models and run migrations

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 