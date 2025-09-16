# STT-TTS Dataset Generator

This is a fork of the original repo for the text-to-speech dataset collection web application [TTS Dataset Generator](https://github.com/Oddadmix/Voice-Dataset-Collection).

The application supports CSV upload and multi-line text input, multiple projects, RTL language support, and export to Amazon S3 and Hugging Face.
## Quick Start

1. Clone the repo
   ```bash
   git clone https://github.com/Kamal-Eldin/ASR-TTS-Data-Collection
   ```
2. Ensure docker daemon is running
3. Open project in vscode devcontainer
   > Ensures the installation of dependencies

4. Execute the make target `deploy`
```shell
> make deploy
```
Visit `http://localhost:8500` to reach the web app


#### Environment Variables
The make target copies `.env.template` into `.env` at the root path for setting up docker compose.

The following environment variables must be declared in the project environment. These variables are curated in `.env.template` at the repo's root.


```bash
# Database Configuration
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_ROOT_PASSWORD=admin
MYSQL_USER=admin
MYSQL_PASSWORD=admin
MYSQL_DATABASE=tts_dataset_generator

# Application Configuration
STORAGE_PATH=recordings

# Export Timeouts (in seconds)
HF_EXPORT_TIMEOUT=300
S3_EXPORT_TIMEOUT=300

# AWS Configuration (for S3 export)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

# Hugging Face Configuration (for HF export)
HUGGINGFACE_TOKEN=your_hf_token
HUGGINGFACE_REPO=your_username/your_repo

#app env vars
APP_PORT=8500

# Backend url with respect to a unified container for both front & backend services
BACKEND_URL=http://localhost:${APP_PORT}
```

## Database 
Available as a docker container, with in the docker compose network.


## Features

- 📁 **Multi-Project Support**: Upload multiple CSV files, each as a separate project
- 🎤 **Audio Recording**: Record audio for each prompt with keyboard controls
- 🗂️ **Project Management**: Create, delete, and manage projects independently
- 📊 **Progress Tracking**: Track recording progress and resume from last position
- 🎵 **Audio Playback**: Play previous recordings within projects
- ☁️ **Export Options**: Export datasets to Amazon S3 or Hugging Face
- ⚙️ **Settings Management**: Configure storage paths and API credentials
- 🗄️ **Database Management**: Clear entire database when needed
- 🌐 **RTL Language Support**: Full support for Right-to-Left languages (Arabic, Persian)
- 📝 **Flexible Input Methods**: CSV upload or multi-line text input
- 🎯 **Smart UI**: RTL text display with English interface

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python + SQLAlchemy
- **Database**: MySQL (with SQLite fallback for development)
- **Storage**: Local filesystem + Amazon S3 + Hugging Face Datasets

## Prerequisites

- Docker Desktop
- Python 3.8+
- Node.js 16+
- MySQL 8.0+ (optional - SQLite fallback available)

## Usage

### Creating a Project

1. Click "New Project" on the main page
2. Enter a project name
3. Choose input method:
   - **CSV Upload**: Select a CSV file with prompts (one prompt per row)
   - **Multi-line Text**: Type or paste prompts directly (one per line)
4. **Optional**: Check "Right-to-Left (RTL) Language" for Arabic, Persian, etc.
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
- Proper text alignment for Arabic, Persian, etc.
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

MIT

## Contributing

Feel free to contribute and open a PR
