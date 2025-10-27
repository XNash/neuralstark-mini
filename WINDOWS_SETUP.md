# Windows Setup Guide - NeuralStark

Complete guide for setting up and running the NeuralStark on Windows 10/11.

---

## 📋 Prerequisites

### Required Software

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
   - ✅ Make sure to check "Add Python to PATH" during installation
   
2. **Node.js 18+** - [Download](https://nodejs.org/)
   - Use LTS version for best compatibility
   
3. **MongoDB 7.0+** - [Download](https://www.mongodb.com/try/download/community)
   - Select "Complete" installation
   - Install as Windows Service (recommended)
   
4. **Git** (optional) - [Download](https://git-scm.com/download/win)
   - For cloning the repository

---

## 🚀 Installation Methods

### Method 1: Automated Setup (Recommended)

Perfect for first-time setup on Windows.

#### Step 1: Open PowerShell

1. Press `Win + X`
2. Select "Windows PowerShell" or "Terminal"

#### Step 2: Allow Script Execution (First Time Only)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Note:** This allows running local scripts. Required only once per user.

#### Step 3: Navigate to Project Directory

```powershell
cd C:\path\to\rag-platform
```

#### Step 4: Run Setup Script

```powershell
.\setup.ps1
```

The script will:
- ✅ Check Python, Node.js, and MongoDB installations
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Install all Node.js dependencies
- ✅ Install pm2 process manager
- ✅ Create environment configuration files
- ✅ Create necessary directories

#### Step 5: Start Services

```powershell
.\start.ps1
```

#### Step 6: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

---

### Method 2: Manual Setup

For users who prefer step-by-step manual installation.

#### 1. Install Python

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```powershell
   python --version
   ```

#### 2. Install Node.js

1. Download Node.js 18+ from [nodejs.org](https://nodejs.org/)
2. Run installer (use default options)
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

#### 3. Install MongoDB

1. Download MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run installer
3. Select "Complete" installation
4. Check "Install MongoDB as a Service"
5. Leave other options as default
6. Verify installation:
   ```powershell
   mongod --version
   ```

#### 4. Install Global Node Tools

```powershell
# Install Yarn
npm install -g yarn

# Install pm2 process manager
npm install -g pm2
```

#### 5. Setup Project

```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
yarn install
cd ..
```

#### 6. Create Environment Files

**Backend** (`backend\.env`):
```ini
# NeuralStark Backend Environment
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_platform
CORS_ORIGINS=*

# Note: Cache paths are set automatically in config_paths.py
```

**Frontend** (`frontend\.env`):
```ini
# NeuralStark Frontend Environment
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=0
```

#### 7. Start Services

```powershell
.\start.ps1
```

---

## 💻 Usage

### Starting Services

```powershell
.\start.ps1
```

### Stopping Services

```powershell
.\stop.ps1
```

### Viewing Status

```powershell
pm2 status
```

### Viewing Logs

```powershell
# All logs
pm2 logs

# Backend only
pm2 logs rag-backend

# Frontend only
pm2 logs rag-frontend

# Live logs
pm2 logs --lines 50
```

### Restarting Services

```powershell
# Restart all
pm2 restart all

# Restart individual service
pm2 restart rag-backend
pm2 restart rag-frontend
```

### Monitoring

```powershell
# Interactive monitoring dashboard
pm2 monit
```

---

## 🔧 Configuration

### API Key Setup

1. Navigate to http://localhost:3000
2. Click on "Settings" in the sidebar
3. Enter your Gemini API key
4. Click "Save Configuration"

### MongoDB Connection

By default, the app connects to `mongodb://localhost:27017`.

To change:
1. Edit `backend\.env`
2. Update `MONGO_URL` value
3. Restart backend: `pm2 restart rag-backend`

### Adding Documents

1. Place documents in the `files\` directory
2. Supported formats: PDF, DOCX, TXT, MD, JSON, CSV, XLSX
3. Documents are automatically indexed on restart
4. Or use "Reindex Documents" button in the UI

---

## 🐛 Troubleshooting

### Issue: PowerShell Script Won't Run

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Issue: Python Not Found

**Error:** "python is not recognized as an internal or external command"

**Solution 1: Add to PATH manually**
1. Search "Environment Variables" in Windows
2. Click "Environment Variables"
3. Under "User variables", select "Path" and click "Edit"
4. Click "New" and add these paths:
   - `C:\Users\YourName\AppData\Local\Programs\Python\Python311`
   - `C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts`
5. Click "OK" on all dialogs
6. Restart PowerShell

**Solution 2: Reinstall Python**
- Reinstall Python and check "Add Python to PATH"

---

### Issue: MongoDB Won't Start

**Error:** MongoDB service not running

**Solution 1: Start as Windows Service**
```powershell
# Start MongoDB service
net start MongoDB

# Check service status
Get-Service MongoDB
```

**Solution 2: Start Manually**
```powershell
# Create data directory
mkdir C:\data\db

# Start MongoDB manually
mongod --dbpath C:\data\db
```

---

### Issue: Port Already in Use

**Error:** "Port 8001 is already in use" or "Port 3000 is already in use"

**Solution:**
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill the process (replace <PID> with actual number)
taskkill /PID <PID> /F

# For port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

### Issue: Virtual Environment Won't Activate

**Solution 1: Use full path**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Solution 2: Use alternative syntax**
```powershell
& .\.venv\Scripts\Activate.ps1
```

---

### Issue: npm/yarn Commands Slow

**Cause:** Windows Defender scanning files

**Solution: Exclude project folder**
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings"
4. Scroll to "Exclusions"
5. Click "Add or remove exclusions"
6. Add your project folder (e.g., `C:\Users\YourName\rag-platform`)

This can significantly speed up `npm install` and `yarn install`.

---

### Issue: pm2 Commands Not Found

**Solution: Install pm2 globally**
```powershell
npm install -g pm2

# Verify installation
pm2 --version
```

---

### Issue: Long Path Error

**Error:** Path too long (> 260 characters)

**Solution: Enable long paths (Windows 10+)**
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Restart computer for changes to take effect
```

---

### Issue: Frontend Won't Connect to Backend

**Symptoms:** API calls failing, CORS errors

**Solution:**
1. Check backend is running:
   ```powershell
   pm2 status
   ```
2. Test backend directly:
   ```powershell
   curl http://localhost:8001/api
   ```
3. Check `frontend\.env` has correct backend URL:
   ```
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```
4. Restart frontend:
   ```powershell
   pm2 restart rag-frontend
   ```

---

## 📁 File Structure

```
rag-platform/
├── backend/              # FastAPI backend
│   ├── server.py        # Main server file
│   ├── config_paths.py  # Cross-platform path configuration
│   ├── rag_service.py   # RAG implementation
│   ├── requirements.txt # Python dependencies
│   └── .env            # Backend configuration
├── frontend/            # React frontend
│   ├── src/            # Source files
│   ├── package.json    # Node dependencies
│   └── .env           # Frontend configuration
├── files/              # Document storage (auto-created)
├── chroma_db/          # Vector database (auto-created)
├── .cache/             # Model cache (auto-created)
│   ├── huggingface/   # HuggingFace models
│   └── sentence_transformers/
├── logs/               # Application logs
├── ecosystem.config.js # pm2 configuration
├── setup.ps1          # Windows setup script
├── start.ps1          # Start services
└── stop.ps1           # Stop services
```

---

## 🎯 Performance Tips

### 1. Use SSD

Store the project on an SSD for better performance, especially for:
- MongoDB database operations
- Model loading (HuggingFace models)
- Document indexing

### 2. Exclude from Windows Defender

Add project folder to Windows Defender exclusions to speed up:
- npm/yarn installations
- Python package installations
- File operations

### 3. Increase Node.js Memory (if needed)

```powershell
$env:NODE_OPTIONS="--max-old-space-size=4096"
```

### 4. Close Unused Applications

The NeuralStark uses:
- Backend: ~1GB RAM
- Frontend: ~500MB RAM
- MongoDB: ~500MB RAM
- Models: ~2GB RAM (cached)

Total: ~4GB RAM recommended

---

## 🗑️ Uninstallation

### Remove Application

```powershell
# Stop services
.\stop.ps1

# Delete pm2 processes
pm2 delete all
pm2 save

# Remove project folder
Remove-Item -Recurse -Force C:\path\to\rag-platform
```

### Remove Global Tools

```powershell
npm uninstall -g pm2
npm uninstall -g yarn
```

### Remove MongoDB (optional)

1. Open "Add or remove programs"
2. Find "MongoDB"
3. Click "Uninstall"

---

## 📚 Additional Resources

- [Python Windows Documentation](https://docs.python.org/3/using/windows.html)
- [Node.js Windows Installation](https://nodejs.org/en/download/)
- [MongoDB Windows Installation](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/)
- [pm2 Documentation](https://pm2.keymetrics.io/)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)

---

## 🆘 Getting Help

### Check Logs

```powershell
# Backend logs
pm2 logs rag-backend --lines 100

# Frontend logs
pm2 logs rag-frontend --lines 100

# All logs
pm2 logs --lines 50
```

### Check Service Status

```powershell
pm2 status
pm2 monit
```

### Test Backend API

```powershell
# Health check
curl http://localhost:8001/api

# API documentation
# Open in browser: http://localhost:8001/docs
```

### Common Log Locations

- **pm2 logs:** `logs\backend-*.log`, `logs\frontend-*.log`
- **MongoDB logs:** `C:\Program Files\MongoDB\Server\7.0\log\mongod.log`

---

## ✅ Quick Reference

| Task | Command |
|------|---------|
| Setup (first time) | `.\setup.ps1` |
| Start services | `.\start.ps1` |
| Stop services | `.\stop.ps1` |
| View status | `pm2 status` |
| View logs | `pm2 logs` |
| Restart all | `pm2 restart all` |
| Monitor | `pm2 monit` |
| Start MongoDB | `net start MongoDB` |
| Stop MongoDB | `net stop MongoDB` |

---

**Windows setup complete!** 🎉

Enjoy using the NeuralStark on Windows!
