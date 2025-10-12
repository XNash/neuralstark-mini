# RAG Platform - run.sh Script Guide

## Overview

The `run.sh` script is a comprehensive, intelligent setup script that works in **two modes**:

1. **Fresh Installation Mode** - On clean Linux systems with no dependencies
2. **Existing Setup Mode** - On systems where the app is already partially or fully set up

## Key Improvements

### ✅ Smart Detection
- Automatically detects existing virtual environments (`/root/.venv`, `/app/.venv`, etc.)
- Detects existing supervisor configurations
- Checks if system dependencies are already installed
- Identifies port conflicts before starting services

### ✅ Better Error Handling
- Continues gracefully when non-critical operations fail
- Provides detailed diagnostics for common errors
- Shows specific error messages from logs
- Suggests fix commands for each error type

### ✅ Works in Both Environments
- **Current Kubernetes Environment**: Respects existing setup, uses current venv
- **Fresh Linux Install**: Installs everything from scratch
- **Partial Setup**: Fills in missing pieces intelligently

### ✅ Enhanced Diagnostics
- Checks for port conflicts (8001, 3000, 27017)
- Validates Python virtual environment
- Tests backend health with actual HTTP requests
- Shows last errors from supervisor logs
- Displays which process is using a port if conflict detected

## Common Issues Fixed

### Issue 1: Backend "Exited too quickly (spawn error)"

**Root Cause**: Supervisor config points to wrong virtual environment path

**Fix Applied**:
- Script now detects existing venv locations automatically
- Uses correct path in supervisor configuration
- Tests venv before using it

### Issue 2: Port Already in Use

**Detection**: Script now checks if ports 8001, 3000, 27017 are in use
**Handling**: Shows which process is using the port and suggests how to fix

### Issue 3: Missing Dependencies

**Detection**: Checks for missing Python packages and suggests installation
**Handling**: Tries to install from requirements.txt, falls back to individual packages

### Issue 4: READONLY Supervisor Config

**Detection**: Checks if supervisor config is marked as READONLY
**Handling**: Skips supervisor configuration if existing config is read-only

### Issue 5: Installation Failures ⚠️ NEW

**Problem**: `pip install -r requirements.txt` fails with some packages
**Solution**: Script now:
- Shows Python and pip versions for debugging
- Tests critical imports before full installation
- Installs critical packages individually if batch fails
- Shows progress during installation (not silent)
- Verifies installation success
- Provides detailed error messages
- Falls back to installing only critical packages if some fail
- Shows count of installed packages

**Frontend Installation Improvements**:
- Checks if node_modules is complete (not just exists)
- Verifies core dependencies (react, react-dom)
- Detects if package.json is newer than node_modules
- Shows progress during installation
- Tries yarn first, falls back to npm
- Uses `--legacy-peer-deps` if standard install fails
- Cleans cache before retry

## Usage

### Basic Usage (Works in All Scenarios)

```bash
cd /app
./run.sh
```

The script will:
1. Detect your environment (fresh vs existing)
2. Skip unnecessary steps automatically
3. Install only what's missing
4. Configure and start services
5. Provide health checks

### What the Script Does

**Step 1/10**: Detect Existing Setup
- Finds virtual environments
- Checks for supervisor configs
- Validates dependencies

**Step 2/10**: Install System Dependencies (skipped if already installed)
- Python 3, Node.js, MongoDB, Supervisor
- OCR tools (Tesseract)
- Document processing tools

**Step 3/10**: Start MongoDB
- Tries systemctl, service, or manual start
- Waits for MongoDB to be ready

**Step 4/10**: Create Directories
- `/app/files` for documents
- `/app/backend/chroma_db` for vector store
- Log directories

**Step 5/10**: Setup Python Virtual Environment
- Uses existing venv if found
- Creates new venv if needed
- Upgrades pip, setuptools, wheel

**Step 6/10**: Install Backend Dependencies
- Installs from requirements.txt if exists
- Falls back to individual package installation
- Includes emergentintegrations library

**Step 7/10**: Install Frontend Dependencies
- Uses yarn (preferred) or npm
- Skips if node_modules exists

**Step 8/10**: Configure Environment Files
- Creates `.env` files if missing
- Validates existing `.env` files

**Step 9/10**: Configure Supervisor
- Detects READONLY configs and skips if present
- Uses correct venv path in config
- Sets up proper log files

**Step 10/10**: Start Services
- Stops existing instances
- Starts backend and frontend
- Checks health with HTTP requests
- Shows detailed errors if services fail

## Troubleshooting

### Backend Won't Start

**Check the logs:**
```bash
tail -50 /var/log/supervisor/backend.err.log
```

**Common Issues:**

1. **Port 8001 in use:**
```bash
sudo lsof -i :8001
# Kill the process using: sudo kill <PID>
```

2. **Missing Python packages:**
```bash
source /root/.venv/bin/activate  # or /app/.venv
pip install fastapi uvicorn motor python-dotenv
```

3. **Wrong virtual environment:**
```bash
# Check which venv supervisor is using:
grep "command=" /etc/supervisor/conf.d/rag-backend.conf
# Should match the actual venv location
```

4. **MongoDB not running:**
```bash
sudo systemctl status mongod
sudo systemctl start mongod
```

**📖 For comprehensive troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

This guide covers:
- Installation issues and solutions
- Runtime errors and fixes
- Performance optimization
- Network problems
- MongoDB issues
- Complete diagnostic procedures

### Frontend Won't Start

**Check the logs:**
```bash
tail -50 /var/log/supervisor/frontend.out.log
```

**Common Issues:**

1. **Port 3000 in use:**
```bash
sudo lsof -i :3000
```

2. **Missing node_modules:**
```bash
cd /app/frontend
yarn install
```

3. **Yarn not found:**
```bash
npm install -g yarn
```

### Services Keep Restarting

**Check supervisor status:**
```bash
sudo supervisorctl status
```

**View real-time logs:**
```bash
# Backend
tail -f /var/log/supervisor/backend.err.log

# Frontend
tail -f /var/log/supervisor/frontend.out.log
```

## Manual Service Control

### Restart Services
```bash
sudo supervisorctl restart all
```

### Start Specific Service
```bash
sudo supervisorctl start backend
sudo supervisorctl start frontend
```

### Stop Services
```bash
sudo supervisorctl stop all
```

### Check Status
```bash
sudo supervisorctl status
```

## Environment Variables

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"
CORS_ORIGINS="*"
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
```

**Important**: 
- In Kubernetes environments, `REACT_APP_BACKEND_URL` will be auto-detected
- Never hardcode URLs in the code - always use environment variables

## Health Checks

The script performs automatic health checks:

### Backend Health
```bash
curl http://localhost:8001/api/
# Should return: {"message": "RAG Platform API", ...}
```

### Frontend Health
```bash
curl http://localhost:3000
# Should return HTML with <!DOCTYPE html>
```

### MongoDB Health
```bash
mongosh --eval "db.adminCommand('ping')"
# Should return: { ok: 1 }
```

## Fresh Linux Installation

On a completely fresh Ubuntu/Debian system:

```bash
# 1. Install git (if not present)
sudo apt-get update
sudo apt-get install -y git

# 2. Clone your repository
git clone <your-repo-url>
cd rag-platform

# 3. Run the script
./run.sh
```

The script will automatically install:
- Python 3 + pip
- Node.js 20 + yarn
- MongoDB 7.0
- Supervisor
- Tesseract OCR
- Poppler utils
- All Python and Node.js dependencies

## Advanced Usage

### Skip System Package Installation
If you already have Python, Node.js, MongoDB installed:

The script auto-detects this! Just run:
```bash
./run.sh
```

It will see dependencies are installed and skip that step.

### Use Custom Virtual Environment Location
The script will automatically use venv in this order:
1. `/app/.venv`
2. `/root/.venv`
3. `$HOME/.venv`
4. `/tmp/rag-platform-venv` (fallback)

### Debug Mode
To see detailed debug output, modify the script or add debug prints:
```bash
# The script already includes debug output for important steps
./run.sh | tee run.log
```

## Differences from Original Script

| Feature | Original | Improved |
|---------|----------|----------|
| Existing setup detection | ❌ No | ✅ Yes |
| Port conflict detection | ❌ No | ✅ Yes |
| Multiple venv locations | ❌ Fixed path | ✅ Auto-detect |
| Error diagnostics | ⚠️ Basic | ✅ Detailed |
| READONLY config handling | ❌ No | ✅ Yes |
| Health checks | ⚠️ Basic curl | ✅ Comprehensive |
| Graceful degradation | ❌ Exits on error | ✅ Continues |
| Supervisor config | ⚠️ Fixed paths | ✅ Dynamic paths |
| Fresh vs existing | ❌ Fresh only | ✅ Both modes |

## Support

For issues not covered here:

1. Check the comprehensive logs in `/var/log/supervisor/`
2. Verify all services are running: `sudo supervisorctl status`
3. Test each service individually
4. Check the original documentation in `README.md`

## Summary

The improved `run.sh` script is now **production-ready** and works reliably in:
- ✅ Fresh Linux installations
- ✅ Existing Kubernetes environments
- ✅ Partial setups with missing dependencies
- ✅ Systems with conflicting ports
- ✅ Multiple virtual environment configurations

Just run `./run.sh` and it will handle the rest intelligently! 🚀
