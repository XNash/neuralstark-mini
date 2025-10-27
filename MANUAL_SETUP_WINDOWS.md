# NeuralStark - Manual Setup Guide for Windows

This guide explains how to run NeuralStark manually on Windows without PM2, Supervisor, or automated scripts.

## Prerequisites

Before starting, ensure you have the following installed:

1. **Python 3.10+** - [Download from python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
3. **MongoDB Community Edition** - [Download from mongodb.com](https://www.mongodb.com/try/download/community)
4. **Git** (optional) - For cloning the repository

## Directory Structure

```
NeuralStark/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── files/            # Documents to index
└── .cache/           # Model cache (auto-created)
```

## Setup Instructions

### 1. Install Backend Dependencies

Open **Command Prompt** or **PowerShell** in the project directory:

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

Open a **new terminal** in the project directory:

```cmd
cd frontend
npm install
```

Or if you prefer Yarn:

```cmd
cd frontend
yarn install
```

### 3. Configure Environment Variables

#### Backend Configuration (`backend/.env`)

Create or edit `backend/.env`:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_platform

# CORS Configuration
CORS_ORIGINS=*

# Cache directories (adjust to your project path)
HF_HOME=C:/path/to/your/project/.cache/huggingface
TRANSFORMERS_CACHE=C:/path/to/your/project/.cache/huggingface
SENTENCE_TRANSFORMERS_HOME=C:/path/to/your/project/.cache/sentence_transformers
```

**Important:** Replace `C:/path/to/your/project` with your actual project path.

#### Frontend Configuration (`frontend/.env`)

Create or edit `frontend/.env`:

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# WebSocket configuration for development
WDS_SOCKET_PORT=0
```

### 4. Add Your Documents

Place your documents (PDF, DOCX, TXT, JSON, etc.) in the `files/` directory:

```
files/
├── company_info.md
├── products.txt
└── faq.json
```

## Running the Application

You'll need **three separate terminal windows**.

### Terminal 1: Start MongoDB

```cmd
mongod --dbpath C:\data\db
```

**Note:** You may need to create the data directory first:
```cmd
mkdir C:\data\db
```

If MongoDB is installed as a Windows service, you can start it with:
```cmd
net start MongoDB
```

### Terminal 2: Start Backend

```cmd
cd backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Options:**
- `--reload` - Auto-restart on code changes (development mode)
- `--host 0.0.0.0` - Accept connections from any IP
- `--port 8001` - Backend runs on port 8001

### Terminal 3: Start Frontend

```cmd
cd frontend
npm start
```

Or with Yarn:
```cmd
cd frontend
yarn start
```

The frontend will automatically open in your browser at `http://localhost:3000`

## Using the Application

1. **Open Browser:** Navigate to `http://localhost:3000`
2. **Configure API Key:**
   - Go to Settings page
   - Enter your Gemini API key (get it from [Google AI Studio](https://aistudio.google.com/app/apikey))
   - Click Save
3. **Index Documents:**
   - Go to Documents page
   - Click "Reindex Documents" button
4. **Start Chatting:**
   - Go to Chat page
   - Ask questions about your documents

## API Endpoints

Backend API is available at `http://localhost:8001`

- `GET /api/` - API info
- `GET /api/health` - Health check
- `POST /api/chat` - Chat with documents
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings
- `GET /api/documents/status` - Document statistics
- `POST /api/documents/reindex` - Reindex documents

## Stopping the Application

To stop the application:

1. Press `Ctrl+C` in each terminal window
2. If MongoDB is running as a service:
   ```cmd
   net stop MongoDB
   ```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

**Find process using port:**
```cmd
netstat -ano | findstr :8001
netstat -ano | findstr :3000
```

**Kill process:**
```cmd
taskkill /PID <process_id> /F
```

### Python Virtual Environment Issues

If `venv\Scripts\activate` doesn't work:

**PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

### MongoDB Connection Failed

1. Check if MongoDB is running:
   ```cmd
   tasklist | findstr mongod
   ```

2. Test MongoDB connection:
   ```cmd
   mongosh
   ```

3. Check MongoDB logs in: `C:\Program Files\MongoDB\Server\7.0\log\`

### Missing Dependencies

If you get import errors:

```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

### Frontend Build Issues

Clear cache and reinstall:

```cmd
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

## Development Tips

### Auto-Reload

Both backend and frontend support auto-reload:
- **Backend:** `--reload` flag (already in command)
- **Frontend:** Automatic with React development server

### Viewing Logs

- **Backend:** Logs appear in the terminal running uvicorn
- **Frontend:** Logs appear in the terminal running npm/yarn
- **Browser Console:** Open DevTools (F12) for frontend errors

### Database Inspection

Use MongoDB Compass or mongosh:

```cmd
mongosh
use rag_platform
db.settings.find()
db.messages.find()
db.document_cache.find()
```

## Optional: Simple Batch Scripts

You can create batch scripts for convenience:

### `start-backend.bat`

```batch
@echo off
cd backend
call venv\Scripts\activate.bat
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### `start-frontend.bat`

```batch
@echo off
cd frontend
npm start
```

### `start-all.bat`

```batch
@echo off
echo Starting NeuralStark...
echo.
echo Starting MongoDB...
start "MongoDB" mongod --dbpath C:\data\db
timeout /t 3 /nobreak >nul

echo Starting Backend...
start "Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 5 /nobreak >nul

echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo All services starting...
echo Frontend will open at http://localhost:3000
echo.
pause
```

Make these executable and double-click to start.

## Next Steps

1. Add your Gemini API key in Settings
2. Add documents to the `files/` directory
3. Reindex documents
4. Start asking questions!

## Support

- Check logs in the terminal windows
- Review error messages in browser console (F12)
- Ensure all services are running
- Verify environment variables are correct

---

**Happy chatting with your documents! 🚀**
