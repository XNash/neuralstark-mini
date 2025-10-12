# 🚀 First Time Setup Guide

**For new machines pulling from GitHub**

This guide ensures you get the same clean, organized configuration on any machine.

---

## Prerequisites

- **Linux Environment** (Ubuntu 20.04+, Debian, CentOS, RHEL, or similar)
- **Root or sudo access**
- **Internet connection** (for downloading dependencies)

---

## Quick Start (Recommended)

### Option 1: Automated Setup (One Command)

```bash
# Clone the repository
git clone <your-repo-url> rag-platform
cd rag-platform

# Run the universal setup script
chmod +x run.sh
./run.sh
```

**That's it!** The script will:
1. Install all system dependencies
2. Create virtual environment at `/app/.venv`
3. Set up cache directories at `/app/.cache`
4. Configure MongoDB
5. Install backend and frontend dependencies
6. Configure supervisor services
7. Start all services

⏱️ **Total time:** 5-10 minutes depending on your internet speed

---

## What Gets Created

After running `run.sh`, you'll have:

```
rag-platform/
├── .venv/                    # Python virtual environment (1.9GB)
├── .cache/                   # Model cache (downloads on first use)
│   ├── huggingface/         # ~837MB after first backend start
│   └── sentence_transformers/ # ~419MB after first backend start
├── backend/
│   ├── .env                 # Created from .env.example
│   └── chroma_db/           # Created on first document processing
├── frontend/
│   ├── .env                 # Created from .env.example
│   └── node_modules/        # ~439MB of dependencies
└── files/                   # Sample documents included
```

**Total disk space required:** ~3-4GB after full setup

---

## Manual Setup (If Needed)

If you prefer to set up manually or the script fails:

### Step 1: Clone Repository
```bash
git clone <your-repo-url> rag-platform
cd rag-platform
```

### Step 2: Create Environment Files
```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env

# Edit if needed (optional)
nano backend/.env
nano frontend/.env
```

### Step 3: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y nodejs npm
sudo apt-get install -y mongodb-org supervisor
sudo npm install -g yarn
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip
sudo yum install -y nodejs npm
sudo yum install -y mongodb-org supervisor
sudo npm install -g yarn
```

### Step 4: Create Directories
```bash
mkdir -p .venv
mkdir -p .cache/huggingface
mkdir -p .cache/sentence_transformers
mkdir -p backend/chroma_db
mkdir -p files
```

### Step 5: Set Up Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
cd ..
```

### Step 6: Set Up Frontend
```bash
cd frontend
yarn install
cd ..
```

### Step 7: Start MongoDB
```bash
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Step 8: Configure Supervisor

Create `/etc/supervisor/conf.d/rag-backend.conf`:
```ini
[program:backend]
command=/app/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=/app/backend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile=/var/log/supervisor/backend.err.log
environment=PATH="/app/.venv/bin:%(ENV_PATH)s",HF_HOME="/app/.cache/huggingface",TRANSFORMERS_CACHE="/app/.cache/huggingface",SENTENCE_TRANSFORMERS_HOME="/app/.cache/sentence_transformers"
stopsignal=TERM
stopwaitsecs=10
stopasgroup=true
killasgroup=true
```

Create `/etc/supervisor/conf.d/rag-frontend.conf`:
```ini
[program:frontend]
command=yarn start
directory=/app/frontend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/frontend.out.log
stderr_logfile=/var/log/supervisor/frontend.err.log
environment=PATH="/usr/bin:%(ENV_PATH)s",NODE_ENV="development",HOST="0.0.0.0",PORT="3000"
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
killasgroup=true
```

### Step 9: Start Services
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start backend frontend
```

---

## Verification

After setup completes:

### 1. Quick Verification
```bash
chmod +x verify-configuration.sh
./verify-configuration.sh
```

**Expected output:** All checks should pass with ✓

### 2. Service Status
```bash
sudo supervisorctl status
```

**Expected output:**
```
backend      RUNNING   pid 1234, uptime 0:01:23
frontend     RUNNING   pid 1235, uptime 0:01:23
mongodb      RUNNING   pid 1236, uptime 0:01:23
```

### 3. API Tests
```bash
# Backend API
curl http://localhost:8001/api/
# Expected: {"message":"RAG Platform API","status":"running"}

# Document Status
curl http://localhost:8001/api/documents/status
# Expected: {"total_documents":3,"indexed_documents":...}

# Frontend
curl http://localhost:3000 | head -c 100
# Expected: HTML content
```

### 4. Web Interface
Open in browser:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001/api/

---

## Configuration Details

### Important Paths

All application files stay within the project directory:

| Component | Path | Size |
|-----------|------|------|
| Virtual Environment | `/app/.venv` | ~1.9GB |
| Model Cache | `/app/.cache` | ~1.3GB |
| Vector Database | `/app/backend/chroma_db` | ~600KB+ |
| Frontend Dependencies | `/app/frontend/node_modules` | ~439MB |
| Documents | `/app/files` | Variable |

### Environment Variables

**Backend** (`backend/.env`):
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `HF_HOME`: HuggingFace cache location
- `TRANSFORMERS_CACHE`: Transformers cache location
- `SENTENCE_TRANSFORMERS_HOME`: Sentence transformers cache location

**Frontend** (`frontend/.env`):
- `REACT_APP_BACKEND_URL`: Backend API URL
- `WDS_SOCKET_PORT`: WebSocket port for development

---

## Post-Setup Configuration

### Add Your Gemini API Key

1. Open http://localhost:3000 in your browser
2. Click **Settings** in the sidebar
3. Enter your Gemini API key
4. Click **Save API Key**
5. Get your key from: https://aistudio.google.com/app/apikey

### Add Your Documents

```bash
# Copy your documents to the files directory
cp /path/to/your/documents/* /app/files/

# The system will automatically detect and index them
# Check the Documents page to see the status
```

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
# Backend
tail -50 /var/log/supervisor/backend.err.log

# Frontend
tail -50 /var/log/supervisor/frontend.out.log
```

**Common issues:**
1. **Port already in use:** Check if another service is using ports 8001, 3000, or 27017
2. **MongoDB not running:** `sudo systemctl start mongod`
3. **Missing dependencies:** Rerun `./run.sh`

### Backend Errors

**"Module not found" errors:**
```bash
source .venv/bin/activate
cd backend
pip install -r requirements.txt
sudo supervisorctl restart backend
```

**MongoDB connection errors:**
```bash
sudo systemctl status mongod
sudo systemctl start mongod
sudo supervisorctl restart backend
```

### Frontend Errors

**Compilation errors:**
```bash
cd frontend
yarn install
sudo supervisorctl restart frontend
```

**Cannot connect to backend:**
- Check `frontend/.env` has correct `REACT_APP_BACKEND_URL`
- Verify backend is running: `curl http://localhost:8001/api/`

### Path Issues

If files are created outside `/app`:

```bash
# Run the verification script
./verify-configuration.sh

# If issues found, check the configuration:
cat backend/.env | grep HF_HOME
cat /etc/supervisor/conf.d/supervisord.conf | grep HF_HOME
```

**Fix paths:**
```bash
# Stop services
sudo supervisorctl stop all

# Move files back to /app
mv /root/.venv /app/.venv
mv /root/.cache /app/.cache

# Update configurations
./run.sh

# Restart services
sudo supervisorctl restart all
```

---

## Directory Structure Explanation

```
rag-platform/
│
├── backend/                      # FastAPI backend
│   ├── .env                     # Environment variables (gitignored)
│   ├── .env.example            # Environment template (committed)
│   ├── server.py               # Main FastAPI application
│   ├── vector_store.py         # ChromaDB vector store
│   ├── rag_service.py          # RAG pipeline
│   ├── document_processor.py   # Document processing
│   ├── requirements.txt        # Python dependencies
│   └── chroma_db/              # Vector database (created at runtime)
│
├── frontend/                     # React frontend
│   ├── .env                     # Environment variables (gitignored)
│   ├── .env.example            # Environment template (committed)
│   ├── package.json            # NPM dependencies
│   ├── src/                    # React source code
│   └── node_modules/           # NPM packages (created at runtime)
│
├── files/                        # Document storage
│   ├── company_info.md         # Sample document
│   ├── products.txt            # Sample document
│   └── faq.json                # Sample document
│
├── .venv/                        # Python virtual environment (gitignored)
├── .cache/                       # Model cache (gitignored)
│   ├── huggingface/            # HuggingFace models
│   └── sentence_transformers/  # Sentence transformer models
│
├── run.sh                        # Universal setup script ⭐
├── verify-configuration.sh      # Verification script
├── test-permanent-config.sh    # Comprehensive test
│
├── README.md                     # Project overview
├── FIRST_TIME_SETUP.md         # This file ⭐
├── PERMANENT_CONFIGURATION.md  # Configuration details
└── CONFIGURATION_SUMMARY.md    # Quick reference
```

**⭐ Key files for new machines:**
- `run.sh` - Run this to set up everything
- `FIRST_TIME_SETUP.md` - Read this first

---

## Next Steps

After successful setup:

1. **Configure API Key**
   - Go to Settings page
   - Add your Gemini API key

2. **Add Documents**
   - Copy files to `/app/files/`
   - Check Documents page for indexing status

3. **Start Chatting**
   - Go to Chat page
   - Ask questions about your documents

4. **Explore Features**
   - Try multilingual queries (English/French)
   - Check sources for each response
   - Reindex documents if needed

---

## Important Notes

### 🔒 Security

- Default configuration uses `CORS_ORIGINS="*"` for development
- Change this for production: `CORS_ORIGINS="https://yourdomain.com"`
- Never commit `.env` files with actual API keys

### 📦 Updates

To update the application:
```bash
cd rag-platform
git pull origin main
sudo supervisorctl restart all
```

### 🗑️ Cleanup

To remove everything:
```bash
sudo supervisorctl stop all
cd ..
rm -rf rag-platform
```

### 💾 Backup

Important directories to backup:
- `/app/files/` - Your documents
- `/app/backend/chroma_db/` - Vector database
- `/app/backend/.env` - Configuration (excluding API keys from repo)

---

## Support

**Documentation:**
- [README.md](README.md) - Project overview
- [PERMANENT_CONFIGURATION.md](PERMANENT_CONFIGURATION.md) - Detailed configuration guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

**Verification:**
```bash
./verify-configuration.sh      # Quick check
./test-permanent-config.sh    # Comprehensive test
./verify-setup.sh             # System verification
```

**Logs:**
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log

# MongoDB logs
sudo journalctl -u mongod -f
```

---

## Success Criteria

Your setup is successful when:

✅ All services show `RUNNING` status  
✅ Backend API responds at http://localhost:8001/api/  
✅ Frontend loads at http://localhost:3000  
✅ Documents are indexed (check Documents page)  
✅ Chat works (after adding API key)  
✅ All verification scripts pass  

---

**Ready to start?** Run `./run.sh` and you're good to go! 🚀
