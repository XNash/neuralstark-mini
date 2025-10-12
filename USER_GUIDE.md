# RAG Platform - Complete User Guide

## 🎯 For Users Cloning from GitHub

This guide ensures you get a **100% working installation** on any Linux system (Ubuntu, Pop_OS, Debian, CentOS, RHEL, Fedora).

---

## 🚀 Quick Start (2 Commands)

```bash
# 1. Clone and enter directory
git clone https://github.com/your-username/rag-platform.git
cd rag-platform

# 2. Run the complete setup
chmod +x complete-setup.sh
./complete-setup.sh
```

That's it! The script does everything automatically.

---

## 📋 What Gets Installed

### System Requirements (Auto-Detected)
- **Python 3.9+** (3.10, 3.11, 3.12, 3.13 all supported)
- **Node.js 18+** 
- **MongoDB 7.0+**
- **Supervisor** for service management

### Python Packages (Auto-Installed)
- **FastAPI** - Web framework
- **Google Generative AI** - Gemini API client  
- **ChromaDB** - Vector database
- **Sentence Transformers** - Text embeddings
- **LangChain** - RAG framework
- **Document Processors** - PDF, Word, Excel, ODT support
- **OCR** - Tesseract for scanned documents
- **File Monitoring** - Auto-reindex on file changes

### Frontend Packages (Auto-Installed)
- **React 18** - UI framework
- **Tailwind CSS** - Styling
- All required dependencies

---

## 🔧 Installation Methods

### Method 1: Complete Automated Setup (Recommended)

```bash
./complete-setup.sh
```

This script:
- ✅ Checks Python version compatibility
- ✅ Creates/activates virtual environment
- ✅ Installs ALL dependencies with retries
- ✅ Verifies every package import
- ✅ Tests backend modules
- ✅ Updates requirements.txt
- ✅ Checks/starts MongoDB
- ✅ Restarts services
- ✅ Tests backend API
- ✅ Provides detailed summary

**Time:** 3-5 minutes

### Method 2: Standard Setup

```bash
./post-clone-setup.sh  # Initial configuration
./run.sh                # Full setup and start
```

**Time:** 5-10 minutes (downloads and installs everything)

### Method 3: Manual Setup (Advanced)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
yarn install

# Configure environment
cd ..
./post-clone-setup.sh

# Start services
./run.sh
```

---

## ✅ Verification

### Check if Everything Works

```bash
# 1. Check service status
sudo supervisorctl status

# Expected output:
# backend    RUNNING   pid 1234, uptime 0:01:23
# frontend   RUNNING   pid 1235, uptime 0:01:23
# mongodb    RUNNING   pid 1236, uptime 0:01:23

# 2. Test backend API
curl http://localhost:8001/api/

# Expected output:
# {"message":"RAG Platform API","status":"running"}

# 3. Check document indexing
curl http://localhost:8001/api/documents/status

# Expected output:
# {"total_documents":3,"indexed_documents":6,"last_updated":"..."}

# 4. Open frontend
# Visit: http://localhost:3000
```

---

## 🎮 Using the Application

### Step 1: Access the Application

Open your browser and go to:
```
http://localhost:3000
```

You'll see the RAG Platform interface with:
- **Chat Page** - Main conversation interface
- **Documents Page** - View indexing status
- **Settings Page** - Configure API key

### Step 2: Configure API Key

1. Click **Settings** in the sidebar
2. Enter your **Gemini API Key**
3. Click **Save API Key**

**Get your API key here:** https://aistudio.google.com/app/apikey

### Step 3: Add Documents

Place your documents in the `files/` directory:

```bash
cp /path/to/your/document.pdf files/
cp /path/to/your/spreadsheet.xlsx files/
cp /path/to/your/text-file.txt files/
```

**Supported formats:**
- PDF (.pdf) - with OCR for scanned documents
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- OpenDocument (.odt)
- Text (.txt, .md)
- Data (.json, .csv)

Documents are automatically indexed within 5 seconds!

### Step 4: Start Chatting

1. Go to the **Chat** page
2. Type your question in the input box
3. Press Enter or click Send
4. Get AI-powered answers based on your documents!

**Example questions:**
- "What are the company's main products?"
- "Summarize the pricing information"
- "What is the refund policy?"

---

## 🔧 Managing Services

### View Service Status

```bash
sudo supervisorctl status
```

### Restart Services

```bash
# Restart all services
sudo supervisorctl restart all

# Restart specific service
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### View Logs

```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log

# MongoDB logs
sudo journalctl -u mongod -f
```

### Stop Services

```bash
sudo supervisorctl stop all
```

### Start Services

```bash
sudo supervisorctl start all
```

---

## 🐛 Troubleshooting

### Problem: "Backend not responding"

**Solution:**
```bash
# Check backend logs
tail -50 /var/log/supervisor/backend.err.log

# Common issue: Missing packages
cd /path/to/rag-platform
source .venv/bin/activate
pip install -r backend/requirements.txt

# Restart backend
sudo supervisorctl restart backend
```

### Problem: "Port already in use"

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :8001  # Backend
sudo lsof -i :3000  # Frontend

# Kill the process or change ports in supervisor config
```

### Problem: "MongoDB connection failed"

**Solution:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Enable MongoDB on boot
sudo systemctl enable mongod

# Test connection
mongosh --eval 'db.adminCommand("ping")'
```

### Problem: "Import errors" or "Module not found"

**Solution:**
```bash
# Run the complete setup script
./complete-setup.sh

# This will:
# - Install all missing packages
# - Verify all imports
# - Fix any issues
```

### Problem: "Frontend won't start"

**Solution:**
```bash
cd frontend

# Check if node_modules exists
ls node_modules

# If not, install dependencies
yarn install

# Restart frontend
sudo supervisorctl restart frontend
```

### Problem: "Documents not indexing"

**Solution:**
```bash
# 1. Check if files exist
ls -la files/

# 2. Check backend logs for errors
tail -30 /var/log/supervisor/backend.err.log

# 3. Trigger manual reindex via UI
# Go to Documents page → Click "Reindex Documents"

# 4. Or via API
curl -X POST http://localhost:8001/api/documents/reindex
```

---

## 🔐 Security Notes

### API Keys

- **Never commit API keys to git**
- API keys are stored in MongoDB (encrypted)
- Can be updated anytime via Settings page

### File Permissions

```bash
# Ensure proper ownership
sudo chown -R $USER:$USER /path/to/rag-platform

# Make scripts executable
chmod +x *.sh
```

---

## 📊 Performance Tips

### For Large Document Collections

1. **Increase Chunk Size** (edit `backend/document_processor.py`):
   ```python
   chunk_size = 1000  # Default: 800
   ```

2. **Adjust Vector Search Results** (edit `backend/rag_service.py`):
   ```python
   n_results=10  # Default: 8
   ```

3. **Use SSD** for ChromaDB storage for faster indexing

### For Better Accuracy

1. **Lower Relevance Threshold** (edit `backend/rag_service.py`):
   ```python
   self.relevance_threshold = 0.2  # Default: 0.3
   ```

2. **Add More Context** - Include related documents

3. **Use Better Prompts** - Be specific in your questions

---

## 🔄 Updating the Application

### Pull Latest Changes

```bash
cd /path/to/rag-platform
git pull origin main

# Reinstall dependencies if needed
./complete-setup.sh

# Restart services
sudo supervisorctl restart all
```

---

## 🌍 Multi-Instance Setup

You can run multiple independent instances:

```bash
# Instance 1
git clone <repo> ~/rag-platform-personal
cd ~/rag-platform-personal
./complete-setup.sh

# Instance 2 (different directory)
git clone <repo> ~/rag-platform-work
cd ~/rag-platform-work
./complete-setup.sh
```

Each instance:
- Has its own virtual environment
- Uses its own MongoDB collections
- Runs on different ports (configure in supervisor)
- Is completely independent

---

## 📚 Additional Resources

- **GitHub Setup Guide:** [GITHUB_SETUP.md](GITHUB_SETUP.md)
- **Portability Details:** [PORTABILITY_CHANGES.md](PORTABILITY_CHANGES.md)
- **API Documentation:** See backend code comments
- **Testing:** Run `./test-portability.sh`

---

## 💡 Pro Tips

1. **Backup Your Data**
   ```bash
   # Backup MongoDB
   mongodump --out backup/

   # Backup documents
   tar -czf documents-backup.tar.gz files/
   ```

2. **Monitor Performance**
   ```bash
   # Watch service status
   watch -n 2 'sudo supervisorctl status'

   # Monitor resources
   htop
   ```

3. **Clean Reinstall**
   ```bash
   # Remove virtual environment
   rm -rf .venv

   # Remove node modules
   rm -rf frontend/node_modules

   # Reinstall everything
   ./complete-setup.sh
   ```

---

## 🤝 Getting Help

1. **Check Logs First**
   ```bash
   tail -100 /var/log/supervisor/backend.err.log
   ```

2. **Run Verification**
   ```bash
   ./complete-setup.sh
   ```

3. **Check GitHub Issues**
   - Search for similar problems
   - Create new issue with details

4. **Provide Information**
   - OS version: `cat /etc/os-release`
   - Python version: `python3 --version`
   - Error logs
   - Steps to reproduce

---

## 📄 License

[Your License Here]

---

**Enjoy your RAG Platform! 🚀📚💬**

For questions or issues, please open a GitHub issue.
