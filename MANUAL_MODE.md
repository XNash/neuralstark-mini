# NeuralStark - Manual Setup Mode

This repository has been configured for **manual operation** without PM2 or Supervisor automation.

## 🎯 What Changed

### Removed
- ❌ PM2 dependency and automation
- ❌ Supervisor automatic process management  
- ❌ Complex automatic setup scripts

### What Remains
- ✅ Backend (FastAPI + Python)
- ✅ Frontend (React + Node.js)
- ✅ MongoDB database
- ✅ All application features

### Configuration Files
- `ecosystem.config.js` - PM2 config (no longer used but kept for reference)
- `run.sh` - Original automation script (no longer used but kept for reference)
- Supervisor configs - No longer used

## 🚀 How to Run

### Option 1: Use Batch Scripts (Easiest)

**Windows:**

1. **Setup (one time):**
   ```cmd
   setup-windows.bat
   ```

2. **Start services (each time):**
   - `start-mongodb.bat` (Terminal 1)
   - `start-backend.bat` (Terminal 2)  
   - `start-frontend.bat` (Terminal 3)

3. **Stop services:**
   ```cmd
   stop-all.bat
   ```

### Option 2: Manual Commands

**Backend:**
```cmd
cd backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**
```cmd
cd frontend
npm start
```

**MongoDB:**
```cmd
net start MongoDB
```
Or:
```cmd
mongod --dbpath C:\data\db
```

## 📂 Project Structure

```
NeuralStark/
├── backend/                    # FastAPI backend
│   ├── server.py              # Main API server
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Backend config (MongoDB, etc.)
│   └── venv/                  # Python virtual environment
├── frontend/                   # React frontend
│   ├── src/                   # React source code
│   ├── package.json           # Node dependencies
│   ├── .env                   # Frontend config (API URL)
│   └── node_modules/          # Node dependencies
├── files/                      # Your documents go here
├── .cache/                     # Model cache (auto-created)
├── start-backend.bat          # Quick start backend
├── start-frontend.bat         # Quick start frontend
├── start-mongodb.bat          # Quick start MongoDB
├── setup-windows.bat          # One-time setup
├── stop-all.bat               # Stop all services
├── QUICKSTART_MANUAL.md       # Quick start guide
└── MANUAL_SETUP_WINDOWS.md    # Detailed setup guide
```

## 📋 Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **MongoDB** - [Download](https://www.mongodb.com/try/download/community)

## 🔧 Configuration

### Backend (.env)
Located at `backend/.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_platform
CORS_ORIGINS=*
```

### Frontend (.env)
Located at `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=0
```

## 🌐 Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **MongoDB:** mongodb://localhost:27017

## 📖 Documentation

- **Quick Start:** `QUICKSTART_MANUAL.md`
- **Detailed Setup:** `MANUAL_SETUP_WINDOWS.md`
- **Original README:** `README.md` (contains app features)

## 🐛 Common Issues

### Port Already in Use
```cmd
netstat -ano | findstr :8001
taskkill /PID <pid> /F
```

### MongoDB Not Starting
1. Check if already running: `tasklist | findstr mongod`
2. Try service: `net start MongoDB`
3. Create data dir: `mkdir C:\data\db`

### Python Virtual Environment
If activation fails in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### Dependencies Issues
```cmd
# Backend
cd backend
venv\Scripts\activate
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rmdir /s /q node_modules
npm install
```

## 💡 Tips

1. **Keep terminals open** - Each service needs its own terminal
2. **Check logs** - Errors appear in the terminal where the service is running
3. **Use Ctrl+C** - To stop individual services
4. **Auto-reload enabled** - Both frontend and backend reload on code changes

## 🚫 What NOT to Use

These files are no longer used (kept for reference only):
- `ecosystem.config.js` - PM2 configuration
- `run.sh` - Automated setup script
- `pm2-*.sh` - PM2 control scripts
- Supervisor configs - Process management

## ✅ Quick Checklist

Before starting:
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed  
- [ ] MongoDB installed
- [ ] Ran `setup-windows.bat`
- [ ] Have Gemini API key ready

To run:
- [ ] Start MongoDB (Terminal 1)
- [ ] Start Backend (Terminal 2)
- [ ] Start Frontend (Terminal 3)
- [ ] Open http://localhost:3000
- [ ] Add API key in Settings
- [ ] Add documents to `files/` folder
- [ ] Click "Reindex Documents"

## 🎉 That's It!

You now have full manual control over NeuralStark. No automatic process managers, just simple commands to start and stop services as needed.

For questions or issues, check the detailed guides or the application logs.

**Happy chatting with your documents! 🚀**
