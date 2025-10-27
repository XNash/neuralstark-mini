# NeuralStark - Portability Fixes Implementation Plan

**Document Version:** 1.0  
**Created:** 2025-01-17  
**Target Platforms:** Windows 10/11, Linux (Ubuntu/Debian/CentOS), macOS

---

## 🎯 Implementation Goals

1. **Eliminate hardcoded absolute paths** from all configuration files
2. **Create Windows-native setup scripts** (PowerShell)
3. **Replace Supervisor with pm2** for cross-platform process management
4. **Maintain backward compatibility** with existing Linux deployments
5. **Single codebase** that works on all platforms

---

## 📋 Phase 1: Fix Hardcoded Paths (HIGH PRIORITY)

### Duration: 1 hour
### Priority: CRITICAL

### 1.1 Create Path Configuration Module

**File:** `/app/backend/config_paths.py`

```python
"""
Cross-platform path configuration for NeuralStark.
Automatically detects project root and sets up cache directories.
"""
import os
from pathlib import Path

# Get project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Define cache directories relative to project root
CACHE_DIR = PROJECT_ROOT / ".cache"
HF_CACHE = CACHE_DIR / "huggingface"
ST_CACHE = CACHE_DIR / "sentence_transformers"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
FILES_DIR = PROJECT_ROOT / "files"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HF_CACHE.mkdir(parents=True, exist_ok=True)
ST_CACHE.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

# Set environment variables for HuggingFace and related libraries
os.environ['HF_HOME'] = str(HF_CACHE)
os.environ['TRANSFORMERS_CACHE'] = str(HF_CACHE)
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(ST_CACHE)

# Export as strings for compatibility
HF_CACHE_STR = str(HF_CACHE)
ST_CACHE_STR = str(ST_CACHE)
CHROMA_DIR_STR = str(CHROMA_DIR)
FILES_DIR_STR = str(FILES_DIR)
PROJECT_ROOT_STR = str(PROJECT_ROOT)

print(f"[Config] Project Root: {PROJECT_ROOT_STR}")
print(f"[Config] HF Cache: {HF_CACHE_STR}")
print(f"[Config] Chroma DB: {CHROMA_DIR_STR}")
print(f"[Config] Files Directory: {FILES_DIR_STR}")
```

### 1.2 Update server.py to Use Dynamic Paths

**File:** `/app/backend/server.py`

**Add at the top** (before other imports):
```python
# Import path configuration FIRST to set environment variables
import config_paths

# Now import other modules
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
# ... rest of imports
```

### 1.3 Update Vector Store to Use Dynamic Paths

**File:** `/app/backend/vector_store.py` and `/app/backend/vector_store_optimized.py`

**Find the ChromaDB initialization** and update:
```python
# OLD (hardcoded)
self.client = chromadb.PersistentClient(path="/app/chroma_db")

# NEW (dynamic)
import config_paths
self.client = chromadb.PersistentClient(path=config_paths.CHROMA_DIR_STR)
```

### 1.4 Update Document Processor to Use Dynamic Paths

**File:** `/app/backend/document_processor.py` and `/app/backend/document_processor_optimized.py`

**Find the files directory** and update:
```python
# OLD (hardcoded)
self.files_dir = Path("/app/files")

# NEW (dynamic)
import config_paths
self.files_dir = Path(config_paths.FILES_DIR_STR)
```

### 1.5 Update run.sh to Generate Relative Paths

**File:** `/app/run.sh`

**Find the backend .env generation** (around line 700) and modify:
```bash
# OLD
HF_HOME="$PROJECT_DIR/.cache/huggingface"
TRANSFORMERS_CACHE="$PROJECT_DIR/.cache/huggingface"
SENTENCE_TRANSFORMERS_HOME="$PROJECT_DIR/.cache/sentence_transformers"

# NEW - Remove these lines entirely since we're setting them in Python
# Or keep them as documentation:
# Note: Cache paths are now set dynamically in config_paths.py
# HF_HOME="<project>/.cache/huggingface"
# TRANSFORMERS_CACHE="<project>/.cache/huggingface"
# SENTENCE_TRANSFORMERS_HOME="<project>/.cache/sentence_transformers"
```

---

## 📋 Phase 2: Create pm2 Configuration (MEDIUM PRIORITY)

### Duration: 2 hours
### Priority: MEDIUM

### 2.1 Install pm2 Globally

**On Linux/macOS:**
```bash
npm install -g pm2
```

**On Windows (PowerShell as Administrator):**
```powershell
npm install -g pm2
# Or
yarn global add pm2
```

### 2.2 Create pm2 Ecosystem Configuration

**File:** `/app/ecosystem.config.js`

```javascript
/**
 * PM2 Ecosystem Configuration for NeuralStark
 * Cross-platform process management for Windows, Linux, and macOS
 * 
 * Usage:
 *   Start all services: pm2 start ecosystem.config.js
 *   Stop all services: pm2 stop ecosystem.config.js
 *   Restart all services: pm2 restart ecosystem.config.js
 *   View logs: pm2 logs
 *   Monitor: pm2 monit
 */

const path = require('path');
const os = require('os');

// Detect platform
const isWindows = os.platform() === 'win32';
const pythonCmd = isWindows ? 'python' : 'python3';
const venvPython = isWindows 
  ? path.join(__dirname, '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, '.venv', 'bin', 'python');

module.exports = {
  apps: [
    {
      name: 'rag-backend',
      script: venvPython,
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001',
      cwd: path.join(__dirname, 'backend'),
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
        MONGO_URL: 'mongodb://localhost:27017',
        DB_NAME: 'rag_platform',
        CORS_ORIGINS: '*'
      },
      error_file: path.join(__dirname, 'logs', 'backend-error.log'),
      out_file: path.join(__dirname, 'logs', 'backend-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    },
    {
      name: 'rag-frontend',
      script: isWindows ? 'yarn.cmd' : 'yarn',
      args: 'start',
      cwd: path.join(__dirname, 'frontend'),
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PORT: '3000',
        BROWSER: 'none',
        REACT_APP_BACKEND_URL: 'http://localhost:8001'
      },
      error_file: path.join(__dirname, 'logs', 'frontend-error.log'),
      out_file: path.join(__dirname, 'logs', 'frontend-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ]
};
```

### 2.3 Create pm2 Helper Scripts

**File:** `/app/pm2-start.sh` (Linux/macOS)
```bash
#!/bin/bash
echo "Starting NeuralStark with pm2..."
pm2 start ecosystem.config.js
pm2 save
echo "Services started. View status with: pm2 status"
echo "View logs with: pm2 logs"
```

**File:** `/app/pm2-stop.sh` (Linux/macOS)
```bash
#!/bin/bash
echo "Stopping NeuralStark..."
pm2 stop ecosystem.config.js
pm2 save
echo "Services stopped."
```

**File:** `/app/pm2-restart.sh` (Linux/macOS)
```bash
#!/bin/bash
echo "Restarting NeuralStark..."
pm2 restart ecosystem.config.js
echo "Services restarted."
```

---

## 📋 Phase 3: Windows PowerShell Scripts (MEDIUM PRIORITY)

### Duration: 3 hours
### Priority: MEDIUM

### 3.1 Create Windows Setup Script

**File:** `/app/setup.ps1`

```powershell
<#
.SYNOPSIS
    NeuralStark - Windows Setup Script
.DESCRIPTION
    Installs all dependencies and sets up the NeuralStark on Windows
.NOTES
    Requires Administrator privileges for some installations
#>

# Require PowerShell 5.1 or higher
#Requires -Version 5.1

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step {
    param($Message)
    Write-Host "`n===================================================" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor Blue
    Write-Host "===================================================" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandExists {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

# Main setup function
function Start-RagSetup {
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                 NeuralStark Setup for Windows              ║
║                                                              ║
║  This script will install and configure:                    ║
║  - Python 3.11+                                             ║
║  - Node.js 18+                                              ║
║  - MongoDB 7.0+                                             ║
║  - pm2 Process Manager                                      ║
║  - All Python and Node.js dependencies                      ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Warning-Custom "Some installations require administrator privileges."
        Write-Warning-Custom "Consider running this script as Administrator for best results."
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y') {
            exit 1
        }
    }

    # Step 1: Check Python
    Write-Step "Step 1/8: Checking Python Installation"
    if (Test-CommandExists python) {
        $pythonVersion = python --version
        Write-Success "Python is installed: $pythonVersion"
    }
    else {
        Write-Error-Custom "Python is not installed!"
        Write-Host "Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
        exit 1
    }

    # Step 2: Check Node.js
    Write-Step "Step 2/8: Checking Node.js Installation"
    if (Test-CommandExists node) {
        $nodeVersion = node --version
        Write-Success "Node.js is installed: $nodeVersion"
    }
    else {
        Write-Error-Custom "Node.js is not installed!"
        Write-Host "Please install Node.js 18+ from: https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }

    # Step 3: Check MongoDB
    Write-Step "Step 3/8: Checking MongoDB Installation"
    if (Test-CommandExists mongod) {
        Write-Success "MongoDB is installed"
    }
    else {
        Write-Warning-Custom "MongoDB is not detected!"
        Write-Host "Install options:" -ForegroundColor Yellow
        Write-Host "  1. Download installer: https://www.mongodb.com/try/download/community" -ForegroundColor Yellow
        Write-Host "  2. Or use Chocolatey: choco install mongodb" -ForegroundColor Yellow
        $continue = Read-Host "Continue without MongoDB? (services won't start) (y/N)"
        if ($continue -ne 'y') {
            exit 1
        }
    }

    # Step 4: Create Python Virtual Environment
    Write-Step "Step 4/8: Creating Python Virtual Environment"
    if (Test-Path ".venv") {
        Write-Success "Virtual environment already exists"
    }
    else {
        Write-Host "Creating virtual environment..."
        python -m venv .venv
        Write-Success "Virtual environment created"
    }

    # Step 5: Install Python Dependencies
    Write-Step "Step 5/8: Installing Python Dependencies"
    Write-Host "Activating virtual environment..."
    & .\.venv\Scripts\Activate.ps1
    
    Write-Host "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel
    
    Write-Host "Installing backend dependencies..."
    Set-Location backend
    pip install -r requirements.txt
    Set-Location ..
    Write-Success "Python dependencies installed"

    # Step 6: Install Node.js Dependencies
    Write-Step "Step 6/8: Installing Node.js Dependencies"
    if (Test-CommandExists yarn) {
        Write-Success "Yarn is installed"
    }
    else {
        Write-Host "Installing Yarn globally..."
        npm install -g yarn
    }
    
    Write-Host "Installing frontend dependencies..."
    Set-Location frontend
    yarn install
    Set-Location ..
    Write-Success "Node.js dependencies installed"

    # Step 7: Install pm2
    Write-Step "Step 7/8: Installing pm2 Process Manager"
    if (Test-CommandExists pm2) {
        Write-Success "pm2 is already installed"
    }
    else {
        Write-Host "Installing pm2 globally..."
        npm install -g pm2
        Write-Success "pm2 installed"
    }

    # Step 8: Create Environment Files
    Write-Step "Step 8/8: Creating Environment Files"
    
    # Backend .env
    if (-not (Test-Path "backend\.env")) {
        Write-Host "Creating backend .env file..."
        @"
# NeuralStark Backend Environment
# Generated: $(Get-Date)

# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_platform

# CORS Configuration
CORS_ORIGINS=*

# Note: Cache paths are set automatically in config_paths.py
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
        Write-Success "Backend .env created"
    }
    else {
        Write-Success "Backend .env already exists"
    }
    
    # Frontend .env
    if (-not (Test-Path "frontend\.env")) {
        Write-Host "Creating frontend .env file..."
        @"
# NeuralStark Frontend Environment
# Generated: $(Get-Date)

# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# WebSocket configuration
WDS_SOCKET_PORT=0
"@ | Out-File -FilePath "frontend\.env" -Encoding UTF8
        Write-Success "Frontend .env created"
    }
    else {
        Write-Success "Frontend .env already exists"
    }

    # Create logs directory
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
        Write-Success "Logs directory created"
    }

    # Setup complete
    Write-Host "`n" -NoNewline
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║              Setup Complete! 🎉                              ║
╚══════════════════════════════════════════════════════════════╝

Next steps:
1. Start MongoDB service (if not running):
   net start MongoDB

2. Start NeuralStark:
   .\start.ps1

3. Access the application:
   Frontend: http://localhost:3000
   Backend:  http://localhost:8001

Useful commands:
- View status: pm2 status
- View logs:   pm2 logs
- Stop all:    .\stop.ps1
- Restart:     pm2 restart all

"@ -ForegroundColor Green
}

# Run setup
try {
    Start-RagSetup
}
catch {
    Write-Error-Custom "Setup failed: $_"
    exit 1
}
```

### 3.2 Create Windows Start Script

**File:** `/app/start.ps1`

```powershell
<#
.SYNOPSIS
    Start NeuralStark services on Windows
#>

$ErrorActionPreference = "Stop"

Write-Host "Starting NeuralStark..." -ForegroundColor Cyan

# Check if MongoDB is running
$mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
if ($mongoService -and $mongoService.Status -eq 'Running') {
    Write-Host "[OK] MongoDB is running" -ForegroundColor Green
}
else {
    Write-Host "[WARNING] MongoDB service is not running!" -ForegroundColor Yellow
    Write-Host "Start MongoDB with: net start MongoDB" -ForegroundColor Yellow
}

# Check if pm2 is installed
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] pm2 is not installed!" -ForegroundColor Red
    Write-Host "Install with: npm install -g pm2" -ForegroundColor Yellow
    exit 1
}

# Start services with pm2
Write-Host "Starting services with pm2..." -ForegroundColor Cyan
pm2 start ecosystem.config.js

# Save pm2 configuration
pm2 save

Write-Host "`n" -NoNewline
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║              NeuralStark Started! 🚀                        ║
╚══════════════════════════════════════════════════════════════╝

Services:
- Backend:  http://localhost:8001
- Frontend: http://localhost:3000

Useful commands:
- View status: pm2 status
- View logs:   pm2 logs
- Stop all:    .\stop.ps1
- Restart:     pm2 restart all

"@ -ForegroundColor Green
```

### 3.3 Create Windows Stop Script

**File:** `/app/stop.ps1`

```powershell
<#
.SYNOPSIS
    Stop NeuralStark services on Windows
#>

Write-Host "Stopping NeuralStark..." -ForegroundColor Cyan

if (Get-Command pm2 -ErrorAction SilentlyContinue) {
    pm2 stop ecosystem.config.js
    pm2 save
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}
else {
    Write-Host "[ERROR] pm2 is not installed!" -ForegroundColor Red
    exit 1
}
```

---

## 📋 Phase 4: Documentation (LOW PRIORITY)

### Duration: 2 hours
### Priority: LOW

### 4.1 Create Windows Setup Guide

**File:** `/app/WINDOWS_SETUP.md`

```markdown
# Windows Setup Guide - NeuralStark

Complete guide for setting up and running the NeuralStark on Windows 10/11.

## Prerequisites

### Required Software
1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **MongoDB 7.0+** - [Download](https://www.mongodb.com/try/download/community)
4. **Git** (optional) - [Download](https://git-scm.com/download/win)

## Installation Methods

### Method 1: Automated Setup (Recommended)

1. **Open PowerShell as Administrator**
   - Right-click PowerShell icon
   - Select "Run as Administrator"

2. **Navigate to project directory**
   ```powershell
   cd C:\path\to\rag-platform
   ```

3. **Allow script execution** (first time only)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Run setup script**
   ```powershell
   .\setup.ps1
   ```

5. **Start services**
   ```powershell
   .\start.ps1
   ```

### Method 2: Manual Setup

#### Step 1: Install Python
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ **Important:** Check "Add Python to PATH"
4. Complete installation
5. Verify: `python --version`

#### Step 2: Install Node.js
1. Download Node.js 18+ from [nodejs.org](https://nodejs.org/)
2. Run installer (use default options)
3. Verify: `node --version` and `npm --version`

#### Step 3: Install MongoDB
1. Download MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run installer
3. Select "Complete" installation
4. Install as a Windows Service (recommended)
5. Verify: `mongod --version`

#### Step 4: Install Global Tools
```powershell
# Install Yarn
npm install -g yarn

# Install pm2
npm install -g pm2
```

#### Step 5: Setup Project
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

#### Step 6: Configure Environment
1. Copy `.env.example` files if they exist
2. Or use the setup script to generate them:
   ```powershell
   .\setup.ps1
   ```

#### Step 7: Start Services
```powershell
.\start.ps1
```

## Usage

### Starting Services
```powershell
.\start.ps1
```

### Stopping Services
```powershell
.\stop.ps1
```

### Viewing Logs
```powershell
# All logs
pm2 logs

# Backend only
pm2 logs rag-backend

# Frontend only
pm2 logs rag-frontend
```

### Checking Status
```powershell
pm2 status
```

### Restarting Services
```powershell
pm2 restart all
# Or restart individual service
pm2 restart rag-backend
pm2 restart rag-frontend
```

## Troubleshooting

### Issue: PowerShell Script Won't Run
**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Python Not Found
**Error:** "python is not recognized"

**Solution:**
1. Add Python to PATH manually:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python311`
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts`
2. Or reinstall Python with "Add to PATH" checked

### Issue: MongoDB Won't Start
**Solution:**
```powershell
# Start as Windows Service
net start MongoDB

# Or run manually
mongod --dbpath C:\data\db
```

### Issue: Port Already in Use
**Error:** Port 8001 or 3000 already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8001
# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Issue: Virtual Environment Not Activating
**Solution:**
```powershell
# Use full path
.\.venv\Scripts\Activate.ps1

# Or
& .\.venv\Scripts\Activate.ps1
```

## File Locations

- **Project Root:** `C:\path\to\rag-platform`
- **Virtual Environment:** `.venv\`
- **Cache Directory:** `.cache\`
- **Database:** `chroma_db\`
- **Documents:** `files\`
- **Logs:** `logs\`

## Performance Tips

1. **Exclude from Windows Defender**
   - Add project folder to exclusions
   - Speeds up npm/pip installs
   - Settings > Update & Security > Windows Security > Virus & threat protection > Exclusions

2. **Use SSD**
   - Store project on SSD for better performance
   - MongoDB benefits greatly from SSD

3. **Increase Node.js Memory**
   ```powershell
   $env:NODE_OPTIONS="--max-old-space-size=4096"
   ```

## Uninstallation

```powershell
# Stop services
.\stop.ps1

# Delete pm2 configuration
pm2 delete all
pm2 save

# Remove virtual environment
Remove-Item -Recurse -Force .venv

# Remove node modules
Remove-Item -Recurse -Force frontend\node_modules

# Remove cache
Remove-Item -Recurse -Force .cache

# Remove database (optional)
Remove-Item -Recurse -Force chroma_db
```

## Additional Resources

- [Python Windows Documentation](https://docs.python.org/3/using/windows.html)
- [Node.js Windows Installation](https://nodejs.org/en/download/package-manager/)
- [MongoDB Windows Installation](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/)
- [pm2 Documentation](https://pm2.keymetrics.io/)
```

### 4.2 Update Main README

Add Windows section to `/app/README.md`:

```markdown
## Installation

### Linux/macOS
```bash
chmod +x run.sh
./run.sh
```

### Windows
See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed Windows installation guide.

Quick start:
```powershell
.\setup.ps1  # First time only
.\start.ps1  # Start services
```
```

---

## 🧪 Testing Plan

### Test Environment Setup
1. **Windows 11 VM** - Fresh installation
2. **Windows 10 VM** - Fresh installation
3. **Ubuntu 22.04 VM** - Test compatibility
4. **macOS** (if available) - Test compatibility

### Test Checklist

#### Windows Testing
- [ ] Clone fresh repository
- [ ] Run `setup.ps1`
  - [ ] Python detected
  - [ ] Node.js detected
  - [ ] MongoDB detected
  - [ ] Virtual environment created
  - [ ] Backend dependencies installed
  - [ ] Frontend dependencies installed
  - [ ] pm2 installed
  - [ ] Environment files created
- [ ] Run `start.ps1`
  - [ ] Backend starts (port 8001)
  - [ ] Frontend starts (port 3000)
  - [ ] MongoDB connection successful
  - [ ] No error logs
- [ ] Functionality tests
  - [ ] Upload document
  - [ ] Index documents
  - [ ] Configure API key
  - [ ] Send chat message
  - [ ] Receive response
  - [ ] View sources
- [ ] Run `stop.ps1`
  - [ ] All services stop cleanly
- [ ] Cache verification
  - [ ] Cache directory exists in project folder
  - [ ] Models downloaded to `.cache`
  - [ ] Database in `chroma_db`

#### Linux Testing
- [ ] Run existing `run.sh`
- [ ] Verify no breaking changes
- [ ] All functionality working
- [ ] pm2 works alongside supervisor (if needed)

#### Path Portability Testing
- [ ] Move project to different directory
- [ ] Restart services
- [ ] Verify cache still works
- [ ] Verify database still accessible
- [ ] No hardcoded path errors

---

## 📊 Implementation Timeline

### Day 1 (2 hours)
- [ ] Create `config_paths.py`
- [ ] Update `server.py` to import config_paths
- [ ] Update `vector_store.py` and `vector_store_optimized.py`
- [ ] Update `document_processor.py` and `document_processor_optimized.py`
- [ ] Test on Linux (ensure no breaking changes)

### Day 2 (2 hours)
- [ ] Create `ecosystem.config.js`
- [ ] Create `pm2-start.sh`, `pm2-stop.sh`, `pm2-restart.sh`
- [ ] Test pm2 on Linux
- [ ] Document pm2 usage

### Day 3 (3 hours)
- [ ] Create `setup.ps1`
- [ ] Create `start.ps1`
- [ ] Create `stop.ps1`
- [ ] Test on Windows VM

### Day 4 (2 hours)
- [ ] Create `WINDOWS_SETUP.md`
- [ ] Update main `README.md`
- [ ] Create troubleshooting guide
- [ ] Final testing on all platforms

---

## 🎯 Success Criteria

### Must Pass
- [ ] All tests pass on Windows 10
- [ ] All tests pass on Windows 11
- [ ] No breaking changes on Linux
- [ ] All functionality works (upload, index, chat)
- [ ] Cache persists correctly
- [ ] Database persists correctly
- [ ] No hardcoded absolute paths remain
- [ ] Setup takes < 10 minutes on Windows
- [ ] Documentation is clear and complete

### Nice to Have
- [ ] macOS compatibility verified
- [ ] Docker still works
- [ ] Performance comparable across platforms
- [ ] Automated tests pass

---

## 📝 Code Review Checklist

- [ ] No hardcoded `/app/` paths
- [ ] No hardcoded `C:\` paths
- [ ] Use `pathlib.Path` for all paths
- [ ] Use `os.path.join` or `/` operator
- [ ] Cross-platform path separators
- [ ] Environment variables set in code, not .env
- [ ] All imports use relative imports where possible
- [ ] No Linux-specific commands in Python code
- [ ] No Windows-specific commands in Python code
- [ ] Error messages are helpful
- [ ] Logs show actual paths being used

---

## 🔄 Rollback Plan

If implementation fails:
1. Git checkout to last working commit
2. Keep `config_paths.py` for future use
3. Document what didn't work
4. Revert run.sh changes
5. Continue using Supervisor on Linux

---

## 📞 Support and Maintenance

### Documentation Created
- [x] `WINDOWS_COMPATIBILITY_ANALYSIS.md`
- [x] `PORTABILITY_FIXES_PLAN.md` (this file)
- [ ] `WINDOWS_SETUP.md`
- [ ] `PM2_GUIDE.md`

### Code Created
- [ ] `config_paths.py`
- [ ] `ecosystem.config.js`
- [ ] `setup.ps1`
- [ ] `start.ps1`
- [ ] `stop.ps1`
- [ ] `pm2-start.sh`
- [ ] `pm2-stop.sh`

---

**Plan Complete** ✅  
Ready for sequential implementation with clear steps and testing procedures.
