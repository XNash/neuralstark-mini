# NeuralStark - Permanent Configuration Guide

**Last Updated:** October 12, 2025  
**Status:** ✅ Production Ready

## Overview

This document describes the permanent configuration that ensures all project files remain within the `/app` directory (excluding system services like MongoDB and Supervisor).

---

## 1. Directory Structure

### Application Root: `/app/`

```
/app/
├── .venv/                          # Python virtual environment (1.9GB)
├── .cache/                         # Model cache directory (1.3GB)
│   ├── huggingface/               # HuggingFace models (837MB)
│   └── sentence_transformers/     # Sentence transformer models (419MB)
├── backend/
│   ├── chroma_db/                 # ChromaDB vector database (236KB)
│   │   ├── chroma.sqlite3        # SQLite database file
│   │   └── [collection dirs]     # Vector collections
│   ├── .env                       # Backend environment variables
│   ├── server.py                  # FastAPI server
│   ├── vector_store.py           # Vector store service
│   ├── rag_service.py            # RAG service
│   └── document_processor.py     # Document processing
├── frontend/
│   ├── node_modules/             # Frontend dependencies
│   ├── .env                      # Frontend environment variables
│   └── [React app files]
├── files/                         # Document storage
│   ├── company_info.md
│   ├── products.txt
│   └── faq.json
├── tests/                         # Test files
├── run.sh                         # Universal setup script
└── [documentation files]
```

---

## 2. Configuration Files

### 2.1 Backend Environment Variables (`/app/backend/.env`)

```bash
# Database Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"
CORS_ORIGINS="*"

# Cache Directories (keep everything within /app)
HF_HOME="/app/.cache/huggingface"
TRANSFORMERS_CACHE="/app/.cache/huggingface"
SENTENCE_TRANSFORMERS_HOME="/app/.cache/sentence_transformers"
```

**Purpose:**
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name for NeuralStark
- `HF_HOME`: HuggingFace cache directory (prevents downloads to `/root/.cache`)
- `TRANSFORMERS_CACHE`: Transformers library cache (prevents downloads to `/root/.cache`)
- `SENTENCE_TRANSFORMERS_HOME`: Sentence transformers cache (prevents downloads to `/root/.cache`)

### 2.2 Frontend Environment Variables (`/app/frontend/.env`)

```bash
REACT_APP_BACKEND_URL=<backend_url>
WDS_SOCKET_PORT=443
```

### 2.3 Git Ignore (`/app/.gitignore`)

Key entries to exclude generated files:
```gitignore
# Python
__pycache__/
*pyc*
venv/
.venv/

# NeuralStark specific
chroma_db/
*.sqlite3

# Build caches
.cache/

# Dependencies
node_modules/
```

---

## 3. System Configuration

### 3.1 Supervisor Configuration (`/etc/supervisor/conf.d/supervisord.conf`)

#### Backend Service
```ini
[program:backend]
command=/app/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
directory=/app/backend
autostart=true
autorestart=true
environment=APP_URL="...",INTEGRATION_PROXY_URL="...",HF_HOME="/app/.cache/huggingface",TRANSFORMERS_CACHE="/app/.cache/huggingface",SENTENCE_TRANSFORMERS_HOME="/app/.cache/sentence_transformers"
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
```

**Key Points:**
- Uses `/app/.venv/bin/uvicorn` (not `/root/.venv/bin/uvicorn`)
- Sets cache environment variables to point to `/app/.cache`
- Working directory is `/app/backend`

#### Frontend Service
```ini
[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
killasgroup=true
```

---

## 4. Code Configuration

### 4.1 Vector Store (`/app/backend/vector_store.py`)

**Updated API Call (Line 15-18):**
```python
self.client = chromadb.PersistentClient(
    path="/app/backend/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)
```

**Why This Matters:**
- ChromaDB 1.1.1+ requires `PersistentClient` instead of `Client(Settings(persist_directory=...))`
- Ensures ChromaDB stores data in `/app/backend/chroma_db`
- Creates SQLite database file in the correct location

---

## 5. Run Script Configuration (`/app/run.sh`)

### 5.1 Virtual Environment Creation (Lines 392-404)

**Priority Order:**
1. `$SCRIPT_DIR/.venv` (i.e., `/app/.venv`) ✅ **Preferred**
2. `/root/.venv` (fallback)
3. `$HOME/.venv` (fallback)
4. `/tmp/rag-platform-venv` (last resort)

**Code:**
```bash
if [ -z "$VENV_PATH" ]; then
    # Try to create in script directory first
    if [ -w "$SCRIPT_DIR" ]; then
        VENV_PATH="$SCRIPT_DIR/.venv"
    elif [ -w "/root" ]; then
        VENV_PATH="/root/.venv"
    # ... other fallbacks
fi
```

### 5.2 Directory Creation (Lines 357-362)

**Creates all necessary directories:**
```bash
mkdir -p "$SCRIPT_DIR/files"
mkdir -p "$SCRIPT_DIR/backend/chroma_db"
mkdir -p "$SCRIPT_DIR/frontend/build"
mkdir -p "$SCRIPT_DIR/tests"
mkdir -p "$SCRIPT_DIR/.cache/huggingface"
mkdir -p "$SCRIPT_DIR/.cache/sentence_transformers"
```

### 5.3 Backend .env Creation (Lines 685-705)

**Includes cache environment variables:**
```bash
cat > "$SCRIPT_DIR/backend/.env" << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"
CORS_ORIGINS="*"

# Cache directories (keep everything within /app)
HF_HOME="$SCRIPT_DIR/.cache/huggingface"
TRANSFORMERS_CACHE="$SCRIPT_DIR/.cache/huggingface"
SENTENCE_TRANSFORMERS_HOME="$SCRIPT_DIR/.cache/sentence_transformers"
EOF
```

### 5.4 Supervisor Configuration Generation (Lines 840-855)

**Includes cache environment variables:**
```bash
environment=PATH="$VENV_PATH/bin:%(ENV_PATH)s",HF_HOME="$SCRIPT_DIR/.cache/huggingface",TRANSFORMERS_CACHE="$SCRIPT_DIR/.cache/huggingface",SENTENCE_TRANSFORMERS_HOME="$SCRIPT_DIR/.cache/sentence_transformers"
```

---

## 6. Verification Commands

### 6.1 Check Directory Structure
```bash
# Verify virtual environment location
ls -d /app/.venv
# Expected: /app/.venv

# Verify cache directories
ls -d /app/.cache/huggingface /app/.cache/sentence_transformers
# Expected: Both directories exist

# Verify ChromaDB location
ls -d /app/backend/chroma_db
# Expected: /app/backend/chroma_db

# Check database file
ls -lh /app/backend/chroma_db/chroma.sqlite3
# Expected: SQLite database file (e.g., 236KB)
```

### 6.2 Check Services
```bash
# Service status
sudo supervisorctl status

# Backend health
curl http://localhost:8001/api/

# Document status
curl http://localhost:8001/api/documents/status

# Frontend
curl http://localhost:3000 | head -c 200
```

### 6.3 Check Logs
```bash
# Backend logs (should have no errors)
tail -50 /var/log/supervisor/backend.err.log

# Frontend logs (should have no errors)
tail -50 /var/log/supervisor/frontend.out.log
```

### 6.4 Check Environment Variables
```bash
# Verify backend uses correct cache paths
grep -E "HF_HOME|TRANSFORMERS_CACHE|SENTENCE_TRANSFORMERS" /app/backend/.env

# Verify supervisor uses correct paths
grep "HF_HOME" /etc/supervisor/conf.d/supervisord.conf
```

---

## 7. Maintenance and Troubleshooting

### 7.1 Restart Services
```bash
# Restart all services
sudo supervisorctl restart all

# Restart individual services
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### 7.2 Clear Caches (if needed)
```bash
# Clear model cache (will redownload on next start)
rm -rf /app/.cache/huggingface/*
rm -rf /app/.cache/sentence_transformers/*

# Restart backend to redownload models
sudo supervisorctl restart backend
```

### 7.3 Reset Vector Database (if needed)
```bash
# Stop backend
sudo supervisorctl stop backend

# Clear ChromaDB
rm -rf /app/backend/chroma_db/*

# Restart backend (will reindex documents)
sudo supervisorctl start backend
```

### 7.4 Recreate Virtual Environment (if needed)
```bash
# Stop services
sudo supervisorctl stop backend frontend

# Remove old venv
rm -rf /app/.venv

# Rerun setup script
cd /app && ./run.sh
```

---

## 8. Migration from Old Configuration

If you have an existing setup with files in `/root/.venv` or `/root/.cache`, follow these steps:

### 8.1 Stop Services
```bash
sudo supervisorctl stop backend frontend
```

### 8.2 Move Virtual Environment
```bash
# Move venv
mv /root/.venv /app/.venv

# Fix shebang paths in all scripts
find /app/.venv/bin -type f -exec sed -i 's|#!/root/.venv/bin/python|#!/app/.venv/bin/python|g' {} \;

# Fix activate script
sed -i 's|/root/.venv|/app/.venv|g' /app/.venv/bin/activate

# Fix pyvenv.cfg
sed -i 's|/root/.venv|/app/.venv|g' /app/.venv/pyvenv.cfg
```

### 8.3 Move Cache
```bash
# Create cache directory
mkdir -p /app/.cache

# Move HuggingFace cache
mv /root/.cache/huggingface /app/.cache/

# Move Sentence Transformers cache (if exists)
[ -d /root/.cache/sentence_transformers ] && mv /root/.cache/sentence_transformers /app/.cache/
```

### 8.4 Update Configuration
```bash
# Update backend .env
cat >> /app/backend/.env << 'EOF'

# Cache directories (keep everything within /app)
HF_HOME="/app/.cache/huggingface"
TRANSFORMERS_CACHE="/app/.cache/huggingface"
SENTENCE_TRANSFORMERS_HOME="/app/.cache/sentence_transformers"
EOF

# Update supervisor config
sudo sed -i 's|/root/.venv|/app/.venv|g' /etc/supervisor/conf.d/supervisord.conf
```

### 8.5 Reload and Restart
```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Restart services
sudo supervisorctl restart all
```

---

## 9. Best Practices

### 9.1 Always Use run.sh for Fresh Setups
The `run.sh` script is configured to maintain this organization. Always use it for:
- Fresh installations
- Setting up new environments
- Recreating the environment after major changes

### 9.2 Check Paths After Updates
After any system updates or package installations, verify:
```bash
# Check venv location
which python
# Should output: /app/.venv/bin/python

# Check cache usage
du -sh /app/.cache/*
# Should show model sizes in /app/.cache/
```

### 9.3 Monitor Disk Usage
```bash
# Check total /app size
du -sh /app

# Break down by component
du -sh /app/.venv /app/.cache /app/frontend/node_modules /app/backend/chroma_db
```

---

## 10. Summary

✅ **All application files are within `/app`**
- Virtual environment: `/app/.venv`
- Model cache: `/app/.cache`
- Vector database: `/app/backend/chroma_db`
- Frontend dependencies: `/app/frontend/node_modules`
- Documents: `/app/files`

✅ **Configuration is permanent**
- Backend .env includes cache paths
- Supervisor config uses correct paths
- run.sh script maintains this organization
- Git ignores generated files

✅ **System services remain in standard locations**
- MongoDB: System service
- Supervisor: System service
- Logs: `/var/log/supervisor/`

This configuration ensures portability, maintainability, and clean separation between application files and system services.
