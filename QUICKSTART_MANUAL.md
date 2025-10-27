# NeuralStark - Quick Start (Manual Mode)

This is a simplified guide for running NeuralStark manually without PM2 or Supervisor.

## 🚀 Quick Setup (Windows)

### 1. Run Setup (One Time)

Double-click `setup-windows.bat` or run in Command Prompt:

```cmd
setup-windows.bat
```

This will:
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies
- Create necessary directories

### 2. Start Services (Each Time)

You need **3 terminal windows**:

#### Terminal 1 - MongoDB
```cmd
start-mongodb.bat
```

#### Terminal 2 - Backend
```cmd
start-backend.bat
```

#### Terminal 3 - Frontend
```cmd
start-frontend.bat
```

### 3. Open Application

Open browser: **http://localhost:3000**

### 4. Configure API Key

1. Go to Settings page
2. Enter your Gemini API key ([Get it here](https://aistudio.google.com/app/apikey))
3. Click Save

### 5. Add Documents

Place your documents in the `files/` folder, then click "Reindex Documents" on the Documents page.

---

## 🛑 Stop Services

To stop everything:

```cmd
stop-all.bat
```

Or press `Ctrl+C` in each terminal window.

---

## 📝 Manual Commands (If You Prefer)

If you don't want to use batch scripts:

### Backend
```cmd
cd backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```cmd
cd frontend
npm start
```

### MongoDB
```cmd
net start MongoDB
```
Or manually:
```cmd
mongod --dbpath C:\data\db
```

---

## 🐛 Troubleshooting

### Port Already in Use
```cmd
netstat -ano | findstr :8001
taskkill /PID <process_id> /F
```

### Virtual Environment Issues
If activation fails, try:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependencies Missing
```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

```cmd
cd frontend
npm install
```

---

## 📚 Full Documentation

See `MANUAL_SETUP_WINDOWS.md` for detailed instructions and troubleshooting.

---

**That's it! Happy chatting with your documents! 🎉**
