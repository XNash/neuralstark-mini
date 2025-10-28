# 🪟 Windows Setup Guide for NeuralStark

This guide provides step-by-step instructions for setting up and running NeuralStark on Windows.

## Prerequisites

### Required Software

1. **Python 3.10+** (recommended: 3.11 or 3.12)
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Node.js 18+** (recommended: 18.x or 22.x)
   - Download from [nodejs.org](https://nodejs.org/)
   - LTS version recommended

3. **Yarn Package Manager**
   ```powershell
   npm install -g yarn
   ```

4. **MongoDB** (one of these options):
   - **MongoDB Community Server** - [Download](https://www.mongodb.com/try/download/community)
   - **MongoDB Atlas** - Free cloud database
   - **Docker Desktop** with MongoDB container

### Optional but Recommended

- **Windows Terminal** - Modern terminal with tabs
- **Git for Windows** - For version control
- **Visual Studio Code** - Recommended code editor

## Installation Steps

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd neuralstark
```

### 2. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env
```

Edit `backend\.env` and configure:

```env
# MongoDB connection (local or Atlas)
MONGO_URL=mongodb://localhost:27017/
DB_NAME=rag_platform

# Cerebras API Key (get from https://cloud.cerebras.ai)
CEREBRAS_API_KEY=your_api_key_here
```

### 3. Frontend Setup

```powershell
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
yarn install

# Create .env file
Copy-Item .env.example .env
```

Edit `frontend\.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 4. Create Required Directories

The application will create these automatically, but you can create them manually:

```powershell
# From project root
New-Item -ItemType Directory -Force -Path files
New-Item -ItemType Directory -Force -Path chroma_db
New-Item -ItemType Directory -Force -Path .cache
```

## Running the Application

### Method 1: Separate Terminals (Recommended for Development)

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python server.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
yarn start:win
```

**Terminal 3 - MongoDB (if running locally):**
```powershell
# If MongoDB is installed as a service, it should start automatically
# Otherwise:
mongod --dbpath C:\data\db
```

### Method 2: Using start-windows.js

```powershell
cd frontend
node start-windows.js
```

### Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## Troubleshooting

### Common Issues on Windows

#### 1. PowerShell Script Execution Policy

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Python Not Found

**Error:** "'python' is not recognized as an internal or external command"

**Solution:**
- Reinstall Python with "Add to PATH" checked
- Or use `py` command instead: `py -m pip install -r requirements.txt`

#### 3. Port Already in Use

**Error:** "Port 3000 is already in use" or "Port 8001 is already in use"

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :3000
# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

#### 4. MongoDB Connection Error

**Error:** "MongoServerError: connect ECONNREFUSED"

**Solutions:**
- Check if MongoDB service is running:
  ```powershell
  Get-Service MongoDB
  ```
- Start MongoDB service:
  ```powershell
  Start-Service MongoDB
  ```
- Or use MongoDB Atlas cloud database instead

#### 5. Node Module Not Found

**Error:** "Cannot find module 'xyz'"

**Solution:**
```powershell
# Clear node_modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item yarn.lock
yarn install
```

#### 6. Deprecation Warnings from Webpack

**Solution:** These are suppressed automatically. If you see them:
```powershell
# Use the Windows-specific start script
yarn start:win
# Or
node start-windows.js
```

#### 7. File Path Issues

**Issue:** Paths with `\` causing errors

**Solution:** The application uses `pathlib.Path` which automatically handles Windows paths. No action needed.

#### 8. Virtual Environment Activation Issues

**PowerShell Error:** "Activate.ps1 cannot be loaded"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\activate
```

**CMD Solution:**
```cmd
venv\Scripts\activate.bat
```

## Windows-Specific Features

### Path Handling
- All file paths use `pathlib.Path` for cross-platform compatibility
- Automatic conversion between Windows (`\`) and Unix (`/`) separators

### Environment Variables
- Uses `.env` files for configuration (works on all platforms)
- Automatic path normalization

### Process Management
- Frontend: Hot reload supported
- Backend: Auto-restart on file changes (development mode)

## Performance Optimization for Windows

### 1. Exclude from Windows Defender

Add these folders to Windows Defender exclusions for better performance:

```
C:\Users\<YourUsername>\<project-folder>\node_modules
C:\Users\<YourUsername>\<project-folder>\.cache
C:\Users\<YourUsername>\<project-folder>\chroma_db
```

**How to add exclusions:**
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings"
4. Scroll to "Exclusions" and click "Add or remove exclusions"
5. Add the folders listed above

### 2. Disable Hot Reload (if CPU usage is high)

Create `frontend/.env.local`:
```env
DISABLE_HOT_RELOAD=true
```

## Project Structure

```
neuralstark/
├── backend/              # FastAPI backend
│   ├── server.py        # Main server file
│   ├── rag_service.py   # RAG logic
│   ├── requirements.txt # Python dependencies
│   └── .env             # Backend configuration
├── frontend/            # React frontend
│   ├── src/             # Source files
│   ├── package.json     # Node dependencies
│   ├── setup-windows.js # Windows setup script
│   ├── start-windows.js # Windows start script
│   └── .env             # Frontend configuration
├── files/               # Document storage
├── chroma_db/           # Vector database
└── .cache/              # ML model cache
```

## Development Tips

### 1. Use Windows Terminal

Windows Terminal provides a better development experience:
- Multiple tabs for backend/frontend
- Split panes
- Better Unicode support
- Customizable appearance

### 2. Install Extensions (VS Code)

Recommended VS Code extensions:
- Python
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Thunder Client (API testing)

### 3. Git Configuration

Configure Git to handle line endings correctly:
```powershell
git config --global core.autocrlf true
```

## Testing the Installation

### 1. Test Backend

```powershell
cd backend
.\venv\Scripts\activate
python -c "import fastapi; import motor; import chromadb; print('All imports successful!')"
```

### 2. Test Frontend

```powershell
cd frontend
node -v  # Should show Node.js version
yarn -v  # Should show Yarn version
```

### 3. Test API Connection

After starting both backend and frontend:

```powershell
# Test backend health
curl http://localhost:8001/api/health

# Or use PowerShell:
Invoke-WebRequest -Uri http://localhost:8001/api/health
```

## Next Steps

1. Configure your Cerebras API key in `backend/.env`
2. Add documents to the `files/` directory
3. Start the backend and frontend
4. Open http://localhost:3000
5. Configure API settings in the Settings page
6. Start chatting with your documents!

## Support

- **Documentation**: See main README.md
- **API Docs**: http://localhost:8001/docs (when backend is running)
- **Frontend README**: `frontend/README.md`

## Windows Version Compatibility

Tested on:
- ✅ Windows 11 (23H2)
- ✅ Windows 10 (21H2 and later)
- ✅ Windows Server 2019+

Node.js v22.19.0 confirmed working on Windows 11.

---

**Happy coding on Windows! 🪟🚀**
