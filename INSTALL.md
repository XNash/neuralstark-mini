# 🚀 NeuralStark - Installation Guide

This guide will help you set up the NeuralStark on any clean Linux environment.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Supported Operating Systems](#supported-operating-systems)
- [Manual Installation](#manual-installation)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)

## ⚡ Quick Start

For a fully automated installation on a clean Linux system:

```bash
# Clone or download the repository
git clone <repository-url>
cd rag-platform

# Run the automated setup script
chmod +x run.sh
./run.sh
```

The script will:
- Detect your Linux distribution
- Install all system dependencies
- Set up Python virtual environment
- Install backend and frontend dependencies
- Configure MongoDB
- Set up and start all services
- Create sample documents

**That's it!** The platform will be accessible at `http://localhost:3000`

## 💻 System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+, Fedora 30+)
- **CPU**: 2 cores (4 recommended)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 10GB free space
- **Network**: Internet connection for initial setup

### Software Dependencies (Auto-installed)
The `run.sh` script automatically installs:
- Python 3.8+
- Node.js 20.x
- MongoDB 7.0
- Yarn package manager
- Supervisor process manager
- Tesseract OCR
- Poppler utilities

## 🐧 Supported Operating Systems

### Tested and Supported
- ✅ Ubuntu 18.04, 20.04, 22.04, 24.04
- ✅ Debian 10, 11, 12
- ✅ CentOS 7, 8
- ✅ RHEL 7, 8, 9
- ✅ Fedora 30+
- ✅ Pop!_OS 20.04+

### Likely Compatible
- ✅ Linux Mint
- ✅ Elementary OS
- ✅ Arch Linux (with manual adjustments)
- ✅ openSUSE

## 🔧 Manual Installation

If you prefer to install dependencies manually or the automated script doesn't work:

### Step 1: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y build-essential wget curl git
sudo apt-get install -y python3 python3-pip python3-venv python3-dev
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra poppler-utils
sudo apt-get install -y supervisor

# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt-get update
sudo apt-get install -y yarn

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### CentOS/RHEL/Fedora
```bash
# Use dnf on Fedora, yum on older systems
sudo dnf install -y epel-release  # or yum
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3 python3-pip python3-devel
sudo dnf install -y tesseract tesseract-langpack-eng tesseract-langpack-fra poppler-utils
sudo dnf install -y supervisor

# Install Node.js 20.x
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Install Yarn
sudo npm install -g yarn

# Install MongoDB
cat <<EOF | sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF
sudo dnf install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Step 2: Set Up Python Environment

```bash
cd /path/to/rag-platform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install backend dependencies
cd backend
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
pip install -r requirements.txt
cd ..
```

### Step 3: Install Frontend Dependencies

```bash
cd frontend
yarn install
cd ..
```

### Step 4: Configure Environment

Create `backend/.env`:
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"
CORS_ORIGINS="*"
```

Create `frontend/.env`:
```bash
REACT_APP_BACKEND_URL="http://localhost:8001"
WDS_SOCKET_PORT=443
```

### Step 5: Set Up Supervisor

Create `/etc/supervisor/conf.d/rag-backend.conf`:
```ini
[program:backend]
command=/path/to/rag-platform/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=/path/to/rag-platform/backend
user=your-username
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile=/var/log/supervisor/backend.err.log
```

Create `/etc/supervisor/conf.d/rag-frontend.conf`:
```ini
[program:frontend]
command=/usr/bin/yarn start
directory=/path/to/rag-platform/frontend
user=your-username
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/frontend.out.log
stderr_logfile=/var/log/supervisor/frontend.err.log
```

### Step 6: Start Services

```bash
sudo systemctl restart supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## 🐛 Troubleshooting

### MongoDB Not Starting

**Problem**: MongoDB service fails to start

**Solutions**:
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Create data directory if missing
sudo mkdir -p /data/db
sudo chown -R mongodb:mongodb /data/db

# Start manually
sudo mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db
```

### Backend Not Starting

**Problem**: Backend service fails to start

**Solutions**:
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Common issues:
# 1. Virtual environment not activated
source /path/to/.venv/bin/activate

# 2. Missing dependencies
cd backend
pip install -r requirements.txt

# 3. Port already in use
sudo lsof -i :8001
# Kill the process using the port

# 4. MongoDB connection failed
# Ensure MongoDB is running and MONGO_URL in .env is correct
```

### Frontend Not Starting

**Problem**: Frontend service fails to start

**Solutions**:
```bash
# Check frontend logs
tail -f /var/log/supervisor/frontend.out.log

# Common issues:
# 1. Node modules not installed
cd frontend
yarn install

# 2. Port already in use
sudo lsof -i :3000

# 3. Clear cache and reinstall
rm -rf node_modules yarn.lock
yarn install
```

### Documents Not Indexing

**Problem**: Documents placed in `/files` directory are not being indexed

**Solutions**:
```bash
# Check if watchdog is running
ps aux | grep python | grep server

# Check backend logs for errors
tail -f /var/log/supervisor/backend.err.log

# Manually trigger reindexing via API
curl -X POST http://localhost:8001/api/documents/reindex

# Or via the web UI: Settings → Reindex Documents button
```

### Permission Denied Errors

**Problem**: Permission errors when running the script or accessing files

**Solutions**:
```bash
# Ensure you have sudo privileges
sudo -v

# Fix file permissions
cd /path/to/rag-platform
chmod +x run.sh
chmod -R 755 backend frontend files

# Fix log directory permissions
sudo chown -R $USER:$USER /var/log/supervisor/
```

### OCR Not Working

**Problem**: PDF documents with images are not being processed

**Solutions**:
```bash
# Install Tesseract language packs
sudo apt-get install tesseract-ocr-eng tesseract-ocr-fra

# Verify Tesseract installation
tesseract --version
tesseract --list-langs

# Install poppler-utils for PDF processing
sudo apt-get install poppler-utils
```

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# MongoDB connection string
MONGO_URL="mongodb://localhost:27017"

# Database name
DB_NAME="rag_platform"

# CORS origins (comma-separated for multiple origins)
CORS_ORIGINS="*"
```

### Frontend Configuration (`frontend/.env`)

```bash
# Backend API URL
REACT_APP_BACKEND_URL="http://localhost:8001"

# WebSocket port for hot reload
WDS_SOCKET_PORT=443
```

### Gemini API Key

The Gemini API key is configured through the web interface:

1. Open the frontend at `http://localhost:3000`
2. Navigate to the **Settings** page
3. Enter your Gemini API key
4. Click **Save API Key**

Get your API key from: [Google AI Studio](https://aistudio.google.com/app/apikey)

### Document Directory

Place your documents in the `/files` directory. Supported formats:
- PDF (`.pdf`)
- Word (`.doc`, `.docx`)
- Excel (`.xls`, `.xlsx`)
- Text (`.txt`, `.md`)
- JSON (`.json`)
- CSV (`.csv`)
- OpenDocument (`.odt`)

Documents are automatically indexed within 5 seconds of being added.

## 🔄 Updating the Platform

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies
./run.sh

# Or manually:
source .venv/bin/activate
cd backend && pip install -r requirements.txt && cd ..
cd frontend && yarn install && cd ..

# Restart services
sudo supervisorctl restart all
```

## 🛡️ Security Considerations

For production deployments:

1. **Change MongoDB credentials**:
   ```bash
   MONGO_URL="mongodb://username:password@localhost:27017"
   ```

2. **Set specific CORS origins**:
   ```bash
   CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
   ```

3. **Use HTTPS**: Set up a reverse proxy (nginx/Apache) with SSL
4. **Secure API keys**: Never commit `.env` files to version control
5. **Firewall rules**: Restrict access to MongoDB (port 27017)
6. **Regular updates**: Keep all dependencies up to date

## 📞 Support

For issues not covered in this guide:

1. Check the main [README.md](README.md) for feature documentation
2. Review backend logs: `/var/log/supervisor/backend.err.log`
3. Review frontend logs: `/var/log/supervisor/frontend.out.log`
4. Check MongoDB logs: `/var/log/mongodb/mongod.log`

## 📝 License

See the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for intelligent document interaction**
